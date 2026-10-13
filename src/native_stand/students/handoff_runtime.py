"""Frozen 31D student prefix, then native Motion; shared HandoffEnv physics."""
import torch
from native_stand.recovery.handoff_runtime import HandoffEnv
from native_stand.recovery.domain import Mode
from .mcu_interface import encode
from .handoff_probe import owners

class StudentMotionProbeEnv(HandoffEnv):
 def __init__(self,*args,**kwargs):
  self.probe_ready=False
  super().__init__(*args,**kwargs)
  self.prefix_leg_scale=1.5
  self.probe_ready=True
  self.probe_student_obs=None
 def control_owner_pre(self):
  return owners(self.fsm.mode==int(Mode.INITIALIZING),self.initialization_checked,self.executed_prefix,self.switch_steps)
 def _pre_physics_step(self,actions):
  owner,student,motion=self.control_owner_pre()
  self.probe_owner_pre=owner.clone()
  super()._pre_physics_step(actions)
  self.controller.copy_(owner)
 def _get_observations(self):
  legacy=super()._get_observations()
  if not getattr(self,'probe_ready',False):return legacy
  angular,gravity=self._motion_state();d=self.robot.data
  initial=self.fsm.mode==int(Mode.INITIALIZING)
  self.probe_student_obs=encode(angular,gravity,d.joint_pos.torch[:,self.ids],d.joint_vel.torch[:,self.ids],self.executed_leg,torch.where(initial[:,None],0.,self.executed_wheel),self.reference,'Recovery',self.reference.new_tensor([0.,0.,.40]).expand(self.num_envs,-1))
  return legacy
