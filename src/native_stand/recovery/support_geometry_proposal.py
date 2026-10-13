"""CPU-only geometric potential proposal; no runtime/reward connection."""
import torch


def geometry(wheel_centers_root,hip_anchors_root,gravity_body,*,short_m=.15,long_m=.375):
    if (wheel_centers_root.shape[-2:]!=(2,3) or gravity_body.shape!=wheel_centers_root.shape[:-2]+(3,)
            or hip_anchors_root.shape!=(2,3) or not 0<short_m<long_m):
        raise ValueError('Explicit root-frame geometry shape/scale differs')
    if not all(torch.isfinite(v).all() for v in (wheel_centers_root,hip_anchors_root,gravity_body)):
        raise ValueError('Nonfinite geometry')
    vector=wheel_centers_root-hip_anchors_root
    length=vector.norm(dim=-1);norm=gravity_body.norm(dim=-1,keepdim=True)
    if (length<=1e-6).any() or (norm<=1e-6).any():raise ValueError('Undefined support direction')
    cosine=(vector*(gravity_body/norm)[...,None,:]).sum(-1)/length
    contraction=((length-short_m)/(long_m-short_m)).clamp(0,1).square()
    direction=(1-cosine.clamp(-1,1))/2
    return {'length_m':length,'down_angle_rad':torch.acos(cosine.clamp(-1,1)),
        'contraction_cost':contraction.mean(-1),'direction_cost':direction.mean(-1),
        'cost':(.5*contraction+.5*direction).mean(-1)}


def potential(cost,height,eligible,*,low_m=.22,high_m=.30):
    if cost.shape!=height.shape or eligible.shape!=height.shape or not low_m<high_m:
        raise ValueError('Potential shape/gate differs')
    # Smoothstep provides exact zero beyond gate; no persistent short-leg target.
    t=((height-low_m)/(high_m-low_m)).clamp(0,1)
    gate=1-(3*t.square()-2*t.pow(3))
    return -eligible.to(cost.dtype)*gate*cost


def shaping(phi_before,phi_after,*,absorbing_terminal,gamma=.99,beta=1.):
    if (phi_before.shape!=phi_after.shape or absorbing_terminal.shape!=phi_before.shape or
            not 0<gamma<=1 or beta<0):raise ValueError('Potential transition declaration invalid')
    nxt=torch.where(absorbing_terminal,torch.zeros_like(phi_after),phi_after)
    return beta*(gamma*nxt-phi_before)


def target_terms(length,down_cosine,height,eligible,*,weight_per_s=.3,dt=.01):
    """Compare proposed negative distance cost and positive support-quality bonus.

    CPU only; both change reward preferences. Product across sides avoids giving
    full quality to one good side; this is NOT a balance/safety certificate.
    """
    if (length.shape[-1]!=2 or down_cosine.shape!=length.shape or
            height.shape!=length.shape[:-1] or eligible.shape!=height.shape or
            weight_per_s<0 or dt<=0):raise ValueError('Target reward shape/scales differ')
    if not all(torch.isfinite(v).all() for v in (length,down_cosine,height)):
        raise ValueError('Nonfinite target geometry')
    contraction=((length-.15)/(.375-.15)).clamp(0,1)
    direction=(1-down_cosine.clamp(-1,1))/2
    cost=(.5*contraction.square()+.5*direction).mean(-1)
    gate=-potential(torch.ones_like(height),height,eligible)
    quality=((1-contraction)*(down_cosine.clamp(0,1))).prod(-1)
    return {'negative_cost':-weight_per_s*dt*gate*cost,
            'positive_quality':weight_per_s*dt*gate*quality,'quality':quality,'gate':gate}
