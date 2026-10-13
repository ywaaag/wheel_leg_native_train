FROZEN_TEST_SCOPE='PORTABLE'
import ast
import copy
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from native_stand.command_v6.domain.input_capture import Recorder,validate,VERSION
from native_stand.command_v6.tools.test_resources import source_file

def recorder():
    return Recorder(3,8,'cpu',std=torch.ones(6)*.05,active_indices=list(range(6)),joint_names=[str(i) for i in range(6)],dt=.01)

def before(r,x):
    r.before(observation=x,mean=torch.zeros(8,6),root=torch.zeros(8,13),joint_pos=torch.zeros(8,6),
        joint_vel=torch.zeros(8,6),command=torch.zeros(8,3),reference=torch.zeros(8,6),
        previous_action=torch.zeros(8,6),contact=torch.zeros(8,2),metadata=torch.zeros(8,6),active=torch.ones(8,dtype=torch.bool))

def after(r):
    r.after(state=torch.zeros(8,39),control=torch.zeros(8,54),reward_total=torch.ones(8),
        reward_raw={'lift':torch.ones(8)},reward_weighted={'lift':torch.ones(8)*.02},initializing=torch.zeros(8,dtype=torch.bool))

def test_pre_state_copied_before_mutation_and_rng_unchanged():
    r=recorder();x=torch.ones(8,150);rng=torch.get_rng_state().clone()
    before(r,x);x.zero_();after(r);a=r.finish()
    assert np.all(a['pre_observation']==1) and np.all(a['post_reward_weighted_dt']==.02)
    assert torch.equal(rng,torch.get_rng_state()) and r.metadata()['random_trajectory_collected'] is False

def test_bound_and_reward_layout_fail_explicitly():
    r=recorder()
    for _ in range(3):before(r,torch.zeros(8,150));after(r)
    with pytest.raises(ValueError):before(r,torch.zeros(8,150))
    with pytest.raises(ValueError):Recorder(2301,8,'cpu',std=torch.ones(6),active_indices=[],joint_names=[],dt=.01)

def test_actual_loop_calls_actor_once_does_not_change_execution():
    tree=ast.parse(source_file('recovery/recipe.py').read_text());f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='evaluate_actor')
    loop=next(x for x in ast.walk(f) if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='index')
    start=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='action' for t in x.targets))
    nodes=copy.deepcopy(loop.body[start:start+4]);code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'capture_loop','exec')
    class Actor:
        calls=0
        def __call__(self,o):self.calls+=1;return o['policy'][:,:6].clone()
    class Env:
        def __init__(self):
            self.robot=SimpleNamespace(data=SimpleNamespace(**{k:SimpleNamespace(torch=torch.zeros(8,n)) for k,n in [('root_state_w',13),('joint_pos',6),('joint_vel',6)]}))
            self.command=torch.zeros(8,3);self.reference=torch.zeros(8,6);self.action=torch.zeros(8,6);self.contact_force=torch.zeros(8,2)
            for k in ['initial_pose_index','reset_count','initialization_checked','task_phase']:setattr(self,k,torch.zeros(8))
            self.fsm=SimpleNamespace(mode=torch.zeros(8),age=torch.zeros(8));self.recovery_snapshot=torch.zeros(8,39)
            self.recovery_control_snapshot=torch.zeros(8,54);self.reward_raw={'lift':torch.ones(8)};self.reward_weighted={'lift':torch.ones(8)*.02}
            self.initializing_step=torch.zeros(8,dtype=torch.bool)
        def step(self,a):self.executed=a.clone();return {},torch.ones(8),torch.zeros(8,dtype=torch.bool),None,None
    for capture in (None,recorder()):
        actor=Actor();env=Env();ns={'torch':torch,'actor':actor,'env':env,'input_recorder':capture,
            'obs':{'policy':torch.ones(8,25),'history':torch.ones(8,125)},'active':torch.ones(8,dtype=torch.bool)}
        exec(code,ns);assert actor.calls==1 and torch.equal(env.executed,torch.ones(8,6))

def test_training_capture_rejected():
    s={'input_capture':{'version':VERSION,'enabled':True,'max_storage_bytes':268435456},'task':'recovery',
        'evaluation_only':True,'evaluation':{'envs':64,'scored_envs':8},'budget':{'smoke_updates':0,'formal_updates':0},
        'source_sha256':'a','evaluation_requests':[{'seconds':23,'sha256':'a'}]*3}
    assert validate(s)
    s['budget']['formal_updates']=1
    with pytest.raises(ValueError):validate(s)
