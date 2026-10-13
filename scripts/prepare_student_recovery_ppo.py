"""Public bounded single-student recipe publication; no direct runtime launch."""
import argparse,copy,json,hashlib
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.training_recipe import declaration,NO_FAILURE_RECIPE,LIFT_RATE_RECIPE,REHEARSAL_RECIPE,STANDING_RECIPE,MOTION_MIRROR_RECIPE,SLIDING_RECIPE
from native_stand.students.recovery_task import configuration
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,differences,checked_input
ROOT=Path(__file__).resolve().parents[1]
def prepare(parent_spec,source_checkpoint,*,write=False,output=None,failure_event_zero=False,lift_rate=False,standing_rehearsal=False,standing_only=False,motion_mirror=False,velocity_huber=False):
 if sum((failure_event_zero,lift_rate,standing_rehearsal,standing_only,motion_mirror,velocity_huber))>1:raise ValueError('select one explicit recipe version')
 continuation=motion_mirror or velocity_huber
 standing_only=standing_only or continuation
 base=Path(parent_spec).resolve();checkpoint=Path(source_checkpoint).resolve()
 inputs=dict([checked_input(base),checked_input(checkpoint)])
 original=json.loads(base.read_text());s=copy.deepcopy(original)
 if inputs[str(checkpoint)]!=declaration(SLIDING_RECIPE if velocity_huber else MOTION_MIRROR_RECIPE if motion_mirror else STANDING_RECIPE if standing_only else 'student_recovery_ppo_bc_v1')['source_actor_sha256']:raise ValueError('Source checkpoint SHA differs from frozen recipe')
 from native_stand.students.model import load
 actor,cp=load(checkpoint,'RecoveryStudent')
 if cp['interface_version']!='multiskill_mcu_v2':raise ValueError('Source interface differs')
 if continuation and cp.get('spec_sha256')!=inputs[str(base)]:raise ValueError('continuation own frozen parent spec differs')
 s.update(source_checkpoint=str(checkpoint),source_sha256=inputs[str(checkpoint)])
 name=new_experiment_name('recovery_standing_velocity_huber_from200' if velocity_huber else 'recovery_standing_motion_mirror_from50' if motion_mirror else 'recovery_mcu_v2_standing_from_distilled' if standing_only else 'recovery_mcu_v2_standing_rehearsal_from_bc' if standing_rehearsal else 'recovery_mcu_v2_lift_rate_from_bc' if lift_rate else 'recovery_mcu_v2_failure_zero_from_bc' if failure_event_zero else 'recovery_mcu_v2_task_ppo_from_bc');folder=Path(output).resolve() if output else ROOT/'configs/experiments'/name
 from native_stand.command_v6.domain.experiment_naming import validate_new_experiment_name
 validate_new_experiment_name(folder.name);name=folder.name
 if folder.exists():raise FileExistsError(folder)
 s.update(experiment=name,student_training=declaration(),reward=configuration(),restore_source_rng=False,restore_recovery_curriculum=False,evaluation_only=False)
 if failure_event_zero:
  s['student_training']=declaration(NO_FAILURE_RECIPE);s['reward']=s['student_training']['reward']
 if lift_rate:
  s['student_training']=declaration(LIFT_RATE_RECIPE);s['reward']=s['student_training']['reward']
 if standing_rehearsal:
  s['student_training']=declaration(REHEARSAL_RECIPE);s['reward']=s['student_training']['reward']
 if standing_only:
  s['student_training']=declaration(SLIDING_RECIPE if velocity_huber else MOTION_MIRROR_RECIPE if motion_mirror else STANDING_RECIPE);s['reward']=s['student_training']['reward']
 for key in ('source_evidence_reference','retention','receiver_training','motion_handoff','source_input_dim','source_update','source_spec_sha256','source_asset_sha256','diagnostics'):s.pop(key,None)
 s['budget'].update(source_eval_updates=0,source_eval_wall_s=900,smoke_updates=12,smoke_wall_s=900,formal_updates=100,formal_wall_s=5400,sample_limit=917504,chain_wall_s=7200)
 s['ppo'].update(envs=64,steps_per_env=128,hidden_dims=[128,64,32],learning_rate=3e-5,epochs=4,minibatches=4,gamma=.99,lam=.95,clip=.2,value_coef=.5,entropy_coef=.001,max_grad_norm=1.)
 rec=s['recovery']
 for key in ('support_record_reward','drawback_guidance','progress_guard','retention_regression_policy','wheel_mean_auxiliary','leg_center_auxiliary','exploration_initialization','reverse_curriculum','actor_update_scope','swing_only'):rec.pop(key,None)
 rec['sampling']={'version':'family_weights_v1','family_weights':{'swing_candidate_from_historical_r1':1.}}
 rec['assessment']={'families':['swing_candidate_from_historical_r1'],'retained_families':[]};rec['active_family']='swing_candidate_from_historical_r1'
 rec['fsm']['timeout_s']=13.52
 rec.pop('curriculum',None)
 rec.pop('rising_task',None)
 rec['runtime_initialization_validated']=False
 for key in ('r0_task_declaration','progress_guard_scope','preview_family','physical_gate_evidence','handover_domain_scope','autonomous_stability_note','scope','authorization_note','settling_reward'):
  rec.pop(key,None)
 for key in ('retention','source_baseline_run','reward','training_episode','note'):rec['standing_task'].pop(key,None)
 rec['stand_frozen']=True
 s['curriculum']['episode_length_s']=13.52;s['control']['height_command_m']=.4
 s['evaluation'].update(run_final_durability=False,checkpoint_every_updates=25,full_every_updates=25,full_at_final=True,light_every_updates=0)
 # exact source 32+8 teacher native, no MotionZero row/old skills.
 previous=s['student_evaluation']['cases']
 required=('normal_native','normal_yaw10','normal_yaw11','student_native','teacher_normal_native') if continuation else ('student_native','student_yaw10','student_yaw11','student_yaw12','teacher_combination_native')
 indexed={}
 for row in previous:
  key=row.get('case_id')
  if not isinstance(key,str) or not key or key in indexed:raise ValueError('Missing or duplicate case_id')
  indexed[key]=row
 missing=set(required)-set(indexed)
 if missing:raise ValueError('Required case_id missing: '+str(sorted(missing)))
 s['student_evaluation']['cases']=[copy.deepcopy(indexed[key]) for key in required]
 if standing_only:
  rows=[]
  for key,seed,yaw in [('normal_native',20261010,0.),('normal_yaw10',20261010,.01),('normal_yaw11',20261011,.01)]:
   rows.append({**copy.deepcopy(indexed['student_native']),'case_id':key,'family':'motion_native_normal','seed':seed,'yaw_rad':yaw})
  rows.append(copy.deepcopy(indexed['student_native']))
  teacher=s['student_teachers'][1];rows.append({**rows[0],'case_id':'teacher_normal_native','kind':'teacher_normal','checkpoint':teacher['checkpoint'],'sha256':teacher['sha256']})
  s['student_evaluation']['cases']=rows
  rec['active_family']='motion_native_normal';rec['sampling']={'version':'family_weights_v1','family_weights':{'motion_native_normal':1.}}
  rec['assessment']={'families':['motion_native_normal'],'retained_families':[]}
  s['budget'].update(formal_updates=300,formal_wall_s=10800,sample_limit=2555904,chain_wall_s=12600)
 if standing_rehearsal:
  normal=copy.deepcopy(indexed['student_native']);normal.update(case_id='student_standing_perturbed',family='motion_native_normal',seed=20261016,yaw_rad=.01)
  s['student_evaluation']['cases'].insert(4,normal)
  rec['sampling']={'version':'fixed_environment_families_v1','family_weights':{'swing_candidate_from_historical_r1':.5,'motion_native_normal':.5},'environment_counts':{'swing_candidate_from_historical_r1':32,'motion_native_normal':32}}
  rec['assessment']={'families':['swing_candidate_from_historical_r1','motion_native_normal'],'retained_families':['motion_native_normal']}
 for row in s['student_evaluation']['cases']:
  if row['kind']=='student':row.update(checkpoint=str(checkpoint),sha256=inputs[str(checkpoint)])
  inputs.update([checked_input(row['checkpoint'],row['sha256'])])
 s['student_evaluation']['max_output_bytes']=512*2**20
 s['authorization']={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'fresh task PPO request awaiting explicit registration'}
 s['resources']={'mode':'exclusive','sharing_authorized':False} # preparation grants no shared-GPU approval
 s['notifications']={'enabled':False}
 s['artifacts']['run_name']=name
 s['artifacts']['terminal_reserve_bytes']=128*2**20
 s['wiring_smoke']={'required_event':'completed_episode','required_event_duration_s':.01,'minimum_event_count':1,'event_offset_s':0.}
 inputs.update([checked_input(rec['pose_library'],rec['pose_library_sha256'])])
 lib=json.loads(Path(rec['pose_library']).read_text())
 if standing_rehearsal or standing_only:
  normal=next(p for p in lib['poses'] if p['family']=='motion_native_normal' and p['split']=='holdout' and p['offline_valid'])
  if normal['initialization_control']!='direct_zero_reset':raise ValueError('native normal initialization contract differs')
  if not any(p['family']=='motion_native_normal' and p['split']=='train' for p in lib['poses']):
   train=copy.deepcopy(normal);train.update(pose_id='motion_native_normal_train_rehearsal',split='train');lib['poses'].append(train)
  provenance=normal['normal_initialization_provenance'];inputs.update([checked_input(provenance['path'],provenance['sha256'])])
 encoded=(json.dumps(lib,indent=2)+'\n').encode();rec['pose_library']=str(folder/'poses.json');rec['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
 # Retain only explicit dependency evidence; no date-specific removal.
 unused={r['checkpoint'] for r in previous if r.get('role')!='RecoveryStudent'}
 retained={r['checkpoint'] for r in s['student_evaluation']['cases']}
 for path in unused-retained:s['student_dependencies'].pop(path,None)
 s['student_dependencies'][str(checkpoint)]=inputs[str(checkpoint)]
 if standing_only:
  dataset=ROOT/'isolated/recovery_standing_reset_teacher_data_20261011/RecoveryStudent.pt'
  manifest=dataset.parent/'manifest.json'
  if sha(dataset)!=cp['dataset_sha256'] or sha(manifest)!=cp['manifest_sha256']:raise ValueError('distilled source dataset/manifest binding differs')
  s['student_dependencies'].update({str(dataset):sha(dataset),str(manifest):sha(manifest)})
 if continuation:
  motion_spec=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/spec.json';reward_code=motion_spec.parent/'domain_reward.py'
  s['student_dependencies'].update({str(motion_spec):sha(motion_spec),str(reward_code):sha(reward_code)})
 s['student_dependencies'][str(base)]=sha(base)
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'evaluate':0,'smoke':12,'formal':s['budget']['formal_updates']},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'sample_limit':s['budget']['sample_limit'],'source_eval_wall_used_s':0.,'hapi_session':None}
 for path,expected in s['student_dependencies'].items():inputs.update([checked_input(path,expected)])
 report={'parent_spec':[str(base),inputs[str(base)]],'source_checkpoint':[str(checkpoint),inputs[str(checkpoint)]],
 'requested_changes':differences(original,s),'case_ids':[r['case_id'] for r in s['student_evaluation']['cases']],'files_written':0,'experiment':name,'spec':str(folder/'spec.json'),'ledger':str(folder/'budget.json'),'source_SHA':s['source_sha256'],'recipe':s['student_training'],'online_updates_max':112,'samples_max':917504,'source_score_episodes':48 if standing_rehearsal else 40,'smoke_score_episodes':8,'formal_score_episodes':152 if standing_rehearsal else 128,'all_score_episodes_max':208 if standing_rehearsal else 176,'wall_s':7200,'storage_bytes':2*2**30,'status':'UNAUTHORIZED_NOT_RUN','BC_new_optimizer_steps':0}
 if standing_only:report.update(online_updates_max=312,samples_max=2555904,wall_s=12600,formal_score_episodes=200,all_score_episodes_max=248)
 if write:publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report},inputs,completion_marker=True,serialized_files={'poses.json':(encoded,rec['pose_library_sha256'])})
 if write:report['files_written']=5
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--parent-spec',type=Path);p.add_argument('--source-checkpoint',type=Path)
 p.add_argument('--continuous-course',action='store_true');p.add_argument('--task-directory',type=Path);p.add_argument('--authorization-scope')
 p.add_argument('--recover-task-from',type=Path,help='explicit new approval for unstarted first dynamic-block dispatch; old task ledger remains read-only')
 p.add_argument('--recover-failed-task-from',type=Path,help='explicit new approval after settled v9 runtime stop; fresh contact-cost recipe from saved assessed Actor')
 p.add_argument('--output-dir',type=Path);p.add_argument('--write',action='store_true');p.add_argument('--failure-event-zero',action='store_true');p.add_argument('--lift-rate',action='store_true');p.add_argument('--standing-rehearsal',action='store_true');p.add_argument('--standing-only',action='store_true');p.add_argument('--motion-mirror',action='store_true');p.add_argument('--velocity-huber',action='store_true');a=p.parse_args()
 if a.continuous_course:
  from native_stand.students.course_io import register_task,recover_unstarted_block,recover_failed_block,prepare_block
  if not a.task_directory or not a.authorization_scope:p.error('continuous course requires explicit task directory and authorization scope')
  if a.recover_task_from and a.recover_failed_task_from:p.error('select one recovery type')
  r=recover_failed_block(a.recover_failed_task_from,a.task_directory,a.authorization_scope,write_files=a.write) if a.recover_failed_task_from else recover_unstarted_block(a.recover_task_from,a.task_directory,a.authorization_scope,write_files=a.write) if a.recover_task_from else register_task(a.task_directory,a.authorization_scope,write_files=a.write)
  if a.write:
   book=json.loads(Path(r['manifest']).with_name('task_ledger.json').read_text())
   source=(book.get('next_decision') or {}).get('resume')
   r['first_block']=prepare_block(r['manifest'],source=source,state=book['state'],index=len(book['blocks']),write_files=True,output=a.output_dir)
  print(json.dumps(r,indent=2));raise SystemExit(0)
 if a.parent_spec is None or a.source_checkpoint is None:p.error('parent-spec and source-checkpoint required')
 print(json.dumps(prepare(a.parent_spec,a.source_checkpoint,write=a.write,output=a.output_dir,failure_event_zero=a.failure_event_zero,lift_rate=a.lift_rate,standing_rehearsal=a.standing_rehearsal,standing_only=a.standing_only,motion_mirror=a.motion_mirror,velocity_huber=a.velocity_huber),indent=2))
