"""PORTABLE contract, fixed-window gate and real CPU PPO update tests; no Isaac."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy,json,os
from pathlib import Path
import pytest,torch
from native_stand.motion_course import symmetry,domain,io
from native_stand.command_v6.domain import reward
from native_stand.command_v6.domain.protocol import FIELDS,score,capability_gate
from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.evaluation_config import scoring
ROOT=Path('/home/kellen/wheel_leg_native_train')

def spec():
    p=ROOT/'manual_train/motion/symmetry_verification/prepared_spec.txt'
    return json.loads(Path(os.environ.get('MOTION_SYMMETRY_TEST_SPEC',p.read_text().strip())).read_text())

def test_named_signs_and_huber_gradient_no_plateau():
    q=torch.tensor([[.2,-.3,-.2,-.3],[.2,-.3,.2,.3]],requires_grad=True)
    cost,e=symmetry.reward_cost(q,symmetry.REWARD)
    assert torch.equal(e[0],torch.zeros(2));assert cost[0]==0 and cost[1]>0
    cost.sum().backward();assert q.grad[1].abs().sum()>0
    large=torch.tensor([[2.,2.,2.,-2.]],requires_grad=True)
    cost,_=symmetry.reward_cost(large,symmetry.REWARD);cost.sum().backward()
    assert cost>1 and large.grad.abs().sum()>0
    wrong=dict(symmetry.REWARD,action_override=True)
    with pytest.raises(ValueError):symmetry.validate_reward(wrong)

def compute(q,dt=.01,mirror=True):
    s=spec();w=s['reward'];n=len(q);z=torch.ones(n)
    return reward.compute(z*.34,z,z*0,z*0,z*0,torch.tensor([[0.,0.,.34]]).repeat(n,1),torch.ones(n,2,dtype=torch.bool),torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,6),q,torch.zeros(n),weights=w,height_width=w['height_width_m'],linear_denominator=.04,yaw_denominator=.09,terminal_penalty=-1.,dt=dt,mirror_config=w['joint_mirror'] if mirror else None)

def test_real_reward_fields_dt_once_and_old_route_unchanged():
    q=torch.tensor([[.2,.1,.2,-.1]])
    new,raw,weighted=compute(q);old,oldraw,oldweighted=compute(q,mirror=False)
    expected=-symmetry.reward_cost(q,symmetry.REWARD)[0]*.01
    assert torch.allclose(new-old,expected,atol=1e-7)
    assert set(raw)==set(reward.fields(spec()['reward'])) and 'joint_mirror' not in oldraw
    doubled=compute(q,dt=.02)[0];assert torch.allclose(doubled,new*2)
    assert compute(torch.tensor([[.1,.1,-.1,.1]]))[1]['joint_mirror']==0

def fixture_report(q_error=.02,target_error=.03):
    s=spec();protocol=protocol_for_spec(s,30.);rows=torch.zeros(3000,8,len(FIELDS));rows[:,:,2]=.34;rows[:,:,8:10]=3.
    valid=torch.ones(3000,8,dtype=torch.bool)
    r=score(rows,valid,torch.zeros_like(valid),torch.zeros(8,6,dtype=torch.bool),torch.zeros(8,dtype=torch.bool),dt=.01,target_window=(10.,20.),requested_steps=3000,full_trace=True,effective_protocol=protocol)
    r.update(seconds=30.,target=[0,0],effective_protocol=protocol)
    controls=torch.zeros(3000,8,54);controls[:,:,0]=q_error;controls[:,:,1]=q_error;controls[:,:,28]=target_error;controls[:,:,29]=target_error
    r['control_diagnostics']={'schema_version':'motion_policy_control_v1','joint_names':['left_hip_pitch','left_active_link_pitch','left_wheel_spin','right_hip_pitch','right_active_link_pitch','right_wheel_spin'],'groups':{'q':[0,6],'leg_target_after_projection':[28,32]},'rows':controls.tolist(),'valid':valid.tolist()}
    return r

def gated(r):
    symmetry.annotate(r);return capability_gate(r,[0,0],r['effective_protocol'])

def test_real_gate_joint_symmetry_and_physics_required():
    r=fixture_report();assert gated(r)['accepted']
    r=fixture_report(.31);g=gated(r);assert not g['accepted'];assert all('joint_mirror_mae' in c['failed_checks'] for c in g['per_env'])
    assert r['per_env'][0]['joint_mirror']['target_mae_rad'][0]==pytest.approx(.03)
    r=fixture_report();r['per_env'][0]['height_steady_mean_m']=.39
    assert not gated(r)['accepted']

def test_incomplete_hold_and_missing_schema_cannot_pass():
    r=fixture_report();r['control_diagnostics']['valid'][1500][0]=False;r['control_diagnostics']['rows'][1500][0]=None
    g=gated(r);assert g['passed_envs']==7 and 'joint_mirror_hold_incomplete' in g['per_env'][0]['failed_checks']
    r=fixture_report();r['control_diagnostics']['joint_names'][0]='wrong'
    with pytest.raises(ValueError,match='named'):gated(r)
    r=fixture_report();r['effective_protocol']['steady_window_s']=[10.,19.]
    with pytest.raises(ValueError,match='complete10s'):gated(r)

def test_p95_detects_short_asymmetry_despite_small_mean():
    r=fixture_report(0);rows=r['control_diagnostics']['rows']
    for i in range(1000,1100):rows[i][0][0]=.20
    g=gated(r);m=r['per_env'][0]['joint_mirror']
    assert m['actual_mae_rad'][0]<.05 and m['actual_p95_rad'][0]>.1
    assert 'joint_mirror_p95' in g['per_env'][0]['failed_checks']

def test_schema_norm_and_first_reward_initialization():
    s=spec();assert validate(s)==[];assert scoring(s['evaluation'])['mirror_error_max_rad']==.05
    assert s['curriculum']['active_stage']==0 and s['curriculum']['stages'][0]['sampling_slots']==[0]*64
    assert s['control']['height_command_m']==.34 and s['ppo']['critic_warmup_updates']==5
    assert s['restore_source_rng'] is False
    for field in ('joint_mirror',):
        bad=copy.deepcopy(s);bad['reward'].pop(field);assert validate(bad)
    bad=copy.deepcopy(s);bad['ppo']['critic_warmup_updates']=0;assert validate(bad)
    bad=copy.deepcopy(s);bad['evaluation']['mirror_error_p95_max_rad']=.3;assert validate(bad)

def test_actual_source_independent_critic_optimizer_and_warmup_updates():
    from tensordict import TensorDict
    from native_stand.command_v6.learning import model
    from rsl_rl.algorithms import PPO
    from rsl_rl.storage import RolloutStorage
    torch.set_num_threads(2);torch.manual_seed(123)
    s=spec();source=torch.load(io.SOURCE,map_location='cpu',weights_only=False);original_sha=io.sha(io.SOURCE)
    obs=TensorDict({'policy':torch.randn(4,25),'history':torch.randn(4,125)},batch_size=[4])
    actor=model(obs,actor=True,spec=s);critic=model(obs,actor=False,spec=s);actor.load_state_dict(source['actor'])
    storage=RolloutStorage('rl',4,8,obs,[6],'cpu')
    ppo=PPO(actor,critic,storage,num_learning_epochs=1,num_mini_batches=1,learning_rate=3e-5,device='cpu')
    from native_stand.command_v6.domain.warmstart import convert_wheel_envelope
    convert_wheel_envelope(actor,critic,ppo.optimizer,old_scale=s['wheel_envelope_conversion']['source_scale_rad_s'],new_scale=s['action']['wheel_scale_rad_s'])
    assert len(ppo.optimizer.state)==0
    proof=symmetry.optimization_initialization(s,actor,critic,ppo.optimizer,source)
    assert not proof['critic_restored'] and proof['optimizer_states']==0
    before={k:v.clone() for k,v in actor.state_dict().items()};beforecritic={k:v.clone() for k,v in critic.state_dict().items()}
    for p in actor.parameters():p.requires_grad_(False)
    def update():
        for i in range(8):
            ppo.act(obs);ppo.process_env_step(obs,torch.arange(1.,5.)*(i+1),torch.zeros(4,dtype=torch.bool),{})
        ppo.compute_returns(obs);ppo.update()
    update();assert all(torch.equal(v,actor.state_dict()[k]) for k,v in before.items())
    assert any(not torch.equal(v,critic.state_dict()[k]) for k,v in beforecritic.items())
    for p in actor.parameters():p.requires_grad_(True)
    update();assert any(not torch.equal(v,actor.state_dict()[k]) for k,v in before.items())
    assert io.sha(io.SOURCE)==original_sha

def test_same_checkpoint_required_and_missing_symmetry_rejected():
    r=fixture_report();gated(r);r['capability_gate']=capability_gate(r,[0,0],r['effective_protocol'])
    row={'kind':'full','update':100,'checkpoint':'x','checkpoint_sha256':'a'*64,'result':r}
    c=domain.aggregate([row]);assert c[0]['accepted']
    r['per_env'][0].pop('joint_mirror');assert not domain.aggregate([row])[0]['accepted']
    with pytest.raises(ValueError,match='duplicate'):domain.aggregate([row,row])

def test_confirmations_and_stagnation_do_not_ignore_mirror():
    row=dict(checkpoint='x',sha256='a'*64,update=100,passed=0,accepted=False,mirror_mae_rad=.3,mean_abs_error=.01,mean_saturation=.01)
    book={'totals':{'formal_updates':300}}
    domain.decide(book,[row],row);better=dict(row,mirror_mae_rad=.2)
    domain.decide(book,[better],better);assert book['best']['mirror_mae_rad']==.2 and book['stagnant_blocks']==0
    good=dict(better,passed=8,accepted=True);assert domain.decide(book,[good],good)['action']=='RESUME'
    assert domain.decide(book,[row],row)['action']=='RESUME' and book['confirmations']==0
    assert domain.decide(book,[good,good],good)['action']=='ACCEPT'


def test_wheel_conversion_fresh_partial_and_initialized_adam_states():
    from native_stand.command_v6.domain.warmstart import convert_wheel_envelope,wheel_parameter_scales
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__();self.mlp=torch.nn.Sequential(torch.nn.Linear(150,2))
    actor,critic=Net(),Net();named=[('actor.'+n,p) for n,p in actor.named_parameters()]+[('critic.'+n,p) for n,p in critic.named_parameters()]
    opt=torch.optim.Adam([p for _,p in named]);before=[p.detach().clone() for _,p in named]
    convert_wheel_envelope(actor,critic,opt,old_scale=100.,new_scale=100.)
    assert len(opt.state)==0 and all(torch.equal(p,b) for (_,p),b in zip(named,before))
    # After critic-only warmup, actor state is legitimately absent; retain it absent.
    sum(p.sum() for p in critic.parameters()).backward();opt.step();opt.zero_grad(set_to_none=True)
    before_params={n:p.detach().clone() for n,p in named};before_states={p:{k:v.clone() if torch.is_tensor(v) else v for k,v in state.items()} for p,state in opt.state.items()}
    scales=wheel_parameter_scales(named,6.,100.)
    convert_wheel_envelope(actor,critic,opt,old_scale=6.,new_scale=100.)
    assert len(opt.state)==2 and all(p not in opt.state for p in actor.parameters())
    for n,p in named:
        assert torch.equal(p,before_params[n]*scales[n])
        if p in before_states:
            assert torch.equal(opt.state[p]['step'],before_states[p]['step'])
            assert torch.equal(opt.state[p]['exp_avg'],before_states[p]['exp_avg']/scales[n])
            assert torch.equal(opt.state[p]['exp_avg_sq'],before_states[p]['exp_avg_sq']/scales[n].square())


def test_wheel_conversion_rejects_partial_moment_before_mutation():
    from native_stand.command_v6.domain.warmstart import convert_wheel_envelope
    actor=torch.nn.Sequential(torch.nn.Linear(150,2));opt=torch.optim.Adam(actor.parameters());p=next(actor.parameters());opt.state[p]={'step':torch.tensor(1.),'exp_avg':torch.zeros_like(p)}
    before={k:v.clone() for k,v in actor.state_dict().items()}
    with pytest.raises(ValueError,match='incomplete'):
        convert_wheel_envelope(actor,optimizer=opt,old_scale=6.,new_scale=100.)
    assert all(torch.equal(v,actor.state_dict()[k]) for k,v in before.items())
