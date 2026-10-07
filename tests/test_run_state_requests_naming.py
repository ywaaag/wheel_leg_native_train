from datetime import datetime
from zoneinfo import ZoneInfo
import json

import pytest

from native_stand.command_v6.tools.run_state import record, transition
from native_stand.command_v6.tools.evaluate_checkpoint import validate_evaluation_request
from native_stand.command_v6.domain.experiment_naming import new_experiment_name, validate_new_experiment_name


def test_shared_state_projections(tmp_path):
    for state in ('SUBMITTED', 'SOURCE_EVAL', 'SMOKE', 'FORMAL', 'COMPLETED'):
        event = record(tmp_path, state, phase=state.lower())
        assert json.loads((tmp_path/'run_state.json').read_text()) == event
        progress = json.loads((tmp_path/'chain_progress.json').read_text())
        assert progress['state'] == progress['status'] == state
    assert json.loads((tmp_path/'supervisor_terminal.json').read_text()) == event
    with pytest.raises(ValueError):
        record(tmp_path, 'FORMAL')


def test_state_does_not_skip_smoke_or_call_bounded_stop_failure():
    with pytest.raises(ValueError):transition('SOURCE_EVAL', 'FORMAL')
    assert transition('SMOKE', 'STOPPED_BOUNDED') == 'STOPPED_BOUNDED'


@pytest.mark.parametrize('field', ['motion_window_s', 'parking_window_s', 'command_schedule'])
def test_recovery_rejects_motion_fields(field):
    with pytest.raises(ValueError, match='foreign evaluation request fields'):
        validate_evaluation_request({'task':'recovery'}, {'target':[0,0], 'seconds':10., field:[]})


def test_motion_rejects_family_and_recovery_duration_mismatch():
    with pytest.raises(ValueError):validate_evaluation_request({}, {'family':'R0'})
    with pytest.raises(ValueError):validate_evaluation_request({'task':'recovery'}, {'seconds':30.})
    assert validate_evaluation_request({'task':'recovery'}, {
        'checkpoint':'source.pt','sha256':'a'*64,'family':'R0','target':[0,0],'seconds':10.})


def test_naming_shanghai_creation_time():
    stamp = datetime(2026,10,7,14,27,tzinfo=ZoneInfo('Asia/Shanghai'))
    assert new_experiment_name('Motion Width AB',stamp) == '2026_10_7-14_27__motion_width_ab'
    assert validate_new_experiment_name('2026_10_7-14_27__motion_width_ab')
    with pytest.raises(ValueError):validate_new_experiment_name('motion_width_ab_20261007')


def test_retention_metadata_coverage_is_labeled_not_balancing():
    import torch
    from native_stand.command_v6.domain.selected_diagnostics import retention_coverage
    metadata=torch.tensor([[1.,0,0,0,1,0,0],[2.,0,0,0,1,0,5],[3.,0,0,1,2,1,9]])
    result=retention_coverage(metadata,eligible=5,total=8,rollout_steps=10,
                              poses=[{'pose_id':'p0','family':'R0'},{'pose_id':'p1','family':'R1'}])
    assert result['discarded']=={'ineligible_mask':3,'sample_limit_or_selection':2}
    assert result['per_episode'][0]['sample_count']==2
    assert result['per_family']=={'R0':2,'R1':1}
    assert sum(result['rollout_position_histogram']['sample_counts'])==3
    assert retention_coverage(None,eligible=0,total=8,rollout_steps=10)['per_episode'] is None


def test_handshake_observes_same_state_without_rewinding(tmp_path):
    from native_stand.command_v6.tools.run_state import write_handshake
    record(tmp_path,'SUBMITTED')
    record(tmp_path,'SOURCE_EVAL')
    result=write_handshake(tmp_path,{'status':'SUBMITTED','started':False})
    assert result['run_state']=='SOURCE_EVAL'
    assert result['state']==result['status']=='SOURCE_EVAL'
    assert result['legacy_handshake_status']=='SUBMITTED'
    assert json.loads((tmp_path/'run_state.json').read_text())['state']=='SOURCE_EVAL'


def test_explicit_no_stand_only_for_new_dependency_free_holding():
    from native_stand.command_v6.domain.episode_result import requires_stand
    config={'requires_stand':False,'fsm':{'success_mode':'autonomous_hold'},
            'standing_task':{'training_episode':{'mode':'fixed_horizon'}}}
    assert requires_stand(config) is False
    with pytest.raises(ValueError):requires_stand({**config,'stand_checkpoint':'old.pt'})
    with pytest.raises(ValueError):requires_stand({'requires_stand':False,'fsm':{'success_mode':'handover'}})
