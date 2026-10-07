import torch
from native_stand.recovery.domain import process_reward,ReverseRecoveryCurriculum
from native_stand.command_v6.domain.warmstart import preserve_rng_state,seed_training

def base():
    return {'lift':3.,'upright':2.,'effort':-.02,'action_delta':-.01,'joint_margin':-.05,
        'success_once':10.,'failure_once':-1.,'support':.5,'support_force_threshold_n':2.,
        'low_height_wheel_spin':-.02,'wheel_gate_start_m':.20,'wheel_gate_full_m':.32}

def call(h, contact, wheel):
    n=len(h); z=torch.zeros(n); return process_reward(torch.tensor(h),torch.full((n,),.168),
        torch.full((n,),.4),torch.ones(n),torch.zeros(n,6),torch.zeros(n,6),z,
        torch.zeros(n,dtype=torch.bool),torch.zeros(n,dtype=torch.bool),weights=base(),dt=.01,
        linear_velocity=torch.zeros(n,3),angular_velocity=torch.zeros(n,3),pitch=z,
        contact=torch.tensor(contact),wheel_velocity=torch.tensor(wheel))

def test_support_is_dense_and_contact_sensitive():
    _,raw,_=call([.18,.18],[[0.,0.],[3.,3.]],[[2.,2.],[2.,2.]])
    assert raw['support'].tolist()==[0.,1.]

def test_low_height_wheel_spin_is_penalized_and_gate_fades():
    _,raw,_=call([.18,.38],[[3.,3.],[3.,3.]],[[4.,4.],[4.,4.]])
    assert raw['low_height_wheel_spin'][0] > raw['low_height_wheel_spin'][1]

def test_roll_level_cost_requires_explicit_roll_and_is_height_gated():
    weights=base();weights.update(roll_level=-2.,roll_level_scale_rad=.15,
        roll_level_start_m=.32,roll_level_full_m=.38)
    z=torch.zeros(2)
    _,raw,weighted=process_reward(torch.tensor([.30,.40]),torch.tensor([.168,.168]),
        torch.full((2,),.4),torch.ones(2),torch.zeros(2,6),torch.zeros(2,6),z,z.bool(),z.bool(),
        weights=weights,dt=.01,roll=torch.tensor([.2,.2]),
        contact=torch.ones(2,2)*3,wheel_velocity=torch.zeros(2,2))
    assert raw['roll_level'][0].item()==0.
    assert raw['roll_level'][1].item()>0.
    assert weighted['roll_level'][1].item()<0.

def test_leg_symmetry_cost_is_high_height_gated():
    weights=base();weights.update(leg_symmetry=-.08,
        leg_symmetry_start_m=.32,leg_symmetry_full_m=.36)
    z=torch.zeros(2)
    _,raw,weighted=process_reward(torch.tensor([.30,.36]),torch.tensor([.168,.168]),
        torch.full((2,),.36),torch.ones(2),torch.zeros(2,6),torch.zeros(2,6),z,
        z.bool(),z.bool(),weights=weights,dt=.01,leg_symmetry=torch.tensor([.25,.25]),
        contact=torch.ones(2,2)*3,wheel_velocity=torch.zeros(2,2))
    assert raw['leg_symmetry'][0].item()==0.
    assert raw['leg_symmetry'][1].item()>0.
    assert weighted['leg_symmetry'][1].item()<0.

def test_reverse_curriculum_requires_two_clean_windows():
    c=ReverseRecoveryCurriculum(['R0','R1','R2'],windows_required=2,episodes_per_window=10)
    assert c.current_level()=='R0'
    c.record_window(attempted=10,successes=10,runtime_faults=0)
    assert c.current_level()=='R0'
    c.record_window(attempted=10,successes=9,runtime_faults=0)
    assert c.current_level()=='R1'
    c.record_window(attempted=10,successes=10,runtime_faults=1)
    assert c.current_level()=='R1'

def test_default_window_rejects_short_window():
    c=ReverseRecoveryCurriculum(['R0','R1'])
    for _ in range(3): c.record_window(attempted=10,successes=10,runtime_faults=0)
    assert c.stage==0

def test_old_stage_episodes_do_not_unlock_new_stage():
    c=ReverseRecoveryCurriculum(['R0','R1','R2'],episodes_per_window=2)
    c.record_episodes([(0,True,False)]*8)
    assert c.stage==1 and not c.pending
    c.record_episodes([(1,True,False)]*4)
    assert c.stage==2

def test_normalized_wheel_cost_cannot_swallow_lift():
    weights=base();weights['wheel_spin_scale_rad_s']=100.
    z=torch.zeros(1)
    _,raw,weighted=process_reward(torch.tensor([.18]),torch.tensor([.168]),torch.tensor([.4]),
        torch.ones(1),torch.zeros(1,6),torch.zeros(1,6),z,z.bool(),z.bool(),
        weights=weights,dt=.01,contact=torch.ones(1,2)*3,wheel_velocity=torch.ones(1,2)*100)
    assert raw['low_height_wheel_spin'].item()==1
    assert abs(weighted['low_height_wheel_spin'].item())<weighted['upright'].item()


def test_recovery_curriculum_checkpoint_preserves_pending_window():
    original=ReverseRecoveryCurriculum(['R0','R1'],episodes_per_window=4)
    original.record_episodes([(0,True,False),(0,True,False)])
    saved=original.checkpoint_state()
    restored=ReverseRecoveryCurriculum(['R0','R1'],episodes_per_window=4)
    state=restored.restore_checkpoint_state(saved)
    assert state['stage']==0 and state['pending_episodes']==2
    restored.record_episodes([(0,True,False),(0,True,False)])
    assert restored.stage==0
    restored.record_episodes([(0,True,False)]*4)
    assert restored.stage==1


def test_new_seed_is_not_overwritten_by_source_rng():
    torch.manual_seed(123)
    expected=torch.rand(4)
    source={'cpu_rng':torch.random.get_rng_state()}
    torch.manual_seed(123)
    # Missing source cuda state is harmless when restoration is not requested.
    info=seed_training(123,source=source,restore_source_rng=False)
    assert not info['restored_source_rng']
    assert torch.allclose(torch.rand(4),expected)


def test_evaluation_rng_state_is_restored():
    torch.manual_seed(77)
    before=torch.random.get_rng_state()
    with preserve_rng_state():
        torch.rand(100)
    assert torch.equal(torch.random.get_rng_state(),before)
