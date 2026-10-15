"""Versioned update700 Actor -> zero speed/49D Critic; publish only, never launch."""
import copy,json,os,argparse
from pathlib import Path
from native_stand.students.standing_zero_privileged import RECIPE,SOURCE,contract
from native_stand.students.training_recipe import declaration
from native_stand.students.requests import validate
from native_stand.students.data import sha
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,differences
ROOT=Path(__file__).resolve().parents[1]

def prepare(write=False):
 parent=ROOT/'runs/2026_10_13-17_16__student_standing034_alignment_v12/formal/source_snapshot/spec.json'
 original=json.loads(parent.read_text());s=copy.deepcopy(original)
 cp=parent.parents[1]/'model_update_700.pt'
 if sha(cp)!=SOURCE:raise ValueError('update700 source SHA differs')
 name=new_experiment_name('standing034_zero_privileged49_v13');folder=ROOT/'configs/experiments'/name
 for k in ('recovery_course','engineering_recovery','source_evidence_reference','initialization_candidate','student_temporal_regularization'):s.pop(k,None)
 s.update(experiment=name,source_checkpoint=str(cp),source_sha256=SOURCE,
  student_training=declaration(RECIPE),reward=declaration(RECIPE)['reward'],student_interface=contract(),
  observation={'frame_dim':22,'actor_dim':31,'critic_dim':49},execution_source_root=str(ROOT/'src'),
  authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'user authorizes update700 combined zero-speed reward and privileged49 training1000 updates'},
  resources={'mode':'shared','sharing_authorized':True,'authorization_note':'user sharedGPU0 preference and current combined1000update approval'},
  notifications={'enabled':True},restore_source_rng=False,restore_recovery_curriculum=False)
 s['artifacts']['run_name']=name
 for case in s['student_evaluation']['cases']:
  if case['kind']=='student':case.update(checkpoint=str(cp),sha256=SOURCE)
 # Inputs remain full ancestry evidence; no copying or overwriting historical artifacts.
 s['student_dependencies'][str(cp)]=SOURCE;s['student_dependencies'][str(parent)]=sha(parent)
 errors=validate(s)
 if errors:raise ValueError(errors)
 b={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':12,'formal':988,'evaluate':0,'play':0},
  'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0,
  'total_online_PPO_limit':1000,'scope':'new inclusive1000update budget, including smoke and critic warmup','wall_deadline':None}
 inputs={str(parent):sha(parent),str(cp):SOURCE,**s['student_dependencies']}
 result={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'source_sha256':SOURCE,
  'recipe':s['student_training'],'changes':differences(original,s),'simulation':0,'ppo':0,'files_written':0}
 if write:
  publish(folder,{'spec.json':s,'budget.json':b,'preparation_manifest.json':result},inputs,completion_marker=True)
  result['files_written']=4
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
 print(json.dumps(prepare(a.write),indent=2))
