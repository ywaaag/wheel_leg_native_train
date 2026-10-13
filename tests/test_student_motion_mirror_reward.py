"""Motion-inspired zero tracking and bounded physical mirror cost."""
FROZEN_TEST_SCOPE='PORTABLE'
import pytest,torch
from native_stand.students.recovery_task import configuration,reward,REHEARSAL_VERSION,MOTION_MIRROR_VERSION
from native_stand.students.training_recipe import declaration,MOTION_MIRROR_RECIPE,UPDATE50_SHA

def args(n=3):
 z=torch.zeros(n);t=torch.ones(n,dtype=torch.bool);f=~t
 return [v.clone() for v in [z+.40,z+.40,torch.zeros(n,2),torch.ones(n,2)*10,z+.01,torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,3),torch.zeros(n,3),z,t,t,f,f,f,f]]

def test_slow_drift_discrimination_combined_tracking_dt_once_and_acceptance_unchanged():
 a=args();a[9][:,0]=torch.tensor([0.,.10,.30]);q=torch.zeros(3,4)
 old=reward(*a,reward_configuration=configuration(REHEARSAL_VERSION))
 new=reward(*a,reward_configuration=configuration(MOTION_MIRROR_VERSION),active_leg_q=q)
 for k in ('raw','weighted_density','continuous_dt','events'):assert torch.equal(old[k],new[k])
 expected=torch.exp(-torch.tensor([0.,.01,.09])/.04)
 torch.testing.assert_close(new['motion_mirror_raw'][:,0],expected)
 torch.testing.assert_close(new['total']-old['total'],expected*.04)
 a[9][:,1]=.2;a[10][:]=.3
 both=reward(*a,reward_configuration=configuration(MOTION_MIRROR_VERSION),active_leg_q=q)
 torch.testing.assert_close(both['motion_mirror_raw'][:,0],expected*torch.exp(torch.tensor(-2.)))

def test_mirror_hip_sum_active_difference_bounded_fault_and_initialization_mask():
 a=args();q=torch.tensor([[.2,.1,-.2,.1],[.2,.1,.2,-.1],[100.,100.,100.,-100.]])
 r=reward(*a,reward_configuration=configuration(MOTION_MIRROR_VERSION),active_leg_q=q)
 torch.testing.assert_close(r['motion_mirror_raw'][:,1],torch.tensor([0.,2.5,4.]))
 assert r['motion_mirror_dt'][:,1].min().item()==pytest.approx(-.002)
 a[12][1]=False;a[13][2]=True
 masked=reward(*a,reward_configuration=configuration(MOTION_MIRROR_VERSION),active_leg_q=q)
 assert masked['total'][1:].eq(0).all()
 with pytest.raises(ValueError,match='requires named'):reward(*args(),reward_configuration=configuration(MOTION_MIRROR_VERSION))

def test_height042_allowed_and_failed_event_not_repeated_by_new_terms():
 a=args();a[0][:]=.42;a[15][0]=True
 r=reward(*a,reward_configuration=configuration(MOTION_MIRROR_VERSION),active_leg_q=torch.zeros(3,4))
 assert r['raw'][:,0].eq(1).all() and r['events'][0,1]==10
 assert r['motion_mirror_raw'][:,0].eq(1).all()
 d=declaration(MOTION_MIRROR_RECIPE)
 assert d['source_actor_sha256']==UPDATE50_SHA and d['BC_coefficient']==0
 assert d['training_family']=='motion_native_normal' and d['milestones']==[25,50,100,200,300]
