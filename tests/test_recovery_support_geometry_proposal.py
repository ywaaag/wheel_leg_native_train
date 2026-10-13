FROZEN_TEST_SCOPE='PORTABLE'
import pytest
import torch
from native_stand.recovery.support_geometry_proposal import geometry,potential,shaping

def test_short_down_vs_long_up_geometry_and_invalid_values():
    anchors=torch.zeros(2,3);g=torch.tensor([[0.,0.,-1.],[0.,0.,-1.]])
    wheels=torch.tensor([[[0.,0.,-.15],[0.,0.,-.15]],[[0.,0.,.375],[0.,0.,.375]]])
    r=geometry(wheels,anchors,g);assert torch.allclose(r['cost'],torch.tensor([0.,1.]))
    with pytest.raises(ValueError):geometry(torch.zeros_like(wheels),anchors,g)
    with pytest.raises(ValueError):geometry(wheels,anchors,g*float('nan'))

def test_exact_gate_and_old_group_zero():
    cost=torch.ones(4);h=torch.tensor([.168,.26,.30,.42]);eligible=torch.tensor([True,True,True,False])
    assert torch.allclose(potential(cost,h,eligible),torch.tensor([-1.,-.5,0.,0.]),atol=1e-6)

@pytest.mark.parametrize('sequence',[[-.7,-.7,-.7,-.7],[-.7,-.4,-.2,0.],[-.7,-.3,-.7,-.3]])
def test_absorbing_endpoint_discounted_total_cancels_path(sequence):
    p=torch.tensor(sequence,dtype=torch.float64);terminal=torch.tensor([False,False,True])
    r=shaping(p[:-1],p[1:],absorbing_terminal=terminal,gamma=.99,beta=.1)
    assert float((r*torch.tensor([1.,.99,.99**2])).sum())==pytest.approx(.07,abs=1e-8)

def test_terminal_release_timeout_bootstrap_and_no_extra_dt():
    pre=torch.tensor([-.7]);post=torch.tensor([-.8])
    assert shaping(pre,post,absorbing_terminal=torch.tensor([True])).item()==pytest.approx(.7)
    # External cutoff retains next potential; requires value bootstrap correction
    # for an invariant full-return comparison, rather than treating it as failure.
    assert shaping(pre,post,absorbing_terminal=torch.tensor([False])).item()==pytest.approx(-.092)
