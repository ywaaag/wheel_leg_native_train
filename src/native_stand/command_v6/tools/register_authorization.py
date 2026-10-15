"""Explicit fresh-declaration authorization registration; zero-write plan, never submit."""
import argparse
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from ..config import validate
from .experiment_preparation import checked_input,verify_publication


def plan(request,*,current_session):
    required={'approval_id','user_scope','session','physical_gpu','gpu_uuid','max_online_updates','max_phase_wall_s','arms'}
    if not isinstance(request,dict) or set(request)!=required:raise ValueError('authorization request schema differs')
    if (any(not isinstance(request[k],str) or not request[k].strip() for k in ('approval_id','user_scope','session'))
            or request['session']!=current_session or not current_session):
        raise ValueError('explicit approval scope and matching current session required')
    if type(request['physical_gpu']) is not int or request['physical_gpu'] not in (0,1) or not str(request['gpu_uuid']).startswith('GPU-'):
        raise ValueError('explicit GPU identity required')
    if type(request['max_online_updates']) is not int or request['max_online_updates']<0:raise ValueError('invalid inclusive update approval')
    if request['max_phase_wall_s'] is not None and (type(request['max_phase_wall_s']) not in (int,float) or not math.isfinite(request['max_phase_wall_s']) or request['max_phase_wall_s']<=0):
        raise ValueError('finite aggregate phase wall ceiling required')
    if not isinstance(request['arms'],list) or not request['arms']:raise ValueError('explicit arms required')
    result=[];seen=set();total=0;wall=0.
    for arm in request['arms']:
        if set(arm)!={'spec','spec_sha256','budget_sha256'}:raise ValueError('arm must bind spec and budget SHA')
        path=Path(arm['spec']).resolve();ledger=path.with_name('budget.json')
        project=Path(__file__).resolve().parents[4]
        from native_stand.students.course_requests import project_root_for
        project=project_root_for(json.loads(path.read_text()),project)
        if not path.is_relative_to(project/'configs/experiments'):raise ValueError('authorization only for this project declarations')
        if path in seen:raise ValueError('duplicate arm')
        seen.add(path);checked_input(path,arm['spec_sha256']);checked_input(ledger,arm['budget_sha256'])
        spec=json.loads(path.read_text());book=json.loads(ledger.read_text())
        from ..domain.execution_limits import validate_budget,ExecutionLimits
        if spec.get('ppo'):validate_budget(spec)
        if book.get('authorization')!='UNAUTHORIZED' or book.get('attempts') or any(book.get('used',{}).values()):
            raise ValueError('fresh unused UNAUTHORIZED ledger required')
        if path.with_name('chain_submission.json').exists() or path.with_name('authorization_receipt.json').exists():
            raise ValueError('declaration already submitted/authorized')
        verify_publication(path)
        for phase in ('smoke','formal'):
            limit=book['limits'].get(phase,0)
            if type(limit) is not int or limit<0 or limit!=spec['budget'].get(phase+'_updates',0):
                raise ValueError('spec/ledger online budget differs')
            total+=limit
        for phase in ('source_eval','smoke','formal','evaluate'):
            if book['limits'].get(phase,0):
                value=spec['budget'].get('evaluation_wall_s' if phase=='evaluate' else phase+'_wall_s')
                if value is None and phase in ('smoke','formal') and request['max_phase_wall_s'] is None:
                    ExecutionLimits.resolve(spec,phase)
                    continue
                if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
                    raise ValueError('authorized phase needs finite wall budget')
                wall+=value
        if spec.get('ppo'):
            expected=(book['limits'].get('smoke',0)+book['limits'].get('formal',0))*spec['ppo']['envs']*spec['ppo']['steps_per_env']
            if spec['budget'].get('sample_limit')!=expected:raise ValueError('inclusive update/sample declaration differs')
        spec=copy.deepcopy(spec);book=copy.deepcopy(book)
        spec['authorization']={'status':'AUTHORIZED','hapi_session':current_session,'user_scope':request['user_scope'],'approval_id':request['approval_id']}
        spec['device']={'physical_index':request['physical_gpu'],'uuid':request['gpu_uuid'],'logical':'cuda:0','headless':True}
        book.update(authorization='AUTHORIZED',hapi_session=current_session,authorization_evidence=request['user_scope'],approval_id=request['approval_id'])
        errors=validate(spec)
        if errors:raise ValueError(errors)
        result.append({'path':path,'ledger':ledger,'spec':spec,'budget':book,'before_spec_sha256':arm['spec_sha256'],'before_budget_sha256':arm['budget_sha256']})
    if total>request['max_online_updates']:raise ValueError('all-arm inclusive updates exceed approved maximum')
    if request['max_phase_wall_s'] is not None and wall>request['max_phase_wall_s']:raise ValueError('all-arm phase wall budgets exceed approval')
    return result,total


def register(request,*,current_session,write=False):
    arms,total=plan(request,current_session=current_session)
    report={'approval_id':request['approval_id'],'online_updates_all_arms':total,'files_written':0,
        'simulation':0,'submitted':False,'arms':[{'spec':str(a['path']),'before_spec_sha256':a['before_spec_sha256']} for a in arms]}
    if not write:return report
    handles=[];originals={};written=[]
    try:
        for arm in sorted(arms,key=lambda a:str(a['ledger'])):
            handle=arm['ledger'].with_suffix('.lock').open('a+');fcntl.flock(handle,fcntl.LOCK_EX);handles.append(handle)
        arms,total=plan(request,current_session=current_session)
        for arm in arms:
            for path,payload in ((arm['path'],arm['spec']),(arm['ledger'],arm['budget'])):
                originals[path]=path.read_bytes()
                fd,name=tempfile.mkstemp(prefix='.authorization-',dir=path.parent)
                try:
                    with os.fdopen(fd,'w') as stream:json.dump(payload,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
                    os.replace(name,path);written.append(path)
                finally:
                    if os.path.exists(name):os.unlink(name)
        for arm in arms:
            receipt=arm['path'].with_name('authorization_receipt.json')
            payload={**report,'user_scope':request['user_scope'],'session':current_session,
                'spec_sha256':hashlib.sha256(arm['path'].read_bytes()).hexdigest(),
                'budget_sha256':hashlib.sha256(arm['ledger'].read_bytes()).hexdigest(),
                'status':'REGISTERED_NOT_SUBMITTED'}
            with receipt.open('x') as stream:written.append(receipt);json.dump(payload,stream,indent=2)
        report['files_written']=3*len(arms)
        return report
    except BaseException:
        for path in reversed(written):
            if path in originals:path.write_bytes(originals[path])
            else:path.unlink()
        raise
    finally:
        for handle in reversed(handles):handle.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True)
    p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(register(json.loads(a.request.read_text()),current_session=os.environ.get('HAPI_SESSION_ID'),write=a.write),indent=2))


if __name__=='__main__':main()
