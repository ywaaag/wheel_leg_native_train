"""Publish one finite512-env straight1.5/2 then yaw1/1.5 course; no launch."""
import argparse,copy,json,os
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.motion_course import VERSION,configuration,stage_config,cases
from native_stand.students.motion_guard import configuration as guard,protocol
from native_stand.students.motion_training import declaration,short_wiring
from native_stand.students.motion_tracking_reward import QUALITY_VERSION
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]
def prepare(confirmation_spec,confirmation_run,*,write=False,minimal_startup=True):
 cs=Path(confirmation_spec).resolve();cr=Path(confirmation_run).resolve();confirmed=json.loads(cs.read_text());parent=Path(confirmed['motion_confirmation']['parent_spec']);source=Path(confirmed['source_checkpoint']);s=copy.deepcopy(json.loads(parent.read_text()))
 name=new_experiment_name('motion31_straight_yaw512_course');folder=ROOT/'configs/experiments'/name
 recipe=declaration(sha(source),reward_version=QUALITY_VERSION);recipe.update(course_version=VERSION,course_stage=0,smoke_wiring=short_wiring(),milestones=list(range(250,1996,250)))
 s.pop('motion_confirmation',None);s.pop('evaluation_only',None)
 s.update(experiment=name,source_checkpoint=str(source),source_sha256=sha(source),student_training=recipe,reward=recipe['reward'],motion_assessment=protocol(),
  motion_course={'configuration':configuration(),'source_parent_spec':str(parent),'source_parent_spec_sha256':sha(parent),'confirmation_spec':str(cs),'confirmation_spec_sha256':sha(cs),'confirmation_run':str(cr),'source_recipe_updates':1600},
  motion_training={'version':recipe['version'],'stage':0,'block_index':1,'spec_path':str(folder/'spec.json'),'resume':{},'early_stop_policy':guard()},
  authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'user explicitly authorizes2000 inclusive updates progressive straight1.5/2 and yaw1/1.5; registration pending'},notifications={'enabled':True},phase_initialization='v3/u1600 full Actor/Critic/Adam/std/RNG/refinement; no reward changes, new physical reset; smoke4critic+1actor/formal5critic counted')
 s['curriculum'].update(active_stage=0,stages=[stage_config(0)],schedule_s=recipe['train_schedule_s'],minimum_zero_fraction=.25,episode_length_s=31.52,task_progression=None,future_order=[])
 s['student_evaluation']={'version':protocol()['version'],'cases':cases(confirmed,0),'max_output_bytes':128*2**20}
 s['evaluation'].update(full_every_updates=250,light_every_updates=0,checkpoint_every_updates=250,protocol_identity=protocol()['version'],run_final_durability=False)
 s['artifacts'].update(run_name=name,storage_max_bytes=2*2**30)
 s['budget'].update(source_eval_updates=0,smoke_updates=5,formal_updates=1995,formal_samples=1995*65536,sample_limit=2000*65536,source_eval_wall_s=3600,smoke_wall_s=3600,formal_wall_s=57600,chain_wall_s=64800,evaluation_wall_s=3600,durability_wall_s=0)
 s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':'user authorizes progressive course on inherited physicalGPU0 shared, no preemption or device switch'}
 s['student_dependencies'].update({str(parent):sha(parent),str(source):sha(source),str(cs):sha(cs),str(cr/'terminal_report.json'):sha(cr/'terminal_report.json')})
 if minimal_startup:
  from native_stand.students.motion_startup import build,smoke_profile
  s['student_training']['smoke_wiring']=smoke_profile()
  s['motion_startup']=build(s,[cr])
 from native_stand.students.requests import validate
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':5,'formal':1995,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':2000}
 r={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'source':str(source),'source_sha256':sha(source),'online_limit_inclusive':2000,'smoke_updates':5,'formal_updates':1995,'wall_s':64800,'storage_max_bytes':2*2**30,'stages':[stage_config(i) for i in range(4)],'simulation':0,'files_written':0}
 if write:
  from native_stand.students.motion_reward_audit import audit
  from native_stand.students import motion_tracking_reward
  snap=audit(s['reward']);snap.update(source_sha256=sha(source),reward_source_sha256=sha(motion_tracking_reward.__file__))
  publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':r,'reward_snapshot.json':snap},s['student_dependencies'],completion_marker=True);r['files_written']=5
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--confirmation-spec',required=True);p.add_argument('--confirmation-run',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.confirmation_spec,a.confirmation_run,write=a.write),indent=2))
