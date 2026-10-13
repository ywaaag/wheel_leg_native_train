"""CPU-only coordinate proposal; intentionally not wired into policy/runtime."""
import math
import torch
from torch.nn.functional import softplus


def squash_wheels(latent):
    if latent.shape[-1]!=6 or not torch.isfinite(latent).all():raise ValueError('Expected finite6D latent action')
    result=latent.clone();result[...,2]=latent[...,2].tanh();result[...,5]=latent[...,5].tanh()
    return result


def bounded_wheel_mean(raw_mean):
    """Mean reparameterization,not a transformed random variable or controller."""
    return squash_wheels(raw_mean)


def bounded_mean_gaussian_log_prob(action,raw_mean,std):
    if action.shape!=raw_mean.shape or std.shape!=raw_mean.shape or (std<=0).any():
        raise ValueError('Expected matched action/mean/std')
    return torch.distributions.Normal(bounded_wheel_mean(raw_mean),std).log_prob(action).sum(-1)


def log_prob_from_latent(latent,mean,std):
    if latent.shape!=mean.shape or mean.shape!=std.shape or latent.shape[-1]!=6 or (std<=0).any():raise ValueError('Coordinate/scale shape differs')
    base=torch.distributions.Normal(mean,std).log_prob(latent).sum(-1)
    u=latent[...,[2,5]]
    # Stable log(1-tanh(u)^2); latent must correspond to the emitted physical action.
    jacobian=(2*(math.log(2)-u-softplus(-2*u))).sum(-1)
    return base-jacobian


def log_prob_from_physical(action,mean,std):
    if (abs(action[...,[2,5]])>=1).any():raise ValueError('Boundary has no finite inverse; preserve latent for exact likelihood')
    latent=action.clone();latent[...,2]=torch.atanh(action[...,2]);latent[...,5]=torch.atanh(action[...,5])
    return log_prob_from_latent(latent,mean,std)
