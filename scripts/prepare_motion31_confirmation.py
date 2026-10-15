"""Prepare trained Motion31 L1 three-seed confirmation, PPO0, no auto curriculum."""
import argparse,copy,json,os
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.motion_confirmation import VERSION,SEEDS,verify
from native_stand.students.motion_guard import protocol
from native_stand.students.motion_training import commands
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]
def prepare(parent_spec,checkpoint,*,write=False):
 parent=Path(parent_spec).resolve();checkpoint=Path(checkpoint).resolve();s=copy.deepcopy(json.loads(parent.read_text()));name=new_experiment_name('motion31_u1600_three_seed_ppo0');folder=ROOT/'configs/experiments'/name
 # Shared runtime consumes the original training declaration; no optimizer is instantiated.
 s.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=sha(checkpoint),evaluation_only=True,
  motion_confirmation={'version':VERSION,'parent_spec':str(parent),'parent_spec_sha256':sha(parent),'checkpoint_sha256':sha(checkpoint),'seeds':SEEDS},motion_assessment=protocol(),
  authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'user agreed route: absolute pitch .1/roll .05 and three-seed source confirmation; PPO0 only, no next online budget'},notifications={'enabled':True})
 s['evaluation'].update(protocol_identity=protocol()['version'],run_final_durability=False)
 s['student_evaluation']={'version':protocol()['version'],'cases':[{'case_id':f'seed_{seed}_command_{i}','kind':'student','role':'MotionZeroStudent','checkpoint':str(checkpoint),'sha256':sha(checkpoint),'family':'motion_native_normal','seed':seed,'yaw_rad':0.,'seconds':31.52,'command':v+[.34]} for seed in SEEDS for i,v in enumerate(commands(0))],'max_output_bytes':512*2**20}
 s['artifacts'].update(run_name=name,storage_max_bytes=2*2**30)
 s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,formal_samples=0,sample_limit=0,source_eval_wall_s=0,smoke_wall_s=0,formal_wall_s=0,evaluation_wall_s=10800,chain_wall_s=10800)
 s['student_dependencies'].update({str(parent):sha(parent),str(checkpoint):sha(checkpoint)})
 s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':'user permits GPU0 sharing; this approval runs one15-case bounded PPO0 confirmation only'}
 from native_stand.students.requests import validate
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'smoke':0,'formal':0,'evaluate':1,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':0}
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'checkpoint':str(checkpoint),'sha256':sha(checkpoint),'cases':15,'environments_per_case':8,'scored_episodes':120,'eval_seeds':SEEDS,'wall_s':10800,'storage_max_bytes':2*2**30,'new_online_updates':0,'simulation':0,'files_written':0}
 if write:
  from native_stand.students.motion_reward_audit import audit
  from native_stand.students import motion_tracking_reward
  snapshot=audit(s['reward']);snapshot.update(source_sha256=sha(checkpoint),reward_source_sha256=sha(motion_tracking_reward.__file__))
  publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report,'reward_snapshot.json':snapshot},s['student_dependencies'],completion_marker=True);report['files_written']=5
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.parent_spec,a.checkpoint,write=a.write),indent=2))
