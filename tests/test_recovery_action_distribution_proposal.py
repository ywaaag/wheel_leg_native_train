FROZEN_TEST_SCOPE='PORTABLE'
import torch
import pytest
from native_stand.recovery.action_distribution_proposal import squash_wheels,log_prob_from_latent,log_prob_from_physical

def test_logprob_matches_torch_transformed_wheel_likelihood_and_legs_unchanged():
    u=torch.tensor([[.2,-.1,-2.,.3,-.4,1.5]],dtype=torch.float64)
    mean=u+.01;std=torch.ones_like(u)*.05;a=squash_wheels(u)
    transformed=torch.distributions.TransformedDistribution(torch.distributions.Normal(mean[:,[2,5]],std[:,[2,5]]),[torch.distributions.TanhTransform(cache_size=1)])
    expected=transformed.log_prob(a[:,[2,5]]).sum(-1)+torch.distributions.Normal(mean[:,[0,1,3,4]],std[:,[0,1,3,4]]).log_prob(u[:,[0,1,3,4]]).sum(-1)
    assert torch.allclose(log_prob_from_latent(u,mean,std),expected,atol=1e-10)
    assert torch.allclose(log_prob_from_physical(a,mean,std),expected,atol=1e-10)
    assert torch.equal(a[:,[0,1,3,4]],u[:,[0,1,3,4]])

def test_bounded_output_has_nonzero_local_slope_at_actual_source_mean():
    u=torch.tensor([[0.,0.,-1.875,0.,0.,-1.71]],requires_grad=True)
    a=squash_wheels(u);a.sum().backward()
    assert (abs(a[:,[2,5]])<1).all() and (u.grad[:,[2,5]]>0).all()

def test_inverse_rejects_exactboundary_and_stable_latent_logprob_extreme():
    u=torch.tensor([[0.,0.,-100.,0.,0.,100.]],dtype=torch.float64)
    assert torch.isfinite(log_prob_from_latent(u,u,torch.ones_like(u))).all()
    with pytest.raises(ValueError):log_prob_from_physical(squash_wheels(u),u,torch.ones_like(u))


def test_bounded_mean_uses_ordinary_gaussian_action_coordinates_and_gradient():
    from native_stand.recovery.action_distribution_proposal import bounded_wheel_mean,bounded_mean_gaussian_log_prob
    raw=torch.tensor([[0.,0.,-1.875,0.,0.,-1.71]],dtype=torch.float64,requires_grad=True)
    action=bounded_wheel_mean(raw).detach()+.01;std=torch.ones_like(raw)*.05
    expected=torch.distributions.Normal(bounded_wheel_mean(raw),std).log_prob(action).sum(-1)
    actual=bounded_mean_gaussian_log_prob(action,raw,std)
    assert torch.equal(actual,expected)
    actual.sum().backward();assert (abs(raw.grad[:,[2,5]])>0).all()
