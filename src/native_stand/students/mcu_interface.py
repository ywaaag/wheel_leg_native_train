"""Explicit MCU v2 pure current-frame encoder; same physical axes as v1."""
import torch
from .interface import frame,labels,targets,LEGS,WHEELS,ORDER
VERSION='multiskill_mcu_v2'
ACTOR_DIM=31
CRITIC_DIM=40
SKILLS=('Motion','Recovery','Jump')
JUMPS=('NONE','SMALL','BIG')
def contract():
 from .interface import contract as legacy
 c=legacy();c.update(version=VERSION,frame_dim=22,frames=1,frame_valid_dim=0,task_dim=9,actor_dim=31,critic_dim=40,
  history_order='none',history_fill='none',task_fields=['vx/4','yaw_rate/4','height/.5','Motion','Recovery','Jump','NONE','SMALL','BIG'],
  previous_target_semantics='actual post-action/post-mechanical-limit target, four legs then two wheels; reset declared initialization target',
  quaternion='xyzw',height_command_m=.40,actor_hidden_dims=[128,64,32],critic_hidden_dims=[256,128,64],
  imu_calibration='simulation USD root body frame; hardware IMU-to-body calibration NOT_VERIFIED',
  joint_calibration='native named rad/rad_s; hardware encoder zero/gear conversion NOT_VERIFIED')
 return c

def task(skill,command,jump='NONE'):
 if skill not in SKILLS or jump not in JUMPS or command.shape[-1]!=3 or not torch.isfinite(command).all():raise ValueError('explicit MCU task/three commands required')
 one=command.new_zeros((*command.shape[:-1],6));one[...,SKILLS.index(skill)]=1;one[...,3+JUMPS.index(jump)]=1
 return torch.cat((command/command.new_tensor([4.,4.,.5]),one),-1)

def actor_input(current,commands):
 if current.shape[-1]!=22 or commands.shape!=(*current.shape[:-1],9):raise ValueError('31D current/task layout differs')
 out=torch.cat((current,commands),-1)
 if not torch.isfinite(out).all():raise ValueError('nonfinite MCU input')
 return out

def encode(angular_body,gravity_body,q,dq,previous_legs,previous_wheels,reference,skill,command,jump='NONE'):
 return actor_input(frame(angular_body,gravity_body,q,dq,previous_legs,previous_wheels,reference),task(skill,command,jump))

def critic_input(actor,height,velocity_native,contacts,controlled_s,entry_s,hold_s):
 extra=torch.cat((height[...,None],velocity_native,contacts/100.,controlled_s[...,None]/2.5,entry_s[...,None]/.2,hold_s[...,None]/10.),-1)
 if actor.shape[-1]!=31 or extra.shape[-1]!=9 or not torch.isfinite(extra).all():raise ValueError('40D critic layout differs')
 return torch.cat((actor,extra),-1)

class PolicyClock:
 """Validation metadata only, never an Actor field. Repeated getters are allowed."""
 def __init__(self,n,device='cpu'):self.last=torch.full((n,),float('nan'),dtype=torch.float64,device=device)
 def reset(self,ids):self.last[ids]=float('nan')
 def check(self,time):
  time=time.to(torch.float64);seen=torch.isfinite(self.last);delta=time-self.last
  if not torch.isfinite(time).all() or (seen& (delta.abs()>1e-8) & ((delta-.01).abs()>2e-6)).any():raise ValueError('MCU duplicate jump/missing/nonmonotonic policy time')
  self.last.copy_(time)
