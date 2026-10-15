"""Prepare one restricted v14 storage-fault continuation; never launch."""
import argparse,copy,json,os
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.storage_resume import VERSION,RETRY_VERSION,verify
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]

def prepare(parent,write=False):
 parent=Path(parent).resolve();old=json.loads(parent.read_text());book=json.loads(parent.with_name('budget.json').read_text())
 formal=[r for r in book['attempts'].values() if r['phase']=='formal']
 if len(formal)!=1:raise ValueError('exact parent formal attempt required')
 folder=Path(formal[0]['output_dir']);n=formal[0]['updates'];cp=folder/f'model_update_{n}.pt'
 used=book['used']['formal']+book['used']['smoke'];total=book['limits']['formal']+book['limits']['smoke'];remaining=total-used
 if remaining<=0:raise ValueError('original budget exhausted')
 inputs={str(p):sha(p) for p in (parent,parent.with_name('budget.json'),folder/'terminal_report.json',cp)}
 for row in book['attempts'].values():
  if row['phase']=='smoke':
   smoke=Path(row['output_dir']);inputs[str(smoke/'wiring_certificate.json')]=sha(smoke/'wiring_certificate.json')
   cert=json.loads((smoke/'wiring_certificate.json').read_text())
   inputs.update({str(smoke/p):h for p,h in cert['inputs'].items()})
 name=new_experiment_name('standing034_v14_storage_resume');target=ROOT/'configs/experiments'/name;s=copy.deepcopy(old)
 s.update(experiment=name,source_checkpoint=str(cp),source_sha256=sha(cp),authorization={'status':'UNAUTHORIZED','hapi_session':os.environ.get('HAPI_SESSION_ID'),'user_scope':'fresh recovery publication; runtime requires explicit registration'},
  student_storage_resume={'version':VERSION,'parent_spec':str(parent),'inputs':inputs,'parent_formal_updates':n,'historical_online_updates':used,'original_online_limit':total,'rng_semantics':'restore_if_present_else_explicit_seed_reset'})
 s['artifacts']['run_name']=name;s['student_training']['source_actor_sha256']=sha(cp)
 s['student_training']['milestones']=sorted(set(list(range(100,remaining+1,100))+[remaining]))
 s['budget'].update(smoke_updates=0,formal_updates=remaining,sample_limit=remaining*8192,formal_samples=remaining*8192)
 s['student_dependencies'].update(inputs)
 for row in s['student_evaluation']['cases']:row.update(checkpoint=str(cp),sha256=sha(cp))
 verify(s);errors=validate(s)
 if errors:raise ValueError(errors)
 newbook={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':0,'formal':remaining,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':remaining,
  'historical_consumption_reference':{'ledger':str(parent.with_name('budget.json')),'sha256':sha(parent.with_name('budget.json')),'online_updates':used,'original_limit':total}}
 result={'spec':str(target/'spec.json'),'run':str(ROOT/'runs'/name),'parent_formal_updates':n,'historical_online_updates':used,'remaining_updates':remaining,'source_sha256':sha(cp),'simulation':0,'ppo':0,'files_written':0}
 if write:
  claims=ROOT/'configs/experiments/.student_storage_resume_publications';claims.mkdir(exist_ok=True)
  claim=claims/(sha(parent)+'.json')
  with claim.open('x') as stream:json.dump({'parent_spec':str(parent),'destination':str(target),'parent_ledger_sha256':sha(parent.with_name('budget.json'))},stream)
  publish(target,{'spec.json':s,'budget.json':newbook,'preparation.json':result},s['student_dependencies'],completion_marker=True);result['files_written']=5
 return result

def retry(parent,write=False):
 parent=Path(parent).resolve();old=json.loads(parent.read_text());book=json.loads(parent.with_name('budget.json').read_text())
 attempts=list(book['attempts'].values())
 if len(attempts)!=1 or attempts[0]['phase']!='source_eval' or attempts[0]['status']!='COMPLETED':raise ValueError('exact completed source-only attempt required')
 folder=Path(attempts[0]['output_dir']);s=copy.deepcopy(old);name=new_experiment_name('standing034_v14_resume_statefix');target=ROOT/'configs/experiments'/name
 s.update(experiment=name,authorization={'status':'UNAUTHORIZED','hapi_session':os.environ.get('HAPI_SESSION_ID'),'user_scope':'new retry needs explicit registration'})
 s['artifacts']['run_name']=name;c=s['student_storage_resume'];c.update(version=RETRY_VERSION,retry_spec=str(parent),source_eval_dir=str(folder))
 paths=[parent,parent.with_name('budget.json'),folder.parent/'chain_terminal_report.json',*[folder/n for n in ('manifest.json','terminal_report.json','progress.json','candidate_registry.json','source_snapshot/spec.json')]]
 for record in json.loads((folder/'terminal_report.json').read_text())['evaluations']:
  raw=folder/record['path'];paths.append(raw);paths.append(folder/json.loads(raw.read_text())['trace']['path'])
 c['inputs'].update({str(p):sha(p) for p in paths});s['student_dependencies'].update(c['inputs']);verify(s)
 errors=validate(s)
 if errors:raise ValueError(errors)
 b=copy.deepcopy(book);b.update(authorization='UNAUTHORIZED',experiment=name,attempts={},used={k:0 for k in book['used']},source_eval_wall_used_s=0.)
 for k in ('hapi_session','authorization_evidence','approval_id'):b.pop(k,None)
 b['historical_retry_reference']={'ledger':str(parent.with_name('budget.json')),'sha256':sha(parent.with_name('budget.json')),'online_updates':0,'source_eval_wall_s':book['source_eval_wall_used_s']}
 result={'spec':str(target/'spec.json'),'run':str(ROOT/'runs'/name),'source_reused':str(folder),'remaining_updates':s['budget']['formal_updates'],'historical_online_updates':c['historical_online_updates'],'simulation':0,'ppo':0,'files_written':0}
 if write:
  claims=ROOT/'configs/experiments/.student_storage_resume_retry_publications';claims.mkdir(exist_ok=True)
  with (claims/(sha(parent)+'.json')).open('x') as f:json.dump({'destination':str(target),'retry_spec':str(parent)},f)
  publish(target,{'spec.json':s,'budget.json':b,'preparation.json':result},s['student_dependencies'],completion_marker=True);result['files_written']=5
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',type=Path,required=True);p.add_argument('--retry-state-failure',action='store_true');p.add_argument('--write',action='store_true');a=p.parse_args()
 print(json.dumps((retry if a.retry_state_failure else prepare)(a.parent_spec,a.write),indent=2))
