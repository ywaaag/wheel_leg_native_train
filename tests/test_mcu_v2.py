FROZEN_TEST_SCOPE='PORTABLE'
import types,importlib,sys
import pytest,torch
from native_stand.students import mcu_interface as m
from native_stand.students.model import Student

def test_fields_units_privilege_and_physical_roundtrip():
 q=torch.tensor([[.1,.2,.3,.4,.5,.6]]);ref=torch.zeros_like(q)
 x=m.encode(torch.ones(1,3)*4,torch.tensor([[0.,-1.,0.]]),q,torch.ones_like(q)*20,torch.tensor([[.3,.6,.9,1.2]]),torch.tensor([[25.,-50.]]),ref,'Recovery',torch.tensor([[0.,0.,.4]]))
 assert x.shape==(1,31);torch.testing.assert_close(x[0,6:10],q[0,list(m.LEGS)]/1.5)
 assert x[0,0:3].tolist()==[1,1,1] and x[0,10:16].tolist()==[1]*6
 torch.testing.assert_close(x[0,16:22],torch.tensor([.2,.4,.6,.8,.25,-.5]))
 assert x[0,22:].tolist()==pytest.approx([0,0,.8,0,1,0,1,0,0])
 label=m.labels(torch.tensor([[.3,.6,.9,1.2]]),torch.tensor([[25.,-50.]]),ref)
 target=m.targets(label,ref);torch.testing.assert_close(target['leg_executed'],x[:,16:20]*1.5);torch.testing.assert_close(target['wheel_executed'],x[:,20:22]*100)
 c=m.critic_input(x,torch.tensor([.4]),torch.tensor([[1.,2.,3.]]),torch.tensor([[100.,200.]]),torch.tensor([2.5]),torch.tensor([.2]),torch.tensor([10.]))
 assert c.shape==(1,40);assert c[0,-9:].tolist()==pytest.approx([.4,1,2,3,1,2,1,1,1])
 with pytest.raises(ValueError):m.labels(torch.ones(1,4)*1.6,torch.zeros(1,2),ref)

def test_factory_network_distribution_and_no_implicit_dimensions():
 from native_stand.command_v6.tools.model_factory import model
 a=model({},actor=True,spec={'interface_version':m.VERSION});c=model({},actor=False,spec={'interface_version':m.VERSION})
 assert [v.out_features for v in a.mlp if isinstance(v,torch.nn.Linear)]==[128,64,32,6]
 assert sum(p.numel() for p in a.mlp.parameters())==14630
 assert sum(v.in_features*v.out_features for v in a.mlp if isinstance(v,torch.nn.Linear))==14400
 assert c.mlp[0].in_features==40
 x=torch.randn(5,31);raw=a(x,stochastic_output=True)
 torch.testing.assert_close(a.get_output_log_prob(raw),a.log_prob(x,raw))
 assert (a.mean(x).abs()<=1).all()
 torch.testing.assert_close(a.log_std.exp(),torch.tensor([.05/1.5,.05/1.5,.02,.05/1.5,.05/1.5,.02]))
 assert model({},actor=True,spec={'interface_version':'multiskill_student_v1'}).mlp[0].in_features==1182
 with pytest.raises(ValueError):model({},actor=True,spec={'interface_version':'unknown'})

def test_clock_boundary_and_nonfinite():
 clock=m.PolicyClock(2);clock.check(torch.zeros(2));clock.check(torch.zeros(2));clock.check(torch.ones(2)*.01)
 with pytest.raises(ValueError):clock.check(torch.ones(2)*.03)
 clock.reset(torch.tensor([0]));clock.check(torch.tensor([0.,.02]))
 with pytest.raises(ValueError):clock.check(torch.tensor([float('nan'),.03]))

def test_runtime_actual_limit_cache_partial_reset_and_no_history(monkeypatch):
 class Base:
  def _get_observations(self):return {}
  def _reset_idx(self,ids):
   self.executed_leg[ids]=.12;self.executed_wheel[ids]=0
 monkeypatch.setitem(sys.modules,'native_stand.recovery.runtime',types.SimpleNamespace(RecoveryEnv=Base))
 monkeypatch.setitem(sys.modules,'isaaclab.utils.math',types.SimpleNamespace(quat_apply_inverse=lambda q,v:v))
 sys.modules.pop('native_stand.students.runtime',None)
 Env=importlib.import_module('native_stand.students.runtime').StudentEnv
 from native_stand.students.interface import History
 from native_stand.recovery.domain import Mode
 from native_stand.recovery.handoff_clock import HandoffClock
 from native_stand.students.protocol import declaration
 env=Env.__new__(Env);env.num_envs=2;env.device='cpu';env.student_ready=True;env.student_role='RecoveryStudent';env.student_command_height=.40;env.interface_version=m.VERSION;env.step_dt=.01
 env.fsm=types.SimpleNamespace(mode=torch.tensor([int(Mode.RECOVERY)]*2));env.initialization_checked=torch.ones(2,dtype=torch.bool)
 for name,shape in [('reference',(2,6)),('action',(2,6)),('previous_action',(2,6)),('raw_action',(2,6)),('leg_target',(2,4)),('wheel_target',(2,2)),('executed_leg',(2,4)),('executed_wheel',(2,2)),('stand_previous',(2,6)),('target_rate',(2,6)),('control_jump',(2,)),('wheel_control_jump',(2,))]:setattr(env,name,torch.zeros(shape))
 env.pose_initial_hold=torch.tensor([False]);env.initial_pose_index=torch.zeros(2,dtype=torch.long);env.initial_leg_targets=torch.zeros(2,4);env.active_limits=torch.tensor([[-.15,.15]]*6)
 env.rise_hold=HandoffClock(2,'cpu',declaration());env.student_history=History(2);env.mcu_clock=m.PolicyClock(2);env.student_clock=torch.zeros(2,dtype=torch.float64);env.episode_length_buf=torch.zeros(2,dtype=torch.long)
 d=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=torch.zeros(2,6)),joint_vel=types.SimpleNamespace(torch=torch.zeros(2,6)),root_quat_w=types.SimpleNamespace(torch=torch.zeros(2,4)),root_lin_vel_w=types.SimpleNamespace(torch=torch.zeros(2,3)))
 env.robot=types.SimpleNamespace(data=d);env.ids=list(range(6));env.root_height=torch.ones(2)*.4;env.contact_force=torch.ones(2,2)*10;env._motion_state=lambda:(torch.zeros(2,3),torch.tensor([[0.,-1.,0.]]).repeat(2,1))
 env._pre_physics_step(torch.ones(2,6)*.2);obs=env._get_observations()
 assert obs['student_actor'].shape==(2,31) and obs['student_critic'].shape==(2,40)
 torch.testing.assert_close(obs['student_actor'][:,16:20],torch.ones(2,4)*.1)
 torch.testing.assert_close(obs['student_actor'][:,20:22],torch.ones(2,2)*.2)
 assert env.student_history.valid.sum()==0
 env._reset_idx(torch.tensor([0]));env.episode_length_buf[0]=0;obs=env._get_observations()
 torch.testing.assert_close(obs['student_actor'][0,16:20],torch.ones(4)*(.12/1.5))
 torch.testing.assert_close(obs['student_actor'][1,16:20],torch.ones(4)*.1)
 assert torch.equal(env._get_rewards(),torch.zeros(2))
 sys.modules.pop('native_stand.students.runtime',None)

def test_public_snapshot_keeps_student_sources_for_replay(tmp_path):
 import json,hashlib
 from native_stand.command_v6.train import _snapshot
 spec=tmp_path/'spec.json';spec.write_text(json.dumps({'interface_version':'multiskill_mcu_v2','task':'cpu_snapshot'}))
 output=tmp_path/'output';output.mkdir();identities=_snapshot(output,spec)
 for name in ['student_mcu_interface.py','student_model.py','student_runtime.py','student_evaluator.py','model_factory.py']:
  path=output/'source_snapshot'/name
  assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==identities[name]
