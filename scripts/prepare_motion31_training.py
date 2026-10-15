"""CPU-only Motion block publication; never authorize, reserve or launch."""
import argparse,copy,hashlib,json
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.motion_training import SOURCE,VERSION,commands,declaration,protocol,stage_config
from native_stand.students.motion_privileged import contract
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,differences

ROOT=Path(__file__).resolve().parents[1]
def json_sha(value):return hashlib.sha256((json.dumps(value,indent=2,allow_nan=False)+'\n').encode()).hexdigest()

def prepare(parent_spec,*,write=False,formal_updates=300,hapi_session=None,task_manifest=None,checkpoint=None,stage=0,envs=64,notify=False,tracking_refinement=False,quality_termination=False,consumption_parent=None,smoke_updates=None):
 if envs not in (64,512):raise ValueError('explicit Motion env count64/512 required')
 parallel=envs==512;ceiling=2000 if parallel else 300
 if type(formal_updates) is not int or not 100<=formal_updates<=ceiling:raise ValueError('Motion formal budget outside declared execution profile')
 if parallel and (task_manifest or stage):raise ValueError('512 first experiment must use original source atL1')
 if tracking_refinement and (not parallel or task_manifest):raise ValueError('refinement first experiment requires512 original-source L1')
 if quality_termination and (not parallel or task_manifest or not consumption_parent):raise ValueError('quality version needs512 original-source L1 and settled consumption parent')
 if smoke_updates is not None and (not quality_termination or smoke_updates!=5):raise ValueError('only explicit quality smoke5 override supported')
 parent_path=Path(parent_spec).resolve();before=json.loads(parent_path.read_text());s=copy.deepcopy(before)
 name=new_experiment_name('motion31_parallel512_l1_2000' if parallel else 'motion31_tracking_block01');folder=ROOT/'configs/experiments'/name;resume={};block=1
 if task_manifest:
  task_path=Path(task_manifest).resolve();task=json.loads(task_path.read_text());block=before['motion_training']['block_index']+1
  if not Path(task['registry_dir']).resolve().is_relative_to(ROOT/'configs/experiments'):raise ValueError('Motion task registry must remain inside project configs')
  name=new_experiment_name(f'motion31_tracking_block{block:02}');folder=ROOT/'configs/experiments'/name
  if not checkpoint:raise ValueError('evaluated parent checkpoint required')
  import torch
  data=torch.load(checkpoint,map_location='cpu',weights_only=False)
  resume={'parent_spec':str(parent_path),'parent_spec_sha256':sha(parent_path),'formal_dir':str(Path(checkpoint).resolve().parent),'parent_recipe_updates':data['recipe_updates']}
 else:
  if stage!=0 or before.get('source_sha256')!=SOURCE:raise ValueError('first block requires original migrated Actor and L1')
  task_path=folder/'task_manifest.json'
  # Stable task identity plus exclusive append-only per-block registrations;
  # later experiments use their actual preparation timestamp.
  task={'version':'motion31_block_task_v1','formal_limit':2000,'source_sha256':SOURCE,'automatic_next_block':False,
    'registry_dir':str(folder/'task_blocks')}
 source=Path(checkpoint or before['source_checkpoint']).resolve()
 if not source.is_file() or (not resume and sha(source)!=SOURCE):raise ValueError('Motion source checkpoint identity differs')
 for key in ('evaluation_only','student_motion_validation','student_survival_probe','student_storage_resume','recovery_course','student_temporal_regularization','wiring_smoke'):
  s.pop(key,None)
 recipe=declaration(sha(source),stage)
 if tracking_refinement:
  from native_stand.students.motion_tracking_reward import REFINEMENT_VERSION
  recipe=declaration(sha(source),stage,reward_version=REFINEMENT_VERSION)
  name=new_experiment_name('motion31_wide_narrow512_2000');folder=ROOT/'configs/experiments'/name
  task_path=folder/'task_manifest.json';task['registry_dir']=str(folder/'task_blocks')
 prior=None
 if quality_termination:
  from native_stand.students.motion_tracking_reward import QUALITY_VERSION
  from native_stand.students.motion_quality_budget import consumption
  prior=consumption(consumption_parent)
  recipe=declaration(sha(source),stage,reward_version=QUALITY_VERSION)
  name=new_experiment_name('motion31_posture_quality512_v3');folder=ROOT/'configs/experiments'/name
  task_path=folder/'task_manifest.json';task['registry_dir']=str(folder/'task_blocks');task['historical_consumption']=prior
 recipe['milestones']=list(range(100,formal_updates+1,100))
 if smoke_updates==5:
  from native_stand.students.motion_training import short_wiring
  recipe['smoke_wiring']=short_wiring()
 s.update(experiment=name,source_checkpoint=str(source),source_sha256=sha(source),task='recovery',
  student_training=recipe,reward=recipe['reward'],student_interface=contract(),motion_assessment=protocol(quality=quality_termination),
  motion_training={'version':VERSION,'stage':stage,'block_index':block,'spec_path':str(folder/'spec.json'),'task_manifest':str(task_path),'task_manifest_sha256':json_sha(task),'resume':resume},
  authorization={'status':'UNAUTHORIZED','hapi_session':hapi_session,'user_scope':'CPU-prepared Motion block; simulation/PPO require separate explicit approval'},
  notifications={'enabled':notify},phase_initialization='Actor/std transfer; fresh Motion49 Critic/Adam first block; full Actor/Critic/Adam/std/RNG on continuation; new physical reset')
 s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':'planned physicalGPU0 sharing requested by user; this is resource policy only, new online budget remains UNAUTHORIZED'}
 if parallel:s['motion_training']['execution_profile']='motion31_parallel512_2000_v1'
 if prior:s['motion_training']['prior_consumption']=prior
 s['ppo']['envs']=envs
 s['curriculum'].update(active_stage=0,stages=[stage_config(stage,envs)],schedule_s=recipe['train_schedule_s'],minimum_zero_fraction=.25,episode_length_s=31.52,episode_curriculum=None,task_progression=None,future_order=[])
 s['artifacts'].update(run_name=name,storage_max_bytes=2*2**30)
 s['evaluation'].update(seconds=31.52,light_every_updates=0,full_every_updates=100,checkpoint_every_updates=100,run_final_durability=False,protocol_identity=protocol(quality=quality_termination)['version'])
 s['performance']={'version':'student_tensor_statistics_v1','evaluation_gpu_buffer':True,'evaluation_reuse_environment':True,'training_gpu_statistics':True,'failure_tail_on_device':True,'trace_buffer_max_bytes':256*2**20}
 from native_stand.students.performance import VERSION as PERF
 s['performance']['version']=PERF
 smoke=0 if resume else smoke_updates or 50
 unit=envs*128;wall=64800 if parallel else 14400
 if prior:wall-=prior['historical_wall_s']
 s['budget'].update(source_eval_updates=0,smoke_updates=smoke,formal_updates=formal_updates,formal_samples=formal_updates*unit,
  sample_limit=(formal_updates+smoke)*unit,source_eval_wall_s=3600,smoke_wall_s=3600,formal_wall_s=wall-7200 if tracking_refinement or quality_termination else wall,chain_wall_s=wall,evaluation_wall_s=3600,durability_wall_s=0)
 rows=[{'case_id':f'motion_{i:02}','kind':'student','role':'MotionZeroStudent','checkpoint':str(source),'sha256':sha(source),
   'family':'motion_native_normal','seed':20261014,'yaw_rad':0.,'seconds':31.52,'command':v+[.34]} for i,v in enumerate(commands(stage))]
 s['student_evaluation']={'version':protocol(quality=quality_termination)['version'],'cases':rows,'max_output_bytes':128*2**20}
 if prior:
  s['student_dependencies'].update({prior['parent_spec']:prior['parent_spec_sha256'],prior['parent_ledger']:prior['parent_ledger_sha256'],prior['parent_terminal']:prior['parent_terminal_sha256']})
 # Retain inherited teacher manifest for provenance, not runtime teacher use.
 s['student_dependencies'].update({str(parent_path):sha(parent_path),str(source):sha(source)})
 errors=validate(s,motion_task_data=task)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':smoke,'formal':formal_updates,'evaluate':0,'play':0},
  'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':smoke+formal_updates}
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'source':str(source),'source_sha256':sha(source),
  'task_manifest':str(task_path),'task_formal_limit':2000,'block_index':block,'stage':stage,'formal_updates':formal_updates,'smoke_updates':smoke,
  'total_online_updates':formal_updates+smoke,'envs':envs,'samples_per_update':unit,'block_wall_s':wall,'block_storage_bytes':2*2**30,
  'commands':commands(stage),'slot_counts':stage_config(stage,envs)['slot_counts'],'differences':differences(before,s),
  'authorization':'UNAUTHORIZED','simulation':0,'online_PPO':0,'files_written':0}
 if write:
  if prior:
   claims=ROOT/'configs/experiments/.motion_quality_consumption_claims';claims.mkdir(exist_ok=True)
   with (claims/(prior['parent_spec_sha256']+'.json')).open('x') as f:json.dump({'destination':name},f)
  from native_stand.students.motion_reward_audit import audit
  from native_stand.students import motion_tracking_reward
  reward_snapshot=audit(s['reward']);reward_snapshot.update(spec_sha256=json_sha(s),source_sha256=s['source_sha256'],reward_source_sha256=sha(Path(motion_tracking_reward.__file__)))
  payloads={'spec.json':s,'budget.json':book,'preparation.json':report,'reward_snapshot.json':reward_snapshot}
  if not task_manifest:payloads['task_manifest.json']=task
  registration={'index':block,'spec':str(folder/'spec.json'),'planned_spec_sha256':json_sha(s)}
  if not task_manifest:payloads[f'task_blocks/block_{block:04}.json']=registration
  publish(folder,payloads,s['student_dependencies'],completion_marker=True);report['files_written']=len(payloads)+1
  if task_manifest:
   registered=Path(task['registry_dir'])/f'block_{block:04}.json'
   with registered.open('x') as stream:json.dump(registration,stream,indent=2)
   report['files_written']+=1
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',required=True);p.add_argument('--formal-updates',type=int,default=300)
 p.add_argument('--hapi-session');p.add_argument('--task-manifest');p.add_argument('--checkpoint');p.add_argument('--stage',type=int,default=0);p.add_argument('--write',action='store_true')
 p.add_argument('--envs',type=int,choices=(64,512),default=64)
 p.add_argument('--notify',action='store_true',help='record requested current-owner terminal notification; does not authorize execution')
 p.add_argument('--tracking-refinement',action='store_true',help='explicit v2 evidence-gated wide/narrow mixture, keeps Huber and weights')
 p.add_argument('--quality-termination',action='store_true');p.add_argument('--consumption-parent',help='settled explicitly user-stopped predecessor, never resets cumulative budget')
 p.add_argument('--smoke-updates',type=int,choices=(5,))
 a=p.parse_args();print(json.dumps(prepare(a.parent_spec,write=a.write,formal_updates=a.formal_updates,hapi_session=a.hapi_session,task_manifest=a.task_manifest,checkpoint=a.checkpoint,stage=a.stage,envs=a.envs,notify=a.notify,tracking_refinement=a.tracking_refinement,quality_termination=a.quality_termination,consumption_parent=a.consumption_parent,smoke_updates=a.smoke_updates),indent=2))
