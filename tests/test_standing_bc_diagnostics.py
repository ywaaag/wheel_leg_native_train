import copy
import json
from pathlib import Path

import pytest
import torch
from tensordict import TensorDict

from native_stand.recovery.standing import StandingRetention,gradient_comparison,retention_coefficient
from native_stand.command_v6.config import validate


class Actor(torch.nn.Module):
    def __init__(self):
        super().__init__();self.layer=torch.nn.Linear(25,6)
    def forward(self,obs,stochastic_output=False):return self.layer(obs['policy'])


def test_schedule_boundaries_and_smoke_constant():
    cfg={'kind':'cosine_to_zero','zero_after_updates':50}
    assert retention_coefficient(.02,cfg,0)==.02
    assert retention_coefficient(.02,cfg,25)==pytest.approx(.01)
    assert retention_coefficient(.02,cfg,50)==0
    assert retention_coefficient(.02,cfg,100)==0
    s=Actor();hook=StandingRetention(s,copy.deepcopy(s),coefficient=.02,max_samples=4,
                                   max_grad_norm=1,schedule=cfg)
    hook.begin_rollout(51,phase='formal');assert hook.effective_coefficient==0
    hook.begin_rollout(51,phase='smoke');assert hook.effective_coefficient==.02


def test_direction_zero_and_reference_when_off():
    p=[torch.tensor([1.,0.])];b=[torch.tensor([-2.,0.])]
    x=gradient_comparison(p,b,.02,.02)
    assert x[3]==-1 and x[4]==pytest.approx(.04)
    x=gradient_comparison(p,b,0.,.02)
    assert x[2]==0 and x[4]==0 and x[6]==pytest.approx(.04)
    assert torch.isnan(gradient_comparison(p,[torch.zeros(2)],.02,.02)[3])
    assert p[0].tolist()==[1.,0.] and b[0].tolist()==[-2.,0.]


def run_hook(source,teacher,obs,diagnostic,*,coefficient=.02,schedule=None,update=1):
    s=copy.deepcopy(source);t=copy.deepcopy(teacher)
    opt=torch.optim.Adam(s.parameters(),lr=3e-5)
    h=StandingRetention(s,t,coefficient=coefficient,max_samples=4,max_grad_norm=1,
        gradient_diagnostics=diagnostic,schedule=schedule,save_gradient_updates=[1])
    opt.register_step_pre_hook(h.before_step);h.begin_rollout(update,phase='formal')
    with torch.inference_mode():h.capture(obs,torch.ones(4,dtype=torch.bool))
    opt.zero_grad();loss=(s(obs)-.5).square().mean();loss.backward()
    torch.nn.utils.clip_grad_norm_(s.parameters(),1.);opt.step()
    return s,h,opt


def test_probe_does_not_change_actual_update_or_teacher():
    torch.manual_seed(17);s=Actor();t=copy.deepcopy(s)
    with torch.no_grad():t.layer.bias.add_(.2)
    obs=TensorDict({'policy':torch.randn(4,25),'history':torch.randn(4,125)},[4])
    plain,_,_=run_hook(s,t,obs,False);probed,h,_=run_hook(s,t,obs,True)
    for p,q in zip(plain.parameters(),probed.parameters()):torch.testing.assert_close(p,q,rtol=0,atol=0)
    assert h.gradient_payload['observations']['policy'].shape==(4,25)
    payload=h.gradient_payload
    for full,leg,wheel in zip(payload['bc_raw_gradients'],
            payload['bc_component_gradients']['legs'],payload['bc_component_gradients']['wheels']):
        torch.testing.assert_close(full,leg+wheel,rtol=1e-5,atol=1e-7)
    assert h.summary()['gradient_comparison']['bc_weighted_norm']>0
    assert not any(p.grad is not None or p.requires_grad for p in h.teacher.parameters())


def test_zero_bc_is_exactly_ppo_only_and_probe_still_available():
    torch.manual_seed(9);s=Actor();t=copy.deepcopy(s)
    with torch.no_grad():t.layer.bias.add_(.2)
    obs=TensorDict({'policy':torch.randn(4,25),'history':torch.randn(4,125)},[4])
    got,h,_=run_hook(s,t,obs,True,schedule={'kind':'cosine_to_zero','zero_after_updates':1},update=2)
    expected=copy.deepcopy(s);opt=torch.optim.Adam(expected.parameters(),lr=3e-5)
    opt.zero_grad();(expected(obs)-.5).square().mean().backward()
    torch.nn.utils.clip_grad_norm_(expected.parameters(),1.);opt.step()
    for p,q in zip(got.parameters(),expected.parameters()):torch.testing.assert_close(p,q,rtol=0,atol=0)
    summary=h.summary();assert summary['weighted']==0 and summary['gradient_comparison']['reference_weighted_norm']>0


def test_schema_rejects_invalid_schedule_channels_payloads():
    root=Path(__file__).resolve().parents[1]
    spec=json.loads((root/'configs/experiments/recovery_standing_yaw_20261006/spec.json').read_text())
    for field,value in [('schedule',{'kind':'typo'}),('channels','legs_typo'),
                        ('gradient_diagnostics',1),('save_gradient_updates',[-1])]:
        bad=copy.deepcopy(spec);bad['recovery']['standing_task']['retention'][field]=value
        assert validate(bad)
