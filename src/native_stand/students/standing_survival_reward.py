"""Versioned pure reward and episode contract; no IO, simulator or optimizer."""
import torch
VERSION='student_standing_survival_quality_reward_v14'
FIELDS=('survival','stationary_upright','height','zero_speed','mirror','wheel_alignment',
        'leg_length_balance','angular','effort','target_change')

def configuration():
 return {'version':VERSION,'dt':.01,'height_target_m':.34,'height_scale_m':.04,
  'speed_scale_mps':.30,'yaw_scale_rad_s':.30,'posture_scale_rad':.15,
  'mirror_scale_rad':.10,'wheel_deadband_m':.01,'wheel_scale_m':.03,
  'leg_difference_scale_m':.02,'angular_scale_rad_s':1.,
  'support_force_n':2.,'support_height_ramp_m':[.20,.30],
  'weights':[1.,5.,1.5,1.,-.20,-.30,-.15,-.10,-.02,-.002],
  'target_delta_scales':[.1,.1,10.,.1,.1,10.],
  'effort_limits_nm':[40.,40.,5.5,40.,40.,5.5],
  'quality_function':'1/(1+x_squared); height rational, no Gaussian far-field underflow',
  'events':[0.,0.,0.],'state':'post_physics_pre_reset','controlled_seconds':30.}

def bounded_cost(x):return x.square()/(1+x.square())

def reward(*,height,angles,velocity_xy,yaw,contacts,leg_q,wheel_offset,leg_lengths,
           angular_pitch_roll,applied_torque,previous_targets,executed_targets,
           controlled,valid,physical_failure,fault):
 n=len(height)
 tensors={'height':(height,(n,)),'angles':(angles,(n,2)),'velocity_xy':(velocity_xy,(n,2)),
  'yaw':(yaw,(n,)),'contacts':(contacts,(n,2)),'leg_q':(leg_q,(n,4)),
  'wheel_offset':(wheel_offset,(n,)),'leg_lengths':(leg_lengths,(n,2)),
  'angular_pitch_roll':(angular_pitch_roll,(n,2)),'applied_torque':(applied_torque,(n,6)),
  'previous_targets':(previous_targets,(n,6)),'executed_targets':(executed_targets,(n,6))}
 for name,(t,shape) in tensors.items():
  if t.shape!=shape or t.device!=height.device or t.dtype!=height.dtype or not torch.isfinite(t).all():
   raise ValueError('standing reward explicit shape/device/dtype/finite differs: '+name)
 for t in (controlled,valid,physical_failure,fault):
  if t.shape!=(n,) or t.dtype!=torch.bool or t.device!=height.device:raise ValueError('standing reward mask differs')
 c=configuration();lo,hi=c['support_height_ramp_m']
 b=(contacts.amin(-1)/c['support_force_n']).clamp(0,1)*((height-lo)/(hi-lo)).clamp(0,1)
 qv=1/(1+(velocity_xy/c['speed_scale_mps']).square().sum(-1)+(yaw/c['yaw_scale_rad_s']).square())
 qp=1/(1+(angles/c['posture_scale_rad']).square().sum(-1))
 gh=1/(1+((height-c['height_target_m'])/c['height_scale_m']).square())
 mirror=torch.stack((leg_q[:,0]+leg_q[:,2],leg_q[:,1]-leg_q[:,3]),-1)
 raw=torch.stack((b,b*qv*qp,b*qv*gh,b*qv,
  bounded_cost(mirror/c['mirror_scale_rad']).mean(-1),
  bounded_cost(torch.relu(wheel_offset.abs()-c['wheel_deadband_m'])/c['wheel_scale_m']),
  bounded_cost((leg_lengths[:,0]-leg_lengths[:,1])/c['leg_difference_scale_m']),
  bounded_cost(angular_pitch_roll/c['angular_scale_rad_s']).mean(-1),
  (applied_torque/height.new_tensor(c['effort_limits_nm'])).square().mean(-1),
  bounded_cost((executed_targets-previous_targets)/height.new_tensor(c['target_delta_scales'])).mean(-1)), -1)
 mask=controlled&valid&~physical_failure&~fault
 raw=raw*mask[:,None];density=raw*height.new_tensor(c['weights']);dt=density*c['dt']
 return {'version':VERSION,'fields':FIELDS,'raw':raw,'density':density,'dt':dt,
         'total':dt.sum(-1),'events':height.new_zeros(n,3),'eligible':mask}

class Episode:
 """Thirty seconds of actual controlled steps, without entry/success reset."""
 def __init__(self,n,device='cpu'):
  self.steps=torch.zeros(n,dtype=torch.long,device=device)
 def reset(self,ids):self.steps[ids]=0
 def observe(self,*,controlled,valid,physical_failure,fault):
  masks=(controlled,valid,physical_failure,fault)
  if any(m.shape!=self.steps.shape or m.dtype!=torch.bool or m.device!=self.steps.device for m in masks):
   raise ValueError('standing episode explicit mask differs')
  terminated=physical_failure|fault
  self.steps+=controlled&valid&~terminated
  truncated=(self.steps>=3000)&~terminated
  return {'terminated':terminated,'truncated':truncated,'runtime_fault':fault,
          'survival_complete':truncated,'certificate_passed':torch.zeros_like(truncated),
          'controlled_seconds':self.steps.to(torch.float64)*.01}
