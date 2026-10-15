"""CPU-only one authorized Motion31 successor declaration; zero-write by default."""
import argparse,copy,hashlib,json
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.motion_successor import VERSION,verify
from native_stand.students.motion_training import declaration,protocol,short_wiring,SOURCE
from native_stand.students.motion_tracking_reward import SUCCESSOR_VERSION
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,differences
ROOT=Path(__file__).resolve().parents[1]
def digest(d):return hashlib.sha256((json.dumps(d,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
def prepare(authorization,selection,*,write=False):
 auth_path=Path(authorization).resolve();review_path=Path(selection).resolve();auth=json.loads(auth_path.read_text());review=json.loads(review_path.read_text());parent_path=Path(review['parent_spec']);before=json.loads(parent_path.read_text());s=copy.deepcopy(before);chosen=review['selected']
 if auth['parent_run']!=review['parent_run'] or auth['owner_session']!=before['authorization']['hapi_session']:raise ValueError('successor owner/parent conflict')
 name=new_experiment_name('motion31_hold_level512_v4');folder=ROOT/'configs/experiments'/name;source=Path(chosen['checkpoint']);task={'version':'motion31_block_task_v1','formal_limit':2000,'source_sha256':SOURCE,'automatic_next_block':False,'registry_dir':str(folder/'task_blocks')}
 recipe=declaration(chosen['sha256'],reward_version=SUCCESSOR_VERSION);recipe['milestones']=list(range(100,1996,100));recipe['smoke_wiring']=short_wiring()
 assessment=protocol(quality=True,successor=True)
 cfg={'version':recipe['version'],'stage':0,'block_index':1,'spec_path':str(folder/'spec.json'),'task_manifest':str(folder/'task_manifest.json'),'task_manifest_sha256':digest(task),'resume':{},'execution_profile':'motion31_parallel512_2000_v1',
  'successor':{'version':VERSION,'authorization_path':str(auth_path),'authorization_sha256':sha(auth_path),'selection_path':str(review_path),'selection_sha256':sha(review_path),'parent_run':review['parent_run'],'parent_spec':str(parent_path),'parent_spec_sha256':sha(parent_path),'parent_recipe_updates':chosen['update'],'initialization':'full Actor/Critic/Adam/std/RNG/refinement; reward-change warmup4 smoke/5 formal; physical new reset'}}
 s.update(experiment=name,source_checkpoint=str(source),source_sha256=chosen['sha256'],student_training=recipe,reward=recipe['reward'],motion_assessment=assessment,motion_training=cfg,
  authorization={'status':'UNAUTHORIZED','hapi_session':auth['owner_session'],'user_scope':'user explicitly authorized one post-terminal successor; registered separately before submission'},
  notifications={'enabled':True},phase_initialization=cfg['successor']['initialization'])
 s['curriculum'].update(schedule_s=recipe['train_schedule_s'])
 s['evaluation'].update(protocol_identity=assessment['version'])
 s['student_evaluation'].update(version=assessment['version'])
 for row in s['student_evaluation']['cases']:row.update(checkpoint=str(source),sha256=chosen['sha256'])
 s['artifacts'].update(run_name=name)
 s['budget'].update(source_eval_updates=0,smoke_updates=5,formal_updates=1995,formal_samples=1995*65536,sample_limit=2000*65536,source_eval_wall_s=3600,smoke_wall_s=3600,formal_wall_s=57600,chain_wall_s=64800)
 s['student_dependencies']={str(parent_path):sha(parent_path),str(source):sha(source),str(auth_path):sha(auth_path),str(review_path):sha(review_path)}
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':5,'formal':1995,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':2000}
 from native_stand.students.requests import validate
 errors=validate(s,motion_task_data=task)
 if errors:raise ValueError(errors)
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'source_checkpoint':str(source),'source_sha256':chosen['sha256'],'online_limit':2000,'smoke_updates':5,'formal_updates':1995,'simulation':0,'files_written':0,'differences':differences(before,s)}
 if write:
  from native_stand.students.motion_reward_audit import audit
  from native_stand.students import motion_tracking_reward
  snapshot=audit(s['reward']);snapshot.update(spec_sha256=digest(s),source_sha256=chosen['sha256'],reward_source_sha256=sha(motion_tracking_reward.__file__))
  payload={'spec.json':s,'budget.json':book,'task_manifest.json':task,'task_blocks/block_0001.json':{'index':1,'spec':str(folder/'spec.json'),'planned_spec_sha256':digest(s)},'reward_snapshot.json':snapshot,'preparation.json':report}
  # A published single-use claim prevents spending this future authorization twice.
  claim_root=ROOT/'configs/experiments/.motion_successor_claims';claim_root.mkdir(exist_ok=True)
  claim=claim_root/(sha(auth_path)+'.json')
  with claim.open('x') as f:json.dump({'destination':str(folder),'authorization_sha256':sha(auth_path)},f)
  try:publish(folder,payload,s['student_dependencies'],completion_marker=True)
  except BaseException:claim.unlink();raise
  report['files_written']=8
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--authorization',required=True);p.add_argument('--selection',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.authorization,a.selection,write=a.write),indent=2))
