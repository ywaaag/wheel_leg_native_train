"""Physical mirrored target proposal; not a runtime action override."""
import torch

def errors(legs):
 if legs.shape[-1]!=4 or not torch.isfinite(legs).all():raise ValueError('finite four physical leg positions required')
 return torch.stack((legs[...,0]+legs[...,2],legs[...,1]-legs[...,3]),-1)

def project(legs):
 errors(legs)
 hip=(legs[...,0]-legs[...,2])/2;active=(legs[...,1]+legs[...,3])/2
 return torch.stack((hip,active,-hip,active),-1)

def progress(controlled_time_s,initializing,*,duration_s=2.5):
 """Elapsed controlled-time hint only; never an achieved-recovery certificate."""
 if controlled_time_s.shape!=initializing.shape or initializing.dtype!=torch.bool or duration_s!=2.5 or not torch.isfinite(controlled_time_s).all() or (controlled_time_s<0).any():raise ValueError('explicit finite pre-action controlled time/initialization required')
 return torch.where(initializing,torch.zeros_like(controlled_time_s),(controlled_time_s/duration_s).clamp(0,1))

def progress_contract():
 return {'version':'recovery_elapsed_progress_proposal_v1','status':'CPU_PROPOSAL_NOT_RUNTIME','actor_dim_proposed':32,'critic_dim_proposed':41,'append_index':31,'source':'deployable policy controlled-time counter; zero during passive initialization','value':'clamp(controlled_time_before_action_s/2.5,0,1)','reset':'actual episode reset only','hold':'remains1 after2.5 seconds, even if recovery failed','uses_simulation_height_contacts':False,'uses_teacher_ID_future_success':False,'fixed_teacher_switch':False,'meaning':'elapsed time hint, not physical progress or success','legacy31D_unchanged':True}
