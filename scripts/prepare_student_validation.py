"""Fresh UNAUTHORIZED student/teacher PPO0 declaration; default zero-write."""
import copy,json,argparse
from pathlib import Path
from native_stand.students.interface import VERSION,contract
from native_stand.students.data import sha,B50,B250
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]
def prepare(write=False,*,interface_version=VERSION,recovery_checkpoint=None,motion_checkpoint=None,dataset_manifest=None,standing_check=False):
 from native_stand.students.mcu_interface import contract as mcu_contract
 mcu=interface_version=="multiskill_mcu_v2"
 if interface_version not in (VERSION,"multiskill_mcu_v2"):raise ValueError("unknown interface version")
 base=ROOT/'configs/experiments/2026_10_10-22_24__receiver_window_ppo0/spec.json';s=json.loads(base.read_text())
 name=new_experiment_name('recovery_standing_distilled_ppo0' if standing_check else 'mcu_v2_student_independent_ppo0' if mcu else 'student_independent_swing_ppo0');folder=ROOT/'configs/experiments'/name
 for key in ('motion_handoff','action_distribution','initialization_candidate','source_evidence_reference','source_spec_sha256','source_asset_sha256','source_update','receiver_training'):s.pop(key,None)
 rec=Path(recovery_checkpoint) if recovery_checkpoint else ROOT/'isolated/recovery_student_bc_20261011/best_validation.pt';mot=Path(motion_checkpoint) if motion_checkpoint else ROOT/'isolated/motion_student_zero_bc_20261011/best_validation.pt'
 manifest=Path(dataset_manifest) if dataset_manifest else ROOT/'isolated/student_teachers_20261011/manifest.json'
 teachers=[]
 for checkpoint,expected in [('runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_50.pt',B50),('runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt',B250)]:
  p=ROOT/checkpoint;assert sha(p)==expected;parent=p.parent/'source_snapshot/spec.json';teachers.append({'checkpoint':str(p),'sha256':expected,'spec':str(parent),'spec_sha256':sha(parent)})
 s.update(experiment=name,interface_version=interface_version,student_interface=mcu_contract() if mcu else contract(),source_checkpoint=str(rec),source_sha256=sha(rec),student_teachers=teachers,
   authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'CPU BC only; physical verification needs new approval'},resources={'mode':'exclusive','sharing_authorized':False},notifications={'enabled':False},restore_source_rng=False,restore_recovery_curriculum=False,
   observation={'frame_dim':22,'actor_dim':31 if mcu else 1182,'critic_dim':40 if mcu else 1191},history={'frames':1 if mcu else 51,'dim':0 if mcu else 1173,'includes_current':True,'validity_per_frame':not mcu})
 if mcu:s['ppo']['hidden_dims']=[128,64,32]
 for unused in ('support_record_reward','drawback_guidance','progress_guard','retention_regression_policy','actor_update_scope'):
  s['recovery'].pop(unused,None)
 s['action'].update(dim=6,leg_scale_rad=1.5,leg_pair_radius_rad=0.,wheel_scale_rad_s=100.)
 s['artifacts']['run_name']=name;s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,sample_limit=0,evaluation_wall_s=1800,chain_wall_s=1800)
 s['curriculum']['episode_length_s']=13.52;s['evaluation']['seconds']=13.52;s['evaluation']['envs']=64;s['evaluation']['scored_envs']=8
 cases=[]
 for yaw,seed,label in [(0.,20261010,'native'),(.01,20261010,'yaw10'),(.01,20261011,'yaw11'),(.01,20261012,'yaw12')]:
  for kind,cp,role in [('student',rec,'RecoveryStudent'),('teacher_combination',Path(teachers[0]['checkpoint']),'RecoveryStudent')]:
   cases.append({'case_id':f'{kind}_{label}','kind':kind,'checkpoint':str(cp),'sha256':sha(cp),'family':'swing_candidate_from_historical_r1','seed':seed,'yaw_rad':yaw,'seconds':13.52,'role':role})
 for kind,cp in [('student',mot),('teacher_normal',Path(teachers[1]['checkpoint']))]:
  cases.append({'case_id':f'{kind}_normal_zero','kind':kind,'checkpoint':str(cp),'sha256':sha(cp),'family':'motion_native_normal','seed':20261010,'yaw_rad':0.,'seconds':13.52,'role':'MotionZeroStudent' if mcu else 'MotionStudent'})
 if standing_check:
  if not mcu:raise ValueError('standing transfer requires MCU v2')
  normal={'case_id':'recovery_distilled_normal','kind':'student','checkpoint':str(rec),'sha256':sha(rec),'family':'motion_native_normal','seed':20261010,'yaw_rad':0.,'seconds':13.52,'role':'RecoveryStudent'}
  old=ROOT/'isolated/recovery_mcu_v2_bc_20261011/best_validation.pt'
  cases=[normal,{**normal,'case_id':'recovery_original_normal','checkpoint':str(old),'sha256':sha(old)},cases[-1],cases[0]]
 s['student_evaluation']={'version':'student_evaluation_v1','cases':cases,'max_output_bytes':512*2**20}
 lib=json.loads(Path(s['recovery']['pose_library']).read_text());encoded=(json.dumps(lib,indent=2)+'\n').encode();import hashlib
 s['recovery']['pose_library']=str(folder/'poses.json');s['recovery']['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
 dependencies={str(p):sha(p) for p in (rec,mot,base,manifest)}
 for row in cases:dependencies[row['checkpoint']]=row['sha256']
 for teacher in teachers:
  for field in ('checkpoint','spec'):dependencies[teacher[field]]=sha(teacher[field])
 for field in ('asset_path','asset_module_path','colleague_config_path'):dependencies[s[field]]=sha(s[field])
 s['student_dependencies']=dependencies
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'sample_limit':0,'source_eval_wall_used_s':0.,'hapi_session':None}
 report={'experiment':name,'spec':str(folder/'spec.json'),'ledger':str(folder/'budget.json'),'PPO':0,'optimizer':0,'score_episodes':len(cases)*8,'simulated_envs':64,'scored_envs':8,'wall_s':1800,'storage_bytes':512*2**20,'status':'UNAUTHORIZED_NOT_RUN','physical_gpu':0,'runtime':'implemented, CPU tested, physical unverified','interface_version':interface_version}
 if write:publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report},dependencies,completion_marker=True,serialized_files={'poses.json':(encoded,s['recovery']['pose_library_sha256'])})
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--interface-version',choices=[VERSION,'multiskill_mcu_v2'],default=VERSION);p.add_argument('--recovery-checkpoint');p.add_argument('--motion-checkpoint');p.add_argument('--dataset-manifest');p.add_argument('--standing-check',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.write,interface_version=a.interface_version,recovery_checkpoint=a.recovery_checkpoint,motion_checkpoint=a.motion_checkpoint,dataset_manifest=a.dataset_manifest,standing_check=a.standing_check),indent=2))
