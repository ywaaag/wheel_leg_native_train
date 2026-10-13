"""CPU-only joint fourleg mixture; not a policy factory/runtime implementation."""
import math
import torch

LEGS=[0,1,3,4]
WHEELS=[2,5]


def local_center_from_frame(obs150):
    if obs150.shape[-1]!=150:raise ValueError('Expected frozen150D')
    # frame[9:13]=2*(q-reference); actiontarget=reference+1.6*a.
    return obs150[...,9:13]/3.2


def log_prob(action,mean,std,center,*,weight=.05,local_std=.05/1.6):
    if not 0<weight<1 or local_std<=0 or action.shape!=mean.shape or std.shape!=mean.shape or center.shape!=mean.shape[:-1]+(4,):raise ValueError('Mixture shapes/parameters differ')
    if not all(torch.isfinite(x).all() for x in (action,mean,std,center)) or (std<=0).any():raise ValueError('Nonfinite/invalid mixture')
    # One component draw for allfour legs; wheels identical in bothcomponents.
    base=torch.distributions.Normal(mean[...,LEGS],std[...,LEGS]).log_prob(action[...,LEGS]).sum(-1)
    local=torch.distributions.Normal(center,torch.full_like(center,local_std)).log_prob(action[...,LEGS]).sum(-1)
    legs=torch.logaddexp(base+math.log1p(-weight),local+math.log(weight))
    wheels=torch.distributions.Normal(mean[...,WHEELS],std[...,WHEELS]).log_prob(action[...,WHEELS]).sum(-1)
    return legs+wheels
