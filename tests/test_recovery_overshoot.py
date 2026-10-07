import torch
from native_stand.recovery.domain import process_reward

def test_overshoot_only_above_target_and_dt():
    h=torch.tensor([.168,.38,.4,.42,.44]);target=torch.full_like(h,.4)
    weights={'lift':3.,'upright':2.,'effort':-.02,'action_delta':-.01,'joint_margin':-.05,
             'success_once':10.,'failure_once':-1.,'height_overshoot':-1.,'height_overshoot_scale_m':.04}
    _,raw,w=process_reward(h,torch.full_like(h,.168),target,torch.ones_like(h),
        torch.zeros(5,6),torch.zeros(5,6),torch.zeros(5),torch.zeros(5,dtype=torch.bool),
        torch.zeros(5,dtype=torch.bool),weights=weights,dt=.01)
    assert torch.allclose(raw['height_overshoot'],torch.tensor([0.,0.,0.,.25,1.]),atol=1e-6)
    assert torch.allclose(w['height_overshoot'],torch.tensor([0.,0.,0.,-.0025,-.01]),atol=1e-6)
    assert torch.allclose(w['upright'],torch.full_like(h,.02))
