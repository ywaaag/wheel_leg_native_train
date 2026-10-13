import json
from pathlib import Path

from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.execution_plan import smoke_plan

ROOT=Path(__file__).resolve().parents[1]


def test_level2_actual_captured_pose_and_cross_asset_identity():
    path=ROOT/'configs/experiments/2026_10_7-17_21__recovery_level2_drawback_from1000/spec.json'
    s=json.loads(path.read_text())
    assert not validate(s)
    c=s['recovery'];record=json.loads(Path(c['initial_pose_record']).read_text())
    poses=json.loads(Path(c['pose_library']).read_text())['poses']
    low=[p for p in poses if p['family']=='drawback_manual0001']
    assert len(low)==2 and all(p['joint_pos']==record['joint_pos'] for p in low)
    assert record['joint_pos']['left_active_link_pitch']>1.4
    assert record['target_leg_rad'][1]<0  # Passive UI request is not the actual pose.
    assert s['source_update']==1000 and s['source_input_dim']==150
    assert s['source_asset_sha256']!=s['asset_sha256']
    assert not c['runtime_initialization_validated']
    assert not c['standing_task']['retention']['enabled']
    assert not c['curriculum']['automatic_upgrade']
    assert {p['family'] for p in poses}=={'R0','drawback_manual0001'}
    assert smoke_plan(s)['budget_sufficient']
    assert {g['family'] for g in smoke_plan(s)['required_groups']}=={'R0','drawback_manual0001'}
