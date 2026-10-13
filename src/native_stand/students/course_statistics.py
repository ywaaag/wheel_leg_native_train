"""Compact per-rollout physical statistics; no file/environment/RNG dependencies."""
import torch
class WheelStatistics:
 def __init__(self,n,device):
  self.count=torch.zeros((),device=device);self.delta=torch.zeros(2,device=device);self.torque=torch.zeros(3,2,device=device);self.limit=torch.zeros(2,device=device);self.sign_changes=torch.zeros(2,device=device)
  self.last=torch.zeros(n,2,device=device);self.have=torch.zeros(n,dtype=torch.bool,device=device);self.run=torch.zeros(n,2,device=device,dtype=torch.long);self.longest=torch.zeros(2,device=device,dtype=torch.long)
 def observe(self,executed,previous,requested,clipped,applied,valid,done):
  self.count+=valid.sum();delta=(executed-previous).square();self.delta+=(delta*valid[:,None]).sum(0)
  for i,t in enumerate((requested,clipped,applied)):self.torque[i]+=(t.square()*valid[:,None]).sum(0)
  sat=(clipped.abs()>=5.5-1e-4)&valid[:,None];self.limit+=sat.sum(0)
  self.sign_changes+=((clipped*self.last<0)&valid[:,None]&self.have[:,None]).sum(0)
  self.run=torch.where(sat,self.run+1,0);self.longest=torch.maximum(self.longest,self.run.amax(0))
  self.last.copy_(clipped);self.have.copy_(valid&~done);self.run[done]=0
 def result(self):
  n=max(1,int(self.count));return dict(student_samples=int(self.count),wheel_target_delta_rms_rad_s=(self.delta/n).sqrt().cpu().tolist(),requested_clipped_applied_torque_rms_nm=(self.torque/n).sqrt().cpu().tolist(),wheel_limit_fraction=(self.limit/n).cpu().tolist(),wheel_torque_sign_changes=self.sign_changes.cpu().tolist(),wheel_longest_limit_s=(self.longest*.01).cpu().tolist(),sampling='100Hz latest held PD torque; not full PD or physics frequency; sign/runs broken at real resets')
