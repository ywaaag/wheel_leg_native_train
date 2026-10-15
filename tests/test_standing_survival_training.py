FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.standing_survival_task import Clock,score,bootstrap_reward,rank

def test_real_clock_timeout_does_not_mean_certificate_or_fall():
 c=Clock(2,'cpu');o=torch.ones(2);yes=o.bool();no=~yes
 c.set_joint(torch.zeros(2,4));c.set_offset(o*.05);c.set_velocity(torch.zeros(2,3))
 for _ in range(2999):
  success,failure,end,fault=c.observe(o*.34,torch.tensor([[.2,0.]]).expand(2,-1),o*.2,torch.ones(2,2)*20,o*.1,o*0,o*0,active=yes,valid=yes,safety_failed=no,fault=no)
  assert not end.any()
 success,failure,end,fault=c.observe(o*.34,torch.tensor([[.2,0.]]).expand(2,-1),o*.2,torch.ones(2,2)*20,o*.1,o*0,o*0,active=yes,valid=yes,safety_failed=no,fault=no)
 assert end.all() and c.normal_timeout.all() and not success.any() and not failure.any()
 c.reset(torch.tensor([0]));assert c.episode.steps.tolist()==[0,3000]

def test_terminal_bootstrap_uses_terminal_value_not_reset_or_previous():
 rewards=torch.tensor([1.,1.,1.]);terminated=torch.tensor([False,True,False]);truncated=torch.tensor([True,True,False])
 result=bootstrap_reward(rewards,terminated,truncated,torch.tensor([10.,20.,30.]),gamma=.99)
 torch.testing.assert_close(result,torch.tensor([10.9,1.,1.]))
 assert torch.equal(rewards,torch.ones(3))

def test_scoring_requires_complete_window_and_joint_quality():
 s=torch.zeros(3000,39);s[:,6]=.34;s[:,10:12]=20;s[:,13]=.1;s[:,29]=1
 p=torch.zeros(3000,10);p[:,2:4]=.3;g=torch.zeros(3000,13);g[:,7]=-1
 yes=torch.ones(3000,dtype=torch.bool);world=torch.zeros(3000,3)
 good=score(s,p,g,controlled=yes,valid=yes,world_velocity=world);assert good['accepted'] and good['survival_passed']
 s[:,7]=2.;world[:,0]=2.;rolling=score(s,p,g,controlled=yes,valid=yes,world_velocity=world)
 assert rolling['survival_passed'] and not rolling['accepted'] and 'horizontal_speed' in rolling['failed_checks']
 assert rank({'update':100,'per_env':[good]})>rank({'update':200,'per_env':[rolling]})
 short=score(s[:-1],p[:-1],g[:-1],controlled=yes[:-1],valid=yes[:-1],world_velocity=world[:-1]);assert not short['accepted']

def test_v14_recipe_keeps_actor_physics_and_declares_no_teacher():
 from native_stand.students.training_recipe import declaration,validate_instance
 from native_stand.students.standing_survival_task import RECIPE,SOURCE
 recipe=declaration(RECIPE);assert recipe['environment_seconds']==31.52
 assert recipe['source_teacher_baseline'] is False and recipe['critic_privileged_version']=='standing_privileged49_v1'
 assert validate_instance(recipe,SOURCE)==recipe

def test_real_ppo_storage_accepts_named_reward_terminal_bootstrap(tmp_path):
 from native_stand.students.model import Student
 from native_stand.students.ppo import assemble
 from native_stand.students.training_recipe import declaration
 from native_stand.students.standing_survival_task import RECIPE
 from native_stand.recovery.controlled_ppo import KEY
 from tensordict import TensorDict
 actor=Student(version='multiskill_mcu_v2');path=tmp_path/'actor.pt'
 torch.save({'interface_version':'multiskill_mcu_v2','role':'RecoveryStudent','actor':actor.state_dict()},path)
 recipe=declaration(RECIPE)
 obs=TensorDict({'student_actor':torch.zeros(2,31),'student_critic':torch.zeros(2,49),KEY:torch.ones(2,1,dtype=torch.bool)},batch_size=[2])
 ppo=assemble(path,obs,steps_per_env=2,recipe=recipe)
 ppo.act(obs)
 rewards=bootstrap_reward(torch.ones(2),torch.tensor([False,True]),torch.tensor([True,False]),torch.tensor([10.,20.]),gamma=ppo.gamma)
 ppo.process_env_step(obs,rewards,torch.ones(2,dtype=torch.bool),{})
 torch.testing.assert_close(ppo.storage.rewards[0].squeeze(-1),torch.tensor([10.9,1.]))

def test_runtime_terminal_capture_precedes_reset_and_legacy_reward(monkeypatch):
 import sys,types,importlib
 from native_stand.students.standing_survival_reward import configuration
 class Base:
  def _get_dones(self):return torch.zeros(2,dtype=torch.bool),torch.zeros(2,dtype=torch.bool)
 monkeypatch.setitem(sys.modules,'native_stand.recovery.runtime',types.SimpleNamespace(RecoveryEnv=Base))
 monkeypatch.setitem(sys.modules,'isaaclab.utils.math',types.SimpleNamespace(quat_apply_inverse=lambda q,v:v))
 sys.modules.pop('native_stand.students.runtime',None)
 try:
  Env=importlib.import_module('native_stand.students.runtime').TrainingStudentEnv
  e=Env.__new__(Env);e.task_ready=True;e.num_envs=2;e.device='cpu';e.ids=list(range(6));e.wheel_body_ids=[0,1]
  e.student_reward_configuration=configuration();e.rise_hold=Clock(2,'cpu')
  e.rise_hold.normal_timeout=torch.tensor([True,False]);e.student_actor_valid=torch.ones(2,dtype=torch.bool)
  e.executed_leg=torch.zeros(2,4);e.executed_wheel=torch.zeros(2,2);e.student_previous_physical=torch.zeros(2,6)
  e.recovery_snapshot=torch.zeros(2,39);e.recovery_snapshot[:,6]=.34;e.recovery_snapshot[:,10:12]=20;e.recovery_snapshot[:,13]=.1;e.recovery_snapshot[:,29]=1
  e.standing_snapshot=torch.zeros(2,10);e.standing_snapshot[:,2:4]=.30;e.wheel_geometry_snapshot=torch.zeros(2,13);e.wheel_geometry_snapshot[:,7]=-1;e.episode_result_snapshot=torch.zeros(2,5)
  e.vx=e.vy=e.yaw=torch.zeros(2)
  values={'root_state_w':torch.zeros(2,13),'root_lin_vel_w':torch.zeros(2,3),'joint_pos':torch.zeros(2,6),'joint_vel':torch.zeros(2,6),
   'body_pos_w':torch.zeros(2,2,3),'root_pos_w':torch.zeros(2,3),'root_quat_w':torch.zeros(2,4),'applied_torque':torch.zeros(2,6)}
  e.robot=types.SimpleNamespace(data=types.SimpleNamespace(**{k:types.SimpleNamespace(torch=v) for k,v in values.items()}))
  e._motion_state=lambda:(torch.zeros(2,3),torch.tensor([[0.,-1.,0.]]).expand(2,-1))
  terminal=torch.ones(2,49)*7;e._get_observations=lambda:{'student_critic':terminal}
  terminated,truncated=e._get_dones();terminal.zero_()
  assert not terminated.any() and truncated.tolist()==[True,False]
  assert (e.student_terminal_critic==7).all() and e.student_reward_result['raw'].shape==(2,10)
  torch.testing.assert_close(e.student_reward_result['total'],torch.ones(2)*.085)
 finally:sys.modules.pop('native_stand.students.runtime',None)

def test_source_cannot_be_accepted_as_new_result():
 from native_stand.students.training import choose
 env={'accepted':True,'survival_passed':True,'controlled_seconds':30.,'quality_metrics':{
  'horizontal_speed_p95_mps':0.,'posture_worst_mean_rad':0.,'wheel_offset_mae_m':0.,'mirror_worst_mae_rad':0.}}
 def c(u):return {'standing_survival_quality':True,'update':u,'checkpoint':str(u),'per_env':[env.copy() for _ in range(24)]}
 assert choose([c(0),c(100)])['accepted_candidate'] is None
 assert choose([c(0),c(100),c(200)])['accepted_candidate']['update']>0

def test_smoke_engineering_does_not_require_standing_skill(tmp_path):
 import json,hashlib
 from native_stand.students.training_evidence import smoke_certificate
 spec={'source_sha256':'1'*64,'budget':{'smoke_updates':26},'student_training':{'version':'student_standing_survival_quality_v14'}}
 (tmp_path/'source_snapshot').mkdir();text=json.dumps(spec);(tmp_path/'source_snapshot/spec.json').write_text(text)
 manifest={'spec_sha256':hashlib.sha256(text.encode()).hexdigest(),'source_sha256':'1'*64}
 progress={'actual_updates':26,'actor_parameters_changed':True,'checkpoint_roundtrip_verified':True}
 terminal={'actual_updates':26,'status':'COMPLETED','failure':None}
 for name,data in [('manifest.json',manifest),('progress.json',progress),('terminal_report.json',terminal)]:
  (tmp_path/name).write_text(json.dumps(data))
 rows=[]
 for u in range(1,27):
  rows.append({'update':u,'controlled_samples':8000,'episode_completed':1 if u==26 else 0,
   'normal_timeout_count':1 if u==26 else 0,'episode_duration_max_s':30. if u==26 else None,
   'reward_fields':['test']*10,'nonzero_rewards':8000,'actor_changed_this_update':u>5,
   'critic_changed_this_update':True,'std_unchanged':True,'BC_loss':0.,'BC_gradient_norm':None,'BC_updates':0,
   'actor_update_scope':{'valid_actor_samples':8000,'invalid_actor_samples':192,'actor_optimizer_steps':16 if u>5 else 0}})
 def save(): (tmp_path/'metrics.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 save();assert smoke_certificate(tmp_path,spec)['status']=='PASSED'
 rows[-1]['normal_timeout_count']=0;save()
 result=smoke_certificate(tmp_path,spec)
 assert result['status']=='PASSED' and result['schema_version']==2
 assert result['capability_evidence']['accepted'] is False
 assert result['capability_evidence']['ppo_timeout_bootstrap_observed'] is False
 assert result['capability_evidence']['normal_timeout_count']==0
 progress['actor_parameters_changed']=False
 (tmp_path/'progress.json').write_text(json.dumps(progress))
 assert smoke_certificate(tmp_path,spec)['status']=='FAILED'
 progress['actor_parameters_changed']=True
 (tmp_path/'progress.json').write_text(json.dumps(progress))
 for r in rows:r['episode_completed']=0
 save();assert 'real episode completion/reset missing' in smoke_certificate(tmp_path,spec)['errors']

def test_online_tail_and_offline_quality_are_identical_and_world_speed_required():
 from native_stand.students.standing_survival_task import quality_features
 s=torch.zeros(3000,39);s[:,6]=.34;s[:,10:12]=20;s[:,13]=.1;s[:,29]=1
 p=torch.zeros(3000,10);p[:,2:4]=.3;g=torch.zeros(3000,13);g[:,7]=-1;world=torch.zeros(3000,3)
 c=Clock(1,'cpu');c.episode.steps[:]=3000;c.normal_timeout=torch.ones(1,dtype=torch.bool)
 c.quality_tail[0]=quality_features(s[-1000:],p[-1000:],g[-1000:],world[-1000:])
 c.record_quality(s[-1:],p[-1:],g[-1:],world[-1:],torch.ones(1,dtype=torch.bool))
 offline=score(s,p,g,controlled=torch.ones(3000,dtype=torch.bool),valid=torch.ones(3000,dtype=torch.bool),world_velocity=world)
 assert bool(c.certificate_passed[0])==offline['accepted']==True
 # Body-plane proxy can be zero while world-horizontal motion is nonzero.
 world[:,0]=2.;bad=score(s,p,g,controlled=torch.ones(3000,dtype=torch.bool),valid=torch.ones(3000,dtype=torch.bool),world_velocity=world)
 c.quality_tail[0]=quality_features(s[-1000:],p[-1000:],g[-1000:],world[-1000:])
 c.record_quality(s[-1:],p[-1:],g[-1:],world[-1:],torch.ones(1,dtype=torch.bool))
 assert bool(c.certificate_passed[0])==bad['accepted']==False
