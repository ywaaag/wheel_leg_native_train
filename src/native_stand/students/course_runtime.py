"""After-AppLauncher adapter: real frozen prefixes, shared StudentEnv physics/PD."""
import torch
from .runtime import TrainingStudentEnv
from .recovery_task import Certificate
from .course import slot_groups,controlled_owners,NORMAL
from native_stand.recovery.domain import Mode
from native_stand.command_v6.domain.contract import frame,history
from native_stand.recovery.motion_handoff import encode_executed

class SuffixCertificate(Certificate):
 def observe(self,*args,active,**kwargs):
  return super().observe(*args,active=active&self.student_control_pre,**kwargs)

class CourseStudentEnv(TrainingStudentEnv):
 def __init__(self,*args,course_configuration,teacher_actors,**kwargs):
  self.course_ready=False;self.course_configuration=course_configuration
  self.student_fault_diagnostics_enabled=True
  self.teacher_actors=teacher_actors
  for a in self.teacher_actors:a.eval();a.requires_grad_(False)
  super().__init__(*args,**kwargs)
  self.rise_hold=SuffixCertificate(self.num_envs,self.device)
  self.rise_hold.student_control_pre=torch.zeros(self.num_envs,device=self.device,dtype=torch.bool)
  self.teacher_intervals=torch.zeros(self.num_envs,device=self.device,dtype=torch.long)
  self.absolute_control_intervals=torch.zeros_like(self.teacher_intervals)
  self.student_started=torch.zeros_like(self.teacher_intervals,dtype=torch.bool)
  self.owner_pre=torch.zeros_like(self.teacher_intervals);self.course_group_index=torch.zeros_like(self.teacher_intervals)
  self.threshold=torch.zeros_like(self.teacher_intervals)
  self.teacher_histories=[torch.zeros(self.num_envs,125,device=self.device) for _ in range(2)]
  self.teacher_obs=[None,None];self.teacher_last_time=torch.full((self.num_envs,),float('nan'),device=self.device,dtype=torch.float64)
  self.handoff_state=torch.zeros(self.num_envs,13+2*len(self.robot.joint_names),device=self.device)
  self.handoff_pulse=torch.zeros_like(self.student_started)
  self.course_ready=True;self.configure_groups()
 def configure_groups(self):
  groups=slot_groups(self.course_configuration['state'],self.num_envs)
  self.slot_families=[r['family'] for r in groups]
  group_names=list(dict.fromkeys(r['group'] for r in groups));self.group_names=group_names
  self.course_group_index.copy_(torch.tensor([group_names.index(r['group']) for r in groups],device=self.device))
  self.threshold.copy_(torch.tensor([r['prefix'] for r in groups],device=self.device))
 def configure_evaluation(self,family,prefix_s):
  self.slot_families=[family]*self.num_envs;self.threshold[:]=round(prefix_s*100)
  self.course_group_index.zero_();self.group_names=['evaluation']
 def _reset_idx(self,ids):
  if not getattr(self,'course_ready',False):return super()._reset_idx(ids)
  ids=torch.arange(self.num_envs,device=self.device) if ids is None else ids
  original=self.recovery_config;family,split=self.family,self.split
  # Family selection occurs only at a real episode reset; no mid-episode state rewrite.
  try:
   from .requests import evaluation_recovery
   for f in dict.fromkeys(self.slot_families[i] for i in ids.tolist()):
    selected=ids[torch.tensor([self.slot_families[i]==f for i in ids.tolist()],device=self.device)]
    self.recovery_config=evaluation_recovery(original,self.pose_library['poses'],f);self.family=f
    super()._reset_idx(selected)
  finally:self.recovery_config=original;self.family=family;self.split=split
  self.teacher_intervals[ids]=0;self.absolute_control_intervals[ids]=0;self.student_started[ids]=False
  self.owner_pre[ids]=0;self.handoff_pulse[ids]=False;self.teacher_last_time[ids]=float('nan')
  for h in self.teacher_histories:h[ids]=0
 def actor_valid_pre(self):
  return controlled_owners(self.fsm.mode==int(Mode.INITIALIZING),self.initialization_checked,self.teacher_intervals,self.threshold)[1]
 def compose_training_action(self,requested):
  owner,valid=controlled_owners(self.fsm.mode==int(Mode.INITIALIZING),self.initialization_checked,self.teacher_intervals,self.threshold)
  action=requested.clone();action[owner==0]=0
  # Frozen means only. Each teacher consumes its own current frame/history.
  with torch.inference_mode():
   for code,model,obs in zip((1,2),self.teacher_actors,self.teacher_obs):
    mask=owner==code
    if mask.any():action[mask]=model({k:v[mask] for k,v in obs.items()},stochastic_output=False)
  return action
 def _pre_physics_step(self,actions):
  initial=self.fsm.mode==int(Mode.INITIALIZING)
  owner,valid=controlled_owners(initial,self.initialization_checked,self.teacher_intervals,self.threshold)
  first_control=(owner!=0)&~self.student_h0_valid
  self.student_h0[first_control]=self.robot.data.root_pos_w.torch[first_control,2]
  self.student_h0_valid|=first_control # original Swing baseline, not raised handoff height
  first_student=valid&~self.student_started;self.handoff_pulse.copy_(first_student&(self.threshold>0))
  self.handoff_state[first_student]=torch.cat((self.robot.data.root_state_w.torch,self.robot.data.joint_pos.torch,self.robot.data.joint_vel.torch),-1)[first_student]
  self.rise_hold.reset(torch.where(first_student)[0]);self.student_started|=valid
  self.student_previous_physical[:,[0,1,3,4]]=self.executed_leg;self.student_previous_physical[:,[2,5]]=self.executed_wheel
  self.owner_pre.copy_(owner);self.student_actor_valid=valid.clone();self.rise_hold.student_control_pre=valid.clone()
  self.previous_action.copy_(self.action);self.raw_action.copy_(actions)
  clipped=actions.clamp(-1,1)
  scale=torch.where(owner==1,1.6,torch.where(owner==2,.5,1.5))[:,None]
  requested=self.reference[:,[0,1,3,4]]+clipped[:,[0,1,3,4]]*scale
  legs=requested.clamp(self.active_limits[[0,1,3,4],0],self.active_limits[[0,1,3,4],1])
  hold=initial&self.pose_initial_hold[self.initial_pose_index]
  legs=torch.where(hold[:,None],self.initial_leg_targets,legs);wheels=torch.where(initial[:,None],0.,clipped[:,[2,5]]*100.)
  self.target_before_joint_limit=requested;self.joint_limit_clip_fraction=(requested!=legs).float().mean(-1)
  self.leg_target.copy_(legs);self.wheel_target.copy_(wheels);self.executed_leg.copy_(legs);self.executed_wheel.copy_(wheels)
  self.action.copy_(encode_executed(legs,wheels,self.reference,leg_scale=1.5,wheel_scale=100.)['clipped']);self.action[initial]=0
  self.control_jump.zero_();self.wheel_control_jump.zero_();self.stand_previous.zero_();self.target_rate.zero_();self.pd_counter=0
  self.teacher_intervals+=(owner==1)|(owner==2);self.absolute_control_intervals+=owner!=0
  self.rise_hold.motion.copy_(valid)
 def _get_dones(self):
  result=super()._get_dones()
  if getattr(self,'course_ready',False):
   self.course_owner_snapshot=self.owner_pre.clone();self.course_absolute_snapshot=self.absolute_control_intervals.clone()
   self.course_teacher_snapshot=self.teacher_intervals.clone();self.course_handoff_snapshot=self.handoff_pulse.clone()
   self.course_handoff_state_snapshot=self.handoff_state.clone()
  return result
 def _get_observations(self):
  result=super()._get_observations()
  if not getattr(self,'course_ready',False):return result
  time=self.episode_length_buf.to(torch.float64)*self.step_dt
  changed=~torch.isfinite(self.teacher_last_time)|(abs(time-self.teacher_last_time)>1e-8)
  if not changed.any():return result
  angular,gravity=self._motion_state();d=self.robot.data;initial=self.fsm.mode==int(Mode.INITIALIZING)
  legs=torch.where(initial[:,None],self.reference[:,[0,1,3,4]],self.executed_leg)
  wheels=torch.where(initial[:,None],0.,self.executed_wheel)
  for i,scale in enumerate((1.6,.5)):
   previous=encode_executed(legs,wheels,self.reference,leg_scale=scale,wheel_scale=100.)
   command=self.reference.new_tensor([0.,0.,.36 if i==0 else .40]).expand(self.num_envs,-1)
   f=frame(angular,gravity,command,d.joint_pos.torch[:,self.ids],d.joint_vel.torch[:,self.ids],previous['clipped'],self.reference)
   h=history(self.teacher_histories[i],f,~torch.isfinite(self.teacher_last_time))
   self.teacher_histories[i][changed]=h[changed]
   self.teacher_obs[i]={'policy':f,'history':self.teacher_histories[i]}
  self.teacher_last_time[changed]=time[changed]
  return result
