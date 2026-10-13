FROZEN_TEST_SCOPE='PORTABLE'
import copy
import pytest
import torch
from tensordict import TensorDict
from native_stand.recovery.mean_auxiliary import MeanAuxiliary,declaration,validate

class Actor(torch.nn.Module):
    def __init__(self):
        super().__init__();self.layer=torch.nn.Linear(150,6)
        with torch.no_grad():self.layer.weight.zero_();self.layer.bias.copy_(torch.tensor([0.,0.,-2.,0.,0.,-1.5]))
    def forward(self,o,stochastic_output=False):return self.layer(torch.cat([o['policy'],o['history']],-1))

def obs(n=4):return TensorDict({'policy':torch.ones(n,25),'history':torch.ones(n,125)},batch_size=[n])

def test_actual_hook_updates_wheels_reclips_preserves_rng_and_source_batch():
    actor=Actor();optimizer=torch.optim.Adam(actor.parameters(),lr=3e-5)
    aux=MeanAuxiliary(actor,declaration(),max_grad_norm=.01)
    optimizer.register_step_pre_hook(aux.before_step)
    with torch.inference_mode():aux.capture(obs(),torch.tensor([True,False,False,False]),torch.ones(4,dtype=torch.bool))
    aux.finalize();before=copy.deepcopy(actor.state_dict());rng=torch.get_rng_state().clone()
    optimizer.zero_grad();(actor(obs()).sum()*0).backward();optimizer.step()
    assert torch.equal(rng,torch.get_rng_state())
    assert actor.layer.bias[2]>before['layer.bias'][2] and actor.layer.bias[5]>before['layer.bias'][5]
    assert torch.equal(actor.layer.bias[[0,1,3,4]],before['layer.bias'][[0,1,3,4]])
    s=aux.summary();assert s['eligible_count']==1 and s['controlled_denominator']==4 and s['nonempty_applications']==1
    assert s['first_step']['combined_actor_norm_after_reclip']<=.010001
    # mean two-wheel excess=(1.1^2+.6^2)/2; denominator includes all4 controlled rows.
    assert s['first_step']['weighted_loss']==pytest.approx(.001*(1.1**2+.6**2)/2/4)

def test_empty_eligible_hook_matches_no_hook_optimizer_exactly():
    a=Actor();b=copy.deepcopy(a);oa=torch.optim.Adam(a.parameters());ob=torch.optim.Adam(b.parameters())
    aux=MeanAuxiliary(a,declaration(),max_grad_norm=1.);oa.register_step_pre_hook(aux.before_step)
    aux.capture(obs(),torch.zeros(4,dtype=torch.bool),torch.ones(4,dtype=torch.bool));aux.finalize()
    for actor,opt in ((a,oa),(b,ob)):
        opt.zero_grad();actor(obs()).square().mean().backward();opt.step()
    assert all(torch.equal(v,b.state_dict()[k]) for k,v in a.state_dict().items())
    assert aux.summary()['nonempty_applications']==0

def test_invalid_eligibility_and_contract_rejected():
    a=MeanAuxiliary(Actor(),declaration(),max_grad_norm=1.)
    a.capture(obs(),torch.ones(4,dtype=torch.bool),torch.zeros(4,dtype=torch.bool))
    with pytest.raises(ValueError):a.finalize()
    s={'task':'recovery','initialization':'warmstart','recovery':{'wheel_mean_auxiliary':declaration(),
        'active_family':declaration()['family']}}
    validate(s);s['recovery']['wheel_mean_auxiliary']['coefficient']=.1
    with pytest.raises(ValueError):validate(s)

def test_actual_sampling_readback_no_rng_and_correct_mask():
    a=MeanAuxiliary(Actor(),declaration(),max_grad_norm=1.)
    mean=torch.tensor([[0.,0.,-2.,0.,0.,-1.2],[0.,0.,-2.,0.,0.,-1.2]])
    sampled=torch.tensor([[0.,0.,-.8,0.,0.,-1.3],[0.,0.,-2.,0.,0.,-1.3]])
    rng=torch.get_rng_state().clone()
    a.observe_policy(mean,torch.ones_like(mean)*.05,sampled,torch.tensor([True,False]))
    d=a.summary()['actual_pre_action_policy_sampling']
    assert d['mean_outside_fraction'][2]==1 and d['sampled_clip_fraction'][2]==0 and d['sampled_clip_fraction'][5]==1
    assert d['eligible_samples']==1 and torch.equal(rng,torch.get_rng_state())

def test_v2_coefficient_explicit_old_version_preserved():
    old=declaration();new=declaration('swing_wheel_mean_excess_rollout_v2')
    assert old['coefficient']==.001 and new['coefficient']==.03
    assert {k:v for k,v in old.items() if k not in ('version','coefficient')}=={k:v for k,v in new.items() if k not in ('version','coefficient')}
    s={'task':'recovery','initialization':'warmstart','recovery':{'wheel_mean_auxiliary':new,'active_family':new['family']}}
    validate(s);s['recovery']['wheel_mean_auxiliary']['version']=old['version']
    with pytest.raises(ValueError):validate(s)
