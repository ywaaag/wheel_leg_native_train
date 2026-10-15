"""Portable real-network/optimizer and pure privilege/reward contract checks."""
FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.standing_zero_privileged import contract,critic_input,configuration,RECIPE,SOURCE

def test_privileged_units_and_no_actor_mutation():
 base=torch.zeros(2,40);base[:,0]=1
 c=critic_input(base,torch.tensor([.2,-.1]),torch.tensor([[40.,40.,5.5,40.,40.,5.5]]).expand(2,-1),torch.ones(2,2)*10,torch.ones(2)*.6)
 assert c.shape==(2,49) and torch.equal(c[:,:40],base)
 assert torch.equal(c[:,41:47],torch.ones(2,6))
 assert torch.allclose(c[:,47:],torch.zeros(2,2),atol=1e-7)
 assert contract()['actor_dim']==31 and contract()['critic_dim']==49
 with pytest.raises(ValueError):critic_input(base,torch.zeros(2),torch.zeros(2,6),torch.zeros(2,2),torch.zeros(2),radius=.07)

def test_reward_only_longitudinal_scale_changes():
 from native_stand.students.standing_alignment import configuration as old,huber
 a=old();b=configuration();assert b['standing_alignment']['velocity_scale']==[.1,.02,.03]
 b['version']=a['version'];b['standing_alignment']['velocity_scale']=a['standing_alignment']['velocity_scale']
 assert b==a
 assert -.5*huber(torch.tensor(1.)/.1)<-.5*huber(torch.tensor(1.)/.5)

def test_real_critic_optimizer_and_legacy_shape():
 from native_stand.students.model import Student
 actor=Student(version='multiskill_mcu_v2');critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='standing_privileged49_v1')
 assert Student(False,version='multiskill_mcu_v2').mlp[0].in_features==40
 x=torch.randn(8,49);x.requires_grad_();loss=critic(x).square().mean();loss.backward()
 assert x.grad[:,40:].abs().sum()>0 and all(p.grad is None for p in actor.parameters())
 opt=torch.optim.Adam(critic.parameters(),lr=3e-5);before=critic.mlp[0].weight.clone();opt.step()
 assert not torch.equal(before,critic.mlp[0].weight)

def test_versioned_recipe_and_required_final_matrix():
 from native_stand.students.training_recipe import declaration,final_assessment_cases
 d=declaration(RECIPE);assert d['source_actor_sha256']==SOURCE and d['warmup_updates_per_phase']==5
 assert d['critic_privileged_version']=='standing_privileged49_v1'
 assert len(final_assessment_cases(d,[{'case_id':'normal_native'},{'case_id':'normal_yaw10'}]))==4
 with pytest.raises(ValueError):declaration(RECIPE,'0'*64)

def test_public_factory_uses_declared_critic_extension():
 from native_stand.command_v6.tools.model_factory import model
 spec={'interface_version':'multiskill_mcu_v2','student_training':{'critic_privileged_version':'standing_privileged49_v1'}}
 assert model({},actor=False,spec=spec).mlp[0].in_features==49
 assert model({},actor=True,spec=spec).mlp[0].in_features==31

def test_runtime_reads_actual_effort_and_world_vertical_before_action(monkeypatch):
 import sys,types,importlib
 class Base:
  def _get_observations(self):return {}
 monkeypatch.setitem(sys.modules,'native_stand.recovery.runtime',types.SimpleNamespace(RecoveryEnv=Base))
 monkeypatch.setitem(sys.modules,'isaaclab.utils.math',types.SimpleNamespace(quat_apply_inverse=lambda q,v:v))
 sys.modules.pop('native_stand.students.runtime',None)
 try:
  Env=importlib.import_module('native_stand.students.runtime').StudentEnv
  from native_stand.students.interface import History
  from native_stand.students.mcu_interface import PolicyClock
  e=Env.__new__(Env);e.student_ready=True;e.interface_version='multiskill_mcu_v2';e.critic_privileged_version='standing_privileged49_v1'
  e.num_envs=2;e.student_role='RecoveryStudent';e.student_command_height=.34;e.step_dt=.01
  e.student_history=History(2);e.mcu_clock=PolicyClock(2);e.episode_length_buf=torch.zeros(2,dtype=torch.long)
  e.fsm=types.SimpleNamespace(mode=torch.ones(2,dtype=torch.long));e.ids=list(range(6))
  e.reference=torch.zeros(2,6);e.executed_leg=torch.zeros(2,4);e.executed_wheel=torch.zeros(2,2)
  e.root_height=torch.ones(2)*.34;e.contact_force=torch.ones(2,2)*20
  e.rise_hold=types.SimpleNamespace(dwell=torch.zeros(2),age=torch.zeros(2),count=torch.zeros(2))
  e.recovery_config={'wheel_radius_m':.06}
  values={'joint_pos':torch.zeros(2,6),'joint_vel':torch.zeros(2,6),'root_quat_w':torch.zeros(2,4),
   'root_lin_vel_w':torch.tensor([[1.,2.,3.],[0.,0.,.2]]),'applied_torque':torch.tensor([[40.,40.,5.5,40.,40.,5.5]]).expand(2,-1)}
  e.robot=types.SimpleNamespace(data=types.SimpleNamespace(**{k:types.SimpleNamespace(torch=v) for k,v in values.items()}))
  e._motion_state=lambda:(torch.zeros(2,3),torch.tensor([[0.,-1.,0.]]).expand(2,-1))
  o=e._get_observations();assert o['student_actor'].shape==(2,31) and o['student_critic'].shape==(2,49)
  torch.testing.assert_close(o['student_critic'][:,40],torch.tensor([3.,.2]))
  torch.testing.assert_close(o['student_critic'][:,41:47],torch.ones(2,6))
 finally:sys.modules.pop('native_stand.students.runtime',None)
