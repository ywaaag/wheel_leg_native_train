"""CPU-safe same-interface Actor transfer; no environment, reward or optimizer."""
import copy
import torch
from .mcu_interface import VERSION,SKILLS,contract

def transfer_actor(source):
 if source.interface_version!=VERSION or not source.is_actor:raise ValueError('explicit MCU v2 Actor required')
 c=contract();first=source.mlp[0]
 if first.in_features!=c['actor_dim'] or first.out_features!=c['actor_hidden_dims'][0]:raise ValueError('Actor topology differs')
 # 22 physical fields, three commands, then Motion/Recovery/Jump one-hot.
 offset=c['frame_dim']+3
 student=copy.deepcopy(source)
 with torch.no_grad():student.mlp[0].weight[:,offset+SKILLS.index('Motion')].copy_(source.mlp[0].weight[:,offset+SKILLS.index('Recovery')])
 return student

def compare(source,student,recovery_observations):
 x=recovery_observations
 if x.ndim!=2 or x.shape[1]!=31 or not len(x) or not torch.isfinite(x).all():raise ValueError('finite31D observations required')
 if not torch.all(x[:,25]==0) or not torch.all(x[:,26]==1) or not torch.all(x[:,27]==0):raise ValueError('Recovery one-hot samples required')
 motion=x.clone();motion[:,25]=1;motion[:,26]=0
 with torch.no_grad():
  teacher=source(x);naive=source(motion);new=student(motion)
 return {'samples':len(x),'naive_switch_action_mae':float((naive-teacher).abs().mean()),
  'naive_switch_action_max':float((naive-teacher).abs().max()),'mapped_action_max':float((new-teacher).abs().max()),
  'std_equal':torch.equal(source.log_std,student.log_std),'scope':'CPU forward identity only; no motion capability evidence'}
