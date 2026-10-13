"""Real RecoveryEnv constructor/_get_dones with a CPU physics-data fixture."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy,importlib,sys,types,torch,pytest
from native_stand.recovery.domain import Mode
from native_stand.students.recovery_task import Certificate

@pytest.mark.parametrize('student_class',['TrainingStudentEnv','StudentEnv'])
@pytest.mark.parametrize('reward_version',['student_recovery_reward_v1','student_recovery_reward_failure_zero_v2','student_recovery_reward_lift_rate_v3','student_recovery_reward_standing_rehearsal_v4','student_recovery_reward_motion_mirror_v6','student_recovery_reward_velocity_huber_v7','student_recovery_reward_dynamic_suffix_v9','student_recovery_reward_dynamic_suffix_contact_v10','student_recovery_reward_standing_mirror_huber_v11'])
def test_new_clock_parent_constructor_and_pre_reset_state(monkeypatch,student_class,request,reward_version):
 imported_names=('native_stand.command_v6.runtime.env','native_stand.recovery.runtime','native_stand.students.runtime','native_stand.recovery.handoff_runtime','native_stand.students.handoff_runtime')
 saved_modules={name:sys.modules.get(name) for name in imported_names}
 def restore():
  for name,old in saved_modules.items():
   sys.modules.pop(name,None)
   if old is not None:sys.modules[name]=old
 request.addfinalizer(restore)
 n=2
 joint_names=['left_hip','left_active','left_wheel','right_hip','right_active','right_wheel']
 class Robot:
  joint_names=joint_names if False else ['left_hip','left_active','left_wheel','right_hip','right_active','right_wheel']
  def __init__(self):
   root=torch.zeros(n,13);root[:,2]=.168;root[:,6]=1
   self.data=types.SimpleNamespace(root_state_w=types.SimpleNamespace(torch=root),root_pos_w=types.SimpleNamespace(torch=root[:,:3]),root_quat_w=types.SimpleNamespace(torch=root[:,3:7]),root_lin_vel_w=types.SimpleNamespace(torch=root[:,7:10]),root_ang_vel_w=types.SimpleNamespace(torch=root[:,10:13]),joint_pos=types.SimpleNamespace(torch=torch.zeros(n,6)),joint_vel=types.SimpleNamespace(torch=torch.zeros(n,6)),body_pos_w=types.SimpleNamespace(torch=torch.zeros(n,2,3)),applied_torque=types.SimpleNamespace(torch=torch.zeros(n,6)))
  def write_root_pose_to_sim_index(self,root_pose,env_ids):self.data.root_state_w.torch[env_ids,:7]=root_pose
  def write_root_velocity_to_sim_index(self,root_velocity,env_ids):self.data.root_state_w.torch[env_ids,7:13]=root_velocity
  def write_joint_position_to_sim_index(self,position,env_ids):self.data.joint_pos.torch[env_ids]=position
  def write_joint_velocity_to_sim_index(self,velocity,env_ids):self.data.joint_vel.torch[env_ids]=velocity
 class Base:
  def __init__(self,cfg,**kwargs):
   self.num_envs=n;self.device='cpu';self.cfg=cfg;self.step_dt=.01;self.robot=Robot();self.ids=list(range(6));self.body_ids={};self.wheel_body_ids=[0,1];self.wheel_sensor_ids=[0,1]
   self.scene=types.SimpleNamespace(env_origins=torch.zeros(n,3));self.sensor=types.SimpleNamespace(body_names=['left_wheel','right_wheel'],data=types.SimpleNamespace(net_forces_w=types.SimpleNamespace(torch=torch.tensor([[[0.,0.,10.],[0.,0.,10.]]]*n))))
   for name,shape in [('history',(n,125)),('reference',(n,6)),('action',(n,6)),('previous_action',(n,6)),('raw_action',(n,6)),('leg_target',(n,4)),('wheel_target',(n,2)),('effort',(n,6)),('effort_pre',(n,6)),('closure_each',(n,4)),('contact_force',(n,2))]:setattr(self,name,torch.zeros(shape))
   self.command=torch.zeros(n,3);self.history_needs_init=torch.zeros(n,dtype=torch.bool)
   self.reset_count=torch.zeros(n,dtype=torch.long);self.episode_length_buf=torch.zeros(n,dtype=torch.long);self.joint_limit_clip_fraction=torch.zeros(n)
  def _reset_idx(self,ids):self.reset_count[ids]+=1
  def _closure(self):pass
  def _motion_state(self):
   self.root_height=self.robot.data.root_pos_w.torch[:,2];self.up=torch.ones(n);self.vx=torch.zeros(n);self.vy=torch.zeros(n);self.yaw=torch.zeros(n)
   return torch.zeros(n,3),torch.tensor([[0.,-1.,0.]]*n)
  def _get_observations(self):return {}
 # Only the Isaac/physical base is a tensor data fixture. Both shared
 # CommandEnv and RecoveryEnv constructors/_get_dones below are real.
 monkeypatch.setitem(sys.modules,'native_stand.env',types.SimpleNamespace(NativeStandEnv=Base,NativeStandCfg=object))
 monkeypatch.setitem(sys.modules,'isaaclab.utils',types.SimpleNamespace(configclass=lambda cls:cls))
 sys.modules.pop('native_stand.command_v6.runtime.env',None)
 monkeypatch.setitem(sys.modules,'isaaclab.utils.math',types.SimpleNamespace(quat_apply=lambda q,v:v,quat_apply_inverse=lambda q,v:v))
 sys.modules.pop('native_stand.recovery.runtime',None);sys.modules.pop('native_stand.students.runtime',None)
 Runtime=importlib.import_module('native_stand.students.runtime')
 # Actual immutable requirements reduced to one legal data fixture, not a dynamics proof.
 gate={'height_m':[.30,.42],'tilt_max_rad':.18,'angular_speed_max_rad_s':1.,'linear_speed_max_mps':1.,'joint_speed_max_rad_s':10.,'joint_abs_max_rad':3.1,'dual_contact_min_n':2.,'chassis_clearance_min_m':0.,'target_jump_max_rad':3.,'wheel_target_jump_max_rad_s':200.,'stand_vx_abs_max_mps':.5,'stand_vy_abs_max_mps':.02,'stand_yaw_abs_max_rad_s':.03,'stand_excursion_max_m':10.}
 initial={'low_root_height_m':[.12,.25],'chassis_clearance_m':[0.,.15],'severe_penetration_m':.005,'settle_min_s':.2,'settle_dwell_s':.2,'settle_max_s':1.,'settled_linear_speed_max_mps':.05,'settled_angular_speed_max_rad_s':.1,'settled_joint_speed_max_rad_s':.3,'tilt_max_rad':.15}
 cfg=types.SimpleNamespace(native_execution_mode='evaluation',closure_fault_m=.005,minimum_up_cos=.5,episode_curriculum=None)
 poses=[{'pose_id':'swing','family':'swing','split':split,'offline_valid':True,'root_height_m':.168,'root_quaternion_xyzw':[0,0,0,1],'joint_pos':{},'initialization_control':'passive_settle'} for split in ['train','holdout']]
 library={'poses':poses,'collision_geometry':[],'joint_limits_rad':{j:[-3.1,3.1] for j in joint_names}}
 recovery={'fsm':{'timeout_s':13.52,'gate_dwell_s':.5,'blend_s':.3,'verify_s':2.,'success_mode':'autonomous_hold'},'active_family':'swing','gate':gate,'initialization':initial,'contacts':{'allowed_candidate':['.*wheel.*'],'restricted_force_max_n':200.},'sampling':{'version':'family_weights_v1','family_weights':{'swing':1.}},'assessment':{'families':['swing'],'retained_families':[]}}
 # Teacher control in the real source-evaluation path also installs its clock
 # after the parent constructor; no legacy rising_task is present here.
 sys.modules.pop('native_stand.recovery.handoff_runtime',None)
 Handoff=importlib.import_module('native_stand.recovery.handoff_runtime').HandoffEnv
 shared={'stage':{'commands':[[0,0]],'weights':[1.]},'command_height':.36,'reward_config':{},'schedule_s':[1,1,1,1]}
 # Exercise the real shared reset/sampler for the normal baseline, not a mocked rollout.
 from native_stand.students.requests import evaluation_recovery
 normal_library=copy.deepcopy(library)
 normal_library['poses'].append({**copy.deepcopy(poses[1]),'pose_id':'normal','family':'motion_native_normal','root_height_m':.4,'initialization_control':'direct_zero_reset'})
 normal_config=evaluation_recovery(recovery,normal_library['poses'],'motion_native_normal')
 normal=Handoff(cfg,**shared,recovery_config=normal_config,pose_library=normal_library,stand_policy=torch.nn.Linear(1,1))
 normal._geometry_gaps=lambda:(torch.ones(n,1)*.01,torch.ones(n)*.01)
 normal.select_initial_family('motion_native_normal','holdout');normal._reset_idx(torch.arange(n))
 assert normal.family=='motion_native_normal'
 torch.testing.assert_close(normal.robot.data.root_state_w.torch[:,2],torch.full((n,),.4))
 if reward_version=='student_recovery_reward_standing_rehearsal_v4':
  from native_stand.students.training_recipe import declaration,REHEARSAL_RECIPE
  from native_stand.students.recovery_task import configuration
  standing=Runtime.TrainingStudentEnv(cfg,**shared,recovery_config=normal_config,pose_library=normal_library,stand_policy=torch.nn.Linear(1,1),student_reward_configuration=configuration(reward_version),standing_rehearsal_configuration=declaration(REHEARSAL_RECIPE)['standing_rehearsal'])
  standing._geometry_gaps=lambda:(torch.ones(n,1)*.01,torch.ones(n)*.01)
  standing.select_initial_family('motion_native_normal','holdout');standing._reset_idx(torch.tensor([0]))
  assert standing.robot.data.root_state_w.torch[0,10:].abs().max()<=.25
  assert standing.robot.data.root_state_w.torch[0,10:].abs().max()>0
  assert standing.initialization_checked[0] and standing.fsm.mode[0]==int(Mode.RECOVERY)
 teacher=Handoff(cfg,**shared,recovery_config=copy.deepcopy(recovery),pose_library=library,stand_policy=torch.nn.Linear(1,1))
 assert teacher.task_phase.shape==(n,)
 teacher._geometry_gaps=lambda:(torch.ones(n,1)*.01,torch.ones(n)*.01)
 teacher._reset_idx(torch.arange(n));teacher.fsm.mode[:]=int(Mode.RECOVERY);teacher.initialization_checked[:]=True
 teacher.configure_case({'switch_s':.5,'kind':'recovery_prefix'})
 teacher._pre_physics_step(torch.full((n,6),.2))
 torch.testing.assert_close(teacher.executed_leg,torch.full((n,4),.32))
 done,timeout=teacher._get_dones()
 assert not done.any() and not timeout.any()
 assert teacher.handoff_controller.tolist()==[1,1]
 assert teacher.handoff_joint_q_post.shape==(n,6)
 sys.modules.pop('native_stand.students.handoff_runtime',None)
 Probe=importlib.import_module('native_stand.students.handoff_runtime').StudentMotionProbeEnv
 probe=Probe(cfg,**shared,recovery_config=copy.deepcopy(recovery),pose_library=library,stand_policy=torch.nn.Linear(1,1))
 probe._geometry_gaps=lambda:(torch.ones(n,1)*.01,torch.ones(n)*.01)
 probe._reset_idx(torch.arange(n));probe.fsm.mode[:]=int(Mode.RECOVERY);probe.initialization_checked[:]=True
 probe.configure_case({'switch_s':.10,'kind':'student_prefix_motion'})
 for _ in range(10):probe._pre_physics_step(torch.full((n,6),.2))
 assert probe.controller.tolist()==[3,3] and probe.executed_prefix.tolist()==[10,10]
 torch.testing.assert_close(probe.executed_leg,torch.full((n,4),.3))
 done,timeout=probe._get_dones();assert not done.any() and not timeout.any()
 probe._pre_physics_step(torch.full((n,6),.2))
 assert probe.controller.tolist()==[2,2]
 torch.testing.assert_close(probe.executed_leg,torch.full((n,4),.1))
 # First Motion interval: no reset/root/joint velocity writes at the switch.
 before=probe.robot.data.root_state_w.torch.clone();done,timeout=probe._get_dones()
 assert torch.equal(before,probe.robot.data.root_state_w.torch)
 assert probe.handoff_motion_age.tolist()==pytest.approx([.01,.01])
 from native_stand.students.recovery_task import configuration
 training_options={'student_reward_configuration':configuration(reward_version)} if student_class=='TrainingStudentEnv' else {}
 if reward_version=='student_recovery_reward_standing_mirror_huber_v11':training_options['student_command_height']=.34
 env=getattr(Runtime,student_class)(cfg,**shared,recovery_config=recovery,pose_library=library,stand_policy=torch.nn.Linear(1,1),interface_version='multiskill_mcu_v2',**training_options)
 assert hasattr(env,'task_phase') and env.task_phase.shape==(n,)
 env._geometry_gaps=lambda:(torch.ones(n,1)*.01,torch.ones(n)*.01)
 env._reset_idx(torch.arange(n));env.fsm.mode[:]=int(Mode.RECOVERY);env.initialization_checked[:]=True
 # Missing inherited task_phase used to fail here, at the real parent _get_dones.
 env._pre_physics_step(torch.zeros(n,6))
 del env.task_phase
 with pytest.raises(AttributeError,match='task_phase'):env._get_dones()
 env.task_phase=torch.zeros(n,dtype=torch.long)
 env.student_fault_diagnostics_enabled=True
 rng_before=torch.get_rng_state().clone()
 done,timeout=env._get_dones()
 assert torch.equal(rng_before,torch.get_rng_state())
 assert env.student_fault_components['initial_rejected'].shape==(n,)
 assert not env.student_fault_components['joint_outside'].any()
 assert not done.any() and not timeout.any();assert env.recovery_snapshot.shape==(n,39)
 if student_class=='TrainingStudentEnv':
  if reward_version=='student_recovery_reward_standing_mirror_huber_v11':
   expected=2.*.01*torch.exp(torch.tensor(-((.168-.34)/.04)**2))
   torch.testing.assert_close(env.student_reward_result['total'],expected.expand(n))
   env.episode_length_buf[:]=1;observation=env._get_observations()
   torch.testing.assert_close(observation['student_actor'][:,24],torch.full((n,),.68))
  else:assert env.student_reward_result['total'].tolist()==[0.,0.]
  assert env.student_h0_valid.all()
 else:assert env._get_rewards().tolist()==[0.,0.]
 # Parent emits a controlled failure without deleting the step's actor validity.
 env.up=torch.zeros(n);env._motion_state=lambda:(torch.zeros(n,3),torch.tensor([[0.,0.,-1.]]*n))
 env._pre_physics_step(torch.zeros(n,6));done,timeout=env._get_dones()
 assert done.all() and not timeout.any() and env.student_actor_valid.all()
 if student_class=='TrainingStudentEnv':
  assert env.student_event_snapshot[:,3].all()
  assert env.student_reward_result['events'][:,2].tolist()==[configuration(reward_version)['failure_once']]*n
 sys.modules.pop('native_stand.recovery.runtime',None);sys.modules.pop('native_stand.students.runtime',None)
 sys.modules.pop('native_stand.recovery.handoff_runtime',None)
