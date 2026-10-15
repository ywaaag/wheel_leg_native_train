"""Explicit 31D Actor/49D Critic standing experiment; pure tensor encoders."""
import torch
RECIPE='student_standing_zero_privileged49_v13'
REWARD='student_standing_zero_privileged49_reward_v13'
PRIVILEGED='standing_privileged49_v1'
SOURCE='73a7a09e713afcb5e96fbc74b0f0527d9bff4d4a439deec105d2bcee3696c2c0'

def configuration():
 from .standing_alignment import configuration as base
 c=base();c['version']=REWARD
 c['standing_alignment']['velocity_scale']=[.1,.02,.03]
 return c

def contract():
 from .mcu_interface import contract as base
 c=base();c['critic_dim']=49;c['critic_privileged_version']=PRIVILEGED
 c['critic_privileged']+=['world_vertical_velocity_mps',
  'left_hip_applied_nm/40','left_active_applied_nm/40','left_wheel_applied_nm/5.5',
  'right_hip_applied_nm/40','right_active_applied_nm/40','right_wheel_applied_nm/5.5',
  'left_rolling_speed_magnitude_residual_mps','right_rolling_speed_magnitude_residual_mps']
 c['rolling_residual']={'wheel_radius_m':.06,'formula':'abs(qdot_wheel)*radius-abs(native_vx)',
  'scope':'magnitude slip proxy, not signed contact-point slip; no direction/polarity claim'}
 return c

def critic_input(base40,vertical_w,applied6,wheel_velocity2,native_vx,*,radius=.06):
 n=base40.shape[0]
 if base40.shape!=(n,40) or vertical_w.shape!=(n,) or applied6.shape!=(n,6) or wheel_velocity2.shape!=(n,2) or native_vx.shape!=(n,) or radius!=.06:
  raise ValueError('explicit privileged49 shapes/radius differ')
 # Root vertical velocity and actual actuator torque read at the same pre-action state.
 residual=wheel_velocity2.abs()*radius-native_vx.abs()[:,None]
 extra=torch.cat((vertical_w[:,None],applied6/base40.new_tensor([40,40,5.5,40,40,5.5]),residual),-1)
 result=torch.cat((base40,extra),-1)
 if not torch.isfinite(result).all():raise ValueError('nonfinite privileged49 observation')
 return result
