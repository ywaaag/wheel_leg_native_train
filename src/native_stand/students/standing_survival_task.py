"""Explicit v14 timing, scoring and selection. CPU-safe, no simulator IO."""
import torch
from .standing_survival_reward import Episode
from .standing_certificate import AlignmentCertificate
RECIPE='student_standing_survival_quality_v14'
SOURCE='2af573b318d7ebd6df7b1a5919c5ea58e873e5d24761905ba773f8ab02cc72cd'

def protocol():
 return {'version':'student_standing_survival_quality30_v1','dt':.01,'controlled_seconds':30.,
  'evaluation_seconds':31.52,'quality_window_controlled_s':[20.,30.],
  'height_target_m':.34,'height_mae_max_m':.02,'height_peak_error_max_m':.04,
  'posture_mean_max_rad':.10,'posture_peak_max_rad':.15,'tilt_peak_max_rad':.18,
  'speed_measurement':'root world XY velocity, not tilted body-plane proxy','horizontal_speed_p95_max_mps':.30,'yaw_abs_mean_max_rad_s':.30,
  'dual_contact_fraction_min':.95,'saturation_fraction_max':.05,
  'closure_peak_max_m':.005,'chassis_clearance_min_m':0.,
  'wheel_offset_mae_max_m':.02,'wheel_offset_p95_max_m':.04,
  'mirror_mae_max_rad':.05,'mirror_p95_max_rad':.10,
  'leg_difference_mae_max_m':.01,'leg_difference_p95_max_m':.02,
  'entry_failure_terminates':False,'success_resets':False,'physical_safety_unchanged':True}

def quality_features(state,posture,geometry,world_velocity):
 from native_stand.recovery.standing import longitudinal_geometry
 wheel=longitudinal_geometry(geometry[...,:6].reshape(-1,2,3),geometry[...,6:9].reshape(-1,3)).abs().reshape(state.shape[:-1])
 return torch.stack(((state[...,6]-.34).abs(),posture[...,0].abs(),posture[...,1].abs(),state[...,15],
  world_velocity[...,:2].norm(dim=-1),state[...,9].abs(),(state[...,10:12]>2).all(-1).to(state.dtype),
  state[...,17],wheel,posture[...,4].abs(),posture[...,5].abs(),(posture[...,2]-posture[...,3]).abs(),
  state[...,12],state[...,13]),-1)

def quality_checks(x):
 """Shared batch [env,1000,14] scoring for online and raw-trace replay."""
 if x.ndim!=3 or x.shape[1:]!=(1000,14) or not torch.isfinite(x).all():raise ValueError('quality tail layout/finite differs')
 cfg=protocol()
 return {'height_mean':x[:,:,0].mean(1)<=cfg['height_mae_max_m'],
  'height_peak':x[:,:,0].amax(1)<=cfg['height_peak_error_max_m'],
  'posture_mean':(x[:,:,1:3].mean(1)<=cfg['posture_mean_max_rad']).all(-1),
  'posture_peak':(x[:,:,1:3].amax(1)<=cfg['posture_peak_max_rad']).all(-1),
  'tilt':x[:,:,3].amax(1)<=cfg['tilt_peak_max_rad'],
  'horizontal_speed':torch.quantile(x[:,:,4],.95,dim=1)<=cfg['horizontal_speed_p95_max_mps'],
  'yaw':x[:,:,5].mean(1)<=cfg['yaw_abs_mean_max_rad_s'],
  'contact':x[:,:,6].mean(1)>=cfg['dual_contact_fraction_min'],
  'saturation':x[:,:,7].mean(1)<=cfg['saturation_fraction_max'],
  'wheel_mean':x[:,:,8].mean(1)<=cfg['wheel_offset_mae_max_m'],
  'wheel_p95':torch.quantile(x[:,:,8],.95,dim=1)<=cfg['wheel_offset_p95_max_m'],
  'mirror_mean':(x[:,:,9:11].mean(1)<=cfg['mirror_mae_max_rad']).all(-1),
  'mirror_p95':(torch.quantile(x[:,:,9:11],.95,dim=1)<=cfg['mirror_p95_max_rad']).all(-1),
  'leg_mean':x[:,:,11].mean(1)<=cfg['leg_difference_mae_max_m'],
  'leg_p95':torch.quantile(x[:,:,11],.95,dim=1)<=cfg['leg_difference_p95_max_m'],
  'closure':x[:,:,12].amax(1)<=cfg['closure_peak_max_m'],
  'clearance':x[:,:,13].amin(1)>cfg['chassis_clearance_min_m']}

class Clock(AlignmentCertificate):
 """Physical safety terminates; duration completion only truncates."""
 def __init__(self,n,device):
  super().__init__(n,device);self.episode=Episode(n,device)
  self.quality_tail=torch.zeros(n,1000,14,device=device)
 def reset(self,ids):
  super().reset(ids)
  if hasattr(self,'episode'):self.episode.reset(ids);self.quality_tail[ids]=0
 def observe(self,h,a,t,c,g,cl,sat,*,active,valid,safety_failed,fault):
  self.age+=active*.01
  outcome=self.episode.observe(controlled=active,valid=valid,physical_failure=safety_failed,fault=fault)
  self.count.copy_(self.episode.steps)
  self.entry[(self.entry<0)&active&valid]=self.age[(self.entry<0)&active&valid]
  self.entry_confirmed.zero_();self.certificate_passed.zero_()
  self.hold_window_complete.copy_(outcome['survival_complete'])
  self.task_failure.copy_(safety_failed&~fault);self.runtime_fault.copy_(fault)
  self.prefix.copy_(self.count);self.sent.copy_(outcome['terminated']|outcome['truncated'])
  self.normal_timeout=outcome['truncated']
  return torch.zeros_like(fault),self.task_failure,self.sent,fault

 def record_quality(self,state,posture,geometry,world_velocity,controlled):
  ids=torch.where(controlled&state[:,29].bool()&~state[:,3].bool()&~state[:,4].bool()&(self.episode.steps>0))[0]
  features=quality_features(state,posture,geometry,world_velocity)
  self.quality_tail[ids,(self.episode.steps[ids]-1)%1000]=features[ids]
  ended=torch.where(self.normal_timeout)[0]
  if len(ended):
   checks=quality_checks(self.quality_tail[ended]);passed=torch.stack(list(checks.values()),-1).all(-1)
   self.certificate_passed[ended]=passed

def score(state,posture,geometry,*,controlled,valid,world_velocity):
 from .survival_probe import score as survival_score
 from native_stand.recovery.standing import longitudinal_geometry
 result=survival_score(state,posture,geometry,controlled=controlled,valid=valid)
 if world_velocity.shape!=(len(state),3) or not torch.isfinite(world_velocity).all():raise ValueError('v14 actual world velocity required')
 cfg=protocol();mask=controlled.bool()&valid.bool()&state[:,29].bool()
 s=state[mask][:3000];p=posture[mask][:3000];g=geometry[mask][:3000]
 checks={'survival30':result['survival_passed']}
 if len(s)==3000:
  s=s[2000:3000];p=p[2000:3000];g=g[2000:3000]
  height=(s[:,6]-.34).abs();angle=p[:,:2].abs();speed=world_velocity[mask][:3000][2000:3000,:2].norm(dim=-1)
  wheel=longitudinal_geometry(g[:,:6].reshape(-1,2,3),g[:,6:9]).abs()
  mirror=p[:,4:6].abs();length=(p[:,2]-p[:,3]).abs()
  checks.update({k:v[0] for k,v in quality_checks(quality_features(s,p,g,world_velocity[mask][:3000][2000:3000]).unsqueeze(0)).items()})
  result['quality_metrics']={'horizontal_speed_p95_mps':float(torch.quantile(speed,.95)),
   'posture_worst_mean_rad':float(angle.mean(0).max()),'wheel_offset_mae_m':float(wheel.mean()),
   'mirror_worst_mae_rad':float(mirror.mean(0).max()),'leg_difference_mae_m':float(length.mean())}
 result.update(version=cfg['version'],checks={k:bool(v) for k,v in checks.items()},
  accepted=all(bool(v) for v in checks.values()),entry_index=None,
  failed_checks=[k for k,v in checks.items() if not bool(v)],
  quality_screen_passed=all(bool(v) for v in checks.values()),
  capability_scope='30s survival with fixed final10s stationary upright alignment; normal stance only')
 return result

def rank(row):
 envs=row['per_env']
 if not envs:raise ValueError('v14 candidate has no per-env evidence')
 quality=sum(e.get('accepted',False) for e in envs)
 survival=sum(e.get('survival_passed',False) for e in envs)
 completed=[e['quality_metrics'] for e in envs if e.get('quality_metrics')]
 # Complete stationary quality beats indefinite rolling; never rank reward.
 cost=max((q['horizontal_speed_p95_mps']/.30+q['posture_worst_mean_rad']/.10+
           q['wheel_offset_mae_m']/.02+q['mirror_worst_mae_rad']/.05 for q in completed),default=float('inf'))
 return (quality,survival,min(e.get('controlled_seconds',0.) for e in envs),-cost,-row.get('update',0))

def bootstrap_reward(rewards,terminated,truncated,terminal_values,*,gamma):
 if rewards.shape!=terminated.shape or rewards.shape!=truncated.shape or terminal_values.shape!=rewards.shape:
  raise ValueError('terminal bootstrap shape differs')
 if terminated.dtype!=torch.bool or truncated.dtype!=torch.bool or not torch.isfinite(terminal_values).all():
  raise ValueError('terminal bootstrap invalid')
 return rewards+gamma*terminal_values*(truncated&~terminated)
