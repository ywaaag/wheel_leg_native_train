"""Fresh v14 proposal using shared tools; UNAUTHORIZED, never launch."""
import argparse,copy,json,os
from pathlib import Path
from native_stand.students.training_recipe import declaration
from native_stand.students.standing_survival_task import RECIPE,SOURCE
from native_stand.students.requests import validate
from native_stand.students.data import sha
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,differences
ROOT=Path(__file__).resolve().parents[1]

def prepare(write=False,formal_updates=974,smoke_updates=26,notify=False):
 if type(formal_updates) is not int or formal_updates<1:raise ValueError('formal update ceiling required')
 if type(smoke_updates) is not int or smoke_updates<6:raise ValueError('smoke must include post-warmup Actor update')
 parent=ROOT/'configs/experiments/2026_10_13-22_14__standing034_zero_privileged49_v13/spec.json'
 cp=ROOT/'runs/2026_10_13-22_14__standing034_zero_privileged49_v13/formal/model_update_988.pt'
 if sha(cp)!=SOURCE:raise ValueError('source update988 SHA differs')
 original=json.loads(parent.read_text());s=copy.deepcopy(original)
 name=new_experiment_name('standing034_survival_quality_v14_wiring2');folder=ROOT/'configs/experiments'/name
 recipe=declaration(RECIPE);recipe['milestones']=sorted(set(list(range(100,formal_updates+1,100))+[formal_updates]))
 s.update(experiment=name,source_checkpoint=str(cp),source_sha256=SOURCE,student_training=recipe,reward=recipe['reward'],execution_source_root=str(ROOT/'src'),
  authorization={'status':'UNAUTHORIZED','hapi_session':os.environ.get('HAPI_SESSION_ID'),'user_scope':'CPU preparation only; proposed1000inclusive updates require new approval'},
  notifications={'enabled':notify})
 s.pop('student_survival_probe',None)
 s['artifacts']['run_name']=name;s['artifacts']['storage_max_bytes']=recipe['storage_max_bytes']
 s['curriculum']['episode_length_s']=31.52;s['recovery']['fsm']['timeout_s']=31.52
 s['student_evaluation']['cases']=[c for c in s['student_evaluation']['cases'] if c['kind']=='student']
 for c in s['student_evaluation']['cases']:c.update(checkpoint=str(cp),sha256=SOURCE,seconds=31.52)
 total=smoke_updates+formal_updates
 s['budget'].update(source_eval_updates=0,smoke_updates=smoke_updates,formal_updates=formal_updates,sample_limit=total*8192,formal_samples=formal_updates*8192,
  source_eval_wall_s=1800,smoke_wall_s=3600,formal_wall_s=None,chain_wall_s=None)
 s['student_dependencies'][str(parent)]=sha(parent);s['student_dependencies'][str(cp)]=SOURCE
 errors=validate(s)
 if errors:raise ValueError(errors)
 b={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':smoke_updates,'formal':formal_updates,'evaluate':0,'play':0},
  'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':total}
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'proposed_updates':total,'source_sha256':SOURCE,
  'changes':differences(original,s),'simulation':0,'ppo':0,'files_written':0,'status':'PREPARED_UNAUTHORIZED'}
 if write:
  publish(folder,{'spec.json':s,'budget.json':b,'preparation.json':report},s['student_dependencies'],completion_marker=True)
  report['files_written']=4
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--formal-updates',type=int,default=974);p.add_argument('--smoke-updates',type=int,default=26);p.add_argument('--notify',action='store_true');a=p.parse_args()
 print(json.dumps(prepare(a.write,a.formal_updates,a.smoke_updates,a.notify),indent=2))
