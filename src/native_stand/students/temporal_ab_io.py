"""Finite temporal-loss A/B using the existing course preparer and chain owner."""
import copy,fcntl,json,os,subprocess,sys
from pathlib import Path
from .data import sha
from .course import plan,CONTACT_SUFFIX_RECIPE
from .temporal import declaration
from native_stand.command_v6.completion import write
ROOT=Path('/home/kellen/wheel_leg_native_train')
SOURCE=ROOT/'runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt'
SOURCE_SHA='bc52456109c79f7a9c5b7abb0b9cab9fc9ef46af7576fbfe5f0f9829ac70be4d'

def validate(spec,task):
 errors=[];ab=task['temporal_ab'];reg=spec.get('student_temporal_regularization',{});arm=reg.get('arm')
 if set(ab)!={'version','specs','source','source_sha256','source_parent','source_parent_sha256','source_terminal','source_terminal_sha256','stopped_task','stopped_ledger_sha256','execution_sha256'} or ab['version']!='recovery_temporal_ab_v1':return ['temporal A/B task fields differ']
 if arm not in ('A','B') or reg!=declaration(arm):errors.append('temporal A/B regularizer differs')
 if arm in ab['specs'] and Path(ab['specs'][arm]).parent.name!=spec['experiment']:errors.append('temporal A/B arm path differs')
 if spec['source_checkpoint']!=ab['source'] or spec['source_sha256']!=ab['source_sha256']:errors.append('temporal A/B common source differs')
 if spec['student_training']['version']!=CONTACT_SUFFIX_RECIPE or spec['recovery_course']['resume'] or spec['recovery_course']['early_end_allowed'] or spec['recovery_course']['state']['prefix']!=180:errors.append('temporal A/B course mode differs')
 if spec['budget']['formal_updates']!=100 or spec['budget']['smoke_updates']!=12:errors.append('temporal A/B budget differs')
 cases=spec['student_evaluation']['cases']
 if len([r for r in cases if r['kind']=='student' and r['family']=='motion_native_normal'])!=3 or len([r for r in cases if r['case_id'].startswith('current_')])!=3:errors.append('temporal A/B requires normal24 and suffix24')
 return errors

def verify_source(spec):
 import torch
 from .course_requests import verify_task
 task=verify_task(spec);ab=task['temporal_ab']
 from native_stand.command_v6.tools.execution_identity import identity
 if identity(spec)['location_independent_modules_sha256']!=ab['execution_sha256']:raise ValueError('temporal A/B common execution bundle changed')
 if validate(spec,task):raise ValueError(validate(spec,task))
 for p,h in [(ab['source'],ab['source_sha256']),(ab['source_parent'],ab['source_parent_sha256']),(ab['source_terminal'],ab['source_terminal_sha256'])]:
  if sha(p)!=h:raise ValueError('temporal source evidence SHA differs')
 parent=json.loads(Path(ab['source_parent']).read_text());cp=torch.load(ab['source'],map_location='cpu',weights_only=False)
 if cp['spec_sha256']!=sha(ab['source_parent']) or cp['training_recipe']!=parent['student_training'] or cp['recipe_version']!=CONTACT_SUFFIX_RECIPE or cp.get('course_resume_version')!='student_full_training_resume_v1':raise ValueError('temporal source training identity differs')
 if cp['asset_sha256']!=spec['asset_sha256'] or cp['interface_version']!=spec['interface_version'] or any(k not in cp for k in ('critic','optimizer','training_rng','recipe_updates','course_state')):raise ValueError('temporal source full state missing')
 if parent['reward']!=spec['reward'] or parent['control']!=spec['control'] or parent['ppo']!=spec['ppo']:raise ValueError('temporal experiment changed reward/control/PPO')
 import hashlib
 receipt=json.loads((Path(ab['source']).parent/'manifest.json').read_text())
 relative=receipt['execution_identity']['relative_modules_sha256']
 digest=hashlib.sha256(json.dumps(relative,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if digest!=cp['source_code_sha256']:raise ValueError('temporal source frozen code receipt differs')
 frozen=Path(ab['source']).parent.parent/'source_snapshot/native_stand'
 if any(sha(frozen/name)!=h for name,h in relative.items()):raise ValueError('temporal source frozen modules changed')
 terminal=json.loads(Path(ab['source_terminal']).read_text())
 if terminal['status']!='COMPLETED' or terminal.get('failure'):raise ValueError('temporal source run incomplete')
 return {'version':'temporal_full_state_initialization_v1','source_sha256':ab['source_sha256'],'Actor_Critic_Adam_RNG_restored':True,'new_smoke_required':True,'source_code_change':'explicit new Actor auxiliary experiment; no normal continuation bypass'}

def prepare(folder,scope,*,write_files=False):
 from native_stand.command_v6.domain.experiment_naming import new_experiment_name
 from .course_io import prepare_block
 prior=ROOT/'isolated/recovery_course_contact_restart_20261012/task/task_manifest.json';old=json.loads(prior.read_text());ledger=prior.with_name('task_ledger.json');book=json.loads(ledger.read_text())
 if not os.environ.get('HAPI_SESSION_ID') or not scope.strip() or book['status']!='ENGINEERING_STOP' or book['active_spec'] is not None:raise ValueError('new explicit approval and settled stopped owner required')
 if sha(SOURCE)!=SOURCE_SHA:raise ValueError('fixed temporal source SHA differs')
 folder=Path(folder).resolve()
 if folder.exists() or not folder.is_relative_to(ROOT/'isolated'):raise ValueError('fresh repo-local temporal task required')
 specs={a:str(ROOT/'configs/experiments'/new_experiment_name('recovery_wheel_temporal_'+a.lower()+'_from100')/'spec.json') for a in ('A','B')}
 parent=SOURCE.parent/'source_snapshot/spec.json';terminal=SOURCE.parent/'terminal_report.json'
 task=copy.deepcopy(old);task.update(session=os.environ['HAPI_SESSION_ID'],user_scope=scope,source_checkpoint=str(SOURCE),source_sha256=SOURCE_SHA,source_parent=str(parent),source_parent_sha256=sha(parent),stop_file=str(folder/'STOP'))
 task['temporal_ab']={'version':'recovery_temporal_ab_v1','specs':specs,'source':str(SOURCE),'source_sha256':SOURCE_SHA,'source_parent':str(parent),'source_parent_sha256':sha(parent),'source_terminal':str(terminal),'source_terminal_sha256':sha(terminal),'stopped_task':str(prior),'stopped_ledger_sha256':sha(ledger)}
 from native_stand.command_v6.tools.execution_identity import identity
 task['temporal_ab']['execution_sha256']=identity({'task':'recovery'})['location_independent_modules_sha256']
 state=copy.deepcopy(book['state']);state.update(cumulative_updates=book['totals']['updates'],confirmation_streak=0,last_confirm_update=None)
 new=copy.deepcopy(book);new.update(status='READY',active_spec=None,state=state,smoke_evidence={},next_decision={'action':'TEMPORAL_AB_A','resume':{'checkpoint':str(SOURCE),'sha256':SOURCE_SHA}})
 report={'manifest':str(folder/'task_manifest.json'),'specs':specs,'historical_totals':book['totals'],'source_sha256':SOURCE_SHA,'files_written':0,'simulation':0,'PPO':0,'max_online_updates':224,'max_samples':1835008,'max_wall_s':28800}
 if not write_files:return report
 folder.mkdir();write(folder/'task_manifest.json',task);write(folder/'task_ledger.json',new)
 report['arms']={}
 for arm in ('A','B'):
  report['arms'][arm]=prepare_block(folder/'task_manifest.json',source={'checkpoint':str(SOURCE),'sha256':SOURCE_SHA},state=state,index=len(book['blocks']),write_files=True,output=Path(specs[arm]).parent)
 report['files_written']=12
 return report

def finish(spec_path,chain,chain_status,failure):
 from .course_io import authorize_block,submission_environment
 spec_path=Path(spec_path);s=json.loads(spec_path.read_text());m=Path(s['recovery_course']['task_manifest']);task=json.loads(m.read_text());ledger=m.with_name('task_ledger.json');arm=s['student_temporal_regularization']['arm']
 with ledger.with_suffix('.lock').open('a+') as handle:
  fcntl.flock(handle,fcntl.LOCK_EX);d=json.loads(ledger.read_text())
  if d['active_spec']!=str(spec_path.resolve()) or any(r['spec']==str(spec_path.resolve()) for r in d['blocks']):raise ValueError('temporal exact-ID conflict')
  terminal=json.loads((Path(chain)/'chain_terminal_report.json').read_text());book=json.loads(spec_path.with_name('budget.json').read_text());updates=book['used']['formal']+book['used']['smoke']
  record={'spec':str(spec_path),'spec_sha256':sha(spec_path),'chain':str(chain),'event_id':terminal['event_id'],'status':chain_status,'updates':updates,'formal_updates':book['used']['formal'],'samples':updates*8192,'effective_actor_samples':sum(r.get('terminal',{}).get('effective_actor_samples',0) for r in terminal['phase_results']),'score_episodes':sum(len(e.get('per_env',[])) for r in terminal['phase_results'] for e in r.get('terminal',{}).get('evaluations',[])),'wall_s':terminal['chain_wall_s'],'attempts':book['attempts'],'arm':arm}
  d['blocks'].append(record)
  for k in d['totals']:d['totals'][k]+=record[k]
  user_stopped=m.with_name('STOP').exists() or any(r.get('terminal',{}).get('stop_kind')=='user_signal' for r in terminal['phase_results'])
  if failure or chain_status!='COMPLETED' or user_stopped:
   d.update(status='STOPPED' if user_stopped else 'ENGINEERING_STOP',active_spec=None,next_decision={'action':'STOP','reason':failure or chain_status});write(ledger,d);return d
  d.setdefault('temporal_results',{})[arm]={'chain':str(chain),'selection':json.loads((Path(chain)/'formal/candidate_selection.json').read_text())}
  d.update(status='READY' if arm=='A' else 'COMPLETED',active_spec=None,next_decision={'action':'TEMPORAL_AB_B' if arm=='A' else 'REVIEW_AB','resume':{'checkpoint':task['source_checkpoint'],'sha256':task['source_sha256']}});write(ledger,d)
 if arm=='B':
  from .temporal_review import review
  write(m.parent/'comparison.json',review(d['temporal_results']));return d
 next_spec=task['temporal_ab']['specs']['B'];authorize_block(m,next_spec)
 cmd=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',next_spec,'--output-dir',str(ROOT/'runs'/Path(next_spec).parent.name),'--physical-gpu','0','--hapi-session',task['session'],'--resource-mode','shared','--sharing-authorization',task['user_scope'],'--launch']
 result=subprocess.run(cmd,capture_output=True,text=True,env=submission_environment(next_spec))
 write(Path(chain)/'next_block_submission.json',{'command':cmd,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
 if result.returncode:
  d.update(status='ENGINEERING_STOP',active_spec=None,next_decision={'action':'STOP','reason':'B public submission rejected; no retry'});write(ledger,d)
 return d

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--task-directory',required=True);p.add_argument('--authorization-scope',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
 print(json.dumps(prepare(a.task_directory,a.authorization_scope,write_files=a.write),indent=2))
