FROZEN_TEST_SCOPE='PORTABLE'
import copy
import torch
import pytest
from native_stand.command_v6.domain.rollout_probe import declaration,validate
from native_stand.command_v6.tools.frozen_rollout_probe import tree_equal

def fixture():
    return {'task':'recovery','evaluation_only':True,'rollout_probe':declaration(),
        'ppo':{'envs':64,'steps_per_env':128},'budget':{'smoke_updates':0,'formal_updates':0},
        'recovery':{'support_record_reward':__import__('native_stand.recovery.support_record_proposal',fromlist=['declaration']).declaration(),
            'sampling':{'environment_counts':{'swing_candidate_from_historical_r1':26,'drawback_manual0001':25,'R0':13}}}}

def test_probe_is_strict_bounded_and_cannot_allocate_training():
    s=fixture();validate(s)
    for mutation in [lambda x:x['rollout_probe'].update(rollouts=3),lambda x:x['budget'].update(formal_updates=1),lambda x:x.update(input_capture={'enabled':True})]:
        t=copy.deepcopy(s);mutation(t)
        with pytest.raises(ValueError):validate(t)

def test_frozen_adam_comparison_detects_moment_or_parameter_mutation():
    a={'state':{0:{'step':torch.tensor(1.),'exp_avg':torch.tensor([1.,2.])}},'param_groups':[{'lr':3e-5}]};b=copy.deepcopy(a)
    assert tree_equal(a,b)
    b['state'][0]['exp_avg'][0]=9;assert not tree_equal(a,b)

def test_probe_restores_rng_and_actor_mode_on_setup_failure(monkeypatch):
    import native_stand.command_v6.tools.frozen_rollout_probe as m
    actor=torch.nn.Linear(1,1);actor.eval();before=torch.get_rng_state().clone()
    def fail(*args,**kwargs):torch.rand(4);actor.train();raise ValueError('setup failure')
    monkeypatch.setattr(m,'_collect',fail)
    with pytest.raises(ValueError):m.collect(actor,None,None,spec={},output=None,stop_requested=None)
    assert not actor.training and torch.equal(before,torch.get_rng_state())

def test_real_rsl_collection_is_two_rollouts_with_no_parameter_update(tmp_path):
    from types import SimpleNamespace
    from tensordict import TensorDict
    from rsl_rl.storage import RolloutStorage
    from rsl_rl.algorithms import PPO
    from native_stand.command_v6.learning import model
    from native_stand.command_v6.tools.frozen_rollout_probe import collect
    from native_stand.command_v6.tools.experiment_preparation import digest
    from native_stand.recovery.domain import Mode
    import numpy as np
    obs=TensorDict({'policy':torch.zeros(64,25),'history':torch.zeros(64,125)},batch_size=[64])
    s=fixture();s.update(ppo={'envs':64,'steps_per_env':128,'hidden_dims':[8,8],'epochs':1,'minibatches':1,'gamma':.99,'lam':.95,'entropy_coef':0.,'learning_rate':3e-5},seed=104)
    actor=model(obs,actor=True,spec=s);critic=model(obs,actor=False,spec=s)
    storage=RolloutStorage('rl',64,128,obs,[6],'cpu');ppo=PPO(actor,critic,storage,device='cpu')
    optimizer=ppo.optimizer.state_dict()
    for index,parameter in zip(optimizer['param_groups'][0]['params'],list(actor.parameters())+list(critic.parameters())):
        optimizer['state'][index]={'step':torch.tensor(1.),'exp_avg':torch.zeros_like(parameter),'exp_avg_sq':torch.zeros_like(parameter)}
    path=tmp_path/'source.pt';torch.save({'actor':actor.state_dict(),'critic':critic.state_dict(),'optimizer':optimizer},path)
    s.update(source_checkpoint=str(path),source_sha256=digest(path))
    families=['swing_candidate_from_historical_r1','drawback_manual0001','R0']
    class Env:
        device='cpu';initialization_checked=torch.ones(64,dtype=torch.bool)
        initial_pose_index=torch.tensor([0]*26+[1]*25+[2]*13);reset_count=torch.ones(64)
        pose_library={'poses':[{'family':f} for f in families]}
        fsm=SimpleNamespace(mode=torch.full((64,),int(Mode.RECOVERY)))
        rise_hold=SimpleNamespace(entry=torch.ones(64)*-1)
        support_record=SimpleNamespace(best=torch.zeros(64),snapshot=torch.zeros(64,7))
        terminal_causes={'nonfinite':torch.zeros(64,dtype=torch.bool),'closure':torch.zeros(64,dtype=torch.bool)}
        recovery_snapshot=torch.zeros(64,39);recovery_control_snapshot=torch.zeros(64,54);wheel_geometry_snapshot=torch.zeros(64,13)
        reward_raw={'fixture':torch.zeros(64)};reward_weighted={'fixture':torch.zeros(64)}
        def reset(self):return obs.clone(),{}
    class Wrapped:
        def get_observations(self):return obs.clone()
        def step(self,action):return obs.clone(),torch.zeros(64),torch.zeros(64,dtype=torch.bool),{'time_outs':torch.zeros(64,dtype=torch.bool)}
    threads=torch.get_num_threads();torch.set_num_threads(1)
    try:r=collect(actor,Wrapped(),Env(),spec=s,output=tmp_path,stop_requested=lambda:False)
    finally:torch.set_num_threads(threads)
    assert r['frozen_state_unchanged'] and r['optimizer_updates']==0
    with np.load(tmp_path/r['capture']['path']) as z:
        assert z['pre_obs150'].shape==(2,128,64,150)
        assert z['advantage_raw'].shape==(2,128,64,1)
        assert np.isfinite(z['advantage_normalized']).all()

def test_rollout_branch_does_not_read_missing_deterministic_profile():
    from native_stand.command_v6.tools.evaluate_checkpoint import recovery_batch_arguments
    assert recovery_batch_arguments(fixture(),{'diagnostic_storage':None}) is None
    assert recovery_batch_arguments({'task':'recovery'},{'family':'Swing','diagnostic_storage':{'profile':'full_transition'}})=={
        'family':'Swing','check_retained':False,'diagnostic_profile':'full_transition'}
