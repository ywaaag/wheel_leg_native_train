FROZEN_TEST_SCOPE='PORTABLE'
import copy
import pytest
import torch
from native_stand.recovery.handoff_protocol import declaration,prefix_steps,duration
from native_stand.recovery.handoff_requests import validate
from native_stand.recovery.handoff_ownership import ownership,yaw_randomize
from native_stand.recovery.handoff_clock import HandoffClock
from native_stand.recovery.controlled_ppo import normalize_valid

def request():
    row=dict(kind='normal_motion_baseline',recovery=None,switch_s=0.,checkpoint='cp',sha256='sha',
             seconds=13.02,family='normal',seed=1,case_id='normal',recovery_spec='r',recovery_spec_sha256='s')
    return {'evaluation_only':True,'evaluation':{'envs':64,'scored_envs':8},'seed':1,
        'recovery':{'initialization':{'settle_max_s':1.}},'motion_handoff':{
        'version':'dual_frozen_handoff_v2','protocol':declaration(),'motion_checkpoint':'m','motion_sha256':'s',
        'motion_spec':'ms','motion_spec_sha256':'s','max_storage_bytes':512*2**20,'normal_initialization_source':{},
        'initialization_randomization':{'version':'reset_yaw_v1','root_yaw_rad':.01,'distribution':'uniform'},
        'cases':[row,dict(row,case_id='receiver_seed2',kind='recovery_prefix_then_motion',recovery='B50',seed=2,
            family='swing',switch_s=.45,seconds=13.47)]}}

def test_arbitrary_case_ids_and_seed_protocol_not_fixed22():
    s=request();validate(s)
    bad=copy.deepcopy(s);bad['motion_handoff']['cases'][1]['case_id']='normal'
    with pytest.raises(ValueError):validate(bad)
    bad=copy.deepcopy(s);bad['motion_handoff']['cases'][0]['ignored']=True
    with pytest.raises(ValueError):validate(bad)
    assert prefix_steps(.45)==45 and duration(.45,1.)==pytest.approx(13.47)
    with pytest.raises(ValueError):prefix_steps(.451)

def test_pre_action_ownership_boundary_and_failure_step():
    init=torch.tensor([True,False,False,False]);checked=torch.tensor([False,True,True,True])
    count=torch.tensor([0,49,50,0]);threshold=torch.tensor([50,50,50,0])
    controller,valid=ownership(init,checked,count,threshold)
    assert controller.tolist()==[0,1,2,2] and valid.tolist()==[False,False,True,True]
    # Post-action failure cannot retroactively change the pre-action mask.
    failed=torch.tensor([False,False,True,False]);assert valid[failed].all()

def test_seed_changes_real_reset_quaternion_without_hidden_velocity():
    q=torch.tensor([[2**-.5,0.,0.,2**-.5]]).repeat(8,1)
    torch.manual_seed(1);a=yaw_randomize(q,torch.rand(8),.01)
    torch.manual_seed(2);b=yaw_randomize(q,torch.rand(8),.01)
    assert not torch.equal(a,b) and torch.allclose(a.norm(dim=-1),torch.ones(8))
    assert torch.equal(yaw_randomize(q,torch.rand(8),0.),q)
    def gravity_body(v):
        x,y,z,w=v.unbind(-1)
        return torch.stack((-2*x*z+2*w*y,-2*y*z-2*w*x,-1+2*x*x+2*y*y),-1)
    assert torch.allclose(gravity_body(a),gravity_body(q),atol=2e-7)

def test_partial_reset_keeps_other_history_and_clock():
    clock=HandoffClock(2,'cpu');clock.motion[:]=True;clock.entry[:]=.2;clock.count[:]=300
    clock.reset(torch.tensor([0]));assert clock.count.tolist()==[0,300] and clock.entry[1]==.2
    from native_stand.recovery.handoff_ownership import phase_metadata
    phase,time=phase_metadata(torch.tensor([0,1,2,2]),torch.tensor([.2,0.,0.,0.]),
        torch.tensor([0,49,50,50]),torch.tensor([0.,0.,.1,1.2]),torch.tensor([-1.,-1.,-1.,1.]),torch.tensor([0,0,0,20]))
    assert phase.tolist()==[0,1,2,3] and torch.allclose(time,torch.tensor([.2,.49,.1,.2]))

def test_invalid_prefix_advantage_does_not_contaminate_actor_statistics():
    valid=torch.tensor([False,False,True,True])[:,None];adv=torch.tensor([9.,2.,1.,3.])[:,None]
    a=normalize_valid(adv,valid);adv[:2]=1e6;assert torch.equal(a,normalize_valid(adv,valid))

def test_diagnostic_protocol_not_main_acceptance_identity():
    from native_stand.recovery.handoff_protocol import validate_protocol
    p=declaration();p.update(version='recovery_motion_extended_diagnostic_v1',settle_s=3.)
    assert validate_protocol(p)['version']!=declaration()['version']
    p['vx_max']=2
    with pytest.raises(ValueError):validate_protocol(p)

def test_receiver_setup_exception_restores_temp_flags_actor_and_rng(monkeypatch):
    from types import SimpleNamespace
    from native_stand.command_v6.tools.evaluation_state import isolated_evaluation
    monkeypatch.setattr(torch.cuda,'is_available',lambda:False)
    class Actor:
        training=True
        def eval(self):self.training=False
        def train(self,v):self.training=v
    class Env:
        family='Swing';split='train';curriculum_training=True;continuous_evaluation=False
        recovery_config={};receiver_config={};rise_hold=SimpleNamespace(defer_completion=False)
        fsm=SimpleNamespace(config={'timeout_s':11.5})
        def select_initial_family(self,f,s):self.family=f;self.split=s
        def reset(self):pass
    @isolated_evaluation
    def fail(actor,wrapped,env):
        torch.manual_seed(999);env.rise_hold.defer_completion=True
        env.motion_command=torch.ones(2,3);env.return_to_original=torch.ones(2,dtype=torch.bool)
        raise ValueError('setup failure')
    actor=Actor();env=Env();rng=torch.get_rng_state().clone()
    with pytest.raises(ValueError,match='setup failure'):fail(actor,None,env)
    assert actor.training and not env.rise_hold.defer_completion
    assert not hasattr(env,'motion_command') and not hasattr(env,'return_to_original')
    assert torch.equal(rng,torch.get_rng_state())


def test_public_receiver_evaluator_full_windows_and_original_return_without_physics(monkeypatch):
    from types import SimpleNamespace
    from tensordict import TensorDict
    from native_stand.recovery.receiver_recipe import evaluate_actor
    from native_stand.recovery.handoff_clock import HandoffClock
    from native_stand.recovery.domain import Mode
    from native_stand.command_v6.domain.evidence import resolve_gate
    monkeypatch.setattr(torch.cuda,'is_available',lambda:False)
    from native_stand.recovery.handoff_protocol import declaration
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    s={'receiver_training':{'evaluation_families':['swing_candidate_from_historical_r1','motion_native_normal'],
        'motion_return_commands':[[.5,0],[-.5,0]],'protocol':declaration()},
        'recovery':{},'evaluation':{'scored_envs':8}}
    class Actor:
        training=True
        def eval(self):self.training=False
        def train(self,v):self.training=v
        def __call__(self,obs,stochastic_output):return torch.zeros(len(obs),6)
    class Env:
        num_envs=8;device='cpu';family='swing_candidate_from_historical_r1';split='train'
        curriculum_training=True;continuous_evaluation=False
        receiver_config=s['receiver_training'];recovery_config=s['recovery'];receiver_spec=s
        fsm=SimpleNamespace(mode=torch.full((8,),int(Mode.RECOVERY)),config={'timeout_s':11.5})
        rise_hold=HandoffClock(8,'cpu');original_motion_actor=Actor()
        initial_age=torch.zeros(8);executed_prefix=torch.zeros(8,dtype=torch.long)
        def select_initial_family(self,f,split):self.family=f;self.split=split
        def reset(self):
            self.rise_hold.reset(torch.arange(8));self.executed_prefix.zero_();self.elapsed=0
            p=torch.zeros(8,25);p[:,8]=1.8
            self.recovery_observation={'policy':p,'history':torch.zeros(8,125)}
        def observation(self):
            p=torch.zeros(8,25);p[:,8]=2
            if hasattr(self,'motion_command'):p[:,6:8]=self.motion_command[:,:2]*torch.tensor([2.,.25])
            return TensorDict({'policy':p,'history':torch.zeros(8,125)},batch_size=[8])
        def actor_valid_pre(self):return self.executed_prefix>= (0 if self.family=='motion_native_normal' else 50)
        def compose_training_action(self,x):return x.clone()
        def receiver_summary(self):return {'receiver':1,'real_handoffs':1}
    env=Env()
    class Wrapped:
        def reset(self):env.reset();return env.observation(),{}
        def step(self,action):
            valid=env.actor_valid_pre();env.executed_prefix+=~valid;env.elapsed+=1
            original=getattr(env,'return_to_original',torch.zeros(8,dtype=torch.bool))
            ctrl=torch.where(valid,2,1);ctrl[original]=4;env.handoff_controller=ctrl
            env.rise_hold.motion.copy_(valid)
            pulse,failed,end,fault=env.rise_hold.observe(torch.full((8,),.4),torch.zeros(8,2),torch.zeros(8),
                torch.full((8,2),100.),torch.full((8,),.3),torch.zeros(8),torch.zeros(8),
                active=torch.ones(8,dtype=torch.bool),valid=torch.ones(8,dtype=torch.bool),
                safety_failed=torch.zeros(8,dtype=torch.bool),fault=torch.zeros(8,dtype=torch.bool))
            st=torch.zeros(8,39);st[:,0]=env.rise_hold.age;st[:,6]=.4;st[:,10:12]=100.;st[:,13]=.3;st[:,29]=1.;st[:,31]=1.
            if hasattr(env,'motion_command'):st[:,7]=env.motion_command[:,0]
            env.recovery_snapshot=st;env.standing_snapshot=torch.zeros(8,10)
            env.recovery_control_snapshot=torch.zeros(8,54);env.wheel_geometry_snapshot=torch.zeros(8,13)
            return env.observation(),torch.zeros(8),end,{}
    actor=Actor();rng=torch.get_rng_state().clone()
    result=evaluate_actor(actor,Wrapped(),env,seconds=13.52,seed=12,full_trace=True)
    assert result['accepted'] and result['recovery_gate']['passed_envs']==8
    assert all(p['hold_complete'] and p['hold_index_half_open'][1]-p['hold_index_half_open'][0]==1000 for p in result['per_env'])
    assert all(r['passed_envs']==8 and all(p['original_motion_intervals']==500 for p in r['per_env']) for r in result['original_motion_return'])
    assert resolve_gate(result,'recovery',expected_envs=8,expected_protocol=protocol_for_spec(s,13.52))['candidate_eligible']
    assert actor.training and torch.equal(rng,torch.get_rng_state())
    assert not hasattr(env,'return_to_original') and not hasattr(env,'motion_command')
