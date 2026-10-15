"""Prepare one frozen Motion31 source rollout; no simulation/authorization on prepare."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from native_stand.students.motion_advantage_probe import declaration, validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input, digest, publish


def prepare(parent, *, session, write=False):
    parent=Path(parent).resolve(); spec=json.loads(parent.read_text())
    inputs=dict([checked_input(parent)])
    for k,path in [('source_sha256',spec['source_checkpoint']),('asset_sha256',spec['asset_path'])]:
        inputs.update([checked_input(path,spec[k])])
    name=new_experiment_name('motion31_u1600_frozen_advantage_probe')
    root=Path(__file__).resolve().parents[1]; output=root/'configs/experiments'/name
    spec.update(experiment=name,evaluation_only=True,motion_advantage_probe=declaration(parent,digest(parent)),
        execution_source_root=str(root/'src'),notifications={'enabled':False},
        authorization={'status':'UNAUTHORIZED','hapi_session':session,'user_scope':'frozen source diagnostic, no optimizer'})
    spec['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,
        sample_limit=0,formal_samples=0,evaluation_wall_s=600,chain_wall_s=600)
    spec['artifacts']['run_name']=name
    validate(spec)
    book={'authorization':'UNAUTHORIZED','experiment':name,'hapi_session':session,
        'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0,'play':0},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0,'play':0},'attempts':{},'sample_limit':0}
    js=lambda obj:hashlib.sha256((json.dumps(obj,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    approval={'approval_id':name+'__approved_ppo0','user_scope':'User agrees next step: one frozen source1600 rollout, no optimizer; GPU0 inherited shared permission;600s/128MiB',
        'session':session,'physical_gpu':spec['device']['physical_index'],'gpu_uuid':spec['device']['uuid'],
        'max_online_updates':0,'max_phase_wall_s':600,
        'arms':[{'spec':str(output/'spec.json'),'spec_sha256':js(spec),'budget_sha256':js(book)}]}
    report={'name':name,'output':str(output),'run':str(root/'runs'/name),'simulation':0,
        'optimizer_updates':0,'inputs_sha256':inputs,'approval_request':approval,'probe':spec['motion_advantage_probe']}
    if write:publish(output,{'spec.json':spec,'budget.json':book,'preparation_manifest.json':report},inputs,completion_marker=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.parent_spec,session=a.session,write=a.write),indent=2))
