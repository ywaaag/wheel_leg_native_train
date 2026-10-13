FROZEN_TEST_SCOPE='PORTABLE'
import copy
import torch
from tensordict import TensorDict
from rsl_rl.algorithms import PPO
from rsl_rl.storage import RolloutStorage
from native_stand.command_v6.tools.model_factory import model
from native_stand.recovery.controlled_ppo import ControlledPPO,KEY,normalize_valid,pre_action_valid


def build(cls):
    obs=TensorDict({'policy':torch.zeros(4,25),'history':torch.zeros(4,125),KEY:torch.ones(4,1,dtype=torch.bool)},batch_size=[4])
    spec={'task':'recovery','ppo':{'hidden_dims':[8,4]}}
    actor=model(obs,actor=True,spec=spec);critic=model(obs,actor=False,spec=spec)
    st=RolloutStorage('rl',4,3,obs,[6],'cpu')
    p=cls(actor,critic,st,num_learning_epochs=2,num_mini_batches=2,learning_rate=3e-5,schedule='fixed',entropy_coef=.001,value_loss_coef=.5,use_clipped_value_loss=False)
    return p,obs


def fill(p,obs,valid=True):
    for step in range(3):
        x=obs.clone();x['policy']=torch.randn(4,25)*.1;x[KEY][:]=valid
        p.act(x);p.process_env_step(x,torch.randn(4),torch.tensor([False,step==1,False,False]),{'time_outs':torch.zeros(4)})
    p.compute_returns(x)
    return x


def test_all_valid_real_update_equivalence_rng_and_gae():
    torch.manual_seed(12);a,obs=build(PPO);b,_=build(ControlledPPO);b.actor.load_state_dict(a.actor.state_dict());b.critic.load_state_dict(a.critic.state_dict())
    rng=torch.get_rng_state();fill(a,obs);torch.set_rng_state(rng);fill(b,obs)
    assert torch.equal(a.storage.returns,b.storage.returns);assert torch.allclose(a.storage.advantages,b.storage.advantages)
    rng=torch.get_rng_state();la=a.update();ra=torch.get_rng_state();torch.set_rng_state(rng);lb=b.update();assert torch.equal(ra,torch.get_rng_state())
    for pa,pb in zip(a.actor.parameters(),b.actor.parameters()):assert torch.allclose(pa,pb,atol=1e-8)
    for pa,pb in zip(a.critic.parameters(),b.critic.parameters()):assert torch.allclose(pa,pb,atol=1e-8)
    assert abs(la['surrogate']-lb['surrogate'])<1e-7


def test_invalid_actor_and_adam_state_unchanged_after_momentum_exists():
    torch.manual_seed(22);p,obs=build(ControlledPPO);fill(p,obs);p.update()
    before=copy.deepcopy(p.actor.state_dict());mom={id(x):copy.deepcopy(p.optimizer.state[x]) for x in p.actor.parameters()};critic=copy.deepcopy(p.critic.state_dict())
    fill(p,obs,False);p.update()
    assert all(torch.equal(v,p.actor.state_dict()[k]) for k,v in before.items())
    for x in p.actor.parameters():
        assert x.grad is None
        assert all(torch.equal(v,p.optimizer.state[x][k]) for k,v in mom[id(x)].items())
    assert any(not torch.equal(v,p.critic.state_dict()[k]) for k,v in critic.items())
    assert p.mask_summary['actor_optimizer_steps']==0


def test_valid_advantage_normalization_independent_of_invalid_values_and_boundary():
    m=torch.tensor([[True],[False],[True]]);a=torch.tensor([[1.],[100.],[3.]]);b=a.clone();b[1]=1e6
    assert torch.equal(normalize_valid(a,m),normalize_valid(b,m))
    assert pre_action_valid(torch.tensor([True,False,False]),torch.tensor([True,True,False])).tolist()==[False,True,False]
    # failure is intentionally absent: last controlled transition remains valid.
    assert pre_action_valid(torch.tensor([False]),torch.tensor([True])).item()


def test_invalid_actions_do_not_affect_actor_update_and_shuffle_preserves_mask():
    torch.manual_seed(9);p,obs=build(ControlledPPO);fill(p,obs);p.storage.observations[KEY][0]=False
    p.storage.advantages=normalize_valid(p.storage.returns-p.storage.values,p.storage.observations[KEY])
    q,_=build(ControlledPPO);q.actor.load_state_dict(p.actor.state_dict());q.critic.load_state_dict(p.critic.state_dict());q.storage=copy.deepcopy(p.storage);q.storage.actions[0]+=100
    rng=torch.get_rng_state();p.update();torch.set_rng_state(rng);q.update()
    assert all(torch.equal(x,y) for x,y in zip(p.actor.parameters(),q.actor.parameters()))
    assert p.mask_summary['valid_actor_samples']==8

def test_two_rollouts_returns_not_spliced_or_masked_and_missing_mask_rejected():
    import pytest
    torch.manual_seed(45);p,obs=build(ControlledPPO);q,_=build(PPO);q.actor.load_state_dict(p.actor.state_dict());q.critic.load_state_dict(p.critic.state_dict())
    for _ in range(2):
        rng=torch.get_rng_state();fill(p,obs);torch.set_rng_state(rng);fill(q,obs)
        assert torch.equal(p.storage.returns,q.storage.returns)
        p.storage.clear();q.storage.clear()
    with pytest.raises(ValueError):p.act(obs.exclude(KEY))
    assert not set(map(id,p.actor.parameters()))&set(map(id,p.critic.parameters()))


def test_episode_boundary_pre_action_mask_not_post_failure_or_reset():
    initial=torch.tensor([True,False,False,True]);checked=torch.tensor([True,True,True,False]);pre=pre_action_valid(initial,checked)
    post_reset=torch.tensor([False,False,True,True])
    assert pre.tolist()==[False,True,True,False]
    assert pre[2] # controlled failed last step must remain, even if post-step resets
