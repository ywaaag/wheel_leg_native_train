"""CPU-only exploration-center auxiliary proposal; not wired into trainer."""
import torch


def eligible_mask(family_is_swing,controlled,pre_clock,entry,failed):
    if not all(x.shape==pre_clock.shape for x in (family_is_swing,controlled,entry,failed)):
        raise ValueError('Eligibility shapes differ')
    return family_is_swing.bool()&controlled.bool()&(pre_clock>=0)&(pre_clock<.1-1e-7)&(entry<0)&~failed.bool()


def terms(mean,obs150,eligible,*,band_rad=.15):
    if mean.shape[-1]!=6 or obs150.shape!=mean.shape[:-1]+(150,) or eligible.shape!=mean.shape[:-1] or band_rad<=0:
        raise ValueError('Explicit mean/observation/mask shapes differ')
    error=1.6*mean[..., [0,1,3,4]]-obs150[...,9:13]/2
    raw=torch.relu(error.abs()-band_rad).square().mean(-1)
    return raw*eligible.to(raw.dtype)
