FROZEN_TEST_SCOPE='PORTABLE'
import copy
import torch
import pytest
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.command_v6.domain.action_distribution import declaration,validate
from native_stand.recovery.learning_distribution import WheelBoundedMeanGaussianDistribution


def spec():
    return {'task':'recovery','source_input_dim':150,'action':{'wheel_scale_rad_s':100},'recovery':{},
        'ppo':{'hidden_dims':[8,8]},'action_distribution':declaration()}


def test_schema_rejects_wrong_coordinates_or_conflicting_conversion():
    s=spec();validate(s);s['action_distribution']['log_prob']='latent'
    with pytest.raises(ValueError):validate(s)


def test_distribution_mean_std_likelihood_KL_entropy_and_export():
    raw=torch.tensor([[.2,-.1,-1.875,.4,-.3,-1.71]],requires_grad=True)
    d=WheelBoundedMeanGaussianDistribution(6);d.update(raw)
    expected=raw.detach().clone();expected[:,[2,5]]=expected[:,[2,5]].tanh()
    assert torch.equal(d.mean,expected) and torch.equal(d.std,d.std_param.expand_as(raw))
    sample=expected+.01
    normal=torch.distributions.Normal(d.mean,d.std)
    assert torch.equal(d.log_prob(sample),normal.log_prob(sample).sum(-1))
    assert torch.equal(d.entropy,normal.entropy().sum(-1))
    assert (d.kl_divergence(d.params,d.params)==0).all()
    assert torch.equal(d.as_deterministic_output_module()(raw),d.mean)
    d.log_prob(sample).sum().backward();assert (abs(raw.grad[:,[2,5]])>0).all()


def test_shared_model_strict_state_adam_and_jit_output():
    s=spec();base=copy.deepcopy(s);base.pop('action_distribution')
    obs=TensorDict({'policy':torch.randn(4,25),'history':torch.randn(4,125)},batch_size=[4])
    original=model(obs,actor=True,spec=base);new=model(obs,actor=True,spec=s)
    new.load_state_dict(original.state_dict(),strict=True)
    assert list(original.state_dict())==list(new.state_dict())
    before=original(obs);after=new(obs)
    assert torch.equal(before[:,[0,1,3,4]],after[:,[0,1,3,4]])
    assert torch.allclose(after[:,[2,5]],before[:,[2,5]].tanh())
    optimizer=torch.optim.Adam(new.parameters());book=copy.deepcopy(optimizer.state_dict())
    new(obs,stochastic_output=True);new.get_output_log_prob(new.output_mean+.01)
    assert optimizer.state_dict()==book
    exported=torch.jit.script(new.as_jit())
    assert torch.allclose(exported(torch.cat((obs['policy'],obs['history']),-1)),after)

def test_actual_rsl_probability_ratio_is_one_before_update_and_update_is_finite():
    from rsl_rl.algorithms import PPO
    from rsl_rl.storage import RolloutStorage
    s=spec();obs=TensorDict({'policy':torch.randn(8,25),'history':torch.randn(8,125)},batch_size=[8])
    actor=model(obs,actor=True,spec=s);critic=model(obs,actor=False,spec=s)
    storage=RolloutStorage('rl',8,4,obs,[6],'cpu')
    ppo=PPO(actor,critic,storage,num_learning_epochs=1,num_mini_batches=1,device='cpu')
    before=copy.deepcopy(actor.state_dict())
    with torch.inference_mode():
        for step in range(4):
            actions=ppo.act(obs);oldprob=ppo.transition.actions_log_prob.clone()
            actor(obs,stochastic_output=True)
            newprob=actor.get_output_log_prob(actions)
            assert torch.allclose(torch.exp(newprob-oldprob),torch.ones_like(oldprob),atol=1e-6)
            ppo.process_env_step(obs,torch.ones(8)*.01,torch.zeros(8,dtype=torch.bool),{})
        ppo.compute_returns(obs)
    # Real minibatch/update path,not just analytic distribution operations.
    loss=ppo.update()
    assert all(torch.isfinite(p).all() for p in actor.parameters())
    assert any(not torch.equal(v,actor.state_dict()[k]) for k,v in before.items())

def test_smoke_certificate_rejects_missing_or_saturated_policy_readback(tmp_path):
    import json,hashlib
    from native_stand.command_v6.wiring import smoke_certificate
    s={'source_sha256':'source','budget':{'smoke_updates':10},'action_distribution':declaration()}
    (tmp_path/'source_snapshot').mkdir();encoded=json.dumps(s).encode();(tmp_path/'source_snapshot/spec.json').write_bytes(encoded)
    records={'manifest.json':{'source_sha256':'source','spec_sha256':hashlib.sha256(encoded).hexdigest()},
        'progress.json':{'actual_updates':10,'actor_parameters_changed':True,'evaluations':[{'cases':[{'path':'eval.json'}]}]},
        'terminal_report.json':{'actual_updates':10,'status':'COMPLETED'},'eval.json':{'per_env':[{}],'outcome_counts':{'runtime_fault':0}}}
    for name,row in records.items():(tmp_path/name).write_text(json.dumps(row))
    policy={'eligible_count':10,'abs_mean_normalized':[.95,.9],'sample_clip_fraction':[.1,.05]}
    for bad in ({},{**policy,'sample_clip_fraction':[1.,.05]},{**policy,'abs_mean_normalized':[1.2,.9]}):
        (tmp_path/'metrics.jsonl').write_text(json.dumps({'support_record_policy':bad})+'\n')
        assert smoke_certificate(tmp_path,s)['status']=='FAILED'
    (tmp_path/'metrics.jsonl').write_text(json.dumps({'support_record_policy':policy})+'\n')
    assert smoke_certificate(tmp_path,s)['status']=='PASSED'
