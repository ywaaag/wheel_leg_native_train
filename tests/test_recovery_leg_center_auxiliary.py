FROZEN_TEST_SCOPE='PORTABLE'
import copy
import torch
import pytest
from tensordict import TensorDict
from native_stand.recovery.leg_center_auxiliary import LegCenterAuxiliary,declaration

class Actor(torch.nn.Module):
    def __init__(self):
        super().__init__();self.weight=torch.nn.Parameter(torch.ones(6)*.2);self.calls=0
    def forward(self,obs,stochastic_output=False):
        self.calls+=1;return self.weight.expand(len(obs['policy']),6)

def test_real_optimizer_hook_excludes_failed_old_late_and_preserves_rng():
    actor=Actor();cfg=declaration();aux=LegCenterAuxiliary(actor,cfg,max_grad_norm=1.)
    obs=TensorDict({'policy':torch.zeros(5,25),'history':torch.zeros(5,125)},batch_size=[5]);obs['policy'][:,9:13]=1.
    rng=torch.get_rng_state().clone()
    with torch.inference_mode():
        aux.capture_pre(obs,family=torch.tensor([1,1,0,1,1],dtype=torch.bool),controlled=torch.ones(5,dtype=torch.bool),
            clock=torch.tensor([0.,.01,.02,.1,.03]),entry=torch.ones(5)*-1)
        aux.finish_transition(torch.tensor([0,1,0,0,0],dtype=torch.bool))
    aux.finalize();assert aux.eligible_count==2 and aux.denominator==5
    optimizer=torch.optim.Adam(actor.parameters(),lr=.001);handle=optimizer.register_step_pre_hook(aux.before_step)
    actor.weight.grad=torch.zeros_like(actor.weight);optimizer.step();handle.remove()
    assert aux.summary()['first_step']['weighted_aux_actor_norm']>0
    assert actor.calls==1 and torch.equal(rng,torch.get_rng_state())
    assert aux.summary()['first_step']['combined_actor_norm_after_reclip']<=1+1e-6

def test_empty_batch_does_not_forward_or_mutate_and_missing_post_rejected():
    actor=Actor();aux=LegCenterAuxiliary(actor,declaration(),max_grad_norm=1.)
    obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
    aux.capture_pre(obs,family=torch.zeros(1,dtype=torch.bool),controlled=torch.ones(1,dtype=torch.bool),clock=torch.zeros(1),entry=torch.ones(1)*-1)
    with pytest.raises(ValueError):aux.finalize()
    aux.finish_transition(torch.zeros(1,dtype=torch.bool));aux.finalize();before=actor.weight.detach().clone()
    aux.before_step(None,None,None);assert actor.calls==0 and torch.equal(before,actor.weight)
