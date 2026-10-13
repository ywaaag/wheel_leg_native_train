"""Deterministic Actor-only ONNX and fixed golden-vector CPU comparison."""
import json,shutil,copy
from pathlib import Path
import numpy as np
import torch
from .model import load
from .data import sha
from . import mcu_interface as interface

class DeterministicActor(torch.nn.Module):
 def __init__(self,actor):super().__init__();self.mlp=copy.deepcopy(actor.mlp)
 def forward(self,x):return torch.tanh(self.mlp(x))

def vectors(root,dataset,role):
 data=torch.load(dataset,map_location='cpu',weights_only=False);selected=torch.linspace(0,len(data['x'])-1,96).long()
 xs=[data['x'][selected]];categories=['teacher_preaction']*len(selected);provenance={str(dataset):sha(dataset)}
 # Actual v1 failure trajectories: same physical fields, new command encoding.
 old=Path(root)/'runs/2026_10_11-00_55__student_independent_swing_ppo0';index=0 if role=='RecoveryStudent' else 8
 ev=old/f'evaluation_{index:02}.json';saved=json.loads(ev.read_text());trace=old/saved['trace']['path'];assert sha(trace)==saved['trace']['sha256'];provenance[str(ev)]=sha(ev);provenance[str(trace)]=sha(trace)
 with np.load(trace) as z:
  valid=z['first_episode_valid']&z['actor_valid'][:,:,0].astype(bool);points=np.argwhere(valid);points=points[np.linspace(0,len(points)-1,64).astype(int)]
  ids=saved['field_schema']['active_indices'];batch=[]
  for t,e in points:
   current=torch.tensor(z['actor_input'][t,e,:1173].reshape(51,23)[-1,:22])[None]
   q=torch.tensor(z['joint_q_pre'][t,e,ids])[None];dq=torch.tensor(z['joint_dq_pre'][t,e,ids])[None];prev=torch.tensor(z['previous_targets'][t,e])[None]
   batch.append(interface.encode(current[:,:3]/.25,current[:,3:6],q,dq,prev[:,:4],prev[:,4:],torch.zeros_like(q),'Recovery' if role=='RecoveryStudent' else 'Motion',torch.tensor([[0.,0.,.4]]))[0])
  xs.append(torch.stack(batch));categories+=['actual_v1_student_failure']*len(batch)
 # Legal deterministic boundary envelopes; no capability claim or future labels.
 g=torch.Generator().manual_seed(20261011);n=32;q=(torch.rand(n,6,generator=g)*2-1)*1.5;dq=(torch.rand(n,6,generator=g)*2-1)*50
 gravity=torch.randn(n,3,generator=g);gravity/=torch.linalg.vector_norm(gravity,dim=-1,keepdim=True)
 boundary=interface.encode(torch.randn(n,3,generator=g)*8,gravity,q,dq,q[:,interface.LEGS],(torch.rand(n,2,generator=g)*2-1)*100,torch.zeros(n,6),'Recovery' if role=='RecoveryStudent' else 'Motion',torch.tensor([[0.,0.,.4]]).repeat(n,1))
 xs.append(boundary);categories+=['legal_input_envelope_not_reachable_certificate']*n
 # Reset and handoff records from audited raw teacher matrices, named schemas.
 manifest=json.loads(Path(dataset).with_name('manifest.json').read_text());ep=next(e for e in manifest['episodes'] if e['role']==role);run,case,eid=ep['name'].split('/');source=Path(root)/'runs'/run;ev=source/f'evaluation_{int(case):02}.json';saved=json.loads(ev.read_text());trace=source/saved['trace']['path'];ids=saved['field_schema']['active_indices'];eid=int(eid)
 provenance[str(ev)]=sha(ev);provenance[str(trace)]=sha(trace)
 with np.load(trace) as z:
  ctrl=z['controller'][:,eid,0];switch=np.flatnonzero(ctrl==2)[0]
  for t in [0,max(0,switch-1),switch,min(switch+1,len(ctrl)-1)]:
   f=torch.tensor(z['recovery_frame'][t,eid])[None];q=torch.tensor(z['joint_q_pre'][t,eid,ids])[None];dq=torch.tensor(z['joint_dq_pre'][t,eid,ids])[None];prev=torch.tensor(z['target_pre'][t,eid])[None]
   xs.append(interface.encode(f[:,:3]/.25,f[:,3:6],q,dq,prev[:,:4],prev[:,4:],torch.zeros_like(q),'Recovery' if role=='RecoveryStudent' else 'Motion',torch.tensor([[0.,0.,.4]])));categories.append('reset_or_teacher_handoff')
 return torch.cat(xs).float(),categories,provenance

def export(checkpoint,dataset,output,root):
 import onnx
 from onnx.reference import ReferenceEvaluator
 output=Path(output)
 if output.exists():raise FileExistsError(output)
 actor,cp=load(checkpoint);assert cp['interface_version']==interface.VERSION
 torch.set_num_threads(4);output.mkdir(parents=True);model=DeterministicActor(actor).eval();x,categories,provenance=vectors(root,dataset,cp['role'])
 onnx_path=output/'actor.onnx'
 with torch.inference_mode():
  torch.onnx.export(model,torch.zeros(1,31),onnx_path,input_names=['input'],output_names=['mean'],opset_version=17,dynamo=False)
  expected=model(x).numpy()
 graph=onnx.load(onnx_path);onnx.checker.check_model(graph,full_check=True)
 assert [d.dim_value for d in graph.graph.input[0].type.tensor_type.shape.dim]==[1,31]
 evaluator=ReferenceEvaluator(graph);actual=np.concatenate([evaluator.run(None,{'input':row[None]})[0] for row in x.numpy()]);error=np.abs(expected-actual)
 np.savez_compressed(output/'golden_vectors.npz',input=x.numpy(),pytorch_mean=expected,onnx_mean=actual,category=np.array(categories))
 parameters=sum(p.numel() for p in model.parameters());mac=sum(m.in_features*m.out_features for m in model.mlp if isinstance(m,torch.nn.Linear))
 assert parameters==14630 and mac==14400
 report={'interface_version':interface.VERSION,'role':cp['role'],'checkpoint':str(Path(checkpoint).resolve()),'checkpoint_sha256':sha(checkpoint),'model_sha256':sha(onnx_path),'contract':interface.contract(),
  'input_shape':[1,31],'output_shape':[1,6],'dtype':'float32','actor_parameters':parameters,'fp32_weight_bytes':parameters*4,'linear_mac':mac,'onnx_file_bytes':onnx_path.stat().st_size,
  'operators':sorted(set(n.op_type for n in graph.graph.node)),'initializer_parameter_count':sum(np.prod(t.dims) for t in graph.graph.initializer).item(),
  'backend':'onnx.reference.ReferenceEvaluator, CPU float32; ONNX Runtime unavailable','normalized_max_abs_error':float(error.max()),'physical_leg_max_abs_error_rad':float(error[:,interface.LEGS].max()*1.5),'physical_wheel_max_abs_error_rad_s':float(error[:,interface.WHEELS].max()*100),
  'per_category':{c:{'vectors':categories.count(c),'max_abs_error':float(error[np.array(categories)==c].max())} for c in sorted(set(categories))},
  'numerical_pass':bool(error.max()<=1e-5),'golden_sha256':sha(output/'golden_vectors.npz'),'vector_sources':provenance,
  'st_tool':next((shutil.which(t) for t in ['stedgeai','stm32ai'] if shutil.which(t)),None),'hardware':'HARDWARE_UNVERIFIED','not_included_in_weight_bytes':['critic','std','runtime','activation','firmware'],
  'estimated_intermediate_float32_activation_bytes':4*(31+128+64+32+6),'activation_note':'sum of forward tensors only; not ST allocation or SRAM/stack measurement',
  'deployment':{'preprocess':'mcu_interface.encode, fields/units in contract; no history, skill constant for full episode','decode':'mcu_interface.targets: clip action→leg1.5/wheel100→declared actual limits→cache→PD','cpu_timing_is_not_MCU_measurement':True}}
 assert report['initializer_parameter_count']==14630
 (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 if not report['numerical_pass']:raise ValueError('ONNX tolerance failed; report saved')
 return report
