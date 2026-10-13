"""CPU contracts for a task-scoped Recovery course; never grants permission."""
import copy,json
from pathlib import Path
from .course import VERSION,SMOOTH_RECIPE,SUFFIX_RECIPE,SWING,NORMAL,plan,validate_state,slot_groups,recipe_for
from .training_recipe import declaration
from .data import sha
CASE_FIELDS={'case_id','kind','checkpoint','sha256','family','seed','yaw_rad','seconds','role','prefix_s'}

def project_root_for(spec,default):
 """Frozen code location is distinct from the explicitly authorized project root."""
 c=spec.get('recovery_course') or spec.get('course_authorization_reference')
 if not c:return Path(default)
 path=Path(c['task_manifest']);task=json.loads(path.read_text())
 if sha(path)!=c['task_manifest_sha256'] or task.get('plan')!=plan() or task.get('authorization')!='AUTHORIZED' or task.get('project_root')!='/home/kellen/wheel_leg_native_train':raise ValueError('task project root/authorization identity differs')
 if spec.get('task')!='recovery' or spec.get('interface_version')!='multiskill_mcu_v2':raise ValueError('task authorization cannot cover another task/interface')
 return Path(task['project_root'])

def validate(spec):
 errors=[];c=spec.get('recovery_course',{})
 if set(c)!={'version','task_manifest','task_manifest_sha256','state','resume','first_recipe_block','smoke_evidence','source_metrics','source_candidate','block_index','early_end_allowed'} or c.get('version')!=VERSION:return ['Recovery course schema differs']
 try:
  state=validate_state(c['state']);slot_groups(state)
  manifest=Path(c['task_manifest']);task=json.loads(manifest.read_text())
  if sha(manifest)!=c['task_manifest_sha256']:raise ValueError('task manifest SHA differs')
  v=recipe_for(state,task)
  expected=declaration(v,source_actor_sha256=spec['source_sha256'])
  ab=task.get('temporal_ab')
  if ab:expected['milestones']=[50,100]
  if spec.get('student_training')!=expected or spec.get('reward')!=expected['reward']:errors.append('course effective recipe differs')
  if spec['interface_version']!='multiskill_mcu_v2':errors.append('course interface requires31D')
  expected_ppo=dict(envs=64,steps_per_env=128,hidden_dims=[128,64,32],learning_rate=3e-5,epochs=4,minibatches=4,gamma=.99,lam=.95,clip=.2,value_coef=.5,entropy_coef=.001,max_grad_norm=1.)
  if any(spec['ppo'].get(k)!=v for k,v in expected_ppo.items()):errors.append('course PPO parameter differs')
  b=spec['budget'];smoke=12 if c['first_recipe_block'] else 0
  formal=100 if ab else min(300,600-state['stage_A_updates']) if state['stage']=='A' else 300
  expected_budget=dict(source_eval_updates=0,smoke_updates=smoke,formal_updates=formal,sample_limit=(formal+smoke)*8192,source_eval_wall_s=900,smoke_wall_s=900 if smoke else 0,formal_wall_s=12600 if smoke else 13500,chain_wall_s=14400)
  if task.get('standing_training'):expected_budget['formal_wall_s']=10800 if smoke else 11700
  for k,v in expected_budget.items():
   if b.get(k)!=v:errors.append('course finite block budget differs '+k)
  if c['first_recipe_block']==c['resume']:errors.append('new reward/resume mode conflict')
  if spec.get('restore_source_rng') is not (True if ab else c['resume']):errors.append('explicit course RNG mode differs')
  if ab:
   from .temporal_ab_io import validate as validate_ab
   errors.extend(validate_ab(spec,task))
  elif 'student_temporal_regularization' in spec:errors.append('temporal regularizer requires explicit A/B task')
  if task.get('standing_training'):
   from .standing import validate_task
   errors.extend(validate_task(task,spec))
  if spec.get('restore_recovery_curriculum') is not False:errors.append('legacy curriculum forbidden')
  rec=spec['recovery'];family=NORMAL if state['stage']=='A' else SWING
  if rec['active_family']!=family or rec['sampling']!={'version':'family_weights_v1','family_weights':{family:1.}} or rec['assessment']!={'families':[family],'retained_families':[]}:errors.append('legacy family retention or course sampling differs')
  if any(k in rec for k in ('rising_task','support_record_reward','drawback_guidance','reverse_curriculum')):errors.append('old Recovery guidance forbidden')
  cases=spec['student_evaluation']['cases']
  if spec['student_evaluation']['version']!='student_course_evaluation_v1':errors.append('course assessment version differs')
  if not cases or len({r['case_id'] for r in cases})!=len(cases):errors.append('course case IDs absent/duplicate')
  for r in cases:
   if set(r)!=CASE_FIELDS or r['kind'] not in ('student','student_suffix','teacher_combination','teacher_normal'):errors.append('course case fields/kind differ')
   if r['family'] not in (SWING,NORMAL) or type(r['seed']) is not int or r['yaw_rad'] not in (0.,.01) or r['role']!='RecoveryStudent':errors.append('course case state differs')
   if not isinstance(r['prefix_s'],(int,float)) or abs(round(r['prefix_s']*100)-r['prefix_s']*100)>1e-8 or not 0<=r['prefix_s']<=1.8:errors.append('course prefix integer intervals required')
   if abs(r['seconds']-(13.52+r['prefix_s']))>1e-8:errors.append('course duration must cover physical prefix and task')
  if len([r for r in cases if r['case_id'].startswith('current_')])!=3:errors.append('course requires three primary assessment cases')
 except (ValueError,KeyError,TypeError) as e:errors.append('course declaration: '+str(e))
 return errors

def verify_task(spec):
 c=spec['recovery_course'];path=Path(c['task_manifest']);task=json.loads(path.read_text())
 if sha(path)!=c['task_manifest_sha256'] or task.get('version')!=VERSION or task.get('plan')!=plan():raise ValueError('task authorization identity/allowed plan differs')
 if task.get('authorization')!='AUTHORIZED' or task.get('session')!=spec['authorization']['hapi_session'] or task.get('physical_gpu')!=0 or task.get('gpu_uuid')!=spec['device']['uuid']:raise ValueError('task authorization resource/session differs')
 if task.get('project_root')!='/home/kellen/wheel_leg_native_train':raise ValueError('course project scope differs')
 ledger=json.loads(path.with_name('task_ledger.json').read_text())
 if ledger['status'] not in ('READY','RUNNING') or path.with_name('STOP').exists():raise ValueError('continuous Recovery task stopped; no new block')
 if ledger.get('active_spec')!=str((Path(task['project_root'])/'configs/experiments'/spec['experiment']/'spec.json').resolve()):raise ValueError('task exact block owner differs')
 return task

def verify_continuation(spec):
 """Normal continuation proof, separate from engineering-failure recovery."""
 import torch
 from native_stand.command_v6.tools.execution_identity import identity
 from native_stand.command_v6.wiring import validate_persisted_certificate
 c=spec['recovery_course'];verify_task(spec)
 if not c['resume']:return False
 cp=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
 if cp.get('recipe_version')!=spec['student_training']['version'] or cp.get('course_resume_version')!='student_full_training_resume_v1':raise ValueError('same-recipe full continuation missing')
 required=('critic','optimizer','training_rng','cumulative_update','recipe_updates','course_state','certified_capabilities')
 if any(k not in cp for k in required):raise ValueError('continuation state incomplete')
 if cp.get('source_code_sha256')!=identity(spec)['location_independent_modules_sha256']:raise ValueError('continuation execution code SHA differs')
 e=c['smoke_evidence'];folder=Path(e['folder']);previous=json.loads((folder/'source_snapshot/spec.json').read_text())
 if sha(folder/'wiring_certificate.json')!=e['sha256'] or previous['student_training']['version']!=spec['student_training']['version']:raise ValueError('continuation wiring recipe/SHA differs')
 if validate_persisted_certificate(folder,previous)['status']!='PASSED':raise ValueError('continuation actual smoke invalid')
 terminal=Path(spec['source_checkpoint']).parent/'terminal_report.json'
 t=json.loads(terminal.read_text())
 if t.get('failure') or t['status'] not in ('COMPLETED','STOPPED_BOUNDED'):raise ValueError('normal resume cannot recover a failed attempt')
 return True
