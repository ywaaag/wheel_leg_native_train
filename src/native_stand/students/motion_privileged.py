"""Motion-only named49D Critic; same architecture, explicitly different semantics."""
import torch
VERSION='motion_privileged49_v1'
def contract():
 from .mcu_interface import contract as base
 c=base();c.update(critic_dim=49,critic_privileged_version=VERSION,height_command_m=.34)
 c['critic_privileged']=['height_error_m:1','native_velocity_mps:3','contact_resultant_N/100:2',
 'effective_vx_yaw/4:2','tracking_error_vx_yaw/4:2','controlled_age/30:1','hold_phase:1','applied_effort/limit:6']
 return c
def critic_input(actor,height,velocity,contacts,command,yaw,age,hold,effort):
 n=len(actor)
 if actor.shape!=(n,31) or velocity.shape!=(n,3) or contacts.shape!=(n,2) or command.shape!=(n,3) or effort.shape!=(n,6):raise ValueError('Motion49 explicit shape differs')
 err=torch.stack((velocity[:,0]-command[:,0],yaw-command[:,1]),-1)
 extra=torch.cat(((height-.34)[:,None],velocity,contacts/100,command[:,:2]/4,err/4,age[:,None]/30,
  hold.to(actor.dtype)[:,None],effort/actor.new_tensor([40,40,5.5,40,40,5.5])),-1)
 result=torch.cat((actor,extra),-1)
 if result.shape!=(n,49) or not torch.isfinite(result).all():raise ValueError('Motion49 finite/layout differs')
 return result
