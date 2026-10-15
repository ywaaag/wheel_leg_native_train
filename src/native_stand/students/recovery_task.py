"""Explicit post-physics reward and first-window certificate; no simulator/IO."""
import torch
from native_stand.recovery.handoff_clock import HandoffClock
from native_stand.recovery.min_height import entry_mask,hold_metrics
from .protocol import declaration

VERSION='student_recovery_reward_v1'
NO_FAILURE_VERSION='student_recovery_reward_failure_zero_v2'
LIFT_RATE_VERSION='student_recovery_reward_lift_rate_v3'
REHEARSAL_VERSION='student_recovery_reward_standing_rehearsal_v4'
MOTION_MIRROR_VERSION='student_recovery_reward_motion_mirror_v6'
SLIDING_VERSION='student_recovery_reward_velocity_huber_v7'
SMOOTH_VERSION='student_recovery_reward_hold_wheel_smooth_v8'
SUFFIX_VERSION='student_recovery_reward_dynamic_suffix_v9'
CONTACT_SUFFIX_VERSION='student_recovery_reward_dynamic_suffix_contact_v10'
SYMMETRY_VERSION='student_recovery_reward_standing_mirror_huber_v11'
FIELDS=('height_progress','support_quality','effort','target_change','post_entry_angular','post_entry_velocity')
WEIGHTS=(2.,3.,-.02,-.002,-.05,-.10)
def configuration(version=VERSION):
 if version=="student_standing_survival_quality_reward_v14":
  from .standing_survival_reward import configuration as survival_configuration
  return survival_configuration()
 if version=="student_standing_zero_privileged49_reward_v13":
  from .standing_zero_privileged import configuration as privileged_config
  return privileged_config()
 if version=="student_standing_alignment_reward_v12":
  from .standing_alignment import configuration as alignment_config
  return alignment_config()
 if version==SYMMETRY_VERSION:
  result=configuration(SLIDING_VERSION);result['version']=version
  result['weak_mirror']={'version':'native_physical_joint_mirror_huber_v2','scale_rad':.20,'huber_delta':1.,'weight_per_s':-.20,'squared_cap':None,'coordinates':'left_hip+right_hip,left_active-right_active','state':'post_physics_pre_reset_active_q','gate':'height_progress','action_override':False}
  result['standing_height']={'target_m':.34,'width_m':.04,'entry_error_max_m':.02,'hold_mean_error_max_m':.02,'hold_peak_error_max_m':.04,'raw_slot0':'height_tracking replaces height_progress; other slots unchanged'}
  return result
 if version==CONTACT_SUFFIX_VERSION:
  result=configuration(SUFFIX_VERSION);result['version']=version
  result['hold_contact_deficit']={'force_scale_n':2.,'weight_per_s':-.2,'gate':'first_entry_confirmed','measurement':'wheel_sensor_resultant_norm','formula':'mean(clamp(relu((2N-contact)/2N),0,1)^2)','dt_once':True}
  return result
 if version in (SMOOTH_VERSION,SUFFIX_VERSION):
  result=configuration(SLIDING_VERSION);result['version']=version
  result['hold_wheel_smooth']={'scale_rad_s':10.,'weight_per_s':-.2,'gate':'first_entry_confirmed','targets':'actual_executed_wheels','dt_once':True}
  if version==SUFFIX_VERSION:
   result['motion_zero_tracking']['gate']='height_progress_times_first_entry_confirmed'
   result['weak_mirror']['gate']='height_progress_times_first_entry_confirmed'
  return result
 if version not in (VERSION,NO_FAILURE_VERSION,LIFT_RATE_VERSION,REHEARSAL_VERSION,MOTION_MIRROR_VERSION,SLIDING_VERSION):raise ValueError('unknown student reward version')
 result={'version':version,'dt':.01,'height_min_m':.30,'level_width_rad':.30,
         'contact_resultant_min_n':2.,'weights':dict(zip(FIELDS,WEIGHTS)),
         'leg_delta_scale_rad':.1,'wheel_delta_scale_rad_s':10.,'entry_once':1.,'success_once':10.,'failure_once':-1. if version==VERSION else 0.,
         'reward_state':'post_physics_pre_reset','runtime_fault_reward':0.,'BC_coefficient':0.}
 if version in (LIFT_RATE_VERSION,REHEARSAL_VERSION,MOTION_MIRROR_VERSION,SLIDING_VERSION):
  result['pre_entry_angular']={'height_ramp_m':[.20,.25],'gate_height':'post_physics_current_height','deadband_rad_s':3.,'scale_rad_s':1.,'squared_cap':9.,'weight_per_s':-.2,'axes_body':[0,2],'contact_gate':False}
 if version in (REHEARSAL_VERSION,MOTION_MIRROR_VERSION,SLIDING_VERSION):result['standing_height_reference']={'initial_height_min_m':.30,'reference_m':.168,'scope':'normal initial stance only; Swing initial height unchanged'}
 if version in (MOTION_MIRROR_VERSION,SLIDING_VERSION):
  result['motion_zero_tracking']={'linear_denominator_mps_squared':.04,'yaw_denominator_rad_s_squared':.09,'weight_per_s':4.,'gate':'height_progress_times_level_quality','tracking':'combined_native_vx_vy_yaw','target':[0.,0.,0.]}
  result['weak_mirror']={'version':'native_physical_joint_mirror_cost_v1','scale_rad':.20,'squared_cap':4.,'weight_per_s':-.05,'coordinates':'left_hip+right_hip,left_active-right_active','state':'post_physics_pre_reset_active_q','gate':'height_progress','action_override':False}
 if version==SLIDING_VERSION:
  result['motion_zero_tracking']={'version':'native_velocity_huber_cost_v1','linear_scale_mps':.5,'yaw_scale_rad_s':.3,'huber_delta':1.,'weight_per_s':-1.,'gate':'height_progress_only','tracking':'sum_smooth_l1_native_vx_vy_yaw','target':[0.,0.,0.],'cap':None,'replaces':'v6 narrow Gaussian positive tracking only'}
 return result

def pre_entry_angular_cost(height,angular_body,entered,controlled,fault,cfg):
 """Smooth height gating; no contact requirement, bounded large-rate cost."""
 item=cfg.get('pre_entry_angular')
 if item is None:return torch.zeros_like(height)
 lo,hi=item['height_ramp_m'];u=((height-lo)/(hi-lo)).clamp(0,1);gate=u.square()*(3-2*u)
 speed=torch.linalg.vector_norm(angular_body[:,item['axes_body']],dim=-1)
 excess=(torch.relu(speed-item['deadband_rad_s'])/item['scale_rad_s']).square().clamp(max=item['squared_cap'])
 return gate*excess*((~entered)&controlled&~fault)
def reward(height,h0,angles,contacts,clearance,torque,previous_targets,executed_targets,angular_body,velocity_native,yaw,entered,controlled,fault,entry_event,success_event,failure_event,*,reward_configuration=None,active_leg_q=None,wheel_heading_offset=None):
 cfg=configuration() if reward_configuration is None else reward_configuration
 if cfg.get('version') in ('student_standing_alignment_reward_v12','student_standing_zero_privileged49_reward_v13'):
  from .standing_alignment import apply
  if cfg!=configuration(cfg['version']):raise ValueError('alignment reward differs')
  result=reward(height,h0,angles,contacts,clearance,torque,previous_targets,executed_targets,angular_body,velocity_native,yaw,entered,controlled,fault,entry_event,success_event,failure_event,reward_configuration=configuration(SYMMETRY_VERSION),active_leg_q=active_leg_q)
  return apply(result,height,active_leg_q,wheel_heading_offset,velocity_native,yaw,controlled,fault,alignment_configuration=cfg['standing_alignment'])
 if cfg.get('version')==SYMMETRY_VERSION:
  if cfg!=configuration(SYMMETRY_VERSION):raise ValueError('standing symmetry reward configuration differs')
  result=reward(height,h0,angles,contacts,clearance,torque,previous_targets,executed_targets,angular_body,velocity_native,yaw,entered,controlled,fault,entry_event,success_event,failure_event,reward_configuration=configuration(SLIDING_VERSION),active_leg_q=active_leg_q)
  old=result['motion_mirror_dt'][:,1].clone()
  anchor=cfg['standing_height_reference'];origin=torch.where(h0>=anchor['initial_height_min_m'],torch.full_like(h0,anchor['reference_m']),h0)
  H=((height-origin)/torch.maximum(.30-origin,torch.full_like(h0,.05))).clamp(0,1)
  x=(result['mirror_error_rad']/cfg['weak_mirror']['scale_rad']).abs()
  cost=torch.where(x<1.,.5*x.square(),x-.5).mean(-1)*H*(controlled&~fault)
  result['motion_mirror_raw'][:,1]=cost
  result['motion_mirror_weighted_density'][:,1]=cost*cfg['weak_mirror']['weight_per_s']
  result['motion_mirror_dt'][:,1]=result['motion_mirror_weighted_density'][:,1]*cfg['dt']
  result['total']=result['total']-old+result['motion_mirror_dt'][:,1]
  height_term=torch.exp(-((height-.34)/.04).square())*(controlled&~fault)
  old_height=result['continuous_dt'][:,0].clone()
  result['raw'][:,0]=height_term;result['weighted_density'][:,0]=height_term*2.;result['continuous_dt'][:,0]=height_term*2.*cfg['dt']
  result['total']=result['total']-old_height+result['continuous_dt'][:,0]
  result['total']=result['total']*(controlled&~fault)
  return result
 if cfg!=configuration(cfg.get('version')):raise ValueError('student reward configuration differs')
 if torque.shape[-1]!=6 or previous_targets.shape!=torque.shape or executed_targets.shape!=torque.shape:raise ValueError('left-first physical targets/torques required')
 anchor=cfg.get('standing_height_reference')
 origin=torch.where(h0>=anchor['initial_height_min_m'],torch.full_like(h0,anchor['reference_m']),h0) if anchor else h0
 H=((height-origin)/(torch.maximum(.30-origin,torch.full_like(h0,.05)))).clamp(0,1)
 U=torch.exp(-angles.square().sum(-1)/.30**2)
 C=((contacts>2).all(-1)&(clearance>0)).to(height.dtype)
 effort=(torque/torque.new_tensor([40,40,5.5,40,40,5.5])).square().mean(-1)
 delta=((executed_targets-previous_targets)/torque.new_tensor([.1,.1,10.,.1,.1,10.])).square().mean(-1)
 W=angular_body[:,[0,2]].square().mean(-1)*entered
 V=((torch.relu(velocity_native[:,0].abs()-.5)/.5).square()+(velocity_native[:,1]/.2).square()+(yaw/.3).square())*entered
 raw=torch.stack((H,H*U*C,effort,delta,W,V),-1)
 eligible=controlled&~fault
 raw=raw*eligible[:,None]
 weighted=raw*raw.new_tensor(WEIGHTS)
 density_dt=weighted*.01
 # Kept separate from the six unchanged v1/v2 terms, so logs retain units.
 pre_raw=pre_entry_angular_cost(height,angular_body,entered,controlled,fault,cfg)
 pre_density=pre_raw*cfg.get('pre_entry_angular',{}).get('weight_per_s',0.)
 pre_dt=pre_density*.01
 events=torch.stack((entry_event.to(height.dtype),success_event.to(height.dtype)*10.,failure_event.to(height.dtype)*cfg['failure_once']),-1)*eligible[:,None]
 total=density_dt.sum(-1)+pre_dt+events.sum(-1)
 extra_raw=torch.zeros((len(height),2),device=height.device,dtype=height.dtype);extra_weighted=extra_raw.clone()
 mirror_error=torch.zeros((len(height),2),device=height.device,dtype=height.dtype)
 if cfg['version'] in (MOTION_MIRROR_VERSION,SLIDING_VERSION,SMOOTH_VERSION,SUFFIX_VERSION,CONTACT_SUFFIX_VERSION):
  if active_leg_q is None or active_leg_q.shape!=(len(height),4) or not torch.isfinite(active_leg_q).all():raise ValueError('motion mirror reward requires named post-physics four-leg q')
  tracking=cfg['motion_zero_tracking'];mirror=cfg['weak_mirror']
  if cfg['version'] in (SLIDING_VERSION,SMOOTH_VERSION,SUFFIX_VERSION,CONTACT_SUFFIX_VERSION):
   residual=torch.cat((velocity_native[:,:2]/tracking['linear_scale_mps'],yaw[:,None]/tracking['yaw_scale_rad_s']),-1).abs()
   velocity_quality=torch.where(residual<1.,.5*residual.square(),residual-.5).sum(-1)
  else:velocity_quality=torch.exp(-velocity_native[:,:2].square().sum(-1)/tracking['linear_denominator_mps_squared']-yaw.square()/tracking['yaw_denominator_rad_s_squared'])
  mirror_error=torch.stack((active_leg_q[:,0]+active_leg_q[:,2],active_leg_q[:,1]-active_leg_q[:,3]),-1)
  symmetry_cost=(mirror_error/mirror['scale_rad']).square().mean(-1).clamp(max=mirror['squared_cap'])
  tracking_gate=H if cfg['version'] in (SLIDING_VERSION,SMOOTH_VERSION,SUFFIX_VERSION,CONTACT_SUFFIX_VERSION) else H*U
  mirror_gate=H
  if cfg['version'] in (SUFFIX_VERSION,CONTACT_SUFFIX_VERSION):tracking_gate=tracking_gate*entered;mirror_gate=mirror_gate*entered
  extra_raw=torch.stack((tracking_gate*velocity_quality,mirror_gate*symmetry_cost),-1)*eligible[:,None]
  extra_weighted=extra_raw*extra_raw.new_tensor([tracking['weight_per_s'],mirror['weight_per_s']])
  total+=extra_weighted.sum(-1)*cfg['dt']
 smooth_raw=((executed_targets[:,[2,5]]-previous_targets[:,[2,5]])/10.).square().mean(-1)*entered*eligible
 smooth_density=smooth_raw*cfg.get('hold_wheel_smooth',{}).get('weight_per_s',0.)
 smooth_dt=smooth_density*cfg['dt'];total+=smooth_dt
 contact_raw=((torch.relu((2.-contacts)/2.)).clamp(max=1.)).square().mean(-1)*entered*eligible
 contact_density=contact_raw*cfg.get('hold_contact_deficit',{}).get('weight_per_s',0.)
 contact_dt=contact_density*cfg['dt'];total+=contact_dt
 if not torch.isfinite(total).all():raise ValueError('nonfinite Recovery task reward')
 return {'raw':raw,'weighted_density':weighted,'continuous_dt':density_dt,'events':events,'total':total,
         'pre_entry_angular_raw':pre_raw,'pre_entry_angular_density':pre_density,'pre_entry_angular_dt':pre_dt,
         'motion_mirror_raw':extra_raw,'motion_mirror_weighted_density':extra_weighted,'motion_mirror_dt':extra_weighted*cfg['dt'],'mirror_error_rad':mirror_error,
         'hold_wheel_smooth_raw':smooth_raw,'hold_wheel_smooth_density':smooth_density,'hold_wheel_smooth_dt':smooth_dt,
         'hold_contact_deficit_raw':contact_raw,'hold_contact_deficit_density':contact_density,'hold_contact_deficit_dt':contact_dt}

class Certificate(HandoffClock):
 """Same observe API as shared RecoveryEnv; completion is not acceptance."""
 def __init__(self,n,device):
  super().__init__(n,device,declaration())
  self.velocity=torch.zeros(n,3,device=device)
  self.angle_sum=torch.zeros(n,2,device=device);self.velocity_sum=torch.zeros(n,3,device=device)
  self.saturation_sum=torch.zeros(n,device=device);self.hard_failed=torch.zeros(n,device=device,dtype=torch.bool)
  self.prefix=torch.zeros_like(self.count);self.prefix_closed=torch.zeros_like(self.hard_failed)
  self.entry_confirmed=torch.zeros_like(self.motion);self.hold_window_complete=torch.zeros_like(self.motion)
  self.certificate_passed=torch.zeros_like(self.motion);self.task_failure=torch.zeros_like(self.motion);self.runtime_fault=torch.zeros_like(self.motion)
 def set_velocity(self,value):
  if value.shape!=self.velocity.shape:raise ValueError('native vx/vy/yaw certificate fields differ')
  self.velocity.copy_(value)
 def reset(self,ids):
  super().reset(ids)
  for name in ('velocity','angle_sum','velocity_sum','saturation_sum','hard_failed','prefix','prefix_closed','entry_confirmed','hold_window_complete','certificate_passed','task_failure','runtime_fault'):getattr(self,name)[ids]=0
 def observe(self,h,a,t,c,g,cl,sat,*,active,valid,safety_failed,fault):
  self.age+=active*self.cfg['dt'];self.motion_age+=active*self.cfg['dt']
  holding=active&(self.entry>=0)&~self.sent
  hard=hold_metrics(h,a,t,c,g,cl,sat,self.p)&valid
  self.hard_failed|=holding&~hard
  self.prefix_closed|=holding&~hard;self.prefix+=holding&~self.prefix_closed
  self.count+=holding
  self.angle_sum+=a.abs()*holding[:,None];self.velocity_sum+=self.velocity.abs()*holding[:,None];self.saturation_sum+=sat*holding
  search=active&(self.entry<0)&~self.sent
  eligible=entry_mask(h,a,t,c,g,valid,self.p)
  self.dwell.copy_(torch.where(search&eligible,self.dwell+1,0))
  confirm=search&(self.dwell>=20)&(self.age<=2.5+1e-5)
  self.entry[confirm]=self.age[confirm]
  complete=holding&(self.count>=1000)
  expired=search&~confirm&(self.age>=2.5-1e-5)
  passed=complete&~self.hard_failed&(self.angle_sum/self.count.clamp_min(1)[:,None]<=.10).all(-1)&(self.saturation_sum/self.count.clamp_min(1)<=.05)&(self.velocity_sum/self.count.clamp_min(1)[:,None]<=self.velocity.new_tensor([.5,.02,.03])).all(-1)
  end=(complete|expired|safety_failed|fault)&~self.sent
  success=end&passed&~safety_failed&~fault
  failure=end&~success&~fault
  self.entry_confirmed.copy_(confirm);self.hold_window_complete.copy_(complete);self.certificate_passed.copy_(success);self.task_failure.copy_(failure);self.runtime_fault.copy_(fault&~self.sent)
  self.sent|=end
  return success,failure,end,fault
