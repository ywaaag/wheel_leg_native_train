FROZEN_TEST_SCOPE='PROJECT_DATA'
from pathlib import Path
import copy,json,torch,pytest
from native_stand.students.data import sha
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/2026_10_11-13_11__recovery_mcu_v2_task_ppo_from_bc/spec.json'
def test_public_preparer_schema_model_and_missing_recipe_refusal():
 from native_stand.command_v6.config import validate
 from native_stand.command_v6.tools.model_factory import model
 from native_stand.students.training_recipe import declaration
 from native_stand.students.ppo import assemble
 from native_stand.students.training import observations
 from tensordict import TensorDict
 from native_stand.recovery.controlled_ppo import KEY
 s=json.loads(SPEC.read_text());assert validate(s)==[]
 bad=copy.deepcopy(s);bad.pop('student_training');assert any('PPO0 only' in e for e in validate(bad))
 a=model({},actor=True,spec=s);c=model({},actor=False,spec=s);assert a.mlp[0].in_features==31 and c.mlp[0].in_features==40
 obs=TensorDict({'student_actor':torch.zeros(4,31),'student_critic':torch.zeros(4,40),KEY:torch.ones(4,1,dtype=torch.bool)},batch_size=[4])
 rng=torch.get_rng_state().clone()
 with pytest.raises(ValueError,match='reward undefined'):assemble(s['source_checkpoint'],obs)
 torch.testing.assert_close(torch.get_rng_state(),rng)
 p=assemble(s['source_checkpoint'],obs,recipe=declaration());assert not p.optimizer.state and not p.actor.log_std.requires_grad
 assert p.critic.mlp[0].in_features==40 and p.gamma==.99 and p.lam==.95 and p.value_loss_coef==.5
 raw=p.act(obs);assert raw.shape==(4,6)
 torch.testing.assert_close(raw,p.transition.actions)
 torch.testing.assert_close(p.transition.actions_log_prob,p.actor.log_prob(obs['student_actor'],raw))

def test_identity_lineage_and_teacher_data_readonly():
 s=json.loads(SPEC.read_text());source=torch.load(s['source_checkpoint'],weights_only=False,map_location='cpu')
 assert sha(s['source_checkpoint'])=='7b3069362f13034d616a22a538856f10935132fed083b896b637c0bb82fdf470'
 manifest=ROOT/'isolated/student_mcu_v2_teachers_20261011/manifest.json';assert sha(manifest)==source['manifest_sha256']
 m=json.loads(manifest.read_text());assert m['RecoveryStudent']['sha256']==source['dataset_sha256']
 for p,h in m['files'].items():assert sha(p)==h
 assert all(sha(v['path'])==v['sha256'] for v in m['teachers'].values())
 assert s['student_training']['BC_coefficient']==0 and not s.get('receiver_training')
 assert s['recovery']['assessment']['retained_families']==[]

@pytest.mark.parametrize('recipe_version',['student_recovery_ppo_bc_v1','student_recovery_ppo_failure_zero_v2','student_recovery_ppo_lift_rate_v3'])
def test_real_checkpoint_save_load_recipe_binding(tmp_path,recipe_version):
 from native_stand.students.model import load
 from native_stand.students.training import save_checkpoint
 from native_stand.students.ppo import assemble
 from native_stand.students.training_recipe import declaration
 from tensordict import TensorDict
 from native_stand.recovery.controlled_ppo import KEY
 s=json.loads(SPEC.read_text());s['student_training']=declaration(recipe_version);s['reward']=s['student_training']['reward']
 (tmp_path/'source_snapshot').mkdir();(tmp_path/'source_snapshot/spec.json').write_text(json.dumps(s))
 _,source=load(s['source_checkpoint']);obs=TensorDict({'student_actor':torch.zeros(4,31),'student_critic':torch.zeros(4,40),KEY:torch.ones(4,1,dtype=torch.bool)},batch_size=[4])
 p=assemble(s['source_checkpoint'],obs,recipe=declaration(recipe_version));row=save_checkpoint(tmp_path,s,p.actor,p.critic,p,source,6)
 actor,cp=load(row['checkpoint']);assert cp['recipe_version']==recipe_version
 bad=copy.deepcopy(cp);bad['training_recipe']['BC_coefficient']=.1;torch.save(bad,tmp_path/'bad.pt')
 with pytest.raises(ValueError,match='recipe'):load(tmp_path/'bad.pt')

@pytest.mark.parametrize('reward_version',['student_recovery_reward_v1','student_recovery_reward_failure_zero_v2','student_recovery_reward_lift_rate_v3'])
def test_real_shared_env_reward_pre_reset_and_first_control_h0(monkeypatch,reward_version):
 import types,sys,importlib
 from native_stand.students.recovery_task import Certificate
 class Base:
  def _get_dones(self):
   c=self.rise_hold
   pulse,failed,done,_=c.observe(torch.tensor([.30]),torch.zeros(1,2),torch.zeros(1),torch.ones(1,2)*10,torch.ones(1)*.1,torch.zeros(1),torch.zeros(1),active=self.student_actor_valid,valid=self.initialization_checked,safety_failed=torch.zeros(1,dtype=torch.bool),fault=torch.zeros(1,dtype=torch.bool))
   self.recovery_snapshot=torch.zeros(1,39);self.recovery_snapshot[:,6]=.3;self.recovery_snapshot[:,10:12]=10;self.recovery_snapshot[:,13]=.1;self.recovery_snapshot[:,29]=1
   self.standing_snapshot=torch.zeros(1,10);return done,torch.zeros(1,dtype=torch.bool)
 monkeypatch.setitem(sys.modules,'native_stand.recovery.runtime',types.SimpleNamespace(RecoveryEnv=Base))
 sys.modules.pop('native_stand.students.runtime',None)
 T=importlib.import_module('native_stand.students.runtime').TrainingStudentEnv
 env=T.__new__(T);env.task_ready=True;env.device='cpu';env.num_envs=1;env.rise_hold=Certificate(1,'cpu');env.student_actor_valid=torch.tensor([True]);env.initialization_checked=torch.tensor([True]);env.student_h0=torch.tensor([.168]);env.student_previous_physical=torch.zeros(1,6);env.executed_leg=torch.zeros(1,4);env.executed_wheel=torch.zeros(1,2);env.vx=torch.zeros(1);env.vy=torch.zeros(1);env.yaw=torch.zeros(1);env.ids=list(range(6))
 from native_stand.students.recovery_task import configuration
 env.student_reward_configuration=configuration(reward_version)
 d=types.SimpleNamespace(root_state_w=types.SimpleNamespace(torch=torch.zeros(1,13)),joint_pos=types.SimpleNamespace(torch=torch.zeros(1,6)),joint_vel=types.SimpleNamespace(torch=torch.zeros(1,6)),applied_torque=types.SimpleNamespace(torch=torch.zeros(1,6)))
 env.robot=types.SimpleNamespace(data=d);env._motion_state=lambda:(torch.tensor([[6.,0.,0.]]),torch.tensor([[0.,-1.,0.]]))
 done,timeout=env._get_dones();assert not done.item() and not timeout.item()
 expected=.032 if reward_version=='student_recovery_reward_lift_rate_v3' else .05
 assert env._get_rewards().item()==pytest.approx(expected)
 # A later simulated reset must not erase the already-produced reward or terminal snapshot.
 env.student_h0[:]=0;env.executed_leg[:]=1
 assert env._get_rewards().item()==pytest.approx(expected) and env.student_event_snapshot.shape==(1,5)
 sys.modules.pop('native_stand.students.runtime',None)

def test_public_evaluation_boundary_exception_restores_rng_and_closes(monkeypatch,tmp_path):
 from native_stand.students import training
 import sys,types
 class Env:
  ids=list(range(6));num_envs=8;reference=torch.zeros(8,6);robot=types.SimpleNamespace(joint_names=['dummy'])
  closed=False
  def close(self):self.closed=True
 env=Env()
 def create(*a,**k):
  torch.rand(3)
  return env
 monkeypatch.setattr(training,'environment',create)
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.configure',types.SimpleNamespace(verify_asset_import=lambda s:{}))
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.control_readback',types.SimpleNamespace(verify=lambda e:{},verify_ground=lambda e,s:{}))
 def explode(*a,**k):
  torch.rand(9)
  raise ValueError('owned test exception')
 monkeypatch.setattr(training,'rollout',explode)
 actor=torch.nn.Linear(1,1);rng=torch.get_rng_state().clone()
 with pytest.raises(ValueError,match='owned test'):
  training.evaluate_cases({'asset_sha256':'a'},tmp_path,actor,[{'case_id':'exception_fixture','kind':'student','role':'RecoveryStudent','family':'swing'}])
 assert env.closed and torch.equal(rng,torch.get_rng_state())
