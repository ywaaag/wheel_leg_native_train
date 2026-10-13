"""Versioned0.34m/symmetry certificate, reward and task continuation contracts."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy
import numpy as np
import pytest
import torch
from native_stand.students import standing
from native_stand.students.standing_certificate import StandingCertificate,score
from native_stand.students.recovery_task import configuration,reward,SYMMETRY_VERSION,SLIDING_VERSION

def episode(height=.34,mirror=0.,samples=1020):
 state=torch.zeros(samples,39);state[:,0]=torch.arange(1,samples+1)*.01;state[:,6]=height;state[:,10:12]=10;state[:,13]=.1;state[:,29]=1;state[:,31]=1;state[:,32]=3
 p=torch.zeros(samples,10);c=torch.zeros(samples,54);c[:,0]=mirror/2;c[:,3]=mirror/2
 return state,p,c

def online(state,control):
 clock=StandingCertificate(1,'cpu');flag=torch.ones(1,dtype=torch.bool);no=~flag;events=[]
 for i,s in enumerate(state):
  clock.set_joint(control[i:i+1,:6][:,[0,1,3,4]])
  success,failed,end,fault=clock.observe(s[6:7],torch.zeros(1,2),s[15:16],s[10:12][None],s[13:14],s[12:13],s[17:18],active=flag,valid=flag,safety_failed=no,fault=no)
  events.append(bool(success[0]))
 return clock,events

@pytest.mark.parametrize('height,mirror,accepted',[(.34,0.,True),(.40,0.,False),(.34,.08,False),(.375,0.,False)])
def test_online_offline_certificate_and_failure_discrimination(height,mirror,accepted):
 s,p,c=episode(height,mirror);clock,events=online(s,c)
 r=score(s,p,c,torch.ones(len(s),dtype=torch.bool),policy_time_s=torch.arange(1,len(s)+1,dtype=torch.float64)*.01,first_episode_valid=torch.ones(len(s),dtype=torch.bool))
 assert r['accepted'] is accepted and any(events) is accepted
 assert sum(events)<=1
 if accepted:assert r['hold_index_half_open']==[20,1020] and clock.count[0]==1000

def test_incomplete_or_invalid_time_cannot_certify():
 s,p,c=episode(samples=1019)
 r=score(s,p,c,torch.ones(len(s),dtype=torch.bool),policy_time_s=torch.zeros(len(s)),first_episode_valid=torch.ones(len(s),dtype=torch.bool))
 assert not r['accepted'] and 'invalid_time_axis' in r['failed_checks']
 r=score(s,p,c,torch.ones(len(s),dtype=torch.bool),policy_time_s=torch.arange(1,len(s)+1)*.01,first_episode_valid=torch.ones(len(s),dtype=torch.bool))
 assert not r['accepted'] and not r['hold_complete']

def values(h=.34,e=.4):
 z=torch.zeros(1);q=torch.tensor([[e/2,e/2,e/2,-e/2]])
 return dict(height=z+h,h0=z+.4,angles=torch.zeros(1,2),contacts=torch.ones(1,2)*10,clearance=z+.1,torque=torch.zeros(1,6),previous_targets=torch.zeros(1,6),executed_targets=torch.zeros(1,6),angular_body=torch.zeros(1,3),velocity_native=torch.zeros(1,3),yaw=z,entered=torch.ones(1,dtype=torch.bool),controlled=torch.ones(1,dtype=torch.bool),fault=torch.zeros(1,dtype=torch.bool),entry_event=torch.zeros(1,dtype=torch.bool),success_event=torch.zeros(1,dtype=torch.bool),failure_event=torch.zeros(1,dtype=torch.bool),active_leg_q=q)

def test_reward_no_mirror_plateau_and_height034_preferred_to040():
 cfg=configuration(SYMMETRY_VERSION);a=reward(**values(e=.4),reward_configuration=cfg);b=reward(**values(e=.8),reward_configuration=cfg)
 assert b['motion_mirror_dt'][0,1]<a['motion_mirror_dt'][0,1]
 old_a=reward(**values(e=.4),reward_configuration=configuration(SLIDING_VERSION));old_b=reward(**values(e=.8),reward_configuration=configuration(SLIDING_VERSION))
 torch.testing.assert_close(old_a['motion_mirror_dt'][:,1],old_b['motion_mirror_dt'][:,1])
 assert reward(**values(h=.34,e=0.),reward_configuration=cfg)['total'][0]>reward(**values(h=.40,e=0.),reward_configuration=cfg)['total'][0]
 v=values();v['controlled'][:]=False;assert reward(**v,reward_configuration=cfg)['total'][0]==0
 torch.testing.assert_close(a['continuous_dt'],a['weighted_density']*.01)
 # Six non-height terms remain original v7. Only slot0 and mirror are changed.
 torch.testing.assert_close(a['raw'][:,1:],old_a['raw'][:,1:])
 torch.testing.assert_close(a['events'],old_a['events'])

def metric(n=0,error=.4):
 return dict(joint_passed=n,physical_passed=n,stable_except_limit=24,complete_windows=24,entry=24,hold_prefix_median_s=10.,mirror_mae_rad=error,limit_fraction=.3)

def test_unlimited_task_finite_blocks_min_learning_and_bounded_rollback():
 assert standing.plan()['total_update_limit'] is None and standing.plan()['formal_block_updates']==300
 c={'update':300,'checkpoint':'candidate','sha256':'a'*64,'standing_metrics':metric()}
 book={'standing_stagnant_blocks':3,'standing_best_metrics':metric(),'blocks':[{'formal_updates':300}]}
 assert standing.decide(book,[c])['action']=='CONTINUE'
 book['blocks']=[{'formal_updates':5100}];book['standing_stagnant_blocks']=3
 assert standing.decide(book,[c])['action']=='ROLLBACK'
 book['standing_stagnant_blocks']=3
 assert standing.decide(book,[c])['action']=='STOP'

def test_no_32_condition_certification_no_task_acceptance():
 candidates=[{'update':100,'standing_metrics':metric(24)},{'update':200,'standing_metrics':metric(24)}]
 book={};assert standing.decide(book,candidates)['action']=='CONTINUE'
 candidates.append({'update':300,'standing_metrics':metric(24),'standing_certification32_pass':True})
 assert standing.decide({},candidates)['action']=='ACCEPT_STANDING'
 failed={'update':300,'standing_metrics':metric()}
 b={'standing_confirmations':1};standing.decide(b,[candidates[0],failed]);assert b['standing_confirmations']==0

def test_recipe_and_actor_height_command_uses_034_without_dimension_change():
 from native_stand.students.training_recipe import declaration
 from native_stand.students.mcu_interface import task
 r=declaration(standing.RECIPE,source_actor_sha256='a'*64)
 assert r['target_height_m']==.34 and r['BC_coefficient']==0 and r['reward']['standing_height']['target_m']==.34
 assert task('Recovery',torch.tensor([[0.,0.,.34]]))[0,2]==pytest.approx(.68)
 assert r['reward']['weak_mirror']['squared_cap'] is None

def test_new_recipe_real_PPO_factory_and_fault_full_joint_capture(tmp_path):
 from native_stand.students.model import Student
 from native_stand.students.training_recipe import declaration
 from native_stand.students.ppo import assemble
 from native_stand.recovery.controlled_ppo import KEY
 from tensordict import TensorDict
 from native_stand.students.data import sha
 from native_stand.students.fault_evidence import capture
 path=tmp_path/'bc.pt';torch.save({'interface_version':'multiskill_mcu_v2','role':'RecoveryStudent','actor':Student(version='multiskill_mcu_v2').state_dict()},path)
 obs=TensorDict({'student_actor':torch.zeros(2,31),'student_critic':torch.zeros(2,40),KEY:torch.ones(2,1,dtype=torch.bool)},batch_size=[2])
 ppo=assemble(path,obs,recipe=declaration(standing.RECIPE,source_actor_sha256=sha(path)))
 assert ppo.actor(obs).shape==(2,6) and ppo.critic(obs).shape==(2,1)
 assert not ppo.optimizer.state and not ppo.actor.log_std.requires_grad
 state=torch.zeros(2,39);state[1,4]=1
 fault=capture(state,torch.zeros(2),{'joint_outside':torch.tensor([False,True])},{'q':torch.arange(12).reshape(2,6),'limits':torch.zeros(2,6,2)})
 assert fault['env_ids'].tolist()==[1] and fault['joint_evidence_q'].tolist()==[[6,7,8,9,10,11]]


def test_height_or_mirror_failure_never_receives_success_event_after_full_window():
 s,p,c=episode(.34,.2);clock,events=online(s,c)
 assert clock.hold_window_complete[0] and clock.task_failure[0] and not any(events)
 clock.reset(torch.tensor([0]));assert not clock.mirror_history.any() and not clock.height_error_sum.any()

def test_engineering_smoke_does_not_require_formal24():
 from native_stand.students.standing import training_phase_metrics
 import pytest
 assert training_phase_metrics([{}]*8,'smoke') is None
 with pytest.raises(ValueError,match='requires24'):training_phase_metrics([{}]*8,'formal')
 with pytest.raises(ValueError,match='unsupported'):training_phase_metrics([],'source_eval')
