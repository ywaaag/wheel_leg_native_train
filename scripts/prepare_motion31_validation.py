"""Prepare migrated Motion Actor fixed-command PPO0; no launch or training quota."""
import json,copy,argparse,os
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.motion_validation import protocol,VERSION
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]
def prepare(actor_manifest,write=False,*,performance=False,physical_gpu=0,gpu_uuid=None):
 mpath=Path(actor_manifest).resolve();m=json.loads(mpath.read_text());cp=Path(m['checkpoint']);parent=Path(m['migration']['source_spec'])
 marker=json.loads(mpath.with_name('publication_complete.json').read_text())
 if sha(cp)!=m['checkpoint_sha256'] or marker['files']['manifest.json']!=sha(mpath) or marker['files']['motion_actor_initial.pt']!=sha(cp):raise ValueError('migration publication SHA differs')
 s=copy.deepcopy(json.loads(parent.read_text()));name=new_experiment_name('motion31_u300_fixed_command_ppo0');folder=ROOT/'configs/experiments'/name
 for k in ('student_training','student_storage_resume','wiring_smoke','student_survival_probe'):s.pop(k,None)
 s.update(experiment=name,source_checkpoint=str(cp),source_sha256=sha(cp),evaluation_only=True,student_motion_validation=protocol(),
  authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'user approves migrated Motion capability validation, PPO0 only'},notifications={'enabled':True})
 if physical_gpu not in (0,1):raise ValueError('physical GPU must be0 or1')
 if physical_gpu!=s['device']['physical_index'] and not gpu_uuid:raise ValueError('changing physical GPU requires explicit UUID')
 if gpu_uuid is not None:
  if not gpu_uuid.startswith('GPU-'):raise ValueError('explicit GPU UUID required')
  s['device'].update(physical_index=physical_gpu,uuid=gpu_uuid,logical='cuda:0')
 if performance:
  from native_stand.students.performance import VERSION as PERF_VERSION
  s['performance']={'version':PERF_VERSION,'evaluation_gpu_buffer':True,'evaluation_reuse_environment':True,'training_gpu_statistics':False,'failure_tail_on_device':False,'trace_buffer_max_bytes':256*2**20}
 rows=[]
 for i,v in enumerate(protocol()['commands_mps']):rows.append({'case_id':f'motion_{i}_vx_{v:+g}','kind':'student','role':'MotionZeroStudent','checkpoint':str(cp),'sha256':sha(cp),'family':'motion_native_normal','seed':20261014,'yaw_rad':0.,'seconds':31.52,'command':[v,0.,.34]})
 s['student_evaluation']={'version':VERSION,'cases':rows,'max_output_bytes':512*2**20}
 s['artifacts']['run_name']=name;s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,sample_limit=0,formal_samples=0,source_eval_wall_s=0,smoke_wall_s=0,formal_wall_s=0,evaluation_wall_s=3600,chain_wall_s=3600)
 s['student_dependencies'].update({str(mpath):sha(mpath),str(cp):sha(cp),str(parent):sha(parent)})
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'smoke':0,'formal':0,'evaluate':1,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':0}
 r={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'commands':protocol()['commands_mps'],'scored_episodes':40,'controlled_seconds_each':30.,'evaluation_wall_s':3600,'online_PPO':0,'simulation':0,'files_written':0}
 if write:publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':r},s['student_dependencies'],completion_marker=True);r['files_written']=4
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--actor-manifest',required=True);p.add_argument('--write',action='store_true');p.add_argument('--performance',action='store_true');p.add_argument('--physical-gpu',type=int,choices=(0,1),default=0);p.add_argument('--gpu-uuid');a=p.parse_args();print(json.dumps(prepare(a.actor_manifest,a.write,performance=a.performance,physical_gpu=a.physical_gpu,gpu_uuid=a.gpu_uuid),indent=2))
