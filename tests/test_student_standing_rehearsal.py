"""Native reset perturbation and mixed-course reward semantics."""
FROZEN_TEST_SCOPE='PORTABLE'
import pytest,torch
from native_stand.students.rehearsal import angular_reset
from native_stand.students.recovery_task import reward,configuration,LIFT_RATE_VERSION,REHEARSAL_VERSION
from native_stand.students.training_recipe import declaration,REHEARSAL_RECIPE

def test_native_angular_reset_is_body_axes_bounded_and_no_pose_or_linear_velocity_change():
 root=torch.zeros(3,13);root[:,2]=.4;root[:,3]=2**-.5;root[:,6]=2**-.5
 samples=torch.tensor([[0.,1.],[.5,.5],[1.,0.]])
 changed=angular_reset(root,samples)
 assert torch.equal(root[:,:10],changed[:,:10]) and root[:,10:].eq(0).all()
 torch.testing.assert_close(changed[:,10:],torch.tensor([[-.25,-.25,0.],[0.,0.,0.],[.25,.25,0.]]),atol=1e-7,rtol=0)
 with pytest.raises(ValueError):angular_reset(root,samples,.5)
 with pytest.raises(ValueError):angular_reset(root,samples+2)

def test_standing_quality_without_artificial_height_gain_and_exact_Swing_equivalence():
 h=torch.tensor([.168,.30,.42,.4,.20]);h0=torch.tensor([.168,.168,.168,.4,.4]);z=torch.zeros(5);b=torch.ones(5,dtype=torch.bool);f=~b
 args=(h,h0,torch.zeros(5,2),torch.ones(5,2)*10,z+.01,torch.zeros(5,6),torch.zeros(5,6),torch.zeros(5,6),torch.zeros(5,3),torch.zeros(5,3),z,f,b,f,f,f,f)
 old=reward(*args,reward_configuration=configuration(LIFT_RATE_VERSION));new=reward(*args,reward_configuration=configuration(REHEARSAL_VERSION))
 for field in ('raw','weighted_density','continuous_dt','events','total'):
  assert torch.equal(old[field][:3],new[field][:3])
 assert new['raw'][3,0].item()==1 and new['raw'][3,1].item()==1
 assert new['total'][3].item()==pytest.approx(.05)
 assert new['raw'][4,0]<.3 and new['total'][4]<new['total'][3]

def test_course_is_one_actor_no_teacher_and_no_normal_retention_stop():
 d=declaration(REHEARSAL_RECIPE);r=d['standing_rehearsal']
 assert r['environment_counts']=={'swing_candidate_from_historical_r1':32,'motion_native_normal':32}
 assert d['retained_families']==[] and r['normal_not_retention_stop']
 assert d['BC_coefficient']==0 and d['source_actor_sha256']=='7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470'
