FROZEN_TEST_SCOPE='PORTABLE'
import copy
import importlib.util
from pathlib import Path
import numpy as np
import pytest
import torch


def script():
    path=Path(__file__).resolve().parents[1]/'scripts/audit_motion31_adam_step.py'
    spec=importlib.util.spec_from_file_location('motion_adam_audit',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def fixture():
    from native_stand.students.model import Student
    torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42)
        actor=Student(True,version='multiskill_mcu_v2');actor.log_std.requires_grad_(False)
        critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1')
        optimizer=torch.optim.Adam(list(actor.parameters())+list(critic.parameters()),lr=3e-5)
        for p in list(actor.parameters())+list(critic.parameters()):
            if p.requires_grad:p.grad=torch.ones_like(p)*.001
        optimizer.step();optimizer.zero_grad(set_to_none=True)
        x=torch.randn(2,7,31)*.1;cx=torch.randn(2,7,49)*.1
        with torch.no_grad():actions=actor.mean(x)+torch.randn(2,7,6)*actor.log_std.exp();returns=critic(cx)+.1
        source={'actor':copy.deepcopy(actor.state_dict()),'critic':copy.deepcopy(critic.state_dict()),'optimizer':copy.deepcopy(optimizer.state_dict())}
        arrays={'actor_valid':np.ones((2,7),bool),'command_index':np.tile(np.arange(7),(2,1)),
            'actor_input':x.numpy(),'critic_input':cx.numpy(),'action_raw':actions.numpy(),'returns':returns.numpy(),
            'advantage_normalized':np.linspace(-1,1,14,dtype=np.float32).reshape(2,7,1)}
    commands=[[0,0],[.5,0],[-.5,0],[1,0],[-1,0],[1.5,0],[-1.5,0]]
    config={'learning_rate':3e-5,'clip':.2,'value_coef':.5,'entropy_coef':.001,'max_grad_norm':1.}
    return source,arrays,commands,config


def test_same_batch_mask_only_actor_and_source_unchanged():
    m=script();source,arrays,commands,config=fixture();before=copy.deepcopy(source);rng=torch.get_rng_state().clone()
    a,da,ca=m.replay_arm(source,arrays,commands,config)
    b,db,cb=m.replay_arm(source,arrays,commands,config,exclude_index=6)
    from native_stand.command_v6.tools.frozen_rollout_probe import tree_equal
    assert a['exact_Adam_restore'] and b['exact_Adam_restore'] and a['std_unchanged'] and b['std_unchanged']
    assert a['denominator']==b['denominator']==14 and a['included_actor_samples']==14 and b['included_actor_samples']==12
    assert torch.equal(ca,cb) and not torch.equal(da,db) and tree_equal(before,source)
    assert torch.equal(rng,torch.get_rng_state()) and a['offline_optimizer_steps']==1


def test_empty_ablation_is_identical_and_missing_Adam_rejected():
    m=script();source,arrays,commands,config=fixture()
    a,da,ca=m.replay_arm(source,arrays,commands,config)
    b,db,cb=m.replay_arm(source,arrays,commands,config,exclude_index=99)
    assert torch.equal(da,db) and torch.equal(ca,cb)
    source['optimizer']['state'].pop(next(iter(source['optimizer']['state'])))
    with pytest.raises(ValueError,match='Adam state'):m.replay_arm(source,arrays,commands,config)


def test_refuse_existing_output_before_reading_inputs(tmp_path):
    with pytest.raises(FileExistsError):script().audit(tmp_path/'missing',tmp_path)


def test_checkpoint_comparison_includes_numpy_rng_metadata():
    m=script();source={'training_rng':{'numpy':('MT19937',np.arange(8,dtype=np.uint32),1,0,0.)},'actor':{'p':torch.ones(2)}}
    other=copy.deepcopy(source);assert m.source_equal(source,other)
    other['training_rng']['numpy'][1][0]=99
    assert not m.source_equal(source,other)


def test_full_update_production_steps_shuffle_and_critic_equality():
    m=script();source,arrays,commands,config=fixture()
    config.update(epochs=4,minibatches=4,gamma=.99,lam=.95)
    # Divisible batch, four samples per cohort.
    for key,value in list(arrays.items()):arrays[key]=np.tile(value,(2,)+(1,)*(value.ndim-1))
    arrays['value']=np.zeros_like(arrays['returns'])
    before=copy.deepcopy(source);rng=torch.get_rng_state().clone()
    a,da,ca=m.replay_full_arm(source,arrays,commands,config)
    b,db,cb=m.replay_full_arm(source,arrays,commands,config,exclude_index=6)
    assert a['offline_optimizer_steps']==b['offline_optimizer_steps']==16
    assert a['production_mask_summary']['actor_optimizer_steps']==16
    assert [r['minibatch'] for r in a['per_step']]==[r['minibatch'] for r in b['per_step']]
    assert a['per_step'][0]['minibatch']==a['per_step'][4]['minibatch']
    assert torch.equal(ca,cb) and not torch.equal(da,db)
    assert m.source_equal(before,source) and torch.equal(rng,torch.get_rng_state())
    assert a['std_unchanged'] and a['final']['old5_KL_mean']>=0
