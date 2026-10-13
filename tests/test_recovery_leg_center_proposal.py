FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.recovery.leg_center_proposal import eligible_mask,terms

def test_mask_excludes_init_failure_oldgroup_entry_and100msboundary():
    family=torch.tensor([1,1,0,1,1,1],dtype=torch.bool);controlled=torch.tensor([1,0,1,1,1,1],dtype=torch.bool)
    t=torch.tensor([0.,.01,.02,.03,.04,.1]);entry=torch.tensor([-1,-1,-1,0,-1,-1]);failed=torch.tensor([0,0,0,0,1,0],dtype=torch.bool)
    assert eligible_mask(family,controlled,t,entry,failed).tolist()==[True,False,False,False,False,False]

def test_gradient_moves_legmeans_toward_q_band_without_wheel_gradient():
    mean=torch.tensor([[0.,0.,-.95,0.,0.,-.9]],requires_grad=True);obs=torch.zeros(1,150);obs[:,9:13]=torch.tensor([2.,-2.,-2.,-2.])
    loss=terms(mean,obs,torch.tensor([True])).sum();loss.backward()
    assert mean.grad[0,[0,1,3,4]].sign().tolist()==[-1.,1.,1.,1.]
    assert (mean.grad[0,[2,5]]==0).all()
    assert terms(mean.detach(),obs,torch.tensor([False])).item()==0
