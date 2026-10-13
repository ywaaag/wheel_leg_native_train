"""Real course adapter methods over explicit CPU physics/parent data fixture."""
FROZEN_TEST_SCOPE='PORTABLE'
import importlib,sys,types,torch,pytest

def test_real_course_targets_owner_history_and_partial_reset(monkeypatch,request):
 names=['native_stand.students.runtime','native_stand.students.course_runtime'];saved={k:sys.modules.get(k) for k in names}
 def cleanup():
  for k,v in saved.items():
   sys.modules.pop(k,None)
   if v is not None:sys.modules[k]=v
 request.addfinalizer(cleanup)
 from native_stand.students.recovery_task import Certificate
 class Base:
  def __init__(self,*a,**kw):
   self.num_envs=64;self.device='cpu';self.step_dt=.01;self.ids=list(range(6))
   root=torch.zeros(64,13);root[:,2]=.168;root[:,6]=1
   self.robot=types.SimpleNamespace(joint_names=list('abcdef'),data=types.SimpleNamespace(root_state_w=types.SimpleNamespace(torch=root),root_pos_w=types.SimpleNamespace(torch=root[:,:3]),joint_pos=types.SimpleNamespace(torch=torch.zeros(64,6)),joint_vel=types.SimpleNamespace(torch=torch.zeros(64,6))))
   self.fsm=types.SimpleNamespace(mode=torch.ones(64,dtype=torch.long)*2)
   self.initialization_checked=torch.ones(64,dtype=torch.bool);self.initial_pose_index=torch.zeros(64,dtype=torch.long)
   self.pose_initial_hold=torch.zeros(1,dtype=torch.bool);self.initial_leg_targets=torch.zeros(64,4);self.active_limits=torch.tensor([[-3.,3.]]*6)
   self.student_h0=torch.zeros(64);self.student_h0_valid=torch.zeros(64,dtype=torch.bool)
   for name,dim in [('reference',6),('student_previous_physical',6),('previous_action',6),('action',6),('raw_action',6),('executed_leg',4),('executed_wheel',2),('leg_target',4),('wheel_target',2),('control_jump',1),('wheel_control_jump',1),('stand_previous',6),('target_rate',6)]:setattr(self,name,torch.zeros(64,dim))
   self.episode_length_buf=torch.zeros(64,dtype=torch.long);self.reset_calls=0
   self.recovery_config={};self.family='x';self.split='train';self.pose_library={'poses':[]}
  def _motion_state(self):return torch.zeros(64,3),torch.tensor([[0.,-1.,0.]]*64)
  def _get_observations(self):return {'student_actor':torch.zeros(64,31),'student_critic':torch.zeros(64,40)}
  def _get_dones(self):return torch.zeros(64,dtype=torch.bool),torch.zeros(64,dtype=torch.bool)
  def _reset_idx(self,ids):self.reset_calls+=1;self.student_h0_valid[ids]=False;self.executed_leg[ids]=0;self.executed_wheel[ids]=0
 monkeypatch.setitem(sys.modules,'native_stand.students.runtime',types.SimpleNamespace(TrainingStudentEnv=Base))
 sys.modules.pop('native_stand.students.course_runtime',None);module=importlib.import_module('native_stand.students.course_runtime')
 from native_stand.students.course import initial_state,SWING
 s=initial_state();s.update(stage='B',prefix=180,previous_prefix=180)
 class Teacher(torch.nn.Module):
  def __init__(self,value):super().__init__();self.value=value;self.inputs=[]
  def forward(self,obs,stochastic_output=False):
   assert not stochastic_output;self.inputs.append({k:v.clone() for k,v in obs.items()});return torch.full((len(obs['policy']),6),self.value)
 teachers=[Teacher(.2),Teacher(.4)];env=module.CourseStudentEnv(course_configuration={'state':s},teacher_actors=teachers)
 env.teacher_intervals[:4]=torch.tensor([0,49,50,180]);env._get_observations()
 old_history=[x.clone() for x in env.teacher_histories];env._get_observations();assert all(torch.equal(a,b) for a,b in zip(old_history,env.teacher_histories))
 raw=torch.ones(64,6)*.1;action=env.compose_training_action(raw);root=env.robot.data.root_state_w.torch.clone();dq=env.robot.data.joint_vel.torch.clone()
 env._pre_physics_step(action)
 assert env.owner_pre[:4].tolist()==[1,1,2,3]
 torch.testing.assert_close(env.executed_leg[:4],torch.tensor([[.32]*4,[.32]*4,[.2]*4,[.15]*4]))
 torch.testing.assert_close(env.executed_wheel[:4],torch.tensor([[20.,20.],[20.,20.],[40.,40.],[10.,10.]]))
 assert env.reset_calls==0 and torch.equal(root,env.robot.data.root_state_w.torch) and torch.equal(dq,env.robot.data.joint_vel.torch)
 assert env.handoff_pulse[3] and env.student_h0[3]==.168 and env.rise_hold.age[3]==0
 env._get_dones();env.episode_length_buf+=1;env._get_observations()
 # Native teacher previous-action encodings are distinct and reflect physical targets.
 torch.testing.assert_close(env.teacher_obs[0]['policy'][2,-6:][[0,1,3,4]],torch.tensor([.125]*4))
 torch.testing.assert_close(env.teacher_obs[1]['policy'][2,-6:][[0,1,3,4]],torch.tensor([.4]*4))
 # A partial real reset clears only those teacher histories and clocks.
 monkeypatch.setattr('native_stand.students.requests.evaluation_recovery',lambda config,poses,f:config)
 unaffected=env.teacher_histories[0][2].clone();env._reset_idx(torch.tensor([1]));assert env.teacher_intervals[1]==0 and torch.equal(unaffected,env.teacher_histories[0][2])
 env._get_observations();assert not env.student_h0_valid[1]
