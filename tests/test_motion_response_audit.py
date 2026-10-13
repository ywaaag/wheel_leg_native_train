import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def tool():
    spec=importlib.util.spec_from_file_location('motion_response_audit',ROOT/'scripts/audit_motion_response.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_same_command_audit_keeps_partial_window_and_original_gate(tmp_path):
    run=ROOT/'runs/2026_10_7-20_29__motion_b250_2p5_short'
    if not run.exists():pytest.skip('local historical raw evidence unavailable')
    result=tool().audit(run,ROOT/'runs/2026_10_7-20_18__motion_b250_endpoint2p5/baseline',tmp_path/'audit')
    b=result['models']['B250'];n=result['models']['formal50']
    assert b['commands']['2.0']['passed_envs']==8
    assert n['commands']['2.0']['passed_envs']==0
    assert n['pairs']['2.0']['gain']>b['pairs']['2.0']['gain']
    assert not n['pairs']['2.5']['complete_hold_both_directions']
    row=n['commands']['-2.5']
    assert row['failed_check_counts']['MISSING_EVIDENCE:full_hold_window']==8
    assert row['geometry_evidence']['roll_rad'] is None
    assert row['geometry_evidence']['wheel_offset_m'] is None
    assert result['online_updates']==0
    with pytest.raises(FileExistsError):tool().audit(run,run,tmp_path/'audit')


def test_prepared_rehearsal_only_changes_ratio_not_learning_contract():
    path=ROOT/'isolated/2026_10_8-14_53__motion_old_endpoint_rehearsal_audit/preparation_result.json'
    if not path.exists():pytest.skip('local prepared declaration unavailable')
    prepared=json.loads(path.read_text())
    spec=prepared['spec']
    old=json.loads((ROOT/'runs/2026_10_7-20_29__motion_b250_2p5_short/formal/source_snapshot/spec.json').read_text())
    for key in ('reward','ppo','action','control','ground','observation','history','termination'):
        assert spec[key]==old[key],key
    assert spec['curriculum']['schedule_s']==old['curriculum']['schedule_s']
    assert spec['curriculum']['episode_length_s']==old['curriculum']['episode_length_s']
    assert [w*64 for w in spec['curriculum']['stages'][1]['weights']]==[16]+[4]*8+[8]*2
    assert 'sampling_slots' not in spec['curriculum']['stages'][1]
    assert spec['source_sha256']==old['source_sha256']
    assert spec['budget']['smoke_updates']==1 and spec['budget']['formal_updates']==50
    assert spec['curriculum']['task_progression']['max_enabled_stage']==1
    book=prepared['budget']
    assert book['authorization']=='UNAUTHORIZED' and not book['attempts']
    assert not any(book['used'].values())
    assert spec['budget']['sample_limit']==51*64*128
