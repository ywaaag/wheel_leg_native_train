"""Independent update988 thirty-second survival diagnostic; publish, not launch."""
import json,copy,os,argparse
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.requests import validate
from native_stand.students.survival_probe import declaration,VERSION
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]

def prepare(write=False):
 parent=ROOT/'configs/experiments/2026_10_13-22_14__standing034_zero_privileged49_v13/spec.json'
 cp=ROOT/'runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt'
 expected='2af573b318d7ebd6df7b1a5919c5ea58e873e5d24761905ba773f8ab02cc72cd'
 if sha(cp)!=expected:raise ValueError('update988 source SHA differs')
 s=copy.deepcopy(json.loads(parent.read_text()));name=new_experiment_name('v13_u988_survival30_ppo0');folder=ROOT/'configs/experiments'/name
 s.pop('student_training',None);s.pop('wiring_smoke',None)
 s.update(experiment=name,source_checkpoint=str(cp),source_sha256=expected,evaluation_only=True,
  student_survival_probe=declaration(),execution_source_root=str(ROOT/'src'),
  authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'user agrees next step: independent30s8env survival diagnostic only, PPO0'},notifications={'enabled':False})
 row=copy.deepcopy(s['student_evaluation']['cases'][0]);row.update(case_id='u988_normal_survival30',checkpoint=str(cp),sha256=expected,seconds=31.52,yaw_rad=0.)
 s['student_evaluation']={'version':VERSION,'cases':[row],'max_output_bytes':256*2**20}
 s['artifacts']['run_name']=name;s['curriculum']['episode_length_s']=31.52;s['recovery']['fsm']['timeout_s']=31.52
 s['evaluation']['seconds']=31.52;s['evaluation']['run_final_durability']=False
 s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,sample_limit=0,formal_samples=0,
  source_eval_wall_s=0,smoke_wall_s=0,formal_wall_s=0,chain_wall_s=900,evaluation_wall_s=900)
 s['student_dependencies'][str(parent)]=sha(parent);s['student_dependencies'][str(cp)]=expected
 errors=validate(s)
 if errors:raise ValueError(errors)
 b={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'smoke':0,'formal':0,'evaluate':1,'play':0},
  'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'sample_limit':0,'source_eval_wall_used_s':0.}
 r={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'wall_s':900,'scored_envs':8,'controlled_seconds':30.,'PPO':0,'files_written':0}
 if write:publish(folder,{'spec.json':s,'budget.json':b,'preparation.json':r},s['student_dependencies'],completion_marker=True);r['files_written']=4
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.write),indent=2))
