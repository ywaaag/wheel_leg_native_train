import torch
import pytest
from native_stand.recovery.domain import process_reward,settling_motion_cost

CFG={'height_start_m':.32,'height_full_m':.38,'linear_scale_mps':.1,'angular_scale_rad_s':.3,'weight':-1.5}


def test_height_gate_no_low_pose_penalty_and_vertical_motion_counts():
    h=torch.tensor([.168,.32,.35,.38,.4])
    v=torch.zeros(5,3);v[:,2]=.1
    cost=settling_motion_cost(h,v,torch.zeros_like(v),CFG)
    assert torch.allclose(cost,torch.tensor([0.,0.,.5,1.,1.]),atol=1e-6)
    assert not settling_motion_cost(h,torch.zeros_like(v),torch.zeros_like(v),CFG).any()


def test_yaw_sign_symmetric_and_reward_dt_and_old_path_identical():
    h=torch.tensor([.4,.4]);z=torch.zeros(2,3);omega=z.clone();omega[:,2]=torch.tensor([.3,-.3])
    assert torch.equal(settling_motion_cost(h,z,omega,CFG),torch.ones(2))
    weights={'lift':3.,'upright':.5,'effort':-.02,'action_delta':-.01,'joint_margin':-.05,'success_once':10.,'failure_once':-1.}
    args=(h,torch.full_like(h,.168),h,torch.ones(2),torch.zeros(2,6),torch.zeros(2,6),torch.zeros(2),torch.zeros(2,dtype=torch.bool),torch.zeros(2,dtype=torch.bool))
    old,raw,_=process_reward(*args,weights=weights,dt=.01)
    new,newraw,weighted=process_reward(*args,weights=weights,dt=.01,settling_config=CFG,linear_velocity=z,angular_velocity=omega)
    assert 'settling_motion' not in raw and len(newraw)==len(raw)+1
    assert torch.allclose(old-new,torch.full_like(h,.015),atol=1e-6)
    assert torch.allclose(weighted['settling_motion'],torch.full_like(h,-.015))


def test_bad_config_rejected():
    with pytest.raises(ValueError):
        settling_motion_cost(torch.ones(1),torch.zeros(1,3),torch.zeros(1,3),{**CFG,'height_full_m':.32})
