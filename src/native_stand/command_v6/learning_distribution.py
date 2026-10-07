"""Explicit physical-output calibration using the installed RSL distribution API.

Keeping trainable mean/std in source coordinates avoids making the wheel std
parameter16.7x smaller while retaining the same3e-5 optimizer learning rate.
"""
import torch
from torch import nn
from torch.distributions import Normal
from rsl_rl.modules.distribution import GaussianDistribution


class WheelScaledGaussianDistribution(GaussianDistribution):
    def __init__(self, output_dim, *, wheel_factor, init_std=.2, std_type='scalar'):
        super().__init__(output_dim,init_std=init_std,std_type=std_type)
        if output_dim!=6 or not 0<wheel_factor<=1 or std_type!='scalar':
            raise ValueError('wheel calibration requires six scalar-std native outputs')
        factor=torch.tensor([1.,1.,wheel_factor,1.,1.,wheel_factor])
        self.register_buffer('output_factor',factor,persistent=False)

    def update(self, mlp_output):
        self._distribution=Normal(mlp_output*self.output_factor,
                                  self.std_param.expand_as(mlp_output)*self.output_factor)

    def deterministic_output(self, mlp_output):
        return mlp_output*self.output_factor

    def as_deterministic_output_module(self):
        return _ScaledOutput(self.output_factor)


class _ScaledOutput(nn.Module):
    def __init__(self, factor):
        super().__init__()
        self.register_buffer('factor',factor.clone())

    def forward(self, value):
        return value*self.factor
