FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.recovery.support_geometry_proposal import target_terms

def test_bilateral_quality_single_side_and_up_do_not_earn_support_bonus():
    L=torch.tensor([[.15,.15],[.15,.375],[.15,.15],[.375,.375]])
    c=torch.tensor([[1.,1.],[1.,1.],[-1.,-1.],[1.,1.]])
    t=target_terms(L,c,torch.ones(4)*.18,torch.ones(4,dtype=torch.bool))
    assert torch.allclose(t['positive_quality'],torch.tensor([.003,0.,0.,0.]))

def test_high_gate_does_not_award_bad_geometry_and_dt_exactly_once():
    L=torch.ones(2,2)*.375;c=torch.zeros_like(L)
    t=target_terms(L,c,torch.tensor([.18,.34]),torch.ones(2,dtype=torch.bool))
    assert (t['positive_quality']==0).all() and t['negative_cost'][1]==0 and t['negative_cost'][0]<0
    t=target_terms(torch.ones(2,2)*.15,torch.ones(2,2),torch.ones(2)*.18,torch.tensor([True,False]))
    assert torch.allclose(t['positive_quality'],torch.tensor([.003,0.]))

def test_bonus_residence_reward_is_visible_not_hidden():
    def total(n):
        t=target_terms(torch.ones(n,2)*.15,torch.ones(n,2),torch.ones(n)*.18,torch.ones(n,dtype=torch.bool))
        return (t['positive_quality']*.99**torch.arange(n)).sum()
    assert total(100)>total(30) # Explicit tradeoff; not declared policy invariant.
