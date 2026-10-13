"""Standing task preparation/finite child dispatch by existing stand_chain owner."""
import copy,fcntl,json,os,subprocess,sys
from pathlib import Path
from . import standing
from .course import VERSION,initial_state,plan as legacy_plan
from .course_io import PROJECT,SOURCE,prepare_block,authorize_block,submission_environment
from .data import sha
from native_stand.command_v6.completion import write
from native_stand.command_v6.domain.experiment_naming import new_experiment_name


def prepare_task(folder,scope,*,write_files=False):
 session=os.environ.get('HAPI_SESSION_ID')
 if not session or not scope.strip():raise ValueError('standing task needs explicit bound session and user scope')
 if sha(SOURCE)!=standing.SOURCE_SHA:raise ValueError('normal-standing source SHA differs')
 parent=SOURCE.parent/'source_snapshot/spec.json';base=json.loads(parent.read_text());folder=Path(folder).resolve()
 task={'version':VERSION,'plan':legacy_plan(),'standing_training':standing.plan(),'authorization':'AUTHORIZED','session':session,'user_scope':scope,'physical_gpu':0,'gpu_uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72','resource_mode':'shared','project_root':str(PROJECT),'source_checkpoint':str(SOURCE),'source_sha256':sha(SOURCE),'source_parent':str(parent),'source_parent_sha256':sha(parent),'teachers':base['student_teachers'],'stop_file':str(folder/'STOP'),'notification_enabled':False}
 if not write_files:return {'task_manifest':task,'simulation':0,'PPO':0,'files_written':0}
 if folder.exists() or not folder.is_relative_to(PROJECT/'isolated'):raise ValueError('fresh repo-local standing task folder required')
 folder.mkdir(parents=True);write(folder/'task_manifest.json',task)
 write(folder/'task_ledger.json',{'version':VERSION,'status':'READY','state':initial_state(),'active_spec':None,'blocks':[],'totals':dict(updates=0,samples=0,effective_actor_samples=0,wall_s=0.,score_episodes=0),'smoke_evidence':{},'standing_best_metrics':None,'standing_stagnant_blocks':0,'standing_rollbacks':0,'standing_confirmations':0,'next_decision':None})
 return prepare_block(folder/'task_manifest.json',output=PROJECT/'configs/experiments'/new_experiment_name('recovery_standing034_mirror_huber_block0000'),write_files=True)


def finish(spec_path,chain,status,failure):
 sp=Path(spec_path).resolve();s=json.loads(sp.read_text());manifest=Path(s['recovery_course']['task_manifest']);task=json.loads(manifest.read_text());ledger=manifest.with_name('task_ledger.json');chain=Path(chain)
 if standing.validate_task(task,s):raise ValueError('standing task scope differs at settlement')
 with ledger.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);d=json.loads(ledger.read_text())
  if d['active_spec']!=str(sp) or any(r['spec']==str(sp) for r in d['blocks']):raise ValueError('standing exact block already settled or wrong owner')
  b=json.loads(sp.with_name('budget.json').read_text());t=json.loads((chain/'chain_terminal_report.json').read_text())
  updates=b['used']['smoke']+b['used']['formal'];record=dict(spec=str(sp),spec_sha256=sha(sp),chain=str(chain),status=status,updates=updates,formal_updates=b['used']['formal'],samples=updates*8192,effective_actor_samples=sum(r.get('terminal',{}).get('effective_actor_samples',0) for r in t['phase_results']),wall_s=t['chain_wall_s'],score_episodes=sum(len(e.get('per_env',[])) for r in t['phase_results'] for e in r.get('terminal',{}).get('evaluations',[])))
  d['blocks'].append(record)
  for k in d['totals']:d['totals'][k]+=record[k]
  d['active_spec']=None
  stopped=manifest.with_name('STOP').exists() or status not in ('COMPLETED','STOPPED_BOUNDED') or failure or any(r.get('terminal',{}).get('stop_kind')=='user_signal' for r in t['phase_results'])
  if stopped:
   d.update(status='STOPPED' if manifest.with_name('STOP').exists() else 'ENGINEERING_STOP',next_decision={'action':'STOP','reason':failure or status});write(ledger,d);return d
  registry=json.loads((chain/'formal/candidate_registry.json').read_text());candidates=[r for r in registry if r.get('update',0)>0 and 'standing_metrics' in r]
  if not candidates:raise ValueError('standing task has no evaluated trained candidate')
  decision=standing.decide(d,candidates);d['next_decision']=decision
  if s['recovery_course']['first_recipe_block']:
   smoke=chain/'smoke';d['smoke_evidence'][standing.RECIPE]={'folder':str(smoke),'sha256':sha(smoke/'wiring_certificate.json')}
  if decision['action']=='ACCEPT_STANDING':
   d.update(status='COMPLETED',accepted_standing_symmetry=decision['candidate'],accepted_full_recovery=None);write(ledger,d);return d
  if decision['action']=='STOP':d['status']='NEEDS_DESIGN';write(ledger,d);return d
  source=decision['resume']
  import torch
  checkpoint=torch.load(source['checkpoint'],map_location='cpu',weights_only=False)
  own_parent=Path(source['checkpoint']).parent/'source_snapshot/spec.json'
  if sha(own_parent)!=checkpoint['spec_sha256'] or checkpoint['training_recipe']['reward']!=s['reward']:raise ValueError('standing resume source own spec/reward differs')
  d['state']=copy.deepcopy(checkpoint['course_state']);d['state']['cumulative_updates']=d['totals']['updates'];d['status']='READY';write(ledger,d)
 state=copy.deepcopy(d['state'])
 prepared=prepare_block(manifest,source={'checkpoint':source['checkpoint'],'sha256':source['sha256']},state=state,resume=True,smoke_evidence=d['smoke_evidence'][standing.RECIPE],index=len(d['blocks']),output=PROJECT/'configs/experiments'/new_experiment_name(f'recovery_standing034_mirror_huber_block{len(d["blocks"]):04d}'),write_files=True)
 # Original course authorization restores source linkage from the owner decision.
 authorize_block(manifest,prepared['spec'])
 if manifest.with_name('STOP').exists():
  d.update(status='STOPPED',active_spec=None,next_decision={'action':'STOP','reason':'user stop before next launch'});write(ledger,d);return d
 command=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',prepared['spec'],'--output-dir',str(PROJECT/'runs'/Path(prepared['spec']).parent.name),'--hapi-session',task['session'],'--physical-gpu','0','--resource-mode','shared','--sharing-authorization',task['user_scope'],'--launch','--handshake-wait-s','30']
 r=subprocess.run(command,env=submission_environment(prepared['spec']),capture_output=True,text=True)
 write(chain/'next_block_submission.json',{'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 if r.returncode:
  d=json.loads(ledger.read_text());d.update(status='ENGINEERING_STOP',next_decision={'action':'STOP','reason':'next public standing submission rejected; no retry'});write(ledger,d)
 return d

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--task-directory',type=Path,required=True);p.add_argument('--authorization-scope',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
 print(json.dumps(prepare_task(a.task_directory,a.authorization_scope,write_files=a.write),indent=2))
