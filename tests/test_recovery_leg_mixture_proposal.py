FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.recovery.leg_mixture_proposal import log_prob,local_center_from_frame

def test_joint_mixture_likelihood_matches_torch_distribution():
    mean=torch.randn(3,6,dtype=torch.float64);std=torch.ones_like(mean)*.1;center=torch.randn(3,4,dtype=torch.float64);action=mean.clone()
    legs=[0,1,3,4];wheels=[2,5]
    mix=torch.distributions.MixtureSameFamily(torch.distributions.Categorical(probs=torch.tensor([.95,.05],dtype=torch.float64)),
        torch.distributions.Independent(torch.distributions.Normal(torch.stack([mean[:,legs],center],-2),torch.stack([std[:,legs],torch.ones_like(center)*(.05/1.6)],-2)),1))
    expected=mix.log_prob(action[:,legs])+torch.distributions.Normal(mean[:,wheels],std[:,wheels]).log_prob(action[:,wheels]).sum(-1)
    assert torch.allclose(log_prob(action,mean,std,center),expected,atol=1e-12)

def test_frame_center_and_basegradient_do_not_inject_signed_bias():
    obs=torch.zeros(2,150);obs[:,9:13]=torch.tensor([2.,-2.,-2.,2.]);center=local_center_from_frame(obs)
    assert torch.allclose(center,obs[:,9:13]/3.2)
    mean=torch.zeros(2,6,requires_grad=True);action=torch.ones_like(mean)*.01
    log_prob(action,mean,torch.ones_like(mean)*.1,center).sum().backward()
    assert torch.isfinite(mean.grad).all() and (abs(mean.grad)>0).all()
