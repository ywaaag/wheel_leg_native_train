FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.recovery.motion_handoff import encode_executed,physical_targets,motion_frame,score,scan_conditions

def test_physical_targets_encoding_and_information_loss_not_scaled_twice():
    ref=torch.zeros(1,6);a=torch.tensor([[1.,.5,.2,-1.,-.5,-.1]])
    legs,wheels=physical_targets(a,ref,controller='Recovery');assert legs.tolist()==[[1.600000023841858,.800000011920929,-1.600000023841858,-.800000011920929]]
    e=encode_executed(legs,wheels,ref,leg_scale=.5,wheel_scale=100.);assert e['outside'][0,[0,1,3,4]].all()
    assert torch.allclose(e['raw'][:,[2,5]],a[:,[2,5]])

def test_history_continues_and_motion_native_height_command():
    z=torch.zeros(1,6);g=torch.tensor([[0.,-1,0.]]);h=torch.arange(125.).reshape(1,125)
    d=motion_frame(torch.zeros(1,3),g,z,z,torch.zeros(1,4),torch.zeros(1,2),z,h,torch.tensor([False]))
    assert torch.equal(d['history'][:,:100],h[:,25:]);assert d['policy'][0,8]==2.

def trace(n=1220):
    s=torch.zeros(n,39);s[:,0]=torch.arange(1,n+1)*.01;s[:,6]=.4;s[:,10:12]=10;s[:,13]=.3;s[:,29]=1;s[:,31]=4
    return s,torch.zeros(n,10),torch.ones(n,dtype=torch.bool)

def test_full_hold_after_dwell_and_no_partial_or_fast_motion_acceptance():
    s,p,m=trace();r=score(s,p,m);assert r['accepted'] and r['hold_index_half_open']==[20,1020]
    assert not score(s[:1019],p[:1019],m[:1019])['accepted']
    s[:,7]=.51;assert 'vx' in score(s,p,m)['failed_checks']

def test_scan_denominator_and_missing_switch_or_late_entry():
    assert len(scan_conditions(['init','25','50','100']))==22
    s,p,m=trace();m[:]=False;assert not score(s,p,m)['accepted']
    m[:]=True;s[:201,6]=.2;assert not score(s,p,m)['accepted']

def test_failure_before_switch_stays_failed_and_episode_identity_required():
    s,p,m=trace();m[:10]=False;s[5,3]=1
    assert score(s,p,m)['failed_checks']==['failed_before_switch']
    s[5,3]=0;s[5,31]=9
    assert score(s,p,m)['failed_checks']==['episode_stitched']


def test_original_zero_time_and_invalid_hold_counterexamples_rejected():
    s,p,m=trace();s[:,0]=0;assert not score(s,p,m)['accepted']
    s,p,m=trace();s[20:1020,29]=0;assert not score(s,p,m)['accepted']
    s,p,m=trace();s[50,0]=s[49,0];assert not score(s,p,m)['accepted']
    s,p,m=trace();s[50:,0]+=.01;assert not score(s,p,m)['accepted']

def test_vx_user_threshold_and_strict_diagnostic_and_dt():
    s,p,m=trace();s[:,7]=.3;r=score(s,p,m);assert r['accepted'] and not r['strict_vx_0p02_pass']
    assert not score(s,p,m,dt=.02)['accepted']

def test_prefix_interval_boundaries_and_same_protocol_duration():
    from native_stand.recovery.handoff_protocol import prefix_steps,duration
    assert [prefix_steps(t) for t in (0,.1,.25,.5,1.,2.)]==[0,10,25,50,100,200]
    assert duration(2.,1.)==15.02

def test_online_clock_deadline_and_fullwindow_match_offline():
    from native_stand.recovery.handoff_clock import HandoffClock
    c=HandoffClock(1,'cpu');c.motion[:]=True
    h=torch.tensor([.4]);a=torch.zeros(1,2);t=torch.zeros(1);force=torch.ones(1,2)*10;g=torch.ones(1);cl=torch.zeros(1);sat=torch.zeros(1);on=torch.ones(1,dtype=torch.bool);off=~on
    with torch.inference_mode():
        for i in range(1020):
            pulse,failed,end,fault=c.observe(h,a,t,force,g,cl,sat,active=on,valid=on,safety_failed=off,fault=off)
            if i<1019:assert not end.item()
        assert pulse.item() and c.count.item()==1000
    c.reset(torch.tensor([0]));assert c.entry.item()==-1 # inference evaluation doesn't create unsafe persistent tensors
