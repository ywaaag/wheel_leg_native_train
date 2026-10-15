"""Fresh versioned v10->normal0.34 alignment PPO declaration; no launch."""
import json,copy,os,argparse
from pathlib import Path
from native_stand.students.standing_alignment import RECIPE,SOURCE
from native_stand.students.training_recipe import declaration
from native_stand.students.requests import validate
from native_stand.students.data import sha
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,differences
ROOT=Path(__file__).resolve().parents[1]

def prepare(write=False):
 parent=ROOT/'runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal/source_snapshot/spec.json'
 original=json.loads(parent.read_text());s=copy.deepcopy(original)
 cp=ROOT/'runs/2026_10_12-13_29__recovery_course_b_prefix180_block0002/formal/model_update_100.pt'
 if sha(cp)!=SOURCE:raise ValueError('v10 source SHA differs')
 name=new_experiment_name('student_standing034_alignment_v12');folder=ROOT/'configs/experiments'/name
 s.update(experiment=name,source_checkpoint=str(cp),source_sha256=SOURCE,source_input_dim=31,student_training=declaration(RECIPE),reward=declaration(RECIPE)['reward'],execution_source_root=str(ROOT/'src'),authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'0.34m stationary alignment,1000 inclusive updates, no wall deadline; explicit runtime registration required'},resources={'mode':'shared','sharing_authorized':True,'authorization_note':'user explicitly allows shared physical GPU0'},notifications={'enabled':True},restore_source_rng=False,restore_recovery_curriculum=False)
 for k in ('recovery_course','engineering_recovery','source_evidence_reference','initialization_candidate','student_temporal_regularization'):s.pop(k,None)
 s['device']={'physical_index':0,'uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72','logical':'cuda:0','headless':True}
 s['artifacts']['run_name']=name;s['control']['height_command_m']=.34
 s['budget'].update(source_eval_updates=0,smoke_updates=12,formal_updates=988,sample_limit=8192000,formal_samples=988*8192,source_eval_wall_s=900,smoke_wall_s=None,formal_wall_s=None,chain_wall_s=None)
 s['student_evaluation']['cases']=[r for r in s['student_evaluation']['cases'] if r['case_id']!='student_native']
 for case in s['student_evaluation']['cases']:
  if case['kind']=='student':case.update(checkpoint=str(cp),sha256=SOURCE)
 s['student_evaluation']['max_output_bytes']=128*2**20
 s['student_training']['storage_max_bytes']=4*2**30
 # Preserve exact declaration: version owns storage ceiling.
 s['student_training']=declaration(RECIPE)
 s['student_dependencies'][str(cp)]=sha(cp);s['student_dependencies'][str(parent)]=sha(parent)
 # Source teaching provenance is inherited by v10; keep and check its exact manifest.
 v10=json.loads((cp.parent/'source_snapshot/spec.json').read_text())
 for p,h in v10['student_dependencies'].items():
  if 'manifest.json' in p:
   if sha(p)!=h:raise ValueError('source teaching identity changed')
   s['student_dependencies'][p]=h
 errors=validate(s)
 if errors:raise ValueError(errors)
 b={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'smoke':12,'formal':988,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0,'total_online_PPO_limit':1000,'scope':'new independent1000update budget incl smoke/warmup; not extension of historical ledger','wall_deadline':None}
 inputs={str(parent):sha(parent),str(cp):sha(cp)}
 inputs.update(s['student_dependencies'])
 result={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'source_sha256':SOURCE,'recipe':s['student_training'],'changes':differences(original,s),'simulation':0,'ppo':0,'files_written':0}
 if write:publish(folder,{'spec.json':s,'budget.json':b,'preparation_manifest.json':result},inputs,completion_marker=True);result['files_written']=4
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.write),indent=2))
