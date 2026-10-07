import torch
from native_stand.recovery.domain import RecoveryFSM,Mode,autonomous_stable,huber_settling_costs


CFG={'success_mode':'autonomous_hold','verify_s':2.,'timeout_s':15.,'blend_s':.3,'gate_dwell_s':.5}
STABLE={'height_m':[.38,.42],'tilt_max_rad':.2,'linear_speed_max_mps':.05,
        'angular_speed_max_rad_s':.3,'dual_contact_min_n':2.,'chassis_clearance_min_m':.25}


def test_hold_two_seconds_no_teacher_and_reset_on_instability():
    f=RecoveryFSM(2,'cpu',CFG);yes=torch.ones(2,dtype=torch.bool);no=~yes
    for _ in range(100):
        pulse,_,_=f.step(yes,yes,no,no,dt=.01)
        assert not pulse.any() and (f.mode==int(Mode.RECOVERY)).all()
    stable=torch.tensor([False,True]);f.step(yes,stable,no,no,dt=.01)
    assert f.verify[0]==0
    for _ in range(99):f.step(yes,yes,no,no,dt=.01)
    assert f.mode[1]==int(Mode.STAND) and f.mode[0]==int(Mode.RECOVERY)
    for _ in range(100):f.step(yes,yes,no,no,dt=.01)
    pulse,_,_=f.step(yes,yes,no,no,dt=.01)
    assert pulse[0] and not pulse[1]
    assert not f.step(yes,yes,no,no,dt=.01)[0].any()
    f.reset(torch.tensor([0]));assert f.verify[0]==0 and f.mode[1]==int(Mode.STAND)


def test_fault_overrides_completion_and_timeout_not_success():
    f=RecoveryFSM(1,'cpu',CFG);yes=torch.ones(1,dtype=torch.bool);no=~yes
    f.verify[:]=1.99
    assert not f.step(yes,yes,yes,no,dt=.01)[0].any()
    assert f.mode[0]==int(Mode.RUNTIME_FAULT)
    f.reset(torch.tensor([0]));f.age[:]=14.99
    pulse,failed,_=f.step(no,no,no,no,dt=.01)
    assert failed.all() and not pulse.any()


def test_full_velocity_tilt_contact_and_height_not_only_height():
    h=torch.full((3,),.4);tilt=torch.zeros(3);v=torch.zeros(3,3);w=v.clone()
    v[1,2]=.1;w[2,2]=2.45
    contact=torch.full((3,2),10.);chassis=torch.full((3,),.3)
    assert autonomous_stable(h,tilt,v,w,contact,chassis,STABLE).tolist()==[True,False,False]
    h[0]=.6
    assert not autonomous_stable(h,tilt,v,w,contact,chassis,STABLE).any()


def test_huber_no_cap_symmetric_no_low_height_cost():
    cfg={'height_start_m':.32,'height_full_m':.38,'linear_scale_mps':.1,'angular_scale_rad_s':.5}
    h=torch.tensor([.168,.4,.4,.4]);v=torch.zeros(4,3);w=v.clone()
    w[:,2]=torch.tensor([10.,.5,2.45,-2.45])
    cost=huber_settling_costs(h,v,w,cfg)['settling_angular']
    assert cost[0]==0 and cost[2]>cost[1] and cost[2]==cost[3]
    assert torch.allclose(cost[2],torch.tensor(4.0009999),atol=1e-5)


def test_autonomous_candidate_requires_two_seconds_not_old_teacher_certificate():
    from native_stand.recovery.selection import classify_recovery
    row={'env_id':0,'continuous_s':5.,'verify_s':2.,'height_min_m':.17,'height_final_m':.4,
         'dual_contact_fraction':1.,'closure_max_m':0.,'tilt_peak_rad':.1,'saturation_fraction_policy':0.,
         'success':True,'recovery_s':3.,'outcome':'success'}
    identity={'scored_envs':1}
    result={'per_env':[row],'recovery_gate':{'accepted':True,'passed_envs':1,'per_env':[{'env_id':0,'failed_checks':[]}]},
            'success_protocol':{'mode':'autonomous_hold','required_stable_s':2.,'teacher_control':False}}
    entry={'identity':identity,'kind':'full','result':result}
    assert classify_recovery(entry,identity)['accepted']
    row['verify_s']=1.9
    assert not classify_recovery(entry,identity)['accepted']
    row['verify_s']=2.
    result.pop('success_protocol')
    assert not classify_recovery(entry,identity)['accepted']
