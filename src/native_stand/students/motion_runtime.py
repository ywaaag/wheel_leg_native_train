"""Explicit Motion branch; imported only after AppLauncher, shared physical targets."""
import torch
from .runtime import TrainingStudentEnv
from .motion_training import stage_config,effective
from .motion_tracking_reward import reward

class MotionStudentEnv(TrainingStudentEnv):
 def __init__(self,*args,motion_training_config,**kwargs):
  self.motion_training_enabled=False;self.motion_config=motion_training_config
  # Manual preview stays off unless enable_motion_preview is called explicitly.
  self.motion_manual_command=None
  super().__init__(*args,**kwargs)
  if motion_training_config.get('course_version'):
   from .motion_course import implementation
   course_stage=implementation(motion_training_config['course_version']).stage_config
   self.stage_spec=course_stage(motion_training_config['course_stage'],self.num_envs)
  else:self.stage_spec=stage_config(motion_training_config['stage'],self.num_envs)
  # Pure metadata slot_counts is not a sampling mode override.
  self.motion_training_enabled=True;self.critic_privileged_version='motion_privileged49_v1'
  self.motion_cohort_mix=torch.zeros(len(self.stage_spec['commands']),device=self.device)
 def enable_motion_preview(self):
  """Explicit manual preview; training and evaluation keep the scheduled command."""
  if not getattr(self,'motion_training_enabled',False):raise ValueError('Motion preview requires the Motion branch')
  self.motion_manual_command=torch.zeros(self.num_envs,3,device=self.device)
  self.motion_manual_command[:,2]=self.student_command_height
  self.set_motion_manual_command(0.,0.)
  return self.motion_manual_command
 def set_motion_manual_command(self,vx,yaw,height=None):
  """One command source for observation, reward and telemetry; no phase schedule."""
  if self.motion_manual_command is None:raise ValueError('Motion preview is not enabled')
  value=self.motion_manual_command
  value[:,0]=float(vx);value[:,1]=float(yaw)
  value[:,2]=self.student_command_height if height is None else float(height)
  self.target_xy.copy_(value[:,:2]);self.command.copy_(value)
 def _get_observations(self):
  if getattr(self,'motion_training_enabled',False):
   if self.motion_manual_command is not None:
    # Manual preview bypasses entry/ramp/hold/exit; acceleration lives in the input device.
    self.motion_observation_command=self.motion_manual_command.clone()
   else:
    age=self.rise_hold.episode.steps.float()*.01
    self.motion_observation_command=effective(self.target_xy,age,training=self.curriculum_training,config=self.motion_config)
   self.command.copy_(self.motion_observation_command)
  # Base pre-action fields/current-frame cache remain identical; no new RNG draws.
  critic_version=self.critic_privileged_version
  if getattr(self,'motion_training_enabled',False):self.critic_privileged_version=None
  try:obs=super()._get_observations()
  finally:self.critic_privileged_version=critic_version
  if not getattr(self,'motion_training_enabled',False) or not self.student_ready:return obs
  if self.motion_manual_command is not None:
   # Manual preview runs no PPO, so the privileged Critic input is never built.
   self.student_obs=obs;return obs
  from .motion_privileged import critic_input
  d=self.robot.data
  from isaaclab.utils.math import quat_apply_inverse
  vel=quat_apply_inverse(d.root_quat_w.torch,d.root_lin_vel_w.torch);native=torch.stack((-vel[:,2],-vel[:,0],vel[:,1]),-1)
  age=self.rise_hold.episode.steps.float()*.01;times=self.motion_config['train_schedule_s'] if self.curriculum_training else [2.,8.,8.,8.]
  hold=(age>=times[0]+times[1])&(age<sum(times[:3]))
  obs['student_critic']=critic_input(obs['student_actor'],self.root_height,native,self.contact_force,self.command,self.yaw,age,hold,d.applied_torque.torch[:,self.ids])
  self.student_obs=obs;return obs
 def _pre_physics_step(self,action):
  if getattr(self,'motion_training_enabled',False):self.motion_action_command=self.command.clone()
  super()._pre_physics_step(action)
  if self.motion_manual_command is not None:
   # The base step re-derives command from target_xy; keep the single manual source.
   self.target_xy.copy_(self.motion_manual_command[:,:2]);self.command.copy_(self.motion_manual_command)
 def _get_dones(self):
  result=super()._get_dones()
  if not getattr(self,'motion_training_enabled',False) or not self.task_ready:return result
  s=self.recovery_snapshot;p=self.standing_snapshot;d=self.robot.data
  targets=torch.zeros_like(self.student_previous_physical);targets[:,[0,1,3,4]]=self.executed_leg;targets[:,[2,5]]=self.executed_wheel
  narrow=None
  if self.motion_manual_command is None and 'refinement' in self.motion_config['reward']:
   narrow=self.motion_cohort_mix[self.command_index]
  self.student_reward_result=reward(command=self.motion_action_command,target=self.target_xy,velocity=torch.stack((self.vx,self.vy,s[:,8]*0),-1),yaw=self.yaw,
   height=s[:,6],angles=p[:,:2],contacts=s[:,10:12],leg_q=d.joint_pos.torch[:,self.ids][:,[0,1,3,4]],wheel_offset=self.rise_hold.offset,leg_lengths=p[:,2:4],
   applied_torque=d.applied_torque.torch[:,self.ids],previous_targets=self.student_previous_physical,executed_targets=targets,
   controlled=self.student_actor_valid,valid=s[:,29].bool(),physical_failure=s[:,3].bool(),fault=s[:,4].bool(),config=self.motion_config['reward'],
   linear_narrow_mix=narrow)
  return result
