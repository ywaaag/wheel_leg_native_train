"""Mirrored teaching and elapsed-progress proposals do not alter legacy IO."""
FROZEN_TEST_SCOPE='PORTABLE'
import pytest,torch
from native_stand.students.standing_mirror import project,errors,progress,progress_contract
from native_stand.students.mcu_interface import contract

def test_projection_is_physical_mirror_and_minimum_pair_change():
 x=torch.tensor([[.2,-.1,-.3,-.2],[.1,.4,-.1,.4]])
 y=project(x);assert errors(y).eq(0).all()
 torch.testing.assert_close(y,torch.tensor([[.25,-.15,-.25,-.15],[.1,.4,-.1,.4]]))
 assert torch.equal(project(y),y)
 with pytest.raises(ValueError):project(torch.zeros(3))

def test_elapsed_progress_is_deployable_preaction_hint_not_success():
 t=torch.tensor([0.,.5,1.25,2.5,10.]);initial=torch.tensor([True,False,False,False,False])
 torch.testing.assert_close(progress(t,initial),torch.tensor([0.,.2,.5,1.,1.]))
 assert progress(t,torch.ones(5,dtype=torch.bool)).eq(0).all()
 assert contract()['actor_dim']==31 and progress_contract()['actor_dim_proposed']==32
 assert progress_contract()['status']=='CPU_PROPOSAL_NOT_RUNTIME'
 with pytest.raises(ValueError):progress(torch.tensor([-1.]),torch.tensor([False]))
