"""PPO0-only full survival window; strict entry certificate is observational."""
import torch
from .standing_certificate import AlignmentCertificate
VERSION='student_standing_survival30_ppo0_v1'

def declaration():
 return {'version':VERSION,'controlled_seconds':30.,'seconds':31.52,
         'entry_failure_terminates':False,'physical_safety_unchanged':True,
         'training_allowed':False,'scored_envs':8}

class SurvivalObserver(AlignmentCertificate):
 def observe(self,*args,**kwargs):
  # Preserve strict certificate bookkeeping, but never turn its failure/success
  # into an episode reset. Physical safety/fault still terminate immediately.
  super().observe(*args,**kwargs)
  fault=kwargs['fault'];failed=kwargs['safety_failed']&~fault
  z=torch.zeros_like(fault)
  self.certificate_passed.zero_();self.task_failure.copy_(failed);self.runtime_fault.copy_(fault)
  return z,failed,failed|fault,fault

def score(s,p,g,*,controlled,valid):
 from native_stand.recovery.standing import longitudinal_geometry
 mask=controlled.bool()&valid.bool()&s[:,29].bool()
 rows=s[mask][:3000];pose=p[mask][:3000];geo=g[mask][:3000]
 if len(rows)==0:return {'accepted':False,'survival_passed':False,'hold_complete':False,'entry_index':None,'failed_checks':['no_valid_control'],'controlled_seconds':0.}
 faults=rows[:,4].bool().any()|rows[:,30].bool().any()
 failed=rows[:,3].bool().any()
 survived=len(rows)==3000 and not bool(faults|failed)
 offset=longitudinal_geometry(geo[:,:6].reshape(-1,2,3),geo[:,6:9]).abs()
 metrics={'height_mean_m':rows[:,6].mean(),'height_mae_m':(rows[:,6]-.34).abs().mean(),
  'vx_mean_mps':rows[:,7].mean(),'vx_abs_mean_mps':rows[:,7].abs().mean(),
  'pitch_abs_mean_rad':pose[:,0].abs().mean(),'roll_abs_mean_rad':pose[:,1].abs().mean(),
  'dual_contact_fraction':((rows[:,10:12]>2).all(-1)).float().mean(),
  'saturation_fraction':rows[:,17].mean(),'wheel_offset_mae_m':offset.mean(),
  'leg_length_difference_mae_m':(pose[:,2]-pose[:,3]).abs().mean(),
  'hip_mirror_mae_rad':pose[:,4].abs().mean(),'active_mirror_mae_rad':pose[:,5].abs().mean()}
 # This probe certifies only survival; quality remains explicitly separate.
 quality=survived and bool((rows[:,6]-.34).abs().mean()<=.02 and pose[:,:2].abs().mean(0).max()<=.10 and rows[:,7].abs().mean()<=.5 and offset.mean()<=.02)
 return {'version':VERSION,'accepted':False,'survival_passed':survived,'quality_screen_passed':quality,
  'hold_complete':survived,'entry_index':None,'controlled_seconds':len(rows)*.01,
  'metrics':{k:float(v) for k,v in metrics.items()},'failed_checks':[] if survived else ['incomplete_survival'],
  'capability_scope':'survival diagnostic only; not full standing certification'}
