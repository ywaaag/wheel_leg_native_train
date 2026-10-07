import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec=importlib.util.spec_from_file_location('scissor_audit',Path(__file__).resolve().parents[1]/'scripts/audit_standing_scissor.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_native_forward_axis_and_symmetric_lengths_can_hide_scissor():
    hips=np.array([[.18,0.,0.],[-.18,0.,0.]])
    wheels=hips+[[0.,-.3,-.09],[0.,-.3,.09]]
    r=module.wheel_geometry(wheels,hips,[0.,-1.,0.])
    assert r['wheel_longitudinal_offset_m']==pytest.approx(.18)
    assert r['leg_length_m'][0]==pytest.approx(r['leg_length_m'][1])
    assert r['leg_pitch_rad'][0]>0 and r['leg_pitch_rad'][1]<0


def test_swap_and_translation_invariance():
    hips=np.array([[.18,0.,0.],[-.18,0.,0.]])
    wheels=hips+[[0.,-.3,-.09],[0.,-.3,.09]]
    baseline=module.wheel_geometry(wheels,hips,[0.,-1.,0.])
    translated=module.wheel_geometry(wheels[::-1]+7.,hips[::-1]+7.,[0.,-1.,0.])
    assert translated['wheel_longitudinal_offset_m']==pytest.approx(baseline['wheel_longitudinal_offset_m'])
    assert translated['leg_pitch_difference_rad']==pytest.approx(baseline['leg_pitch_difference_rad'])


def test_horizontal_projection_does_not_count_vertical_offset():
    up=np.array([0.,2**-.5,2**-.5]);hips=np.array([[.18,0.,0.],[-.18,0.,0.]])
    wheels=hips-.3*up
    wheels[0]+=.04*up
    assert module.wheel_geometry(wheels,hips,-up)['wheel_longitudinal_offset_m']==pytest.approx(0.,abs=1e-12)


def test_invalid_gravity_cannot_become_zero_measurement():
    with pytest.raises(ValueError):module.wheel_geometry(np.zeros((2,3)),np.zeros((2,3)),[0.,0.,0.])
    with pytest.raises(ValueError):module.wheel_geometry(np.zeros((2,3)),np.zeros((2,3)),[0.,0.,-1.])


def test_geometry_cost_has_deadband_and_expected_scale():
    import torch
    from native_stand.recovery.domain import process_reward
    z=torch.zeros(3);h=torch.ones(3)*.36
    matrix=torch.zeros(3,6)
    out,raw,weighted=process_reward(h,h,h,z,matrix,matrix,z,torch.zeros(3,dtype=torch.bool),
        torch.zeros(3,dtype=torch.bool),weights={'lift':0.,'upright':0.,'effort':0.,
        'action_delta':0.,'joint_margin':0.,'wheel_longitudinal_offset':-0.1875,
        'wheel_longitudinal_deadband_m':.03,'wheel_longitudinal_scale_m':.03,
        'success_once':0.,'failure_once':0.},dt=.01,wheel_longitudinal_offset=torch.tensor([0.,.03,.18]))
    torch.testing.assert_close(raw['wheel_longitudinal_offset'],torch.tensor([0.,0.,25.]))
    torch.testing.assert_close(weighted['wheel_longitudinal_offset'],torch.tensor([0.,0.,-.046875]))


def test_tensor_geometry_matches_offline_projection():
    import torch
    from native_stand.recovery.standing import longitudinal_geometry
    wheels=np.array([[.18,-.3,-.09],[-.18,-.3,.09]])
    expected=module.wheel_geometry(wheels,np.zeros((2,3)),[0.,-1.,0.])
    result=longitudinal_geometry(torch.tensor(wheels)[None],torch.tensor([[0.,-1.,0.]],dtype=torch.float64))
    assert float(result.abs()[0])==pytest.approx(expected['wheel_longitudinal_offset_m'])


def test_terminal_geometry_buffer_not_reset_state():
    import torch,json
    from test_recovery_standing_balance import FakeStandingEnv
    from native_stand.recovery.recipe import evaluate_actor
    cfg=json.loads((Path(__file__).resolve().parents[1]/'configs/experiments/recovery_standing_balance_20261006/spec.json').read_text())
    env=FakeStandingEnv(cfg,fall_step=300)
    env.wheel_geometry_snapshot=torch.zeros(8,13)
    env.wheel_geometry_snapshot[:,6:9]=torch.tensor([0.,-1.,0.])
    env.wheel_geometry_snapshot[:,2]=-.09;env.wheel_geometry_snapshot[:,5]=.09
    result=evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=10.,seed=321,full_trace=True)
    assert all(row['wheel_geometry']['mean_offset_m']==pytest.approx(.18) for row in result['per_env'])
    assert all(len(row['wheel_geometry_trace_100hz'])==300 for row in result['per_env'])


def test_schema_rejects_invalid_scissor_scale():
    import json
    from native_stand.command_v6.config import validate
    cfg=json.loads((Path(__file__).resolve().parents[1]/'configs/experiments/standing_scissor_20261006/spec.json').read_text())
    assert validate(cfg)==[]
    cfg['reward']['wheel_longitudinal_scale_m']=0.
    assert validate(cfg)
