"""Recovery-only bounded wheel mean; ordinary Gaussian action likelihood."""
import torch
from torch import nn
from torch.distributions import Normal
from rsl_rl.modules.distribution import GaussianDistribution

class _BoundedWheelMean(nn.Module):
    def forward(self,value):
        # Four leg means stay in the original action coordinates.
        return torch.cat((value[...,0:2],value[...,2:3].tanh(),
                          value[...,3:5],value[...,5:6].tanh()),-1)


class WheelBoundedMeanGaussianDistribution(GaussianDistribution):
    """Only mean is reparameterized; ordinary Gaussian action likelihood."""
    def __init__(self,output_dim,init_std=.2,std_type='scalar'):
        super().__init__(output_dim,init_std=init_std,std_type=std_type)
        if output_dim!=6 or std_type!='scalar':raise ValueError('Expected six scalar-std outputs')

    def update(self,mlp_output):
        self._distribution=Normal(self.deterministic_output(mlp_output),self.std_param.expand_as(mlp_output))

    def deterministic_output(self,mlp_output):
        return _BoundedWheelMean()(mlp_output)

    def as_deterministic_output_module(self):
        return _BoundedWheelMean()
