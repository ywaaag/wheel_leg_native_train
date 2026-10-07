import copy
import json
from pathlib import Path
import torch
import pytest
from tensordict import TensorDict

from native_stand.command_v6.config import validate, schedule
from native_stand.command_v6.domain.warmstart import initialize_state, initialize_adam,convert_wheel_envelope
from native_stand.command_v6.domain.task_curriculum import TaskProgression
from native_stand.command_v6.domain import command_schedule, reward
from native_stand.command_v6.ledger import transfer_unused_updates, Ledger
from native_stand.command_v6.learning import model
from native_stand.command_v6.domain.protocol import standing_gate, motion_gate

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/'configs/experiments/height40_from500_20261002/spec.json').read_text())


def test_new_spec_control_and_reward_frozen():
    assert validate(SPEC)==[]
    assert SPEC['source_input_dim']==150 and SPEC['source_update']==500
    assert SPEC['budget']['total_samples']==(SPEC['budget']['formal_updates']+SPEC['budget']['smoke_updates'])*8192
    assert SPEC['budget']['phase_sum_wall_s']<SPEC['budget']['chain_wall_s']
    assert SPEC['reward']['height']==2 and SPEC['control']['height_command_m']==.40
    for h in [.35,.36,.38,.40,.42]:
        total,raw,weighted=reward.compute(torch.tensor([h]),torch.ones(1),
            torch.zeros(1),torch.zeros(1),torch.zeros(1),torch.tensor([[0.,0.,.4]]),
            torch.ones(1,2,dtype=torch.bool),torch.zeros(1,6),torch.zeros(1,6),
            torch.zeros(1,6),torch.zeros(1,4),torch.zeros(1,dtype=torch.bool),
            weights=SPEC['reward'],height_width=.06,linear_denominator=.01,
            yaw_denominator=.09,terminal_penalty=-1.)
        expected=torch.exp(-((torch.tensor(h)-.4)/.06)**2)
        assert torch.allclose(raw['height'],expected[None])
        assert torch.allclose(weighted['height'],2*expected[None])
        assert torch.allclose(total,(3.5+2*expected[None])*.01)
    assert not schedule(10,'formal',SPEC['evaluation'])['full']
    assert schedule(500,'formal',SPEC['evaluation'])['full']


def test_strict150_native_network_and_adam_no_expansion():
    source=torch.load(SPEC['source_checkpoint'],map_location='cpu',weights_only=False)
    obs=TensorDict({'policy':torch.randn(16,25),'history':torch.randn(16,125)},batch_size=[16])
    actor=model(obs,actor=True,spec=SPEC);critic=model(obs,actor=False,spec=SPEC)
    actor.load_state_dict(initialize_state(source['actor'],actor.state_dict(),input_dim=150),strict=True)
    critic.load_state_dict(initialize_state(source['critic'],critic.state_dict(),input_dim=150),strict=True)
    golden=model(obs,actor=True,spec=SPEC);golden.load_state_dict(source['actor'],strict=True)
    assert torch.equal(actor(obs,stochastic_output=False),golden(obs,stochastic_output=False))
    src=[('actor.'+n,p) for n,p in source['actor'].items()]+[('critic.'+n,p) for n,p in source['critic'].items()]
    dst=[('actor.'+n,p) for n,p in actor.named_parameters()]+[('critic.'+n,p) for n,p in critic.named_parameters()]
    optimizer=torch.optim.Adam([p for _,p in dst],lr=.123)
    initialize_adam(source['optimizer'],optimizer,src,dst,learning_rate=3e-5,input_dim=150)
    assert optimizer.param_groups[0]['lr']==3e-5 and len(optimizer.state)==17
    ids=source['optimizer']['param_groups'][0]['params']
    for (_,param),key in zip(dst,ids):
        assert torch.equal(optimizer.state[param]['exp_avg'].cpu(),source['optimizer']['state'][key]['exp_avg'])
        assert torch.equal(optimizer.state[param]['exp_avg_sq'].cpu(),source['optimizer']['state'][key]['exp_avg_sq'])


def test_capability_stage_requires_both_directions_and_preserves_zero():
    manager=TaskProgression(SPEC['curriculum']['task_progression'])
    good=lambda cmd:{'command':cmd,'gate':{'accepted':True}}
    assert not manager.confirm(250,[good([0,0])],episode_length_s=6).get('promoted')
    assert manager.confirm(500,[good([0,0])],episode_length_s=10)['next_stage']==1
    cases=[good([0,0]),good([.1,0]),{'command':[-.1,0],'gate':{'accepted':False}}]
    assert not manager.confirm(1000,cases).get('promoted')
    cases[-1]['gate']['accepted']=True
    assert not manager.confirm(1500,cases).get('promoted')
    assert manager.confirm(2000,cases)['next_stage']==2
    for stage in SPEC['curriculum']['stages'][1:3]:
        values,counts=command_schedule.sample(stage['commands'],stage['weights'],50000,
            device='cpu',generator=torch.Generator().manual_seed(12))
        assert counts[0]/50000>.38
        assert float(values[:,1].abs().max())==0
        assert float(values[:,0].abs().max())<=.201
        for index in range(1,len(stage['commands']),2):
            assert abs(float(counts[index]-counts[index+1]))/50000<.01


def test_quota_transfer_debits_old_once_and_preserves_attempts(tmp_path):
    old=tmp_path/'old.json';new=tmp_path/'new.json'
    original={'limits':{'formal':3000},'used':{'formal':500},'attempts':{'old':{'status':'FAILED'}}}
    old.write_text(json.dumps(original))
    book=json.loads((ROOT/'configs/experiments/height40_from500_20261002/budget_transfer_plan.json').read_text())
    assert transfer_unused_updates(old,new,book,transfer_id='fixture',requested=2500)==2500
    assert json.loads(old.read_text())['limits']['formal']==500
    assert json.loads(old.read_text())['attempts']==original['attempts']
    assert json.loads(new.read_text())['limits']['formal']==2495
    assert transfer_unused_updates(old,new,book,transfer_id='fixture',requested=2500)==2500
    assert json.loads(old.read_text())['limits']['formal']==500
    with pytest.raises(ValueError):
        transfer_unused_updates(old,tmp_path/'another.json',copy.deepcopy(book),transfer_id='other',requested=2500)
    # An interrupted destination publish is recoverable, not a second debit.
    new.unlink()
    transfer_unused_updates(old,new,book,transfer_id='fixture',requested=2500)
    assert new.is_file() and json.loads(old.read_text())['limits']['formal']==500


def test_height_band_and_motion_not_moving_cannot_pass():
    row={'env_id':0,'outcome':'completed','continuous_s':10.,'net_drift_m':0.,
         'max_excursion_m':0.,'closure_max_m':0.,'peak_tilt_rad':0.,'saturation_fraction':0.,
         'mean_abs_vx_error_mps':0.,'mean_abs_yaw_error_rad_s':0.,'mean_abs_vy_mps':0.,
         'dual_contact_fraction':1.,'height_steady_mean_m':.4,'height_steady_fraction':1.,
         'mean_vx_mps':0.,'vx_direction_fraction':0.,'stop_vx_abs_mps':0.,'stop_yaw_abs_rad_s':0.}
    result={'per_env':[{**row,'env_id':i} for i in range(8)]}
    assert standing_gate(result,SPEC['evaluation'])['accepted']
    assert not motion_gate(result,[.1,0],SPEC['evaluation'])['accepted']
    result['per_env'][3]['height_steady_fraction']=.89
    assert not standing_gate(result,SPEC['evaluation'])['accepted']


def test100_wheel_envelope_preserves_mean_std_critic_and_physical_targets():
    source=torch.load(SPEC['source_checkpoint'],map_location='cpu',weights_only=False)
    old_spec=copy.deepcopy(SPEC);old_spec.pop('wheel_envelope_conversion');old_spec['action']['wheel_scale_rad_s']=6.
    generator=torch.Generator().manual_seed(103)
    data=torch.randn(64,150,generator=generator)*.05
    for f in range(6):
        data[:,f*25+3:f*25+6]=torch.tensor([0.,-1.,0.])
        data[:,f*25+6:f*25+9]=torch.tensor([0.,0.,2.])
    old_obs=TensorDict({'policy':data[:,:25],'history':data[:,25:]},batch_size=[64])
    new_data=data.clone()
    columns=[f*25+c for f in range(6) for c in (21,24)]
    new_data[:,columns]*=.06
    new_obs=TensorDict({'policy':new_data[:,:25],'history':new_data[:,25:]},batch_size=[64])
    old_actor=model(old_obs,actor=True,spec=old_spec);old_actor.load_state_dict(source['actor'])
    new_actor=model(new_obs,actor=True,spec=SPEC);new_actor.load_state_dict(source['actor'])
    old_critic=model(old_obs,actor=False,spec=old_spec);old_critic.load_state_dict(source['critic'])
    new_critic=model(new_obs,actor=False,spec=SPEC);new_critic.load_state_dict(source['critic'])
    named=[('actor.'+n,p) for n,p in new_actor.named_parameters()]+[('critic.'+n,p) for n,p in new_critic.named_parameters()]
    src=[('actor.'+n,p) for n,p in source['actor'].items()]+[('critic.'+n,p) for n,p in source['critic'].items()]
    optimizer=torch.optim.Adam([p for _,p in named],lr=3e-5)
    initialize_adam(source['optimizer'],optimizer,src,named,learning_rate=3e-5,input_dim=150)
    convert_wheel_envelope(new_actor,new_critic,optimizer,old_scale=6.,new_scale=100.)
    old=old_actor(old_obs,stochastic_output=False);new=new_actor(new_obs,stochastic_output=False)
    assert old[:,(2,5)].abs().max()<1 # Explicit old clipping-equivalence domain.
    assert torch.allclose(old[:,(0,1,3,4)],new[:,(0,1,3,4)],atol=2e-6,rtol=2e-6)
    assert torch.allclose(old[:,(2,5)]*6,new[:,(2,5)]*100,atol=2e-5,rtol=2e-5)
    assert torch.allclose(old_critic(old_obs),new_critic(new_obs),atol=2e-6,rtol=2e-6)
    torch.manual_seed(33);old_actor(old_obs,stochastic_output=True)
    torch.manual_seed(33);new_actor(new_obs,stochastic_output=True)
    assert torch.allclose(old_actor.output_std[:,(2,5)]*6,new_actor.output_std[:,(2,5)]*100,atol=1e-6)
    assert torch.equal(source['actor']['distribution.std_param'],new_actor.distribution.std_param)
    assert optimizer.param_groups[0]['lr']==3e-5


def test_standing_reward_physical_action_delta_preserved_after_normalization():
    old=torch.tensor([[.02,.03,.04,-.02,-.03,-.04]])
    new=old.clone();new[:,(2,5)]*=.06
    common=(torch.tensor([.4]),torch.ones(1),torch.zeros(1),torch.zeros(1),torch.zeros(1),
            torch.tensor([[0.,0.,.4]]),torch.ones(1,2,dtype=torch.bool),torch.zeros(1,6))
    kw=dict(weights=SPEC['reward'],height_width=.06,linear_denominator=.01,yaw_denominator=.09,terminal_penalty=-1.)
    _,a,_=reward.compute(*common,old,torch.zeros_like(old),torch.zeros(1,4),torch.zeros(1,dtype=torch.bool),**kw)
    _,b,_=reward.compute(*common,new,torch.zeros_like(new),torch.zeros(1,4),torch.zeros(1,dtype=torch.bool),action_delta_wheel_factor=100/6,**kw)
    assert torch.allclose(a['action_delta'],b['action_delta'])
