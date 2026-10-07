import json
from types import SimpleNamespace

import pytest
import torch

from native_stand.command_v6.domain.evidence import (effective_protocol,observed_protocol,
    resolve_gate,validate_effective_protocol)
from native_stand.command_v6.tools.evaluation_state import isolated_evaluation


def protocol():
    return effective_protocol({},requested_seconds=10.,steady_window_s=[2.,10.],sample_rate_hz=100.,
        scored_envs=2,termination_semantics='first_episode_pre_reset; early termination fails continuous window')


def test_early_end_retains_gate_window_and_records_each_environment():
    requested=protocol()
    actual=observed_protocol(requested,[.2,.5])
    assert actual['requested_seconds']==10 and actual['actual_duration_seconds']==.5
    assert actual['steady_window_s']==[2.,10.]
    assert actual['observed_duration_per_env_s']==[.2,.5]
    validate_effective_protocol(actual)
    gate={'accepted':False,'passed_envs':0,'per_env':[{'accepted':False}]*2}
    assert resolve_gate({'effective_protocol':actual,'standing_gate':gate},'standing',
        expected_envs=2,expected_protocol=requested)['status']=='FAILED'
    with pytest.raises(ValueError):observed_protocol(requested,[.2])
    with pytest.raises(ValueError):validate_effective_protocol({**actual,'scoring_protocol_sha256':'bad'})


@pytest.mark.parametrize('gate',[{'accepted':True,'passed_envs':0,'per_env':[]},
    {'accepted':True,'passed_envs':1,'per_env':{'x':1}},
    {'accepted':True,'passed_envs':'bad','per_env':[{}]},
    {'accepted':None,'passed_envs':0,'per_env':[{}]}])
def test_malformed_gate_cannot_pass(gate):
    assert not resolve_gate({'standing_gate':gate},'standing')['candidate_eligible']


def test_gate_row_conflicts_and_termination_identity():
    result={'standing_gate':{'accepted':False,'passed_envs':2,'per_env':[{'accepted':True}]*2}}
    assert resolve_gate(result,'standing')['status']=='CONFLICTING_EVIDENCE'
    result={'recovery_gate':{'accepted':True,'passed_envs':2,
        'per_env':[{'failed_checks':[]},{'failed_checks':['tilt']}]}}
    assert resolve_gate(result,'recovery')['status']=='CONFLICTING_EVIDENCE'
    result={'effective_protocol':protocol(),'standing_gate':{'accepted':True,'passed_envs':2,'per_env':[{'accepted':True}]*2}}
    different=effective_protocol({},requested_seconds=10.,steady_window_s=[2.,10.],sample_rate_hz=100,
        scored_envs=2,termination_semantics='reset bootstrap different')
    assert resolve_gate(result,'standing',expected_protocol=different)['status']=='CONFLICTING_EVIDENCE'


@pytest.mark.parametrize('fail', ['none','setup','cleanup'])
def test_evaluation_guard_restores_rng_after_reset_and_on_exception(fail):
    class Env:
        family='R0';split='train';curriculum_training=True;continuous_evaluation=False
        recovery_config={'gate_diagnostics':False}
        fsm=SimpleNamespace(config={'timeout_s':20})
        def select_initial_family(self,family,split):self.family,self.split=family,split
        def reset(self):
            torch.rand(7)
            if fail=='cleanup':raise RuntimeError('cleanup fault')
    env=Env();actor=torch.nn.Linear(1,1).train()
    @isolated_evaluation
    def evaluate(actor,wrapped,env,*,seconds):
        env.family='R1';env.curriculum_training=False;env.recovery_config['gate_diagnostics']=True
        torch.manual_seed(17);torch.rand(3)
        if fail=='setup':raise RuntimeError('setup fault')
        return seconds
    torch.manual_seed(91);before=torch.get_rng_state().clone()
    if fail=='none':assert evaluate(actor,None,env,seconds=1)==1
    else:
        with pytest.raises(RuntimeError):evaluate(actor,None,env,seconds=1)
    assert torch.equal(before,torch.get_rng_state())
    assert actor.training and env.family=='R0' and env.curriculum_training
    assert env.recovery_config['gate_diagnostics'] is False


def test_unknown_evaluator_argument_does_not_reset_or_consume_rng():
    env=SimpleNamespace()
    @isolated_evaluation
    def evaluate(actor,wrapped,env,*,seconds):raise AssertionError('not called')
    with pytest.raises(TypeError):evaluate(None,None,env,seconds=1,typo=True)


def test_runtime_fault_evidence_has_partial_duration_and_terminal_state():
    from native_stand.command_v6.tools.evaluation_state import failure_evidence
    valid=torch.zeros(1000,2,dtype=torch.bool);valid[:3,0]=True;valid[:5,1]=True
    fault=failure_evidence(RuntimeError('closure runtime fault'),protocol(),valid,.01,torch.ones(2,18))
    evidence=fault.evaluation_evidence
    assert evidence['effective_protocol']['actual_duration_seconds']==.05
    assert evidence['effective_protocol']['observed_duration_per_env_s']==[.03,.05]
    assert evidence['effective_protocol']['steady_window_s']==[2.,10.]
    assert not evidence['completed'] and evidence['terminal_pre_reset'][0][0]==1
    fault=failure_evidence(RuntimeError('nonfinite'),protocol(),valid,.01,torch.full((2,18),float('nan')))
    assert fault.evaluation_evidence['terminal_pre_reset'][0][0] is None
    json.dumps(fault.evaluation_evidence,allow_nan=False)


def test_field_level_validity_rejects_nonfinite_without_marking_real_zero_missing():
    from native_stand.command_v6.domain.evidence import tensor_field_validity
    rows=torch.tensor([[[0.,float('nan')]],[[0.,1.]]]);valid=torch.ones(2,1,dtype=torch.bool)
    result=tensor_field_validity(rows,valid,['zero','invalid'],requested=True,enabled=True,scope='fixture')
    assert result['zero']['valid'] and result['zero']['sample_count']==2
    assert not result['invalid']['valid'] and result['invalid']['missing_reason']=='nonfinite_samples'
    assert result['invalid']['value'] is None


def test_native_durability_uses_effective_window_and_generates_full_gate():
    from pathlib import Path
    from tensordict import TensorDict
    from native_stand.command_v6.tools.evaluate_checkpoint import evaluate_actor,protocol_for_spec
    spec=json.loads((Path(__file__).resolve().parents[1]/'configs/experiments/stand_plane.json').read_text())
    spec['evaluation'].update(scored_envs=1,durability_seconds=100,durability_steady_window_s=[4,100])
    actual=protocol_for_spec(spec,100)
    assert actual['steady_window_s']==[4,100] and actual['seconds']==100
    class Actor(torch.nn.Module):
        def forward(self,obs,stochastic_output=False):return torch.zeros(1,6)
    class Env:
        device='cpu';num_envs=1;step_dt=.1;command_height=.363
        schedule_s=[.5,.5,3,.5];target_xy=torch.zeros(1,2)
        episode_length_buf=torch.zeros(1,dtype=torch.long)
        cfg=SimpleNamespace(episode_length_s=6.)
        terminal_snapshot=[None];capture_terminal=False
        vx=torch.zeros(1);vy=torch.zeros(1);yaw=torch.zeros(1)
        contact_force=torch.ones(1,2)*10;effort=torch.zeros(1,6)
        closure_each=torch.zeros(1,4);up=torch.ones(1)
        terminal_causes={'nonfinite':torch.tensor([False]),'closure':torch.tensor([False])}
        robot=SimpleNamespace(data=SimpleNamespace(root_pos_w=SimpleNamespace(torch=torch.tensor([[0.,0.,.363]]))))
        def set_evaluation_target(self,*target):self.target_xy[:]=torch.tensor(target)
        def clear_evaluation_target(self):self.target_xy.zero_()
        def reset(self,seed):
            torch.manual_seed(seed);torch.rand(3)
            self.episode_length_buf.zero_()
            return {'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},{}
    class Wrapped:
        def step(self,actions):
            env.episode_length_buf+=1
            return TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},[1]),torch.zeros(1),torch.tensor([False]),{}
    env=Env();actor=Actor().train()
    actual['sample_rate_hz']=10.
    # Rebuild its SHA for this isolated timing fixture, not the physical runtime.
    actual=effective_protocol(actual,requested_seconds=100,steady_window_s=[4,100],sample_rate_hz=10,
        scored_envs=1,termination_semantics=actual['termination_semantics'])
    old_rng=torch.get_rng_state().clone()
    result=evaluate_actor(actor,Wrapped(),env,target=(0.,0.),seconds=100.,scored_envs=1,
        seed=11,full_trace=False,target_window=[4,100],standing_protocol=spec['evaluation'],effective_protocol=actual)
    assert result['standing_gate']['accepted'] and result['effective_protocol']['actual_duration_seconds']==100
    assert result['effective_protocol']['steady_window_s']==[4,100]
    assert env.cfg.episode_length_s==6. and actor.training and torch.equal(old_rng,torch.get_rng_state())
