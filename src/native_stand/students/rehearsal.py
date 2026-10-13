"""Explicit native normal-stance reset perturbation, pure tensor coordinates."""
import torch

def angular_reset(root,samples,maximum=.25):
 if root.ndim!=2 or root.shape[-1]!=13 or samples.shape!=(len(root),2):raise ValueError('root xyzw/velocity and two reset samples required')
 if not torch.isfinite(root).all() or not torch.isfinite(samples).all() or ((samples<0)|(samples>1)).any() or maximum!=.25:raise ValueError('invalid standing reset perturbation')
 body=torch.zeros_like(root[:,:3]);body[:,[0,2]]=(samples*2-1)*maximum
 xyz=root[:,3:6];w=root[:,6:7]
 world=body+2*torch.cross(xyz,torch.cross(xyz,body,dim=-1)+w*body,dim=-1)
 result=root.clone();result[:,10:13]=world
 return result
