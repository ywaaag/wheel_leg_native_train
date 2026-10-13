"""CLI/owner I/O for the public continuous Recovery course. No watcher or trainer."""
import copy,fcntl,json,os,subprocess,sys,time
from pathlib import Path
from .course import *
from .data import sha
from native_stand.command_v6.completion import write
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,checked_input

PROJECT=Path('/home/kellen/wheel_leg_native_train')
SOURCE=PROJECT/'runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/model_update_300.pt'

def register_task(folder,scope,*,write_files=False):
 session=os.environ.get('HAPI_SESSION_ID')
 if not session or not scope.strip():raise ValueError('explicit current-session course approval required')
 checked_input(SOURCE,SOURCE_SHA)
 manifest={'version':VERSION,'plan':plan(),'authorization':'AUTHORIZED','user_scope':scope,'session':session,'physical_gpu':0,'gpu_uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72','resource_mode':'shared','project_root':str(PROJECT),'source_checkpoint':str(SOURCE),'source_sha256':SOURCE_SHA,'source_parent':str(SOURCE.parent/'source_snapshot/spec.json'),'source_parent_sha256':sha(SOURCE.parent/'source_snapshot/spec.json'),'teachers':json.loads((SOURCE.parent/'source_snapshot/spec.json').read_text())['student_teachers'],'stop_file':str(Path(folder).resolve()/'STOP'),'notification_enabled':False}
 if not write_files:return {'requested_task':manifest,'files_written':0,'simulation':0,'PPO':0}
 folder=Path(folder).resolve()
 if not folder.is_relative_to(PROJECT/'isolated') or folder.exists():raise ValueError('fresh repo-local task folder required')
 folder.mkdir();write(folder/'task_manifest.json',manifest)
 write(folder/'task_ledger.json',{'version':VERSION,'status':'READY','state':initial_state(),'active_spec':None,'blocks':[],'totals':{'updates':0,'samples':0,'effective_actor_samples':0,'wall_s':0.,'score_episodes':0},'smoke_evidence':{},'next_decision':None})
 return {'manifest':str(folder/'task_manifest.json'),'manifest_sha256':sha(folder/'task_manifest.json'),'files_written':2,'simulation':0,'PPO':0}

def recover_unstarted_block(prior_manifest,folder,scope,*,write_files=False):
 """Explicit user recovery into a new task ledger; original evidence is immutable."""
 prior_manifest=Path(prior_manifest).resolve();old=json.loads(prior_manifest.read_text())
 prior_ledger=prior_manifest.with_name('task_ledger.json');book=json.loads(prior_ledger.read_text())
 session=os.environ.get('HAPI_SESSION_ID')
 if not session or not scope.strip() or book['status']!='ENGINEERING_STOP' or old['plan']!=plan():raise ValueError('explicit stopped-course recovery required')
 failed=Path(book['active_spec']);spec=json.loads(failed.read_text());budget=failed.with_name('budget.json');b=json.loads(budget.read_text())
 if b['attempts'] or any(b['used'].values()) or failed.with_name('chain_submission.json').exists() or (PROJECT/'runs'/spec['experiment']).exists():raise ValueError('recovery entry only covers unstarted rejected child submission')
 if spec['recovery_course']['resume'] or spec['recovery_course']['state']!=book['state']:raise ValueError('unstarted new-reward state differs')
 source={'checkpoint':spec['source_checkpoint'],'sha256':spec['source_sha256']};checked_input(source['checkpoint'],source['sha256'])
 if book['state']['stage']!='B' or book['state']['prefix']!=180:raise ValueError('this recovery covers the first dynamic-course dispatch only')
 evidence={'prior_manifest':[str(prior_manifest),sha(prior_manifest)],'prior_ledger':[str(prior_ledger),sha(prior_ledger)],'failed_spec':[str(failed),sha(failed)],'failed_budget':[str(budget),sha(budget)],'actual_physical_attempts':0,'user_recovery_scope':scope}
 manifest=copy.deepcopy(old);manifest.update(session=session,user_scope=old['user_scope']+'\n'+scope,recovery_origin=evidence,stop_file=str(Path(folder).resolve()/'STOP'))
 new=copy.deepcopy(book);new.update(status='READY',active_spec=None,next_decision={'action':'NEW_REWARD','resume':source})
 new.setdefault('recovery_history',[]).append(evidence)
 report={'requested_manifest':manifest,'preserved_totals':new['totals'],'source':source,'state':new['state'],'files_written':0,'simulation':0,'PPO':0}
 if not write_files:return report
 folder=Path(folder).resolve()
 if not folder.is_relative_to(PROJECT/'isolated') or folder.exists():raise ValueError('fresh repo-local recovery task required')
 folder.mkdir();write(folder/'task_manifest.json',manifest);write(folder/'task_ledger.json',new)
 report.update(manifest=str(folder/'task_manifest.json'),manifest_sha256=sha(folder/'task_manifest.json'),files_written=2)
 return report

def cases_for(s,state,source):
 teachers=s['student_teachers'];current=state['prefix']/100 if state['stage']!='A' else 0.
 family=NORMAL if state['stage']=='A' else SWING
 def row(id,family,kind='student',prefix=0.,seed=20261010,yaw=0.):
  cp=source['checkpoint'] if kind.startswith('student') else teachers[1]['checkpoint'];h=source['sha256'] if kind.startswith('student') else teachers[1]['sha256']
  return dict(case_id=id,kind=kind,checkpoint=cp,sha256=h,family=family,seed=seed,yaw_rad=yaw,seconds=13.52+prefix,role='RecoveryStudent',prefix_s=prefix)
 result=[row('current_native',family,'student_suffix' if current else 'student',current),row('current_yaw10',family,'student_suffix' if current else 'student',current,20261010,.01),row('current_yaw11',family,'student_suffix' if current else 'student',current,20261011,.01)]
 if state['stage']=='A':result.extend([row('unassisted_Swing',SWING),row('teacher_normal_native',NORMAL,'teacher_normal')])
 else:result.extend([row('previous_suffix',SWING,'student_suffix' if state['previous_prefix'] else 'student',state['previous_prefix']/100),row('normal_native',NORMAL),row('unassisted_Swing',SWING),row('teacher_combination_native',SWING,'teacher_combination')])
 return result

def recover_failed_block(prior_manifest,folder,scope,*,write_files=False):
 """New explicit approval, settled fault evidence and new reward; never retry in place."""
 import torch
 prior_manifest=Path(prior_manifest).resolve();prior_ledger=prior_manifest.with_name('task_ledger.json')
 old=json.loads(prior_manifest.read_text());book=json.loads(prior_ledger.read_text())
 session=os.environ.get('HAPI_SESSION_ID')
 if not session or not scope.strip() or book['status']!='ENGINEERING_STOP' or book['active_spec'] is not None or old['plan']!=plan():raise ValueError('explicit settled failed-course recovery required')
 if prior_manifest.with_name('STOP').exists():raise ValueError('user stop prevents recovery')
 last=book['blocks'][-1];spec_path=Path(last['spec']);spec=json.loads(spec_path.read_text());budget=spec_path.with_name('budget.json');b=json.loads(budget.read_text())
 terminal=Path(last['chain'])/'formal/terminal_report.json';end=json.loads(terminal.read_text())
 if sha(spec_path)!=last['spec_sha256'] or last['status']!='FAILED' or end['status']!='FAILED' or not end.get('failure'):raise ValueError('settled failed block identity differs')
 if any(a['status']=='RUNNING' for a in b['attempts'].values()) or b['used']['formal']!=end['actual_updates'] or last['formal_updates']!=end['actual_updates']:raise ValueError('failed block not fully settled')
 if book['state']['stage']!='B' or spec['student_training']['version']!=SUFFIX_RECIPE:raise ValueError('contact recipe recovery requires prior v9 dynamic course')
 registry=json.loads((Path(last['chain'])/'formal/candidate_registry.json').read_text())
 assessed=[x for x in registry if x.get('update',0)>0 and len(x.get('per_env',[]))==24]
 if not assessed:raise ValueError('no assessed saved dynamic candidate')
 source=max(assessed,key=lambda x:(rank(summary(x['per_env'])),-x['update']))
 cp=Path(source['checkpoint']).resolve();checked_input(cp,source['sha256'])
 if cp.parent!=terminal.parent:raise ValueError('recovery checkpoint must belong to settled failed phase')
 data=torch.load(cp,map_location='cpu',weights_only=False)
 if data.get('recipe_version')!=SUFFIX_RECIPE or data.get('interface_version')!='multiskill_mcu_v2' or data['update']!=source['update'] or data['course_state']['prefix']!=book['state']['prefix']:raise ValueError('recovery candidate training identity differs')
 parent=cp.parent/'source_snapshot/spec.json';checked_input(parent,sha(parent))
 state=copy.deepcopy(book['state']);state.update(cumulative_updates=book['totals']['updates'],confirmation_streak=0,last_confirm_update=None,best_metrics=None,best=None,latest=None,stagnant=0)
 evidence={'prior_manifest':[str(prior_manifest),sha(prior_manifest)],'prior_ledger':[str(prior_ledger),sha(prior_ledger)],'failed_spec':[str(spec_path),sha(spec_path)],'failed_budget':[str(budget),sha(budget)],'failed_terminal':[str(terminal),sha(terminal)],'checkpoint':[str(cp),source['sha256']],'saved_update':source['update'],'completed_formal_updates':end['actual_updates'],'unsaved_updates_not_restored':end['actual_updates']-source['update'],'old_fault_reason':'UNKNOWN among runtime fault / initial rejection / nonfinite reward; saved tail covers env0-7 only','user_recovery_scope':scope,'new_recipe':CONTACT_SUFFIX_RECIPE,'optimizer_reinitialized_reason':'explicit reward change; Actor only from assessed candidate'}
 manifest=copy.deepcopy(old);manifest.update(session=session,user_scope=old['user_scope']+'\n'+scope,recovery_origin=evidence,dynamic_recipe=CONTACT_SUFFIX_RECIPE,source_checkpoint=str(cp),source_sha256=source['sha256'],source_parent=str(parent),source_parent_sha256=sha(parent),stop_file=str(Path(folder).resolve()/'STOP'))
 source_identity={'checkpoint':str(cp),'sha256':source['sha256']}
 new=copy.deepcopy(book);new.update(status='READY',state=state,active_spec=None,next_decision={'action':'NEW_REWARD','resume':source_identity},smoke_evidence={})
 new.setdefault('recovery_history',[]).append(evidence)
 report={'requested_manifest':manifest,'preserved_totals':new['totals'],'source':source_identity,'state':state,'files_written':0,'simulation':0,'PPO':0}
 if not write_files:return report
 folder=Path(folder).resolve()
 if not folder.is_relative_to(PROJECT/'isolated') or folder.exists():raise ValueError('fresh repo-local recovery task required')
 folder.mkdir();write(folder/'task_manifest.json',manifest);write(folder/'task_ledger.json',new)
 report.update(manifest=str(folder/'task_manifest.json'),manifest_sha256=sha(folder/'task_manifest.json'),files_written=2)
 return report

def prepare_block(manifest_path,*,source=None,state=None,resume=False,smoke_evidence=None,source_metrics=None,source_candidate=None,index=0,write_files=False,output=None):
 from .training_recipe import declaration
 from .requests import validate
 task=json.loads(Path(manifest_path).read_text());state=copy.deepcopy(state or initial_state());validate_state(state)
 source=source or {'checkpoint':task['source_checkpoint'],'sha256':task['source_sha256']}
 checked_input(source['checkpoint'],source['sha256']);base=json.loads(Path(task['source_parent']).read_text());s=copy.deepcopy(base)
 purpose=f'recovery_course_{state["stage"].lower()}_prefix{state["prefix"]}_block{index:04d}'
 name=new_experiment_name(purpose);folder=Path(output).resolve() if output else PROJECT/'configs/experiments'/name
 from native_stand.command_v6.domain.experiment_naming import validate_new_experiment_name
 validate_new_experiment_name(folder.name)
 if folder.exists():raise FileExistsError(folder)
 version=recipe_for(state,task)
 recipe=declaration(version,source_actor_sha256=source['sha256']);smoke=0 if resume else 12
 formal=min(300,600-state['stage_A_updates']) if state['stage']=='A' else 300
 ab=task.get('temporal_ab')
 arm=None
 if ab:
  arm=next((k for k,v in ab['specs'].items() if v==str(folder/'spec.json')),None)
  if arm is None or resume or state['stage']!='B':raise ValueError('temporal A/B exact arm/state differs')
  formal=100;recipe['milestones']=[50,100]
 s.update(experiment=folder.name,source_checkpoint=source['checkpoint'],source_sha256=source['sha256'],student_training=recipe,reward=recipe['reward'],restore_source_rng=resume,restore_recovery_curriculum=False)
 s['recovery_course']={'version':VERSION,'task_manifest':str(Path(manifest_path).resolve()),'task_manifest_sha256':sha(manifest_path),'state':state,'resume':resume,'first_recipe_block':not resume,'smoke_evidence':smoke_evidence,'source_metrics':source_metrics,'source_candidate':source_candidate or source,'block_index':index,'early_end_allowed':True}
 if task.get('standing_training'):
  s['recovery_course']['early_end_allowed']=False;s['control']['height_command_m']=.34
 if ab:
  from .temporal import declaration as temporal_declaration
  s['student_temporal_regularization']=temporal_declaration(arm)
  s['recovery_course']['early_end_allowed']=False
  s['restore_source_rng']=True
 for k in ('engineering_recovery','source_evidence_reference','retention','receiver_training','motion_handoff','diagnostics'):s.pop(k,None)
 rec=s['recovery'];family=NORMAL if state['stage']=='A' else SWING
 rec.update(active_family=family,sampling={'version':'family_weights_v1','family_weights':{family:1.}},assessment={'families':[family],'retained_families':[]})
 for k in ('rising_task','curriculum','support_record_reward','drawback_guidance','reverse_curriculum','retention_regression_policy'):rec.pop(k,None)
 duration=13.52+(max(state['prefix'],state['previous_prefix'])/100 if state['stage']!='A' else 0.)
 rec['fsm']['timeout_s']=duration;s['curriculum']['episode_length_s']=duration
 s['budget'].update(source_eval_updates=0,source_eval_wall_s=900,smoke_updates=smoke,smoke_wall_s=900 if smoke else 0,formal_updates=formal,formal_wall_s=12600 if smoke else 13500,chain_wall_s=14400,sample_limit=(formal+smoke)*8192)
 if task.get('standing_training'):s['budget'].update(formal_wall_s=10800 if smoke else 11700)
 s['student_evaluation']={'version':'student_course_evaluation_v1','cases':cases_for(s,state,source),'max_output_bytes':512*2**20}
 if task.get('standing_training'):
  extra=copy.deepcopy(s['student_evaluation']['cases'][2]);extra.update(case_id='normal_certification_yaw12',seed=20261012)
  s['student_evaluation']['cases'].insert(3,extra)
 if ab:
  normal=s['student_evaluation']['cases'][4]
  s['student_evaluation']['cases'][3:4]=[{**normal,'case_id':'normal_yaw10','seed':20261010,'yaw_rad':.01},{**normal,'case_id':'normal_yaw11','seed':20261011,'yaw_rad':.01}]
 s['artifacts']['run_name']=folder.name;s['artifacts']['terminal_reserve_bytes']=128*2**20
 s['evaluation'].update(checkpoint_every_updates=100,full_every_updates=100,run_final_durability=False)
 s['notifications']={'enabled':False};s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':task['user_scope']}
 s['authorization']={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'course block awaiting task-derived registration'}
 # All child execution uses the same currently imported/frozen code bundle.
 s['execution_source_root']=str(Path(__file__).resolve().parents[2])
 s['student_dependencies'][str(Path(manifest_path).resolve())]=sha(manifest_path)
 s['student_dependencies'][source['checkpoint']]=source['sha256']
 poses=json.loads(Path(base['recovery']['pose_library']).read_text())
 encoded=(json.dumps(poses,indent=2)+'\n').encode();import hashlib
 rec['pose_library']=str(folder/'poses.json');rec['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
 inputs={str(Path(task['source_parent'])):task['source_parent_sha256']}
 for path,h in s['student_dependencies'].items():inputs.update([checked_input(path,h)])
 for t in s['student_teachers']:
  inputs.update([checked_input(t['checkpoint'],t['sha256']),checked_input(t['spec'],t['spec_sha256'])])
 errors=validate(s)
 if errors:raise ValueError(errors)
 report={'version':VERSION,'spec':str(folder/'spec.json'),'ledger':str(folder/'budget.json'),'state':state,'resume':resume,'total_update_limit':None,'block_updates':formal,'block_wall_s':14400,'smoke_updates':smoke,'files_written':0,'simulation':0,'PPO':0}
 book={'authorization':'UNAUTHORIZED','experiment':folder.name,'limits':{'source_eval':1,'evaluate':0,'smoke':smoke,'formal':formal},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'sample_limit':s['budget']['sample_limit'],'source_eval_wall_used_s':0.,'hapi_session':None}
 if write_files:
  publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report},inputs,completion_marker=True,serialized_files={'poses.json':(encoded,rec['pose_library_sha256'])})
  report['files_written']=5
 return report

def authorize_block(manifest_path,spec_path):
 """Task authorization creates a fresh finite child receipt via the public registrar."""
 from native_stand.command_v6.tools.register_authorization import register
 m=json.loads(Path(manifest_path).read_text());spec_path=Path(spec_path);s=json.loads(spec_path.read_text())
 if m['authorization']!='AUTHORIZED' or m['session']!=os.environ.get('HAPI_SESSION_ID') or m['plan']!=plan() or s['recovery_course']['task_manifest_sha256']!=sha(manifest_path):raise ValueError('task scope cannot authorize this block')
 ledger=Path(manifest_path).with_name('task_ledger.json');d=json.loads(ledger.read_text())
 if d['status'] not in ('READY','RUNNING') or ledger.with_name('STOP').exists():raise ValueError('task stopped')
 if d['active_spec'] not in (None,str(spec_path.resolve())):raise ValueError('another task block already active')
 if d['state']!=s['recovery_course']['state']:raise ValueError('block cannot skip/overwrite owner course state')
 expected_source=(d.get('next_decision') or {}).get('resume')
 if d['blocks'] and (not expected_source or expected_source['sha256']!=s['source_sha256']):raise ValueError('block source differs from authorized owner decision')
 req={'approval_id':Path(manifest_path).parent.name+'_'+s['experiment'],'user_scope':m['user_scope'],'session':m['session'],'physical_gpu':m['physical_gpu'],'gpu_uuid':m['gpu_uuid'],'max_online_updates':s['budget']['smoke_updates']+s['budget']['formal_updates'],'max_phase_wall_s':14400,'arms':[{'spec':str(spec_path.resolve()),'spec_sha256':sha(spec_path),'budget_sha256':sha(spec_path.with_name('budget.json'))}]}
 result=register(req,current_session=m['session'],write=True)
 # Additional course binding is part of the registered spec, not an untracked edit.
 # Existing authorization API supports opaque approval_id/user_scope only; course_spec
 # is derivable from experiment and consumed by the task validator instead.
 d.update(status='RUNNING',active_spec=str(spec_path.resolve()));write(ledger,d)
 write(spec_path.with_name('task_authorization_receipt.json'),{'manifest':str(manifest_path),'manifest_sha256':sha(manifest_path),'spec_sha256':sha(spec_path),'finite_registration':result})
 return result

def _latest_course_result(chain):
 return json.loads((Path(chain)/'formal/course_result.json').read_text())

def submission_environment(spec_path,environment=None):
 """Execute the newly published child's declared bundle, not its parent's path."""
 spec=json.loads(Path(spec_path).read_text());root=Path(spec['execution_source_root']).resolve()
 if not root.is_relative_to(PROJECT) or not (root/'native_stand/command_v6/supervisor.py').is_file():raise ValueError('child execution source root missing/outside project')
 return {**(os.environ if environment is None else environment),'PYTHONPATH':str(root)}

def finish_block(spec_path,chain,chain_status,failure):
 """Called once by the existing stand_chain owner after settled terminal reports."""
 spec_path=Path(spec_path);s=json.loads(spec_path.read_text());c=s['recovery_course'];manifest=Path(c['task_manifest']);task=json.loads(manifest.read_text());ledger=manifest.with_name('task_ledger.json')
 if task.get('standing_training'):
  from .standing_io import finish
  return finish(spec_path,chain,chain_status,failure)
 if task.get('temporal_ab'):
  from .temporal_ab_io import finish
  return finish(spec_path,chain,chain_status,failure)
 with ledger.with_suffix('.lock').open('a+') as handle:
  fcntl.flock(handle,fcntl.LOCK_EX);d=json.loads(ledger.read_text())
  if d['active_spec']!=str(spec_path.resolve()) or any(r['spec']==str(spec_path.resolve()) for r in d['blocks']):raise ValueError('task block terminal exact-ID conflict')
  book=json.loads(spec_path.with_name('budget.json').read_text());terminal=json.loads((Path(chain)/'chain_terminal_report.json').read_text())
  actual=book['used']['smoke']+book['used']['formal'];effective=sum(r.get('terminal',{}).get('effective_actor_samples',0) for r in terminal['phase_results'])
  episodes=sum(len(e.get('per_env',[])) for r in terminal['phase_results'] for e in r.get('terminal',{}).get('evaluations',[]))
  record={'spec':str(spec_path.resolve()),'spec_sha256':sha(spec_path),'chain':str(chain),'event_id':terminal['event_id'],'status':chain_status,'updates':actual,'formal_updates':book['used']['formal'],'samples':actual*8192,'effective_actor_samples':effective,'score_episodes':episodes,'wall_s':terminal['chain_wall_s'],'attempts':book['attempts']}
  d['blocks'].append(record)
  for k in d['totals']:d['totals'][k]+=record[k]
  stopped=manifest.with_name('STOP').exists() or chain_status not in ('COMPLETED','STOPPED_BOUNDED') or failure or any(r.get('terminal',{}).get('stop_kind')=='user_signal' for r in terminal['phase_results'])
  if stopped:d.update(status='STOPPED' if manifest.with_name('STOP').exists() else 'ENGINEERING_STOP',active_spec=None,next_decision={'action':'STOP','reason':failure or chain_status});write(ledger,d);return d
  result=_latest_course_result(chain);state=result['state'];source_metrics=c['source_metrics']
  if source_metrics is None:
   registry=json.loads((Path(chain)/'source_eval/candidate_registry.json').read_text());source_metrics=summary(registry[0]['per_env'])
  best=result['best'];latest=result['latest'];m=result['metrics']
  if state['stage']=='A':
   origin=c['source_candidate']
   if not m['all_other_passed'] or standing_rank(m)<standing_rank(source_metrics):best=origin;m=source_metrics
  state,decision=advance(state,m,formal_updates=book['used']['formal'],cumulative_update=d['totals']['updates'],best=best,latest=latest,source_metrics=source_metrics)
  if c['first_recipe_block']:
   smoke=Path(chain)/'smoke/wiring_certificate.json';d['smoke_evidence'][s['student_training']['version']]={'folder':str(smoke.parent),'sha256':sha(smoke)}
  d.update(state=state,next_decision=decision,active_spec=None,status='READY');write(ledger,d)
 if decision['action']=='STOP':d['status']='NEEDS_DESIGN';write(ledger,d);return d
 if decision['action'] in ('CERTIFY32','FINAL_RECHECK'):
  # Certification is a separate bounded evaluation request owned by this chain.
  from .course_certification import run as certify
  outcome=certify(spec_path,chain,decision,d)
  with ledger.with_suffix('.lock').open('a+') as handle:
   fcntl.flock(handle,fcntl.LOCK_EX);d=json.loads(ledger.read_text());d['certification']=outcome
   d['totals']['score_episodes']+=outcome.get('score_episodes',0);d['totals']['wall_s']+=outcome.get('wall_s',0.)
   if decision['action']=='CERTIFY32' and outcome['accepted']:
    d['state'].update(stage='CONSOLIDATE',accepted_full_recovery=decision['resume'],confirmation_streak=0,last_confirm_update=None)
    decision={'action':'PROMOTE','resume':decision['resume']};d['next_decision']=decision
   elif decision['action']=='FINAL_RECHECK':
    d['state']['accepted_full_recovery']=outcome['checkpoint'] if outcome['accepted'] else decision['fallback'];d['status']='COMPLETED';d['active_spec']=None;write(ledger,d);return d
   else:d['status']='NEEDS_DESIGN';d['next_decision']={'action':'STOP','reason':'independent32 certification failed; new design decision required'};write(ledger,d);return d
   write(ledger,d)
 resume=decision['action']!='NEW_REWARD'
 next_source=decision['resume'];next_recipe=recipe_for(d['state'],task)
 prepared=prepare_block(manifest,source=next_source,state=d['state'],resume=resume,smoke_evidence=d['smoke_evidence'].get(next_recipe),source_metrics=source_metrics if d['state']['stage']=='A' else None,source_candidate=c['source_candidate'],index=len(d['blocks']),write_files=True)
 authorize_block(manifest,prepared['spec'])
 command=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',prepared['spec'],'--output-dir',str(PROJECT/'runs'/Path(prepared['spec']).parent.name),'--physical-gpu','0','--hapi-session',task['session'],'--resource-mode','shared','--sharing-authorization',task['user_scope'],'--launch']
 # Public supervisor verifies resource/UUID/identity afresh, then one bounded handshake.
 result=subprocess.run(command,capture_output=True,text=True,env=submission_environment(prepared['spec']))
 write(Path(chain)/'next_block_submission.json',{'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
 if result.returncode:
  with ledger.with_suffix('.lock').open('a+') as handle:
   fcntl.flock(handle,fcntl.LOCK_EX);d=json.loads(ledger.read_text());d['status']='ENGINEERING_STOP';d['next_decision']={'action':'STOP','reason':'next public submission failed; no retry'};write(ledger,d)
 return d
