import copy
FROZEN_TEST_SCOPE='PORTABLE'
import torch
import pytest
from native_stand.command_v6.domain.posture_geometry import bounded_cost, validate_balance
from native_stand.command_v6.domain.reward import compute


def config():
    return {'version':'bounded_geometry_v1','weight':-.5,
        'deadbands':{'wheel_heading_offset_m':.02,'leg_length_difference_m':.005,'roll_rad':.02},
        'denominators':{'wheel_heading_offset_m':.01,'leg_length_difference_m':.01,'roll_rad':.04}}


def geometry(x=.0,l=.0,r=.0):
    return {'wheel_heading_offset_m':torch.tensor([x]),'leg_length_difference_m':torch.tensor([l]),
            'roll_rad':torch.tensor([r]),'valid':torch.tensor([True])}


def test_bounded_cost_units_sign_deadband_and_invalid():
    c=config();cost,_=bounded_cost(geometry(),c);assert cost.item()==0.
    cost,_=bounded_cost(geometry(.062,.02,.3),c);assert 0<cost.item()<1
    mirror,_=bounded_cost(geometry(-.062,-.02,-.3),c);assert cost.item()==mirror.item()
    maximum,_=bounded_cost(geometry(100,100,100),c);assert maximum.item()==1.
    g=geometry();g['valid'].fill_(False)
    assert torch.isnan(bounded_cost(g,c)[0]).all()
    c['weight']=.5
    with pytest.raises(ValueError):validate_balance(c)


def test_reward_added_once_and_original_components_unchanged():
    z=torch.zeros(1);command=torch.tensor([[0.,0.,.4]])
    weights={'upright':2.,'height':2.,'velocity_tracking':8.,'two_wheel_contact':.5,
        'effort':-.02,'action_delta':-.01,'joint_margin':-.05}
    args=(torch.tensor([.4]),torch.ones(1),z,z,z,command,torch.ones(1,2,dtype=torch.bool),
        torch.zeros(1,6),torch.zeros(1,6),torch.zeros(1,6),torch.zeros(1,4),torch.zeros(1,dtype=torch.bool))
    kwargs=dict(weights=weights,height_width=.06,linear_denominator=1.,yaw_denominator=.09,terminal_penalty=-1.)
    base,raw,weighted=compute(*args,**kwargs)
    c=config();g=geometry(.062,.02,.3)
    total,new_raw,new_weighted=compute(*args,**kwargs,posture_geometry=g,posture_config=c)
    expected=bounded_cost(g,c)[0]*c['weight']*.01
    assert torch.allclose(total-base,expected)
    assert all(torch.equal(v,new_raw[k]) for k,v in raw.items())
    assert all(torch.equal(v,new_weighted[k]) for k,v in weighted.items())
    off=compute(*args,**kwargs,posture_config=None)
    assert torch.equal(base,off[0])
    with pytest.raises(ValueError):compute(*args,**kwargs,posture_config=c)


def test_trainer_reward_registration_accepts_real_posture_reward_and_remains_strict():
    from native_stand.command_v6.domain.metrics import motion_reward_fields,RolloutMetrics
    names=motion_reward_fields({'posture_balance':config()})
    assert names[-1]=='posture_balance' and len(names)==8
    assert len(motion_reward_fields({}))==7
    z=torch.zeros(1);weights=dict(zip(names[:-1],[2.,2.,8.,.5,-.02,-.01,-.05]))
    total,raw,weighted=compute(torch.tensor([.4]),torch.ones(1),z,z,z,torch.tensor([[0.,0.,.4]]),
        torch.ones(1,2,dtype=torch.bool),torch.zeros(1,6),torch.zeros(1,6),torch.zeros(1,6),
        torch.zeros(1,4),torch.zeros(1,dtype=torch.bool),weights=weights,height_width=.06,
        linear_denominator=1.,yaw_denominator=.09,terminal_penalty=-1.,
        posture_geometry=geometry(.06,.02,.1),posture_config=config())
    metric=RolloutMetrics(names,('height',),1,'cpu')
    args=({'height':torch.zeros(1,dtype=torch.bool)},torch.ones(1,2,dtype=torch.bool),
        torch.zeros(1,4),torch.zeros(1,6),[40,40,5.5,40,40,5.5])
    metric.add(raw,weighted,*args)
    assert metric.summary()['weighted_mean']['posture_balance']<0
    old=RolloutMetrics(motion_reward_fields({}),('height',),1,'cpu')
    with pytest.raises(ValueError,match='fields changed'):old.add(raw,weighted,*args)
    from native_stand.command_v6.tools.test_resources import source_file
    source=source_file('command_v6/train.py').read_text()
    assert "else motion_reward_fields(spec['reward'])" in source


def entry(role,update,cost,accepted=True):
    return {'role':role,'update':update,'checkpoint':role+str(update),
        'checkpoint_sha256':role+str(update),'eligible':True,'accepted':accepted,'passed_envs':int(accepted),
        'command':[0,0],'per_env':[{'env_id':0,'peak_tilt_rad':.1,'dual_contact_fraction':1.,
            'mean_abs_vx_error_mps':.01,'posture_cost_mean':cost,
            'posture_geometry':{'posture_component_means':{'wheel_heading_offset_m':cost,
                'leg_length_difference_m':cost,'roll_rad':cost}}}],
        'gate':{'per_env':[{'env_id':0,'accepted':accepted}]}}


def test_posture_candidate_requires_motion_and_two_spaced_improvements():
    from native_stand.command_v6.completion import choose_capability
    expected={'capability_commands':[[0,0]],'scored_envs':1,'source_sha256':'source0',
        'posture_acceptance':{'minimum_relative_improvement':.2,'required_confirmations':2,
            'maximum_component_regression_fraction':.1,'minimum_confirmation_spacing_updates':25}}
    source=entry('source',0,.5);one=entry('candidate',25,.3)
    assert choose_capability([source,one],None,expected)['accepted_candidate'] is None
    two=entry('candidate',50,.3)
    result=choose_capability(copy.deepcopy([source,one,two]),None,expected)
    assert result['accepted_candidate'] and result['accepted_candidate']['role']=='candidate'
    assert choose_capability([entry('source',0,.5),entry('candidate',25,.3),entry('candidate',50,.3,False)],None,expected)['accepted_candidate'] is None
    assert choose_capability([entry('source',0,.5),entry('candidate',25,.3),entry('candidate',26,.3)],None,expected)['accepted_candidate'] is None
