import json
from pathlib import Path
import numpy as np
import torch
from native_stand.command_v6.config import validate
from native_stand.recovery.domain import process_reward

ROOT=Path(__file__).resolve().parents[1]

def test_stop_keeps_far_limit_and_signed_extension():
    from native_stand.recovery.asset_poses import AssetPoses
    asset=AssetPoses(ROOT/'assets/diagnostic/rmuc_robot_closed_loop_knee_stop_0233_v2.usd')
    knees={j['name']:j['limits'] for j in asset.joints if 'knee' in j['name']}
    assert np.allclose(knees['left_knee_pitch'],[-.233,2.5],atol=1e-6)
    assert np.allclose(knees['right_knee_pitch'],[-2.5,.233],atol=1e-6)

def test_initial_pose_is_closed_and_zero_reset_contract():
    from native_stand.recovery.asset_poses import AssetPoses
    directory=ROOT/'configs/experiments/recovery_knee_stop_pitch_20261004'
    spec=json.loads((directory/'spec.json').read_text())
    asset=AssetPoses(spec['asset_path'])
    for pose in json.loads((directory/'poses.json').read_text())['poses']:
        assert np.linalg.norm(asset.residual(pose['joint_pos']).reshape(-1,3),axis=-1).max()<1e-4
        assert pose['joint_pos']['left_knee_pitch']>=-.233-1e-6
        assert pose['joint_pos']['right_knee_pitch']<=.233+1e-6

def test_unlimited_wall_keeps_finite_update_budget():
    spec=json.loads((ROOT/'configs/experiments/recovery_knee_stop_pitch_20261004/spec.json').read_text())
    assert validate(spec)==[]
    assert spec['budget']['formal_wall_s'] is None
    assert spec['budget']['smoke_updates']+spec['budget']['formal_updates']==10000

def test_pitch_cost_is_high_position_gated_and_signed_symmetric():
    spec=json.loads((ROOT/'configs/experiments/recovery_knee_stop_pitch_20261004/spec.json').read_text())
    h=torch.tensor([.17,.4,.4,.4])
    _,raw,w=process_reward(h,torch.full_like(h,.17),torch.full_like(h,.4),torch.ones_like(h),
        torch.zeros(4,6),torch.zeros(4,6),torch.zeros(4),torch.zeros(4,dtype=torch.bool),
        torch.zeros(4,dtype=torch.bool),weights=spec['reward'],dt=.01,pitch=torch.tensor([.3,0.,.2,-.2]))
    assert torch.allclose(raw['pitch_level'],torch.tensor([0.,0.,1.,1.]))
    assert torch.allclose(w['pitch_level'],torch.tensor([0.,0.,-.01,-.01]))

def test_pitch_reward_is_registered_for_rollout():
    source=(ROOT/'src/native_stand/command_v6/train.py').read_text()
    assert "reward_fields=(*reward_fields,'pitch_level')" in source
