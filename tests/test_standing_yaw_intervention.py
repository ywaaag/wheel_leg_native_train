import copy
import json
from pathlib import Path

import torch

from native_stand.command_v6.config import validate
from native_stand.command_v6.ledger import transfer_unused_updates
from native_stand.recovery.domain import huber_settling_costs, process_reward


ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/recovery_standing_level_v2_long_20261006/spec.json'


def test_native_yaw_only_signed_symmetric_and_height_independent():
    cfg=json.loads(SPEC.read_text())['recovery']['settling_reward']
    h=torch.tensor([.2,.36,.36,.36]);z=torch.zeros(4,3)
    w=torch.tensor([[0.,.35,0.],[0.,-.35,0.],[.35,0.,0.],[0.,0.,.35]])
    old=huber_settling_costs(h,z,w,cfg)
    new=huber_settling_costs(h,z,w,{**cfg,'settling_yaw_weight':-.8,'yaw_scale_rad_s':.35})
    for key in old:torch.testing.assert_close(old[key],new[key])
    torch.testing.assert_close(new['settling_yaw'],torch.tensor([2**.5-1,2**.5-1,0.,0.]))


def test_yaw_penalty_is_unbounded_and_dt_once():
    spec=json.loads(SPEC.read_text());cfg=spec['recovery']['settling_reward']
    h=torch.ones(4)*.36;v=torch.zeros(4,3);w=v.clone();w[:,1]=torch.tensor([0.,.1,.35,2.45])
    args=(h,h,h,torch.ones(4),torch.zeros(4,6),torch.zeros(4,6),torch.zeros(4),
          torch.zeros(4,dtype=torch.bool),torch.zeros(4,dtype=torch.bool))
    weights={'lift':0.,'upright':0.,'effort':0.,'action_delta':0.,'joint_margin':0.,
             'success_once':10.,'failure_once':-1.}
    old,_,_=process_reward(*args,weights=weights,dt=.01,settling_config=cfg,
                          linear_velocity=v,angular_velocity=w)
    new,raw,weighted=process_reward(*args,weights=weights,dt=.01,
        settling_config={**cfg,'settling_yaw_weight':-.8,'yaw_scale_rad_s':.35},
        linear_velocity=v,angular_velocity=w)
    torch.testing.assert_close(weighted['settling_yaw'],raw['settling_yaw']*(-.8)*.01)
    torch.testing.assert_close(new-old,weighted['settling_yaw'])
    assert raw['settling_yaw'][0]==0 and torch.all(torch.diff(raw['settling_yaw'])>0)


def test_yaw_schema():
    spec=json.loads(SPEC.read_text());cfg=spec['recovery']['settling_reward']
    cfg.update(settling_yaw_weight=-.8,yaw_scale_rad_s=.35)
    assert validate(spec)==[]
    for key,value in [('settling_yaw_weight',0.),('yaw_scale_rad_s',0.),('settling_yaw_weight',float('nan'))]:
        bad=copy.deepcopy(spec);bad['recovery']['settling_reward'][key]=value
        assert validate(bad)


def test_three_smoke_plus100_exact_transfer_and_idempotence(tmp_path):
    old=tmp_path/'old.json';new=tmp_path/'new/budget.json'
    original={'limits':{'formal':2000},'used':{'formal':498},'attempts':{}}
    old.write_text(json.dumps(original));book={'limits':{},'used':{},'attempts':{}}
    assert transfer_unused_updates(old,new,book,transfer_id='yaw',requested=103,smoke_updates=3)==103
    result=json.loads(new.read_text());assert result['limits']=={'smoke':3,'formal':100}
    assert json.loads(old.read_text())['limits']['formal']==1897
    assert transfer_unused_updates(old,new,book,transfer_id='yaw',requested=103,smoke_updates=3)==103
    assert json.loads(old.read_text())['used']['formal']==498
