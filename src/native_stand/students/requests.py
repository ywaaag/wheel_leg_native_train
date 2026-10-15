"""Strict new-interface declaration and CPU public submission adapter."""
import json,sys
from pathlib import Path
from .interface import contract,VERSION
from .data import sha

def evaluation_recovery(config,poses,family):
 """Case-local evaluation reset contract; never mutate a training declaration."""
 import copy
 from native_stand.recovery.sampling import sample_poses
 scoped=copy.deepcopy(config)
 scoped['active_family']=family
 scoped['sampling']={'version':'family_weights_v1','family_weights':{family:1.}}
 scoped['assessment']={'families':[family],'retained_families':[]}
 scoped['curriculum']={'automatic_upgrade':False,'levels':[]}
 sample_poses(poses,scoped,family,'holdout',training=False)
 return scoped

def validate(spec,*,motion_task_data=None):
 errors=[]
 if spec.get('motion_advantage_probe'):
  try:
   from .motion_advantage_probe import validate as validate_probe
   validate_probe(spec)
  except (OSError,ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
  return errors
 try:
  from .performance import settings
  settings(spec)
 except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
 try:
  from native_stand.command_v6.domain.execution_limits import validate_budget
  from native_stand.command_v6.domain.artifact_policy import validate as retention_policy
  validate_budget(spec);retention_policy(spec)
  if spec.get('student_training'):
   from .artifacts import storage
   storage(spec)
 except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
 mcu=spec.get('interface_version')=='multiskill_mcu_v2'
 from .mcu_interface import contract as mcu_contract
 expected=mcu_contract() if mcu else contract()
 survival=spec.get('student_survival_probe') is not None
 motion=spec.get('student_motion_validation') is not None
 v14=spec.get('student_training',{}).get('version')=='student_standing_survival_quality_v14'
 motion_train=spec.get('student_training',{}).get('version')=='student_motion31_training_v1'
 privileged49=spec.get('student_training',{}).get('version')=='student_standing_zero_privileged49_v13' or survival or v14 or motion
 if privileged49:
  from .standing_zero_privileged import contract as privileged_contract
  expected=privileged_contract()
 if motion_train:
  from .motion_privileged import contract as motion_contract
  expected=motion_contract();privileged49=True
 if spec.get('interface_version') not in (VERSION,'multiskill_mcu_v2') or spec.get('student_interface')!=expected:errors.append('student interface contract differs')
 if spec.get('action',{}).get('leg_scale_rad')!=1.5 or spec['action'].get('wheel_scale_rad_s')!=100. or spec['action'].get('dim')!=6:errors.append('student physical actions differ')
 if spec.get('observation')!=({'frame_dim':22,'actor_dim':31,'critic_dim':49 if privileged49 else 40} if mcu else {'frame_dim':22,'actor_dim':1182,'critic_dim':1191}) or spec.get('history')!=({'frames':1,'dim':0,'includes_current':True,'validity_per_frame':False} if mcu else {'frames':51,'dim':1173,'includes_current':True,'validity_per_frame':True}):errors.append('student observation/history differs')
 control=spec.get('control',{})
 if [control.get(k) for k in ('physics_dt_s','pd_dt_s','policy_dt_s','leg_kp','leg_kd','wheel_kv','effort_limits_nm')]!=[.001,.005,.01,60.,2.,1.,[40,40,5.5,40,40,5.5]]:errors.append('student shared physics differs')
 if [spec.get('termination',{}).get(k) for k in ('fall_root_height_m','minimum_up_cos','body_contact_max_n','active_leg_angle_max_rad')]!=[0.,.5,200.,3.1]:errors.append('student cannot inherit Motion .5rad task termination')
 if spec.get('ground',{}).get('collider')!='plane':errors.append('student first asset requires Plane')
 if spec.get('ppo',{}).get('hidden_dims')!=([128,64,32] if mcu else [256,128,64]):errors.append('student network shape differs')
 section=spec.get('student_evaluation',{})
 course=bool(spec.get('recovery_course'))
 probe=section.get('version')=='student_motion_probe_v1'
 if survival:
  from .survival_probe import declaration
  from .standing_zero_privileged import configuration
  if spec['student_survival_probe']!=declaration() or spec.get('student_training') or spec.get('reward')!=configuration():errors.append('survival PPO0 declaration differs')
  if section.get('version')!='student_standing_survival30_ppo0_v1' or set(section)!={'version','cases','max_output_bytes'}:errors.append('survival case schema differs')
 if probe:
  try:
   from .handoff_probe import validate as validate_probe
   validate_probe(spec)
  except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
 elif not survival and (set(section)!={'version','cases','max_output_bytes'} or section.get('version')!=('motion31_forward_capability_v1' if spec.get('student_training',{}).get('course_version')=='motion31_forward_progression_v1' else 'motion31_absolute_posture_assessment_v4' if motion_train and (spec.get('motion_confirmation') or spec.get('motion_training',{}).get('early_stop_policy')) else 'motion31_hold_level_assessment_v3' if motion_train and spec['reward']['version']=='student_motion31_hold_level_reward_v4' else 'motion31_quality_assessment_v2' if motion_train and spec['reward']['version']=='student_motion31_quality_reward_v3' else 'motion31_training_assessment_v1' if motion_train else 'student_motion31_validation_v1' if motion else 'student_course_evaluation_v1' if course else 'student_evaluation_v1')):errors.append('unknown student evaluation fields')
 if motion:
  try:
   from .motion_validation import validate as validate_motion
   validate_motion(spec)
  except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
 cases=section.get('cases',[])
 if type(section.get('max_output_bytes')) is not int or not 0<section.get('max_output_bytes',0)<=512*2**20:errors.append('student output cap differs')
 if not cases or len(cases)>32 or len({r['case_id'] for r in cases})!=len(cases):errors.append('student case IDs absent/duplicate')
 for row in cases:
  if course:continue # Exact course case schema is checked below, not dimension inferred.
  fields={'case_id','kind','checkpoint','sha256','family','seed','yaw_rad','seconds','role'}
  if not probe and set(row) not in ((fields|{'command'},) if motion or motion_train else (fields,fields|{'command_height_m'})):errors.append('unknown student case fields')
  if 'command_height_m' in row and (not mcu or row.get('kind')!='student' or type(row['command_height_m']) not in (int,float) or not .30<=row['command_height_m']<=.42):
   errors.append('explicit MCU student diagnostic height must be within .30/.42m')
  if survival and (row.get('kind')!='student' or row.get('family')!='motion_native_normal' or row.get('yaw_rad')!=0.):errors.append('survival only independent normal zero command')
  if row.get('kind') not in (('teacher_combination','teacher_normal','student_prefix_motion') if probe else ('student','teacher_combination','teacher_normal')):errors.append('unknown student case kind')
  if row.get('role') not in (('RecoveryStudent','MotionZeroStudent') if mcu else ('RecoveryStudent','MotionStudent')) or row.get('yaw_rad') not in (0.,.01) or not isinstance(row.get('seed'),int) or (not probe and row.get('seconds')!=(31.52 if survival or v14 or motion or motion_train else 13.52)):errors.append('student case protocol differs')
 if spec.get('student_training'):
  if motion_train:
   from .motion_training_requests import validate as validate_training
   errors.extend(validate_training(spec,task_data=motion_task_data))
  else:
   from .training_recipe import validate as validate_training
   errors.extend(validate_training(spec))
 elif spec.get('budget',{}).get('smoke_updates')!=0 or spec['budget'].get('formal_updates')!=0:errors.append('student first declaration is PPO0 only')
 return errors

def preflight(spec_path,output,phase,attempt_id=None):
 from native_stand.command_v6.tools.experiment_preparation import verify_publication
 from native_stand.command_v6.tools.execution_identity import identity
 from native_stand.command_v6.tools.preflight import classify_errors
 spec_path=Path(spec_path);spec=json.loads(spec_path.read_text());schema_errors=validate(spec);errors=list(schema_errors);book={}
 training=bool(spec.get('student_training')) and not spec.get('motion_advantage_probe')
 if spec.get('student_storage_resume'):
  try:
   from .storage_resume import verify
   verify(spec)
  except (OSError,ValueError,KeyError,TypeError) as exc:errors.append('student storage resume: '+str(exc))
 if phase not in (('source_eval','smoke','formal','evaluate','play') if training else ('evaluate','play')):errors.append('Student online PPO not authorized or implemented by evaluation declaration')
 try:
  publication=verify_publication(spec_path,authorized=True)
  for path,key in [(spec['source_checkpoint'],'source_sha256'),(spec['asset_path'],'asset_sha256'),(spec['recovery']['pose_library'],'pose_library_sha256')]:
   expected=spec['recovery'][key] if key.startswith('pose_') else spec[key]
   if sha(path)!=expected:errors.append('student source/asset/pose SHA differs')
  for row in spec['student_evaluation']['cases']:
   if sha(row['checkpoint'])!=row['sha256']:errors.append('student/teacher case SHA differs')
  poses=json.loads(Path(spec['recovery']['pose_library']).read_text())['poses']
  for row in spec['student_evaluation']['cases']:
   evaluation_recovery(spec['recovery'],poses,row['family'])
  for path,expected in spec['student_dependencies'].items():
   if sha(path)!=expected:errors.append('student dependency SHA differs '+path)
  from .model import load
  for row in spec['student_evaluation']['cases']:
   if row['kind'] in ('student','student_suffix','student_prefix_motion'):
    _,cp=load(row['checkpoint'],row['role'])
    if cp['interface_version']!=spec['interface_version']:errors.append('case interface version differs')
  book=json.loads(spec_path.with_name('budget.json').read_text())
  if spec.get('recovery_course'):
   from .course_requests import verify_task,verify_continuation
   verify_task(spec)
   if spec.get('student_temporal_regularization'):
    from .temporal_ab_io import verify_source
    verify_source(spec)
   if spec['recovery_course']['resume']:verify_continuation(spec)
  if book['authorization']!='AUTHORIZED':errors.append('new simulation/PPO budget has not been authorized')
  if Path(output).exists():errors.append('output path already exists')
  if book['used'].get(phase,0)>=book['limits'].get(phase,0):errors.append('phase budget exhausted')
  if training and phase=='formal':
   from native_stand.command_v6.wiring import completed_smoke
   if not completed_smoke(book,spec):errors.append('formal requires identity-matched student wiring certificate')
  partial=spec.get('motion_training',{}).get('partial_smoke_recovery')
  if partial:
   from .motion_wiring_recovery import verify_partial
   verify_partial(spec)
  if training and phase=='smoke' and not partial and not any(r['phase']=='source_eval' and r['status']=='COMPLETED' for r in book['attempts'].values()):errors.append('student smoke requires engineering-valid source evaluation')
  if any(v['status']=='RUNNING' and key!=attempt_id for key,v in book['attempts'].items()):errors.append('budget already occupied')
  import shutil
  probe=Path(output).resolve().parent
  while not probe.exists():probe=probe.parent
  if training:
   from .artifacts import storage
   limits=storage(spec);required=limits['chain_max_bytes']+limits['terminal_reserve_bytes']
  else:required=spec['student_evaluation']['max_output_bytes']+256*2**20
  if shutil.disk_usage(probe).free<required:errors.append('student output filesystem reserve insufficient')
  if spec['interpreter']!=sys.executable:errors.append('student interpreter differs')
 except (OSError,ValueError,KeyError) as exc:errors.append(str(exc));publication=None
 reason,action=classify_errors(errors)
 return {'status':'FAIL' if errors else 'PASS','errors':errors,'reason_code':reason,'action':action,'cpu_valid':not errors,'config_valid':not schema_errors,'authorized':book.get('authorization')=='AUTHORIZED','prerequisites_ready':not any(e!='new simulation/PPO budget has not been authorized' for e in errors),'resource_ready':None,
   'execution_identity':identity(spec),'spec_sha256':sha(spec_path),'source_sha256':spec['source_sha256'],'asset_sha256':spec['asset_sha256'],
   'publication_integrity':publication,'simulation':0,'ppo':0,'files_written':0}

def plan(args,spec):
 from native_stand.command_v6.tools.preflight import check
 p=check(args.spec,args.output,'evaluate',attempt_id=getattr(args,'attempt_id',None))
 if spec.get('motion_advantage_probe'):
  return {'preflight':p,'requested':spec,'effective_recipe':{'scope':'real Motion31 stochastic training-distribution rollout; actual reward/GAE; no optimizer or capability gate','probe':spec['motion_advantage_probe']},
   'requests':[{'kind':'frozen_rollout','checkpoint':spec['source_checkpoint'],'sha256':spec['source_sha256'],'simulated_envs':512,'steps':928}],
   'execution_identity':p['execution_identity'],'simulation':0,'online_PPO':0,'offline_optimizer_updates':0,'files_written':0}
 return {'preflight':p,'requested':spec,'effective_recipe':{'interface':spec['student_interface'],'physics':'shared RecoveryEnv/PD','reward':'PPO0 zero; no reward optimization','student_control':'explicit frozen student prefix then Motion; rescue not independent student success' if spec['student_evaluation']['version']=='student_motion_probe_v1' else 'all intervals after legal initialization; no teacher forwards','teacher_cases':'explicit frozen controls only'},'requests':spec['student_evaluation']['cases'],'execution_identity':p['execution_identity'],
         'simulation':0,'online_PPO':0,'offline_optimizer_updates':0,'files_written':0}
