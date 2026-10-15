"""0.34m normal stance: exact same online/offline fixed-window extras."""
import torch
import numpy as np
from .recovery_task import Certificate
from .standing import annotate

class StandingCertificate(Certificate):
 def __init__(self,n,device):
  super().__init__(n,device);self.standing_height_target=.34
  self.height_error_sum=torch.zeros(n,device=device);self.joint_q=torch.zeros(n,4,device=device)
  self.mirror_history=torch.zeros(n,1000,2,device=device)
 def reset(self,ids):
  super().reset(ids)
  if hasattr(self,'mirror_history'):
   self.height_error_sum[ids]=0;self.joint_q[ids]=0;self.mirror_history[ids]=0
 def set_joint(self,q):
  if q.shape!=self.joint_q.shape:raise ValueError('standing four physical leg q required')
  self.joint_q.copy_(q)
 def observe(self,h,a,t,c,g,cl,sat,*,active,valid,safety_failed,fault):
  holding=active&(self.entry>=0)&~self.sent
  error=(h-.34).abs();self.height_error_sum+=error*holding
  ids=torch.where(holding&(self.count<1000))[0]
  q=self.joint_q;mirror=torch.stack((q[:,0]+q[:,2],q[:,1]-q[:,3]),-1).abs()
  self.mirror_history[ids,self.count[ids]]=mirror[ids]
  height_valid=error<=torch.where(self.entry>=0,.04,.02)+1e-7
  success,failure,end,fault=super().observe(h,a,t,c,g,cl,sat,active=active,valid=valid&height_valid,safety_failed=safety_failed,fault=fault)
  ids=torch.where(self.hold_window_complete)[0]
  extra=torch.ones_like(success)
  if len(ids):
   e=self.mirror_history[ids];extra[ids]=(e.mean(1)<=.05).all(-1)&(torch.quantile(e,.95,dim=1)<=.10).all(-1)&(self.height_error_sum[ids]/1000<=.02+1e-7)
  success=success&extra;failure=end&~success&~fault
  self.certificate_passed.copy_(success);self.task_failure.copy_(failure)
  return success,failure,end,fault

def score(state,posture,control,student_control,*,policy_time_s,first_episode_valid):
 from native_stand.recovery.motion_handoff import score as base
 from .protocol import declaration
 result=base(state,posture,student_control,policy_time_s=policy_time_s,configuration=declaration(),entry_extra=(state[:,6]-.34).abs()<=.02+1e-7)
 result['version']='student_standing_height034_symmetry_v1'
 result.update(annotate(result,control.detach().cpu().numpy(),first_episode_valid.detach().cpu().numpy()))
 if result.get('hold_complete'):
  lo,hi=result['hold_index_half_open'];err=(state[lo:hi,6]-.34).abs()
  result['height_target_mae_m']=float(err.mean());result['height_target_peak_error_m']=float(err.max())
  checks=result['checks'];checks.update(height_target_mean=bool(err.mean()<=.02+1e-7),height_target_peak=bool(err.max()<=.04+1e-7),leg_symmetry=result['standing_symmetry_pass'])
  result['failed_checks']=[k for k,v in checks.items() if not v];result['accepted']=not result['failed_checks']
  result['standing_physical_pass']=all(v for k,v in checks.items() if k not in ('leg_symmetry','early_failure'))
  result['standing_joint_pass']=result['accepted']
 return result


class AlignmentCertificate(StandingCertificate):
 def __init__(self,n,device):
  super().__init__(n,device)
  self.offset=torch.zeros(n,device=device)
  self.offset_history=torch.zeros(n,1000,device=device)
 def reset(self,ids):
  super().reset(ids)
  if hasattr(self,'offset_history'):self.offset_history[ids]=0;self.offset[ids]=0
 def set_offset(self,offset):self.offset.copy_(offset)
 def observe(self,*args,**kwargs):
  ids=torch.where(kwargs['active']&(self.entry>=0)&~self.sent&(self.count<1000))[0]
  self.offset_history[ids,self.count[ids]]=self.offset[ids].abs()
  success,failure,end,fault=super().observe(*args,**kwargs)
  ids=torch.where(self.hold_window_complete)[0];good=torch.ones_like(success)
  if len(ids):
   values=self.offset_history[ids]
   good[ids]=(values.mean(-1)<=.02)&(torch.quantile(values,.95,dim=1)<=.04)
  success&=good;failure=end&~success&~fault
  self.certificate_passed.copy_(success);self.task_failure.copy_(failure)
  return success,failure,end,fault


def alignment_score(result,geometry):
 """Same fixed window, explicit additional wheel geometry gate."""
 from native_stand.recovery.standing import longitudinal_geometry
 result['version']='student_standing_alignment034_v12'
 if result.get('hold_complete'):
  lo,hi=result['hold_index_half_open'];g=geometry[lo:hi]
  offset=longitudinal_geometry(g[:,:6].reshape(-1,2,3),g[:,6:9]).abs()
  mae=float(offset.mean());p95=float(torch.quantile(offset,.95))
  result.update(wheel_offset_mae_m=mae,wheel_offset_p95_m=p95)
  result['checks']['wheel_alignment']=bool(torch.isfinite(offset).all() and mae<=.02 and p95<=.04)
  result['failed_checks']=[k for k,v in result['checks'].items() if not v]
  result['accepted']=not result['failed_checks'];result['standing_joint_pass']=result['accepted']
 return result
