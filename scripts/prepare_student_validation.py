"""Fresh UNAUTHORIZED student/teacher PPO0 declaration; default zero-write."""
import copy,json,argparse
from pathlib import Path
from native_stand.students.interface import VERSION,contract
from native_stand.students.data import sha
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]
def prepare(write=False,*,parent_spec,recovery_checkpoint,motion_checkpoint,dataset_manifest,interface_version=VERSION,standing_check=False,comparison_checkpoint=None):
 from native_stand.students.mcu_interface import contract as mcu_contract
 mcu=interface_version=="multiskill_mcu_v2"
 if interface_version not in (VERSION,"multiskill_mcu_v2"):raise ValueError("unknown interface version")
 base=Path(parent_spec).resolve();s=json.loads(base.read_text())
 if s.get('interface_version')!=interface_version:raise ValueError('explicit parent interface differs')
 from native_stand.students.model import load
 rec=Path(recovery_checkpoint).resolve();mot=Path(motion_checkpoint).resolve();manifest=Path(dataset_manifest).resolve()
 source_models=[load(rec,'RecoveryStudent')[1],load(mot,'MotionZeroStudent' if mcu else 'MotionStudent')[1]]
 for model in source_models:
  if model['interface_version']!=interface_version or model['manifest_sha256']!=sha(manifest):raise ValueError('source interface/dataset manifest differs from explicit inputs')
 dataset=json.loads(manifest.read_text());dataset_inputs={}
 if dataset.get('interface_version')!=interface_version:raise ValueError('dataset manifest interface differs')
 for model in source_models:
  row=dataset.get(model['role'],{})
  if row.get('sha256')!=model['dataset_sha256']:raise ValueError('source dataset SHA differs from manifest role')
  data_path=(manifest.parent/row['file']).resolve()
  if not data_path.is_relative_to(manifest.parent.resolve()) or sha(data_path)!=row['sha256']:raise ValueError('dataset file identity differs')
  dataset_inputs[str(data_path)]=row['sha256']
 name=new_experiment_name('recovery_standing_distilled_ppo0' if standing_check else 'mcu_v2_student_independent_ppo0' if mcu else 'student_independent_swing_ppo0');folder=ROOT/'configs/experiments'/name
 for key in ('motion_handoff','action_distribution','initialization_candidate','source_evidence_reference','source_spec_sha256','source_asset_sha256','source_update','receiver_training','student_training','recovery_course','student_temporal_regularization'):s.pop(key,None)
 teachers=copy.deepcopy(s.get('student_teachers'))
 if not isinstance(teachers,list) or len(teachers)!=2 or len({row['checkpoint'] for row in teachers})!=2:
  raise ValueError('parent must bind two distinct teachers explicitly')
 for row in teachers:
  for field,hash_key in (('checkpoint','sha256'),('spec','spec_sha256')):
   if sha(row[field])!=row[hash_key]:raise ValueError('parent teacher '+field+' SHA differs')
 by_checkpoint={str(Path(row['checkpoint']).resolve()):row for row in teachers}
 ordered=[]
 for kind in ('teacher_combination','teacher_normal'):
  bindings={(str(Path(row['checkpoint']).resolve()),row['sha256']) for row in s.get('student_evaluation',{}).get('cases',[]) if row.get('kind')==kind}
  if len(bindings)!=1:raise ValueError('parent teacher case identity missing/ambiguous: '+kind)
  checkpoint,expected=next(iter(bindings));row=by_checkpoint.get(checkpoint)
  if row is None or row['sha256']!=expected:raise ValueError('parent teacher case SHA differs')
  ordered.append(row)
 teachers=ordered
 s.update(experiment=name,evaluation_only=True,interface_version=interface_version,student_interface=mcu_contract() if mcu else contract(),source_checkpoint=str(rec),source_sha256=sha(rec),student_teachers=teachers,
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
  if comparison_checkpoint is None:raise ValueError('standing comparison requires explicit comparison checkpoint')
  old=Path(comparison_checkpoint).resolve()
  load(old,'RecoveryStudent')
  cases=[normal,{**normal,'case_id':'recovery_original_normal','checkpoint':str(old),'sha256':sha(old)},cases[-1],cases[0]]
 s['student_evaluation']={'version':'student_evaluation_v1','cases':cases,'max_output_bytes':512*2**20}
 original_library=Path(s['recovery']['pose_library'])
 if sha(original_library)!=s['recovery']['pose_library_sha256']:raise ValueError('parent pose library SHA differs')
 lib=json.loads(original_library.read_text());encoded=(json.dumps(lib,indent=2)+'\n').encode();import hashlib
 s['recovery']['pose_library']=str(folder/'poses.json');s['recovery']['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
 dependencies={**dataset_inputs,**{str(p):sha(p) for p in (rec,mot,base,manifest,original_library)}}
 for row in cases:dependencies[row['checkpoint']]=row['sha256']
 for teacher in teachers:
  for field in ('checkpoint','spec'):dependencies[teacher[field]]=sha(teacher[field])
 for field in ('asset_path','asset_module_path','colleague_config_path'):
  actual=sha(s[field])
  if actual!=s[field.removesuffix('_path')+'_sha256']:raise ValueError('parent '+field+' SHA differs')
  dependencies[s[field]]=actual
 s['student_dependencies']=dependencies
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'sample_limit':0,'source_eval_wall_used_s':0.,'hapi_session':None}
 report={'experiment':name,'spec':str(folder/'spec.json'),'ledger':str(folder/'budget.json'),'PPO':0,'optimizer':0,'score_episodes':len(cases)*8,'simulated_envs':64,'scored_envs':8,'wall_s':1800,'storage_bytes':512*2**20,'status':'UNAUTHORIZED_NOT_RUN','physical_gpu':None,'resource_check':'NOT_RUN','files_written':5 if write else 0,'parent_spec':str(base),'parent_spec_sha256':sha(base),'source_models':[{'checkpoint':str(cp),'sha256':sha(cp),'interface':model['interface_version'],'manifest_sha256':model['manifest_sha256']} for cp,model in zip((rec,mot),source_models)],'runtime':'implemented, physical unverified','interface_version':interface_version}
 from native_stand.command_v6.tools.experiment_preparation import differences
 report['requested_changes']=differences(json.loads(base.read_text()),s)
 if write:publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report},dependencies,completion_marker=True,serialized_files={'poses.json':(encoded,s['recovery']['pose_library_sha256'])})
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--interface-version',choices=[VERSION,'multiskill_mcu_v2'],default=VERSION);p.add_argument('--parent-spec',required=True);p.add_argument('--recovery-checkpoint',required=True);p.add_argument('--motion-checkpoint',required=True);p.add_argument('--dataset-manifest',required=True);p.add_argument('--comparison-checkpoint');p.add_argument('--standing-check',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.write,parent_spec=a.parent_spec,comparison_checkpoint=a.comparison_checkpoint,interface_version=a.interface_version,recovery_checkpoint=a.recovery_checkpoint,motion_checkpoint=a.motion_checkpoint,dataset_manifest=a.dataset_manifest,standing_check=a.standing_check),indent=2))
