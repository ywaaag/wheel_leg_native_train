"""Finite drift costs keep feedback outside the old Gaussian support."""
FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.recovery_task import reward,configuration,MOTION_MIRROR_VERSION,SLIDING_VERSION
from native_stand.students.training_recipe import declaration,SLIDING_RECIPE,UPDATE200_SHA

def arguments(vx):
 n=len(vx);z=torch.zeros(n);b=torch.ones(n,dtype=torch.bool);f=~b
 return [x.clone() for x in [z+.4,z+.4,torch.zeros(n,2),torch.ones(n,2)*10,z+.01,torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,3),torch.stack((vx,z,z),-1),z,b,b,f,f,f,f]]

def test_cost_has_large_error_slope_symmetry_dt_once_old_terms_unchanged():
 vx=torch.tensor([0.,.1,.5,1.5,2.,-1.5],requires_grad=True);a=arguments(vx);q=torch.zeros(6,4)
 old=reward(*a,reward_configuration=configuration(MOTION_MIRROR_VERSION),active_leg_q=q)
 new=reward(*a,reward_configuration=configuration(SLIDING_VERSION),active_leg_q=q)
 for k in ('raw','weighted_density','continuous_dt','events','pre_entry_angular_dt'):assert torch.equal(old[k],new[k])
 torch.testing.assert_close(new['motion_mirror_raw'][:,0],torch.tensor([0.,.02,.5,2.5,3.5,2.5]))
 torch.testing.assert_close(new['motion_mirror_dt'][:,0],-new['motion_mirror_raw'][:,0]*.01)
 gradient=torch.autograd.grad(new['motion_mirror_dt'][:,0].sum(),vx)[0]
 assert gradient[3].item()==pytest.approx(-.02) and gradient[5].item()==pytest.approx(.02)
 assert new['motion_mirror_dt'][:,1].eq(0).all()

def test_cost_is_not_disabled_by_pitch_and_masks_fault_initialization():
 a=arguments(torch.tensor([1.5,1.5,1.5]));a[2][:]=.5;a[12][1]=False;a[13][2]=True
 r=reward(*a,reward_configuration=configuration(SLIDING_VERSION),active_leg_q=torch.zeros(3,4))
 assert r['motion_mirror_raw'][0,0].item()==2.5
 assert r['total'][1:].eq(0).all()
 a[0][:]=.42;r=reward(*a,reward_configuration=configuration(SLIDING_VERSION),active_leg_q=torch.zeros(3,4));assert r['raw'][0,0]==1

def test_only_tracking_declaration_changes_and_source_is_new200():
 old=configuration(MOTION_MIRROR_VERSION);new=configuration(SLIDING_VERSION)
 assert {k for k in old if old[k]!=new[k]}=={'version','motion_zero_tracking'}
 d=declaration(SLIDING_RECIPE);assert d['source_actor_sha256']==UPDATE200_SHA and d['BC_coefficient']==0
 assert d['milestones']==[25,50,100,200,300] and d['training_family']=='motion_native_normal'
