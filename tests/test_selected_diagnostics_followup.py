import copy
from types import SimpleNamespace

import pytest
import torch
from tensordict import TensorDict

from native_stand.command_v6.learning import model
from native_stand.command_v6.domain.selected_diagnostics import (
    PolicyUpdateSummary,configuration,selected,storage_summary)
from native_stand.recovery.standing import StandingRetention
from native_stand.command_v6.domain.retention import RetentionBatch,attach_optimizer_retention


def actor_and_storage():
    obs=TensorDict({'policy':torch.randn(4,25),'history':torch.randn(4,125)},[4])
    actor=model(obs,actor=True,spec={'ppo':{'hidden_dims':[256,128,64]}})
    # Build a live autograd distribution cache, as PPO does during updates.
    actions=actor(obs,stochastic_output=True).detach()
    log_prob=actor.get_output_log_prob(actions).detach()
    params=tuple(value.detach().clone().reshape(2,2,-1) for value in actor.output_distribution_params)
    storage=SimpleNamespace(num_envs=2,num_transitions_per_env=2,
        observations=TensorDict({k:v.reshape(2,2,-1) for k,v in obs.items()},[2,2]),
        actions=actions.reshape(2,2,6),actions_log_prob=log_prob.reshape(2,2,1),
        distribution_params=params,values=torch.ones(2,2,1),returns=torch.full((2,2,1),2.),
        advantages=torch.zeros(2,2,1))
    return actor,storage


def test_full_rollout_probe_no_rng_parameter_or_distribution_change():
    torch.manual_seed(17)
    actor,storage=actor_and_storage()
    rng=torch.get_rng_state().clone()
    parameters={name:value.detach().clone() for name,value in actor.state_dict().items()}
    cached=actor.distribution._distribution
    probe=PolicyUpdateSummary(actor,storage,.2)
    result=probe.summary(actor)
    assert result['before']['ratio']['mean']==pytest.approx(1.)
    assert result['before']['KL']['max']==pytest.approx(0.,abs=1e-6)
    assert result['after']['clip_fraction']==0
    assert torch.equal(rng,torch.get_rng_state())
    assert actor.distribution._distribution is cached
    for name,value in actor.state_dict().items():torch.testing.assert_close(value,parameters[name],rtol=0,atol=0)
    with torch.no_grad():actor.mlp[-1].bias.add_(.1)
    changed=probe.summary(actor)['after']
    assert changed['KL']['mean']>0 and changed['ratio']['std']>0


def test_storage_raw_and_normalized_advantages_are_distinct():
    _,storage=actor_and_storage()
    summary=storage_summary(storage)
    assert summary['raw_advantages']['mean']==1
    assert summary['advantages']['mean']==0
    assert not selected({},1)
    with pytest.raises(ValueError):configuration({'diagnostics':True})


def test_retention_metadata_eligible_selected_and_gradient_no_behavior_change():
    torch.manual_seed(23)
    actor,storage=actor_and_storage()
    # Clear cached non-leaf distribution before copying the fixture model.
    actor.distribution._distribution=None
    teacher=copy.deepcopy(actor)
    teacher.distribution._distribution=None
    probe=StandingRetention(actor,teacher,coefficient=.02,max_samples=2,max_grad_norm=1.,gradient_diagnostics=True)
    optimizer=torch.optim.SGD(actor.parameters(),lr=1e-4)
    optimizer.register_step_pre_hook(probe.before_step)
    probe.begin_rollout(1,phase='formal')
    obs=storage.observations.flatten(0,1)
    eligible=torch.tensor([True,False,True,True])
    metadata=torch.tensor([[1.,0.,0.],[2.,.5,0.],[3.,0.,0.],[4.,0.,0.]])
    probe.capture(obs,eligible,metadata)
    optimizer.zero_grad();actor(obs).square().mean().backward();optimizer.step()
    assert int(probe.eligible_count)==3 and probe.selected==2
    assert probe.selected_metadata[:,0].tolist()==[1.,3.]
    assert probe.channel_error.shape==(6,)
    assert probe.summary()['gradient_comparison'] is not None
    assert all(parameter.grad is None for parameter in teacher.parameters())


def test_fixed_reference_gradient_probe_preserves_exact_optimizer_update():
    torch.manual_seed(57)
    actor,storage=actor_and_storage();actor.distribution._distribution=None
    teacher=copy.deepcopy(actor)
    with torch.no_grad():teacher.mlp[-1].bias.add_(.1)
    obs=storage.observations.flatten(0,1)
    reference=RetentionBatch(torch.cat((obs['policy'],obs['history']),-1)[:3],
        torch.tensor([[0.,0.],[.5,0.],[-.5,0.]]),torch.tensor([6.,7.,8.]),{})
    def update(enabled):
        student=copy.deepcopy(actor)
        optimizer=torch.optim.Adam(student.parameters(),lr=3e-5)
        ppo=SimpleNamespace(actor=student,optimizer=optimizer,max_grad_norm=1.,
            _record_retention_diagnostics=enabled,_reference_gradient=None)
        attach_optimizer_retention(ppo,teacher,reference,lam=.02)
        optimizer.zero_grad();student(obs).square().mean().backward()
        torch.nn.utils.clip_grad_norm_(student.parameters(),1.)
        optimizer.step()
        return student,ppo
    plain,_=update(False);probed,ppo=update(True)
    for p,q in zip(plain.parameters(),probed.parameters()):torch.testing.assert_close(p,q,rtol=0,atol=0)
    assert ppo._reference_gradient is not None and ppo._reference_gradient[2]>0
    assert all(p.grad is None for p in teacher.parameters())
