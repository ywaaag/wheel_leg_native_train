"""Strict versioned Recovery learning declaration, separate from 31D IO."""
from .recovery_task import configuration,NO_FAILURE_VERSION,LIFT_RATE_VERSION,REHEARSAL_VERSION,MOTION_MIRROR_VERSION,SLIDING_VERSION
VERSION='student_recovery_ppo_bc_v1'
NO_FAILURE_RECIPE='student_recovery_ppo_failure_zero_v2'
LIFT_RATE_RECIPE='student_recovery_ppo_lift_rate_v3'
REHEARSAL_RECIPE='student_recovery_ppo_standing_rehearsal_v4'
STANDING_RECIPE='student_recovery_ppo_standing_from_distilled_v5'
STANDING_SOURCE_SHA='06c33cf7552d2f43b015fca589b927d4634a914a1e9680a4c07da38109e4e365'
MOTION_MIRROR_RECIPE='student_recovery_ppo_motion_mirror_from50_v6'
UPDATE50_SHA='d1db35ffe83fe462edab55934621cf4ea59b59ff8d60665b4e06720cb66a5a92'
SLIDING_RECIPE='student_recovery_ppo_velocity_huber_from200_v7'
UPDATE200_SHA='34be92249e25069f7a31e063e42c2451a3f560e8be589b118607d9b8a3384143'
SOURCE_SHA='7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470'
def final_assessment_cases(recipe,students):
 """Use only explicitly declared assessment tasks, including optional regression."""
 by_id={r['case_id']:r for r in students}
 normal=recipe['training_family']=='motion_native_normal'
 native='normal_native' if normal else 'student_native'
 yaw='normal_yaw10' if normal else 'student_yaw10'
 cases=[{**by_id[native],'case_id':'final_native'},
        *[{**by_id[yaw],'case_id':f'final_yaw_{seed}','seed':seed}
          for seed in recipe['final_seeds']]]
 if normal and 'student_native' in by_id:
  cases.append({**by_id['student_native'],'case_id':'final_Swing_regression'})
 return cases

def declaration(version=VERSION,source_actor_sha256=None):
 if version=='student_motion31_training_v1':
  from .motion_training import declaration as motion_declaration,SOURCE
  return motion_declaration(source_actor_sha256 or SOURCE)
 if version=='student_standing_survival_quality_v14':
  from .standing_survival_task import SOURCE,protocol
  from .standing_survival_reward import configuration as survival_configuration
  if source_actor_sha256 not in (None,SOURCE):raise ValueError('v14 update988 source differs')
  r=declaration('student_standing_zero_privileged49_v13')
  r.update(version=version,source_actor_sha256=SOURCE,reward=survival_configuration(),protocol=protocol(),environment_seconds=31.52,source_teacher_baseline=False,selection_scope='30s survival plus fixed final10s stationary alignment',resume_semantics='update988 Actor/std; new Critic49/Adam/seed; physical reset',milestones=[100,200,300])
  return r
 if version=='student_standing_zero_privileged49_v13':
  from .standing_zero_privileged import SOURCE,configuration as privileged_config,PRIVILEGED
  if source_actor_sha256 not in (None,SOURCE):raise ValueError('v13 update700 source differs')
  r=declaration('student_standing_alignment034_v12')
  r.update(version=version,source_actor_sha256=SOURCE,reward=privileged_config(),critic_privileged_version=PRIVILEGED,critic='new_random_49D',optimizer='new_Adam',source_rng_restore=False,resume_semantics='update700 Actor/std only; new Critic49/Adam/seed; physics reset')
  return r
 if version=='student_standing_alignment034_v12':
  from .standing_alignment import SOURCE,configuration as alignment_config
  if source_actor_sha256 not in (None,SOURCE):raise ValueError('v12 frozen v10 source differs')
  result=declaration('student_recovery_ppo_standing_mirror_huber_v11',SOURCE)
  result.update(version=version,reward=alignment_config(),storage_max_bytes=4*2**30,milestones=[100,200,300,400,500,600,700,800,900,988],selected_rollouts_smoke=[],selected_rollouts_formal=[],training_family='motion_native_normal')
  return result
 if version=='student_recovery_ppo_standing_mirror_huber_v11':
  from .recovery_task import SYMMETRY_VERSION
  if not isinstance(source_actor_sha256,str) or len(source_actor_sha256)!=64:raise ValueError('standing task source SHA required')
  result=declaration(SLIDING_RECIPE);result.update(version=version,source_actor_sha256=source_actor_sha256,reward=configuration(SYMMETRY_VERSION),critic='student_control_only',milestones=[100,200,300],selected_rollouts_formal=[],target_height_m=.34,protocol='student_standing_height034_symmetry_v1',selection_scope='normal standing at0.34m and physical leg symmetry; not Swing recovery',resume_semantics='full_state_same_recipe_no_repeated_warmup')
  return result
 from .course import SMOOTH_RECIPE,SUFFIX_RECIPE,CONTACT_SUFFIX_RECIPE
 if version in (SMOOTH_RECIPE,SUFFIX_RECIPE,CONTACT_SUFFIX_RECIPE):
  from .recovery_task import SMOOTH_VERSION,SUFFIX_VERSION,CONTACT_SUFFIX_VERSION
  result=declaration(SLIDING_RECIPE)
  result.update(version=version,source_actor_sha256=source_actor_sha256,training_family='motion_native_normal' if version==SMOOTH_RECIPE else 'swing_candidate_from_historical_r1',milestones=[100,200,300],selected_rollouts_formal=[],selected_rollouts_smoke=[1,6],selection_scope='normal standing' if version==SMOOTH_RECIPE else 'declared dynamic suffix only; prefix0 independent Swing')
  result['reward']=configuration({SMOOTH_RECIPE:SMOOTH_VERSION,SUFFIX_RECIPE:SUFFIX_VERSION,CONTACT_SUFFIX_RECIPE:CONTACT_SUFFIX_VERSION}[version])
  result['critic']='student_control_only';result['resume_semantics']='full_state_same_recipe_new_critic_on_reward_change'
  if not isinstance(source_actor_sha256,str) or len(source_actor_sha256)!=64:raise ValueError('course source SHA required')
  return result
 if version not in (VERSION,NO_FAILURE_RECIPE,LIFT_RATE_RECIPE,REHEARSAL_RECIPE,STANDING_RECIPE,MOTION_MIRROR_RECIPE,SLIDING_RECIPE):raise ValueError('unknown student training recipe')
 result={'version':version,'source_actor_sha256':SOURCE_SHA,'critic':'new_random','optimizer':'new_Adam','source_rng_restore':False,
  'warmup_updates_per_phase':5,'BC_coefficient':0.,'fixed_log_std':True,'physical_std_leg_rad':.05,'physical_std_wheel_rad_s':2.,
  'training_family':'swing_candidate_from_historical_r1','training_yaw_rad':.01,'retained_families':[],
  'reward':configuration({VERSION:'student_recovery_reward_v1',NO_FAILURE_RECIPE:NO_FAILURE_VERSION,LIFT_RATE_RECIPE:LIFT_RATE_VERSION,REHEARSAL_RECIPE:REHEARSAL_VERSION,STANDING_RECIPE:REHEARSAL_VERSION,MOTION_MIRROR_RECIPE:MOTION_MIRROR_VERSION,SLIDING_RECIPE:SLIDING_VERSION}[version]),'protocol':'student_autonomous_swing_v1','environment_seconds':13.52,
  'storage_max_bytes':2*2**30,'selected_rollouts_smoke':[1,6],'selected_rollouts_formal':[1,6,25,100],
  'milestones':[25,50,100],'final_seeds':[20261013,20261014,20261015],'entry_is_not_smoke_prerequisite':True}
 if version==REHEARSAL_RECIPE:result['standing_rehearsal']={'version':'native_stance_angular_reset_v1','family':'motion_native_normal','environment_counts':{'swing_candidate_from_historical_r1':32,'motion_native_normal':32},'angular_body_axes':[0,2],'angular_velocity_max_rad_s':.25,'distribution':'uniform','source':'B250 frozen native normal initial posture','evaluation_applies_same_perturbation':True,'normal_not_retention_stop':True}
 if version in (STANDING_RECIPE,MOTION_MIRROR_RECIPE,SLIDING_RECIPE):
  result.update(source_actor_sha256=STANDING_SOURCE_SHA,training_family='motion_native_normal',milestones=[25,50,100,200,300],selected_rollouts_formal=[1,6,25,100,300],selection_scope='normal standing only; Swing regression separate; not full recovery accepted')
 if version==MOTION_MIRROR_RECIPE:result['source_actor_sha256']=UPDATE50_SHA
 if version==SLIDING_RECIPE:result['source_actor_sha256']=UPDATE200_SHA
 return result
def validate_instance(recipe,source_sha256):
 """Bind source/cadence/storage per experiment; algorithm/reward remain versioned."""
 if not isinstance(recipe,dict):raise ValueError('student training recipe required')
 if not isinstance(source_sha256,str) or len(source_sha256)!=64 or any(c not in '0123456789abcdef' for c in source_sha256):raise ValueError('explicit student source SHA required')
 version=recipe.get('version')
 try:expected=declaration(version)
 except ValueError:expected=declaration(version,source_actor_sha256=source_sha256)
 expected['source_actor_sha256']=source_sha256
 if version=='student_motion31_training_v1':
  from .motion_training import declaration as motion_declaration
  expected=motion_declaration(source_sha256,recipe.get('stage'),reward_version=recipe.get('reward',{}).get('version'))
  if recipe.get('course_version'):
   from .motion_course import implementation
   course=implementation(recipe['course_version'])
   if type(recipe.get('course_stage')) is not int or recipe['course_stage'] not in range(len(course.TARGETS)) or recipe['stage']!=recipe['course_stage']:raise ValueError('explicit course recipe differs')
   expected.update(course_version=course.VERSION,course_stage=recipe['course_stage'])
  if recipe.get('smoke_wiring'):
   from .motion_training import short_wiring
   from .motion_tracking_reward import QUALITY_VERSIONS
   allowed=[short_wiring()]
   if recipe.get('course_version'):
    from .motion_startup import smoke_profile
    allowed.append(smoke_profile())
   if recipe['reward']['version'] not in QUALITY_VERSIONS or recipe['smoke_wiring'] not in allowed:raise ValueError('short smoke explicit quality profile differs')
   expected['smoke_wiring']=recipe['smoke_wiring']
 for name in ('milestones','selected_rollouts_smoke','selected_rollouts_formal','final_seeds'):
  values=recipe.get(name)
  if not isinstance(values,list) or any(type(v) is not int or v<1 for v in values) or values!=sorted(set(values)):
   raise ValueError('invalid instance '+name)
  if name=='final_seeds' and not values:raise ValueError('final evaluation seeds required')
  expected[name]=values
 maximum=recipe.get('storage_max_bytes')
 if type(maximum) is not int or maximum<=0:raise ValueError('instance storage ceiling required')
 expected['storage_max_bytes']=maximum
 if recipe!=expected:raise ValueError('student recipe algorithm/reward or initialization contract differs')
 return expected

def validate(spec):
 if spec.get('student_training',{}).get('version')=='student_motion31_training_v1':
  from .motion_training_requests import validate
  return validate(spec)
 if spec.get('recovery_course'):
  from .course_requests import validate as validate_course
  return validate_course(spec)
 errors=[]
 try:expected_recipe=validate_instance(spec.get('student_training'),spec.get('source_sha256'))
 except (ValueError,TypeError):expected_recipe=None
 if spec.get('interface_version')!='multiskill_mcu_v2' or spec.get('student_training')!=expected_recipe or expected_recipe is None:errors.append('Recovery student training recipe absent/differs')
 if spec.get('source_sha256')!=(expected_recipe or {}).get('source_actor_sha256'):errors.append('fixed student Actor source differs')
 p=spec.get('ppo',{})
 for key,value in {'envs':64,'steps_per_env':128,'hidden_dims':[128,64,32],'learning_rate':3e-5,'epochs':4,'minibatches':4,'gamma':.99,'lam':.95,'clip':.2,'value_coef':.5,'entropy_coef':.001,'max_grad_norm':1.}.items():
  if p.get(key)!=value:errors.append('student PPO '+key+' differs')
 for key in ('retention','receiver_training','source_evidence_reference','initialization_candidate','motion_handoff'):
  if key in spec:errors.append('inherited '+key+' forbidden')
 recovery=spec.get('recovery',{})
 for key in ('support_record_reward','drawback_guidance','progress_guard','retention_regression_policy','wheel_mean_auxiliary','leg_center_auxiliary','exploration_initialization','reverse_curriculum'):
  if key in recovery:errors.append('inherited recovery '+key+' forbidden')
 sampling=recovery.get('sampling',{})
 rehearsal=bool(expected_recipe and expected_recipe.get('standing_rehearsal'))
 standing=bool(expected_recipe and expected_recipe['version'] in (STANDING_RECIPE,MOTION_MIRROR_RECIPE,SLIDING_RECIPE,'student_standing_alignment034_v12','student_standing_zero_privileged49_v13','student_standing_survival_quality_v14'))
 expected_sampling={'version':'fixed_environment_families_v1','family_weights':{'swing_candidate_from_historical_r1':.5,'motion_native_normal':.5},'environment_counts':{'swing_candidate_from_historical_r1':32,'motion_native_normal':32}} if rehearsal else {'version':'family_weights_v1','family_weights':{'swing_candidate_from_historical_r1':1.0}}
 expected_assessment={'families':['swing_candidate_from_historical_r1','motion_native_normal'],'retained_families':['motion_native_normal']} if rehearsal else {'families':['swing_candidate_from_historical_r1'],'retained_families':[]}
 if standing:
  expected_sampling={'version':'family_weights_v1','family_weights':{'motion_native_normal':1.}}
  expected_assessment={'families':['motion_native_normal'],'retained_families':[]}
 if sampling!=expected_sampling or recovery.get('assessment')!=expected_assessment:errors.append('student declared family sampling differs')
 if spec.get('restore_source_rng') is not False or spec.get('restore_recovery_curriculum') is not False:errors.append('source RNG/course restore forbidden')
 budget=spec.get('budget',{})
 try:
  from native_stand.command_v6.domain.execution_limits import validate_budget
  validate_budget(spec)
 except (ValueError,KeyError,TypeError) as exc:errors.append('student execution limits: '+str(exc))
 if expected_recipe is None or spec.get('reward')!=expected_recipe['reward']:errors.append('effective student reward differs')
 cases=spec.get('student_evaluation',{}).get('cases',[])
 expected=[('student_native','student',20261010,0.),('student_yaw10','student',20261010,.01),('student_yaw11','student',20261011,.01),('student_yaw12','student',20261012,.01),('teacher_combination_native','teacher_combination',20261010,0.)]
 if rehearsal:expected.insert(4,('student_standing_perturbed','student',20261016,.01))
 if standing:expected=[('normal_native','student',20261010,0.),('normal_yaw10','student',20261010,.01),('normal_yaw11','student',20261011,.01),('student_native','student',20261010,0.),('teacher_normal_native','teacher_normal',20261010,0.)]
 if expected_recipe and expected_recipe['version'] in ('student_standing_alignment034_v12','student_standing_zero_privileged49_v13','student_standing_survival_quality_v14'):expected=[r for r in expected if r[0]!='student_native']
 if expected_recipe and expected_recipe['version']=='student_standing_survival_quality_v14':expected=[r for r in expected if r[1]=='student']
 if [(r.get('case_id'),r.get('kind'),r.get('seed'),r.get('yaw_rad')) for r in cases]!=expected or any(r.get('family')!=('motion_native_normal' if standing and r.get('case_id')!='student_native' or r.get('case_id')=='student_standing_perturbed' else 'swing_candidate_from_historical_r1') or r.get('role')!='RecoveryStudent' for r in cases):errors.append('common student assessment matrix differs')
 if recovery.get('standing_task',{}).get('retention') or recovery.get('standing_task',{}).get('training_episode') or recovery.get('rising_task'):errors.append('legacy hold/retention/rise deadline forbidden')
 return errors
