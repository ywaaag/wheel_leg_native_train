import copy
import json
from pathlib import Path
import pytest
import torch
from native_stand.command_v6.config import validate,schedule
from native_stand.recovery.domain import process_reward

ROOT=Path(__file__).resolve().parents[1]

def spec():
    return json.loads((ROOT/'configs/experiments/2026_10_7-20_42__recovery_level2_alignment_from50/spec.json').read_text())

def replay(weights,heights):
    n=len(heights);z=torch.zeros(n);v=torch.zeros(n,6)
    return process_reward(torch.tensor(heights),torch.full((n,),.168),torch.full((n,),.36),
        torch.ones(n),v,v,z,z.bool(),z.bool(),weights=weights,dt=.01,
        pitch=z,roll=z,contact=torch.ones(n,2)*3,wheel_velocity=torch.zeros(n,2),
        support_balance=z,wheel_longitudinal_offset=torch.full((n,),.24))

def test_real_recipe_single_reward_delta_and_milestones():
    s=spec();parent=json.loads(Path(s['recipe_parent_spec']).read_text())
    assert not validate(s)
    for key in ('action','observation','history','control','ppo','termination','ground'):
        assert s[key]==parent[key]
    for key,value in parent['reward'].items():assert s['reward'][key]==value
    for update in (25,50,100):assert schedule(update,'formal',s['evaluation'])['full']
    assert s['recovery']['rising_task']==parent['recovery']['rising_task']
    assert s['recovery']['standing_task']['protocol']==parent['recovery']['standing_task']['protocol']

def test_gated_cost_delta_and_historical_ungated_semantics():
    s=spec();base=copy.deepcopy(s['reward'])
    for key in list(base):
        if key.startswith('wheel_longitudinal'):del base[key]
    heights=[.168,.32,.34,.36,.4]
    old=replay(base,heights);new=replay(s['reward'],heights)
    expected=torch.tensor([0.,0.,-.0005,-.001,-.001])
    assert torch.allclose(new[0]-old[0],expected,atol=1e-7)
    assert torch.allclose(new[2]['wheel_longitudinal_offset'],expected,atol=1e-7)
    for k in old[2]:assert torch.equal(old[2][k],new[2][k])
    legacy=copy.deepcopy(s['reward'])
    for key in ('wheel_longitudinal_start_m','wheel_longitudinal_full_m'):del legacy[key]
    assert torch.allclose(replay(legacy,heights)[2]['wheel_longitudinal_offset'],torch.full((5,),-.001))

@pytest.mark.parametrize('start,full',[(.36,.32),(.32,None),(float('nan'),.36),(True,.36)])
def test_gate_invalid_rejected(start,full):
    s=spec();s['reward'].update(wheel_longitudinal_start_m=start,wheel_longitudinal_full_m=full)
    assert any('height gate' in e for e in validate(s))

def test_holding_still_rejects_alignment_cost():
    s=spec();del s['recovery']['rising_task']
    assert any('motion or symmetry' in e for e in validate(s))

def test_trace_selector_rejects_nonmilestone():
    s=spec();s['evaluation']['full_trace_updates']=[24]
    assert any('full_trace_updates' in e for e in validate(s))


def test_full_training_evaluation_config_is_accepted_by_protocol_boundary():
    from native_stand.command_v6.domain.evidence import PROTOCOL_FIELDS,effective_protocol
    s=spec();evaluation=s['evaluation']
    # train.py passes the complete evaluation declaration into standing_protocol.
    assert not set(evaluation)-PROTOCOL_FIELDS
    result=effective_protocol(evaluation,requested_seconds=23.,sample_rate_hz=100.,
        scored_envs=8,termination_semantics='first_episode_pre_reset')
    assert result['full_trace_updates']==[25,50,100]
    with pytest.raises(ValueError,match='unknown evaluation protocol fields'):
        effective_protocol({**evaluation,'unknown_storage_option':True},requested_seconds=23.,
            sample_rate_hz=100.,scored_envs=8,termination_semantics='first_episode_pre_reset')
