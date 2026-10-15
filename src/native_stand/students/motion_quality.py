"""Versioned posture-quality failure; explicit tensors, no environment/IO/RNG."""
import torch

VERSION='motion31_quality_termination_v1'
CAUSES=('pitch','roll','leg_length_difference','wheel_offset','joint_mirror','height','lost_support')

def configuration():
 return {'version':VERSION,'dt_s':.01,'controlled_grace_s':.5,'consecutive_violation_s':.25,
  'pitch_soft_zero_rad':.35,'pitch_soft_motion_rad':.45,'pitch_hard_rad':.70,
  'roll_soft_rad':.25,'roll_hard_rad':.50,'leg_difference_soft_m':.05,'leg_difference_hard_m':.10,
  'wheel_offset_soft_m':.06,'wheel_offset_hard_m':.12,'mirror_soft_rad':.30,'mirror_hard_rad':.60,
  'height_soft_band_m':[.26,.42],'height_hard_band_m':[.20,.50],
  'contact_threshold_n':2.,'both_wheels_lost_consecutive_s':.20,
  'termination':'consecutive soft violations after grace; hard violations immediately during controlled valid policy steps',
  'scope':'native posture and measured hip-wheel geometry; no action or physical override',
  'failure_event_reward':-1.,'failure_reward_dt_scaled':False,'failed_transition_actor_valid':'preserve pre-action mask',
  'bootstrap':'task terminated has no bootstrap; normal timeout only bootstraps',
  'terminal_priority':'runtime/physical/task termination overrides simultaneous normal timeout'}

def huber(x):
 a=x.abs();return torch.where(a<=1,.5*x.square(),a-.5)

class QualityTermination:
 def __init__(self,n,device,config):
  if config!=configuration():raise ValueError('Motion quality termination declaration differs')
  self.config=config;self.ticks=torch.zeros(n,len(CAUSES),device=device,dtype=torch.long)
  self.age=torch.zeros(n,device=device,dtype=torch.long);self.sent=torch.zeros(n,device=device,dtype=torch.bool)
 def reset(self,ids):self.ticks[ids]=0;self.age[ids]=0;self.sent[ids]=False
 def observe(self,*,posture,height,wheel_offset,contacts,target,controlled,valid):
  c=self.config;n=len(self.age)
  if posture.shape!=(n,10) or height.shape!=(n,) or wheel_offset.shape!=(n,) or contacts.shape!=(n,2) or target.shape!=(n,2):raise ValueError('quality observation shape differs')
  if controlled.shape!=(n,) or valid.shape!=(n,) or controlled.dtype!=torch.bool or valid.dtype!=torch.bool:raise ValueError('quality control masks differ')
  active=controlled&valid&~self.sent;self.age+=active
  pitch=posture[:,0].abs();roll=posture[:,1].abs();leg=(posture[:,2]-posture[:,3]).abs();wheel=wheel_offset.abs();mirror=posture[:,4:6].abs().amax(-1)
  pitch_limit=torch.where((target!=0).any(-1),pitch.new_tensor(c['pitch_soft_motion_rad']),pitch.new_tensor(c['pitch_soft_zero_rad']))
  soft=torch.stack((pitch>pitch_limit,roll>c['roll_soft_rad'],leg>c['leg_difference_soft_m'],wheel>c['wheel_offset_soft_m'],mirror>c['mirror_soft_rad'],
   (height<c['height_soft_band_m'][0])|(height>c['height_soft_band_m'][1]),(contacts<=c['contact_threshold_n']).all(-1)),-1)
  hard=torch.stack((pitch>c['pitch_hard_rad'],roll>c['roll_hard_rad'],leg>c['leg_difference_hard_m'],wheel>c['wheel_offset_hard_m'],mirror>c['mirror_hard_rad'],
   (height<c['height_hard_band_m'][0])|(height>c['height_hard_band_m'][1]),torch.zeros_like(active)),-1)
  eligible=active&(self.age*c['dt_s']>c['controlled_grace_s'])
  # Keep the persistent normal buffer across inference rollouts and eager resets.
  self.ticks.copy_(torch.where(soft&eligible[:,None],self.ticks+1,0))
  limits=self.ticks.new_tensor([round(c['consecutive_violation_s']/c['dt_s'])]*6+[round(c['both_wheels_lost_consecutive_s']/c['dt_s'])])
  causes=(hard|((self.ticks>=limits)&eligible[:,None]))&active[:,None]
  failed=causes.any(-1);self.sent|=failed
  return {'terminated':failed,'causes':causes,'consecutive_s':self.ticks*c['dt_s'],'controlled_age_s':self.age*c['dt_s']}

def apply_reward(base,*,posture,wheel_offset,leg_q,controlled,valid,quality_failed,physical_failed,fault,config,reward_config=None):
 """Keep failed samples, suppress ongoing positive payoff, emit one unscaled event."""
 if config!=configuration():raise ValueError('quality reward declaration differs')
 raw=base['raw'].clone();weights=raw.new_tensor(reward_config['weights'] if reward_config else [.5,4,2,1,2,2,-1,-.5,-.5,-.2,-.3,-.15,-.02,-.002])
 mirror=torch.stack((leg_q[:,0]+leg_q[:,2],leg_q[:,1]-leg_q[:,3]),-1)
 raw[:,9]=huber(mirror/.10).mean(-1)
 raw[:,10]=huber(torch.relu(wheel_offset.abs()-.01)/.03)
 raw[:,11]=huber((posture[:,2]-posture[:,3])/.02)
 failed=(quality_failed|physical_failed)&controlled&valid&~fault
 eligible=controlled&valid&~quality_failed&~physical_failed&~fault
 raw=torch.where(eligible[:,None],raw,torch.zeros_like(raw))
 tails=torch.stack((huber(torch.relu(posture[:,0].abs()-.10)/.20),huber(torch.relu(posture[:,1].abs()-.05)/.10)),-1)
 tails=torch.where(eligible[:,None],tails,torch.zeros_like(tails))
 raw=torch.cat((raw,tails),-1);weights=torch.cat((weights,raw.new_tensor(reward_config['posture_tail']['weights'] if reward_config else [-.5,-.5])))
 density=raw*weights;dt=density*.01;events=raw.new_zeros(len(raw),3);events[:,1]=failed*config['failure_event_reward']
 return {**base,'fields':(*base['fields'],'pitch_excess','roll_excess'),'raw':raw,'density':density,'dt':dt,'events':events,
  'total':dt.sum(-1)+events.sum(-1),'eligible':eligible,'failure_event_mask':failed}

def score_quality(result,state,posture,geometry,controlled):
 from native_stand.recovery.standing import longitudinal_geometry
 mask=controlled.bool()&state[:,29].bool();s=state[mask];p=posture[mask];g=geometry[mask]
 checks=result['checks'];complete=len(s)>=3000
 checks['quality_complete_window']=complete
 if complete:
  p=p[1000:1800];g=g[1000:1800]
  offset=longitudinal_geometry(g[:,:6].reshape(-1,2,3),g[:,6:9]).abs()
  checks.update(roll_quality=float(p[:,1].abs().mean())<=.10 and float(torch.quantile(p[:,1].abs(),.95))<=.20,
   leg_balance_quality=float((p[:,2]-p[:,3]).abs().mean())<=.02,
   wheel_alignment_quality=float(offset.mean())<=.04,
   joint_mirror_quality=float(p[:,4:6].abs().mean(0).max())<=.10)
 result.update(accepted=all(checks.values()),failed_checks=[k for k,v in checks.items() if not v],quality_termination_version=VERSION)
 return result
