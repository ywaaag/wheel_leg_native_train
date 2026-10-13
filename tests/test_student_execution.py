FROZEN_TEST_SCOPE='PORTABLE'
import copy,types,torch,pytest
from native_stand.students.evaluator import rollout
from native_stand.students.protocol import score
from native_stand.students.model import Student
from native_stand.students.interface import contract

class ScriptedEnv:
    """Protocol fixture only: no dynamics/ability claim. Pre-reset rows survive."""
    num_envs=8;device='cpu'
    def __init__(self,fail=False):
        self.fail=fail;self.family='original';self.split='original';self.initialization_checked=torch.ones(8,dtype=torch.bool)
        self.fsm=types.SimpleNamespace(mode=torch.ones(8,dtype=torch.long));self.robot=types.SimpleNamespace(data=types.SimpleNamespace())
        d=self.robot.data
        for name,size in [('root_state_w',13),('joint_pos',6),('joint_vel',6)]:setattr(d,name,types.SimpleNamespace(torch=torch.zeros(8,size)))
        self.executed_leg=torch.zeros(8,4);self.executed_wheel=torch.zeros(8,2)
    def select_initial_family(self,family,split):self.family=family;self.split=split
    def reset(self):self.steps=0;return {'student_actor':torch.zeros(8,1182),'student_critic':torch.zeros(8,1191)},{}
    def step(self,action):
        self.steps+=1;s=torch.zeros(8,39);s[:,6]=.4;s[:,10:12]=10;s[:,13]=.1;s[:,29]=1
        self.recovery_snapshot=s;self.standing_snapshot=torch.zeros(8,10);self.recovery_control_snapshot=torch.zeros(8,54)
        self.wheel_geometry_snapshot=torch.zeros(8,13);self.student_root_post=torch.zeros(8,13);self.recovery_cause_snapshot=torch.zeros(8,6,dtype=torch.bool)
        done=torch.zeros(8,dtype=torch.bool)
        if self.fail and self.steps==10:done[4]=True;s[4,3]=1
        if self.steps>=1020:done[:]=True
        return {'student_actor':torch.zeros(8,1182),'student_critic':torch.zeros(8,1191)},torch.zeros(8),done,torch.zeros_like(done),{}

def row():return dict(seed=1,kind='student',role='RecoveryStudent',family='swing',yaw_rad=0.,seconds=13.52)

def test_autonomous_rollout_full_window_denominator_and_cleanup():
    actor=Student();actor.train();env=ScriptedEnv(fail=True);rng=torch.get_rng_state().clone()
    payload,arrays=rollout(env,actor,row())
    assert payload['scored_envs']==8 and payload['passed_envs']==7
    assert not payload['per_env'][4]['accepted'];assert arrays['first_episode_valid'][:,4].sum()==10
    assert (arrays['controller']==3).all();assert arrays['actor_input'].shape[-1]==1182
    assert env.family=='original' and actor.training;assert torch.equal(rng,torch.get_rng_state())

def test_exception_restores_mode_rng_and_temporary_configuration():
 actor=Student();env=ScriptedEnv();state=torch.get_rng_state().clone()
 with pytest.raises(TimeoutError):rollout(env,actor,row(),stop=lambda:True)
 assert actor.training and env.family=='original' and not hasattr(env,'student_yaw_amplitude')
 assert torch.equal(state,torch.get_rng_state())

def test_student_protocol_timestamp_invalid_samples_and_deadline():
 s=torch.zeros(1020,39);s[:,6]=.4;s[:,10:12]=10;s[:,13]=.1;s[:,29]=1;p=torch.zeros(1020,10);c=torch.ones(1020,dtype=torch.bool);t=torch.arange(1,1021)*.01
 assert score(s,p,c,policy_time_s=t)['accepted']
 assert not score(s,p,c,policy_time_s=torch.zeros_like(t))['accepted']
 bad=s.clone();bad[100,29]=0;assert not score(bad,p,c,policy_time_s=t)['accepted']
 bad=s.clone();bad[100,31]=1;assert not score(bad,p,c,policy_time_s=t)['accepted']
 assert not score(s[:-1],p[:-1],c[:-1],policy_time_s=t[:-1])['accepted']

def test_factory_strict_version_and_critic_input_consumed():
 from native_stand.command_v6.tools.model_factory import model
 from native_stand.command_v6.config import validate
 obs={'student_actor':torch.zeros(2,1182),'student_critic':torch.zeros(2,1191)}
 spec={'interface_version':'multiskill_student_v1'}
 actor=model(obs,actor=True,spec=spec);critic=model(obs,actor=False,spec=spec)
 assert critic.mlp[0].in_features==1191 and actor.mlp[0].in_features==1182
 before=critic(obs);obs['student_critic'][:,-9:]=1;assert not torch.equal(before,critic(obs))
 with pytest.raises(ValueError):model(obs,actor=True,spec={'interface_version':'anything'})
 assert validate({'interface_version':'anything'})==['Unknown interface version']
 raw=actor(obs,stochastic_output=True);torch.testing.assert_close(actor.get_output_log_prob(raw),actor.log_prob(obs['student_actor'],raw))
 assert actor.output_distribution_params[0].shape==(2,6)

def test_real_runtime_methods_student_only_scale_and_privileged_history(monkeypatch):
 import sys,importlib
 class Base:
  def _get_observations(self):return {}
  def _reset_idx(self,ids):pass
 monkeypatch.setitem(sys.modules,'native_stand.recovery.runtime',types.SimpleNamespace(RecoveryEnv=Base))
 monkeypatch.setitem(sys.modules,'isaaclab.utils.math',types.SimpleNamespace(quat_apply_inverse=lambda q,v:v))
 sys.modules.pop('native_stand.students.runtime',None)
 runtime=importlib.import_module('native_stand.students.runtime');Env=runtime.StudentEnv
 from native_stand.students.interface import History
 from native_stand.recovery.domain import Mode
 from native_stand.students.protocol import declaration
 from native_stand.recovery.handoff_clock import HandoffClock
 env=Env.__new__(Env);env.num_envs=2;env.device='cpu';env.student_ready=True;env.student_role='RecoveryStudent';env.step_dt=.01
 env.fsm=types.SimpleNamespace(mode=torch.tensor([int(Mode.RECOVERY),int(Mode.INITIALIZING)]));env.initialization_checked=torch.tensor([True,False])
 for name,shape in [('reference',(2,6)),('action',(2,6)),('previous_action',(2,6)),('raw_action',(2,6)),('leg_target',(2,4)),('wheel_target',(2,2)),('executed_leg',(2,4)),('executed_wheel',(2,2)),('stand_previous',(2,6)),('target_rate',(2,6)),('control_jump',(2,)),('wheel_control_jump',(2,))]:setattr(env,name,torch.zeros(shape))
 env.pose_initial_hold=torch.tensor([False]);env.initial_pose_index=torch.zeros(2,dtype=torch.long);env.initial_leg_targets=torch.zeros(2,4)
 env.active_limits=torch.tensor([[-3.,3.]]*6);env.rise_hold=HandoffClock(2,'cpu',declaration())
 env.student_history=History(2);env.student_clock=torch.zeros(2,dtype=torch.float64);env.episode_length_buf=torch.zeros(2,dtype=torch.long)
 d=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=torch.zeros(2,6)),joint_vel=types.SimpleNamespace(torch=torch.zeros(2,6)),root_quat_w=types.SimpleNamespace(torch=torch.zeros(2,4)),root_lin_vel_w=types.SimpleNamespace(torch=torch.tensor([[1.,2.,3.],[0,0,0]])))
 env.robot=types.SimpleNamespace(data=d);env.ids=list(range(6));env.root_height=torch.tensor([.4,.17]);env.contact_force=torch.ones(2,2)*10
 env._motion_state=lambda:(torch.zeros(2,3),torch.tensor([[0.,-1.,0.]]).repeat(2,1))
 env._pre_physics_step(torch.ones(2,6)*.2)
 torch.testing.assert_close(env.leg_target,torch.ones(2,4)*.3)
 assert env.wheel_target[:,0].tolist()==[20.,0.];assert env.student_actor_valid.tolist()==[True,False]
 obs=env._get_observations();assert obs['student_actor'].shape==(2,1182) and obs['student_critic'].shape==(2,1191)
 assert obs['student_critic'][0,-8:-5].tolist()==[-3.,-1.,2.]
 assert obs['student_actor'][:,-9:-5].tolist()==[[0,1,0,0]]*2
 env._get_observations();assert env.student_history.valid.sum(1).tolist()==[1,1]
 env.episode_length_buf+=1;env._get_observations();assert env.student_history.valid.sum(1).tolist()==[2,2]
 env._reset_idx(torch.tensor([0]));assert env.student_history.valid.sum(1).tolist()==[0,2]
 sys.modules.pop('native_stand.students.runtime',None)

def test_interrupted_owned_rollout_keeps_partial_raw_without_success():
 env=ScriptedEnv();actor=Student()
 with pytest.raises(TimeoutError) as caught:rollout(env,actor,row(),stop=lambda:env.steps>=7)
 arrays=caught.value.student_partial_arrays
 assert len(arrays['state'])==7 and len(arrays['first_episode_valid'])==7
 assert not hasattr(env,'student_trace_capture')

def test_phase_balanced_physical_group_loss():
 from native_stand.students.distill import loss
 target=torch.zeros(2,6);prediction=target.clone();prediction[:,(0,1,3,4)]=.1/1.5;prediction[:,(2,5)]=10/100
 assert float(loss(prediction,target))==pytest.approx(2.)
