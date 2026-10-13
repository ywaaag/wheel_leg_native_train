"""Std coordinates before clipping; explicit parameterization/calibration/action units."""
import torch


def readback(parameter,*,parameterization,output_factor,leg_scale_rad,wheel_scale_rad_s):
    value=torch.as_tensor(parameter).detach()
    if value.shape!=(6,) or not torch.isfinite(value).all():raise ValueError('std requires finite six channels')
    if parameterization in ('scalar','positive_scalar'):std=value
    elif parameterization=='log':std=value.exp()
    else:raise ValueError('unsupported std parameterization')
    factor=torch.as_tensor(output_factor,device=std.device,dtype=std.dtype)
    if factor.ndim==0:factor=factor.expand_as(std)
    if factor.shape!=(6,) or not torch.isfinite(factor).all() or not (factor>0).all() or not (std>0).all():
        raise ValueError('positive finite std/output factors required')
    scales=std.new_tensor([leg_scale_rad,leg_scale_rad,wheel_scale_rad_s,leg_scale_rad,leg_scale_rad,wheel_scale_rad_s])
    if not torch.isfinite(scales).all() or not (scales>0).all():raise ValueError('positive physical action scales required')
    return {'parameterization':parameterization,'parameter':value.cpu().tolist(),
        'source_coordinate_std':std.cpu().tolist(),'output_factor':factor.cpu().tolist(),
        'normalized_action_std':(std*factor).cpu().tolist(),'physical_target_std':(std*factor*scales).cpu().tolist(),
        'units':['rad','rad','rad/s','rad','rad','rad/s'],
        'scope':'Gaussian raw action before clipping/projection; not torque or executed-target std',
        'trainable_during_PPO':True}
