FROZEN_TEST_SCOPE='PORTABLE'
import copy,pytest,torch,numpy as np
from native_stand.students.course import *
from native_stand.students.recovery_task import configuration,reward,SLIDING_VERSION,SMOOTH_VERSION,SUFFIX_VERSION

def m(passed=0,entry=0,prefix=0.,sat=.4,other=True):return dict(passed=passed,entry=entry,prefix_median_s=prefix,limit_fraction=sat,wheel_delta_rms=9.,all_other_passed=other)
def test_infinite_task_finite_blocks_and_standing_exit():
 p=plan();assert p['total_update_limit'] is None and p['formal_block_updates']==300
 s=initial_state();s,d=advance(s,m(sat=.3),formal_updates=300,cumulative_update=312,best={'checkpoint':'best'},latest={'checkpoint':'last'},source_metrics=m())
 assert s['stage']=='A' and d['action']=='CONTINUE'
 s,d=advance(s,m(sat=.2),formal_updates=300,cumulative_update=612,best={'checkpoint':'best'},latest={},source_metrics=m())
 assert s['stage']=='B' and s['prefix']==180 and d['action']=='NEW_REWARD'
 s,d=advance(initial_state(),m(sat=.4),formal_updates=300,cumulative_update=312,best={},latest={},source_metrics=m())
 assert s['stage']=='B'

def test_confirmations_fail_pass_fail_and_update_separation():
 s=initial_state()
 s=observe_confirmation(s,m(),100);assert s['confirmation_streak']==0
 s=observe_confirmation(s,m(24),200);assert s['confirmation_streak']==1
 assert observe_confirmation(s,m(24),200)['confirmation_streak']==1
 s=observe_confirmation(s,m(),300);assert s['confirmation_streak']==0
 s=observe_confirmation(s,m(24),400);s=observe_confirmation(s,m(24),500);assert s['confirmation_streak']==2

def test_fixed_groups_final_no_teacher_and_boundaries():
 s=initial_state();s.update(stage='B',prefix=65,previous_prefix=80)
 g=slot_groups(s);assert [sum(x['group']==k for x in g) for k in ['current','previous','normal','unassisted']]==[32,16,8,8]
 for prefix in [0,10,25,40,50,65,80,100,120,150,180]:
  steps=torch.tensor([prefix-1,prefix,prefix+1]).clamp(min=0);owner,valid=controlled_owners(torch.zeros(3,dtype=torch.bool),torch.ones(3,dtype=torch.bool),steps,torch.full_like(steps,prefix))
  assert valid.tolist()==([False,True,True] if prefix else [True]*3)
 s['stage']='CONSOLIDATE';assert all(x['prefix']==0 for x in slot_groups(s));assert sum(x['family']==SWING for x in slot_groups(s))==56

def inputs(entered=True,controlled=True):
 return [torch.tensor([.4]),torch.tensor([.168]),torch.zeros(1,2),torch.ones(1,2)*10,torch.ones(1),torch.zeros(1,6),torch.zeros(1,6),torch.tensor([[0.,0.,10.,0.,0.,-10.]]),torch.zeros(1,3),torch.tensor([[1.,0.,0.]]),torch.zeros(1),torch.tensor([entered]),torch.tensor([controlled]),torch.tensor([False]),torch.tensor([False]),torch.tensor([False]),torch.tensor([False])]
def test_smooth_post_entry_only_dt_once_dynamic_gating():
 q=torch.tensor([[.2,.2,.1,.1]])
 for entered in [False,True]:
  a=inputs(entered);old=reward(*a,reward_configuration=configuration(SLIDING_VERSION),active_leg_q=q);new=reward(*a,reward_configuration=configuration(SMOOTH_VERSION),active_leg_q=q)
  torch.testing.assert_close(new['total']-old['total'],torch.tensor([-.002 if entered else 0.]))
  dynamic=reward(*a,reward_configuration=configuration(SUFFIX_VERSION),active_leg_q=q)
  if not entered:assert dynamic['motion_mirror_dt'].abs().sum()==0
  else:torch.testing.assert_close(dynamic['total'],new['total'])
 a=inputs(controlled=False);assert reward(*a,reward_configuration=configuration(SUFFIX_VERSION),active_leg_q=q)['total'].item()==0

def test_stagnation_resume_then_finite_equal_prefix_rollback():
 s=initial_state();s.update(stage='B',prefix=180,previous_prefix=180)
 for _ in range(4):s,d=advance(s,m(),formal_updates=300,cumulative_update=s['cumulative_updates']+300,best={'checkpoint':'x'},latest={'checkpoint':'y'})
 assert d['action']=='ROLLBACK'
 for _ in range(4):s,d=advance(s,m(),formal_updates=300,cumulative_update=s['cumulative_updates']+300,best={'checkpoint':'x'},latest={'checkpoint':'y'})
 assert d['action']=='STOP'

def test_resume_rng_and_adam_exact_in_memory():
 from native_stand.students.model import Student
 from native_stand.students.resume import rng_state,restore
 from native_stand.students.training_recipe import declaration
 from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
 from rsl_rl.storage import RolloutStorage
 from tensordict import TensorDict
 obs=TensorDict({'student_actor':torch.zeros(8,31),'student_critic':torch.zeros(8,40),KEY:torch.ones(8,1,dtype=torch.bool)},batch_size=[8])
 def make():
  a=Student(True,'multiskill_mcu_v2');a.log_std.requires_grad_(False);c=Student(False,'multiskill_mcu_v2');return ControlledPPO(a,c,RolloutStorage('rl',8,1,obs,[6],device='cpu'),num_mini_batches=2,num_learning_epochs=1,device='cpu',schedule='fixed',use_clipped_value_loss=False)
 p=make()
 with torch.inference_mode():p.act(obs);p.process_env_step(obs,torch.arange(8).float(),torch.zeros(8,dtype=torch.bool),{});p.compute_returns(obs)
 p.update();rec=declaration(SMOOTH_RECIPE,source_actor_sha256='a'*64)
 d=dict(course_resume_version='student_full_training_resume_v1',recipe_version=rec['version'],interface_version='multiskill_mcu_v2',fixed_std=True,actor=copy.deepcopy(p.actor.state_dict()),critic=copy.deepcopy(p.critic.state_dict()),optimizer=copy.deepcopy(p.optimizer.state_dict()),training_rng=rng_state(),cumulative_update=300,recipe_updates=300)
 expected=torch.rand(3);q=make();r=restore(q,d,rec);assert torch.equal(torch.rand(3),expected)
 assert r['warmup_repeated'] is False and all(torch.equal(v,q.actor.state_dict()[k]) for k,v in p.actor.state_dict().items())
 assert all(torch.equal(v,q.critic.state_dict()[k]) for k,v in p.critic.state_dict().items())
 for k,x in p.optimizer.state_dict()['state'].items():
  for field,v in x.items():torch.testing.assert_close(v,q.optimizer.state_dict()['state'][k][field])

def test_all_invalid_no_actor_or_critic_adam_step_and_real_timeline():
 from native_stand.students.model import Student
 from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
 from rsl_rl.storage import RolloutStorage
 from tensordict import TensorDict
 obs=TensorDict({'student_actor':torch.zeros(8,31),'student_critic':torch.zeros(8,40),KEY:torch.ones(8,1,dtype=torch.bool)},batch_size=[8])
 a=Student(True,'multiskill_mcu_v2');c=Student(False,'multiskill_mcu_v2');p=ControlledPPO(a,c,RolloutStorage('rl',8,2,obs,[6],device='cpu'),num_mini_batches=2,num_learning_epochs=1,device='cpu',schedule='fixed',use_clipped_value_loss=False);p.critic_control_only=True
 def collect(valid):
  obs[KEY][:]=valid
  with torch.inference_mode():
   for _ in range(2):p.act(obs);p.process_env_step(obs,torch.arange(8).float(),torch.zeros(8,dtype=torch.bool),{})
   p.compute_returns(obs)
 collect(True);p.update();before=copy.deepcopy(p.optimizer.state_dict());pa=copy.deepcopy(a.state_dict());pc=copy.deepcopy(c.state_dict())
 collect(False);ret=p.storage.returns.clone();assert ret.shape==(2,8,1)
 p.update();assert p.mask_summary['critic_optimizer_steps']==p.mask_summary['actor_optimizer_steps']==0
 assert all(torch.equal(v,a.state_dict()[k]) for k,v in pa.items()) and all(torch.equal(v,c.state_dict()[k]) for k,v in pc.items())
 for k,x in before['state'].items():
  for field,v in x.items():torch.testing.assert_close(v,p.optimizer.state_dict()['state'][k][field])

def test_two_midpoints_share_original_interval_and_single_rollback():
 s=initial_state();s.update(stage='B',prefix=100,previous_prefix=120,interval_id='120:100',base_index=3)
 checkpoint={'checkpoint':'best'};latest={'checkpoint':'latest'}
 for _ in range(4):s,d=advance(s,m(),formal_updates=300,cumulative_update=s['cumulative_updates']+300,best=checkpoint,latest=latest)
 assert d['action']=='ROLLBACK' and s['prefix']==110 and s['return_stack']==[100]
 for _ in range(4):s,d=advance(s,m(),formal_updates=300,cumulative_update=s['cumulative_updates']+300,best=checkpoint,latest=latest)
 assert d['action']=='SPLIT' and s['prefix']==115 and s['insertions']['120:100']==2
 for _ in range(4):s,d=advance(s,m(),formal_updates=300,cumulative_update=s['cumulative_updates']+300,best=checkpoint,latest=latest)
 assert d['action']=='STOP' and s['rollback_counts']['120:100']==1

def test_suffix_certificate_and_selection_never_accepts_assisted_swing():
 from native_stand.students.training import choose
 rows=[dict(accepted=True,entry_index=19,valid_hold_prefix_s=10.)]*24
 result=choose([{'checkpoint':'suffix','update':100,'per_env':rows,'teacher_prefix_intervals':50}])
 assert result['accepted_candidate'] is None and result['accepted_suffix_candidate']['checkpoint']=='suffix'
 result=choose([{'checkpoint':'zero','update':100,'per_env':rows,'teacher_prefix_intervals':0}])
 assert result['accepted_candidate']['checkpoint']=='zero'


def test_wheel_stats_reset_breaks_frequency_and_request_clipped_applied():
 from native_stand.students.course_statistics import WheelStatistics
 s=WheelStatistics(2,'cpu');v=torch.tensor([True,False]);done=torch.tensor([False,False])
 a=torch.ones(2,2);s.observe(a,torch.zeros_like(a),a*12,a*5.5,a*5.5,v,done)
 s.observe(-a,a,-a*12,-a*5.5,-a*5.5,v,torch.tensor([True,False]))
 s.observe(a,-a,a*12,a*5.5,a*5.5,v,done);r=s.result()
 assert r['wheel_torque_sign_changes']==[1.,1.] and r['wheel_limit_fraction']==[1.,1.]
 assert r['requested_clipped_applied_torque_rms_nm'][0]==[12.,12.]
