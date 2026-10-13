FROZEN_TEST_SCOPE='PORTABLE'
import pytest
import torch
from native_stand.recovery.proposal_costs import wheel_mean_excess,low_height_wheel_effort

def test_mean_gradient_points_inside_without_touching_legs_or_masked_group():
    x=torch.tensor([[.2,-1.2,-2.,.3,-1.1,1.5],[.2,-1.2,-2.,.3,-1.1,1.5]],requires_grad=True)
    loss=wheel_mean_excess(x,torch.tensor([True,False])).sum();loss.backward()
    assert x.grad[0,2]<0 and x.grad[0,5]>0
    assert torch.equal(x.grad[0,[0,1,3,4]],torch.zeros(4)) and torch.equal(x.grad[1],torch.zeros(6))
    # The first-order gradient descent direction reduces both excess magnitudes.
    assert wheel_mean_excess(x.detach()-.01*x.grad,torch.tensor([True,False])).sum()<loss

def test_effort_gate_bounded_dt_not_inside_and_sign_independent():
    h=torch.tensor([.168,.26,.32,.42]);effort=torch.zeros(4,6);effort[:,[2,5]]=5.5
    cost=low_height_wheel_effort(h,effort)
    assert torch.allclose(cost,torch.tensor([1.,.5,0.,0.]))
    assert torch.equal(cost,low_height_wheel_effort(h,-effort))
    assert torch.allclose(-.1*.01*cost,torch.tensor([-.001,-.0005,0.,0.]))
    with pytest.raises(ValueError):low_height_wheel_effort(h,effort,full=.1)
