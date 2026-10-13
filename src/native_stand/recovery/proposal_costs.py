"""CPU proposal terms only; not wired into training/reward or runtime control."""
import torch


def wheel_mean_excess(mean,eligible,*,margin=.9):
    """Differentiable policy loss before clipping; zero on ineligible rows."""
    if mean.shape[-1]!=6 or eligible.shape!=mean.shape[:-1] or not 0<margin<1:
        raise ValueError('Invalid mean/mask/margin')
    excess=torch.relu(mean[..., [2,5]].abs()-margin)
    return eligible.to(mean.dtype)*excess.square().mean(-1)


def low_height_wheel_effort(height,effort,*,start=.20,full=.32,limit=5.5):
    """Bounded physical-effort reward cost proposal, no command filtering.

    Input must be measured physical clipped effort in left-first6 order. This
    neither brakes a wheel nor enforces zero effort; weight and dt live outside.
    """
    if effort.shape[-1]!=6 or height.shape!=effort.shape[:-1] or full<=start or limit<=0:
        raise ValueError('Invalid height/effort/gate')
    gate=(1-(height-start)/(full-start)).clamp(0,1)
    gate=torch.where(height>=full,torch.zeros_like(gate),gate)
    return gate*(effort[..., [2,5]]/limit).square().mean(-1)
