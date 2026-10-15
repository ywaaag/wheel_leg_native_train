"""Per-command pre-reset GPU reductions; one host export per PPO rollout."""
import torch

FIELDS=('vx_mps','vx_mae_mps','yaw_abs_rad_s','height_m','pitch_abs_rad','roll_abs_rad',
 'leg_length_difference_m','hip_mirror_abs_rad','active_mirror_abs_rad','wheel_offset_abs_m','closure_m',
 'both_wheel_contact','controller_effort_limit_hit_any','raw_action_clip_any','task_failure','runtime_fault')

class MotionStatistics:
 def __init__(self,commands,device,*,schedule_s,parking_s):
  self.commands=commands
  prep,ramp,hold,exit=schedule_s
  self.windows=((prep+ramp,prep+ramp+hold),(prep+ramp+hold+exit,prep+ramp+hold+exit+parking_s))
  self.count=torch.zeros(3,len(commands),device=device,dtype=torch.long)
  self.sum=torch.zeros(3,len(commands),len(FIELDS),device=device)
  self.direction=torch.zeros(3,len(commands),device=device)
 def observe(self,index,valid,age,command,state,posture,geometry):
  # State/posture are the existing runtime snapshot taken before automatic reset.
  from native_stand.recovery.standing import longitudinal_geometry
  offset=longitudinal_geometry(geometry[:,:6].reshape(-1,2,3),geometry[:,6:9]).abs()
  data=torch.stack((state[:,7],(state[:,7]-command[:,0]).abs(),state[:,9].abs(),state[:,6],
   posture[:,0].abs(),posture[:,1].abs(),(posture[:,2]-posture[:,3]).abs(),
   posture[:,4].abs(),posture[:,5].abs(),offset,state[:,12],(state[:,10:12]>2).all(-1).float(),
   state[:,17],(state[:,27]>1).float(),state[:,3],state[:,4]),-1)
  masks=[valid]+[valid&(age>=start)&(age<end) for start,end in self.windows]
  for scope,mask in enumerate(masks):
   ids=index[mask]
   self.count[scope].index_add_(0,ids,torch.ones_like(ids))
   self.sum[scope].index_add_(0,ids,data[mask])
   self.direction[scope].index_add_(0,ids,(state[mask,7]*command[mask,0]>0).float())
 def export(self):
  counts=self.count.cpu().tolist();means=(self.sum/self.count.clamp_min(1)[...,None]).cpu().tolist()
  directions=(self.direction/self.count.clamp_min(1)).cpu().tolist()
  result={}
  for scope,label in enumerate(('controlled','hold','parking')):
   result[label]={}
   for i,command in enumerate(self.commands):
    result[label][f'cohort_{i}']={'target_vx':command[0],'target_yaw':command[1],
     'samples':counts[scope][i],'mean':dict(zip(FIELDS,means[scope][i])) if counts[scope][i] else None,
     'vx_direction_rate':directions[scope][i] if counts[scope][i] and command[0] else None}
  return result
