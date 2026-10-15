FROZEN_TEST_SCOPE='PORTABLE'
import math
import torch
import pytest
from native_stand.students.motion_reward_audit import audit
from native_stand.students.motion_tracking_reward import configuration
from native_stand.students.motion_statistics import MotionStatistics
from native_stand.students.performance import RolloutCounts
from native_stand.command_v6.tools.metrics_tensorboard import row_scalars

def test_actual_reward_curves_are_finite_symmetric_correct_direction_and_rng_neutral():
 rng=torch.get_rng_state().clone();result=audit(configuration())
 assert torch.equal(rng,torch.get_rng_state())
 for row in result['curves']:
  assert all(math.isfinite(row[k]) for k in ('weighted_density','dt_contribution','state_error_derivative'))
  assert row['dt_contribution']==pytest.approx(row['weighted_density']*.01)
  assert row['state_error_derivative']<=1e-12
 assert len(result['warnings'])==3
 widths=result['proposed_width_comparison']['curves']
 wide=next(r for r in widths if r['error_mps']==1 and r['denominator_mps_squared']==1)
 narrow=next(r for r in widths if r['error_mps']==1 and r['denominator_mps_squared']==.04)
 assert abs(wide['state_error_derivative'])>.7 and abs(narrow['state_error_derivative'])<1e-8
 with pytest.raises(ValueError):audit({**configuration(),'dt':.02})

def test_named_tensorboard_rewards_preserve_real_zero_and_do_not_invent_missing_dt():
 row={'update':1,'reward_fields':['support','cost'],'reward_raw_mean':[1,0], 'reward_dt_mean':[.005,-.002]}
 tags=dict(row_scalars(row));assert tags['reward/raw/cost']==0
 assert tags['reward/total_per_step']==pytest.approx(.003)
 assert not any(k.startswith('reward/weighted_density') for k in tags)
 tags=dict(row_scalars({**row,'reward_dt_s':.01}));assert tags['reward/weighted_density/cost']==pytest.approx(-.2)
 assert not any(k.startswith('reward/raw/') for k in dict(row_scalars({**row,'reward_raw_mean':[1]})))

def test_cohort_scopes_use_pre_reset_state_and_separate_parking():
 stats=MotionStatistics([[0,0],[.5,0]],'cpu',schedule_s=[.5,1,25.5,1],parking_s=2)
 state=torch.zeros(2,39);state[:,7]=torch.tensor([.2,.4]);state[:,6]=.34;state[:,10:12]=10
 posture=torch.zeros(2,10);posture[:,2]=.32;posture[:,3]=.30;posture[1,1]=.1
 geometry=torch.zeros(2,13);geometry[:,7]=-1;geometry[:,5]=.02
 index=torch.tensor([0,1]);valid=torch.ones(2,dtype=torch.bool);command=torch.tensor([[0.,0.,.34],[.5,0.,.34]])
 stats.observe(index,valid,torch.tensor([10.,29.]),command,state,posture,geometry)
 state.zero_();posture.zero_();geometry.zero_()
 result=stats.export()
 assert result['hold']['cohort_0']['mean']['vx_mps']==pytest.approx(.2)
 assert result['hold']['cohort_1']['mean'] is None
 assert result['parking']['cohort_1']['mean']['vx_mae_mps']==pytest.approx(.1)
 assert result['parking']['cohort_1']['mean']['wheel_offset_abs_m']==pytest.approx(.02)
 assert result['controlled']['cohort_0']['vx_direction_rate'] is None
 assert result['controlled']['cohort_1']['vx_direction_rate']==1

def test_duration_uses_explicit_episode_clock_instead_of_fsm_clock():
 counts=RolloutCounts(1,1,'cpu');s=torch.zeros(1,39);s[:,0]=1.2
 yes=torch.ones(1,dtype=torch.bool);events=torch.zeros(1,3);posture=torch.zeros(1,10)
 counts.observe(yes,torch.ones(1),yes,s,events,posture,episode_duration_s=torch.tensor([30.]))
 assert counts.export()[1]==[30.]
