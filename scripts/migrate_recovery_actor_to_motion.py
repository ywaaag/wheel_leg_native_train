"""Publish an independent Motion initialization Actor; default zero-write CPU plan."""
import argparse,io,json,hashlib,os
from pathlib import Path
import numpy as np
import torch
from native_stand.students.model import load
from native_stand.students.data import sha
from native_stand.students.motion_transfer import transfer_actor,compare
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
ROOT=Path(__file__).resolve().parents[1]

def migrate(checkpoint,parent_spec,expected_sha,evaluation,write=False):
 cp=Path(checkpoint).resolve();parent=Path(parent_spec).resolve();evaluation=Path(evaluation).resolve()
 raw=json.loads(evaluation.read_text());trace=(evaluation.parent/raw['trace']['path']).resolve()
 if not trace.is_relative_to(evaluation.parent) or sha(trace)!=raw['trace']['sha256'] or raw['checkpoint_sha256']!=expected_sha:raise ValueError('reference evaluation/trace/checkpoint SHA differs')
 for p in (cp,parent,trace,evaluation):
  if not p.is_relative_to(ROOT):raise ValueError('inputs must belong to this project')
 if sha(cp)!=expected_sha:raise ValueError('source checkpoint SHA differs')
 source,data=load(cp,'RecoveryStudent');spec=json.loads(parent.read_text())
 if data.get('spec_sha256')!=sha(parent) or data.get('asset_sha256')!=spec['asset_sha256'] or data.get('recipe_version')!=spec['student_training']['version']:raise ValueError('source checkpoint/spec/asset identity differs')
 if sha(spec['asset_path'])!=spec['asset_sha256']:raise ValueError('asset SHA differs')
 with np.load(trace,allow_pickle=False) as archive:
  x=torch.from_numpy(archive['actor_input'].reshape(-1,31).copy())
 mask=(x[:,25]==0)&(x[:,26]==1)&(x[:,27]==0);x=x[mask]
 if not len(x):raise ValueError('trace has no Recovery inputs')
 x=x[::max(1,len(x)//3000)][:3000];student=transfer_actor(source);proof=compare(source,student,x)
 if proof['mapped_action_max']>1e-6 or not proof['std_equal']:raise ValueError('function-preserving transfer failed')
 changes=[k for k,v in student.state_dict().items() if not torch.equal(v,source.state_dict()[k])]
 if changes!=['mlp.0.weight']:raise ValueError('unexpected Actor changes')
 for col in range(31):
  if col!=25 and not torch.equal(source.mlp[0].weight[:,col],student.mlp[0].weight[:,col]):raise ValueError('non-Motion input column changed')
 name=new_experiment_name('motion31_from_recovery_u300');out=ROOT/'isolated'/name
 inputs={str(p):sha(p) for p in (cp,parent,trace,evaluation,Path(spec['asset_path']),Path(__file__),ROOT/'src/native_stand/students/motion_transfer.py')}
 metadata={'version':'recovery_to_motion_actor_column_transfer_v1','source_checkpoint':str(cp),'source_sha256':expected_sha,'source_spec':str(parent),'source_spec_sha256':sha(parent),
  'mapping':{'source_skill':'Recovery','destination_skill':'Motion','source_first_layer_column':26,'destination_first_layer_column':25},
  'target_height_m':.34,'source_capability':'normal stance30s survival and alignment improvements; full quality gate failed; Swing and motion not certified',
  'initialization_only':True,'critic_initialization':'not transferred; fresh49D Critic planned for new Motion recipe','optimizer_initialization':'not transferred; new Adam planned','RNG_restored':False}
 saved={'interface_version':data['interface_version'],'role':'MotionZeroStudent','actor':student.state_dict(),'asset_sha256':data['asset_sha256'],
  'source_sha256':expected_sha,'source_spec_sha256':sha(parent),'migration':metadata,'actor_interface':spec['student_interface'],
  'dataset_sha256':data['dataset_sha256'],'manifest_sha256':data['manifest_sha256'],'offline_bc_steps':data.get('offline_bc_steps',0),
  'accepted':False,'online_updates':0,'distillation_steps':0}
 # No inherited recipe_version/update/critic/optimizer: this is a new Actor seed, not a resumed Recovery run.
 buffer=io.BytesIO();torch.save(saved,buffer);content=buffer.getvalue();digest=hashlib.sha256(content).hexdigest()
 result={'experiment':name,'output':str(out),'checkpoint':str(out/'motion_actor_initial.pt'),'checkpoint_sha256':digest,'inputs':inputs,'proof':proof,'migration':metadata,
  'actor_layers':[31,128,64,32,6],'actor_output':'Tanh mean with unchanged unsquashed Gaussian std',
  'physical_action_contract':{'action':spec['action'],'control':spec['control']},'training_ready':False,
  'remaining_work':['versioned Motion reward/task/critic initialization','real vx/yaw commands to Actor and task clock','independent zero-command and bidirectional evaluation','new budget/spec/ledger and explicit runtime authorization'],
  'simulation':0,'online_PPO':0,'CPU_optimizer_updates':0,'distillation_steps':0,'files_written':0}
 if write:
  out.mkdir(parents=True,exist_ok=False)
  try:
   with (out/'motion_actor_initial.pt').open('xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
   reloaded,_=load(out/'motion_actor_initial.pt','MotionZeroStudent')
   if not all(torch.equal(v,reloaded.state_dict()[k]) for k,v in student.state_dict().items()):raise ValueError('checkpoint roundtrip differs')
   if any(sha(p)!=h for p,h in inputs.items()):raise ValueError('source inputs changed during publication')
   result['files_written']=3
   with (out/'manifest.json').open('x') as f:json.dump(result,f,indent=2)
   with (out/'publication_complete.json').open('x') as f:json.dump({'status':'COMPLETE','files':{'motion_actor_initial.pt':digest,'manifest.json':sha(out/'manifest.json')}},f,indent=2)
  except BaseException:
   # Only files in the just-created owned directory can be removed on failed publication.
   for p in out.iterdir():p.unlink()
   out.rmdir();raise
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',required=True);p.add_argument('--parent-spec',required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--reference-evaluation',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
 print(json.dumps(migrate(a.checkpoint,a.parent_spec,a.expected_sha256,a.reference_evaluation,a.write),indent=2))
