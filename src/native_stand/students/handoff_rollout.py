"""PPO0 frozen student/Motion sequential execution, no resets at handoff."""
import numpy as np,torch
from .handoff_probe import KIND
from native_stand.recovery.motion_handoff import score
from native_stand.recovery.handoff_protocol import declaration,prefix_steps

def rollout(env,actor,row,motion,stop=None,scored_envs=8):
 env.configure_case({'switch_s':row['switch_s'],'kind':KIND});env.configure_protocol(declaration());env.configure_randomization({'version':'reset_yaw_v1','root_yaw_rad':row['yaw_rad'],'distribution':'uniform'})
 torch.manual_seed(row['seed']);env.select_initial_family(row['family'],'holdout');obs,_=env.reset()
 active=torch.ones(scored_envs,dtype=torch.bool,device=env.device);buffers={};valid=[];switch_records=[];prior=env.controller.clone()
 def add(k,v):buffers.setdefault(k,[]).append(v[:scored_envs].detach().cpu().numpy().copy())
 env.student_trace_capture={'buffers':buffers,'valid':valid}
 with torch.inference_mode():
  for step in range(round(row['seconds']/.01)):
   if stop and stop():raise TimeoutError('student Motion probe wall budget exhausted')
   owner,student,on_motion=env.control_owner_pre();action=torch.zeros(env.num_envs,6,device=env.device)
   if student.any():action[student]=actor(env.probe_student_obs[student])
   if on_motion.any():action[on_motion]=motion({k:env.motion_obs[k][on_motion] for k in ('policy','history')},stochastic_output=False)
   add('student_actor_input',env.probe_student_obs)
   add('motion_policy_input',env.motion_obs['policy']);add('motion_history_input',env.motion_obs['history'])
   rb=env.motion_obs['previous_action_readback']
   for k in ('raw','clipped','information_loss','outside'):add('motion_previous_'+k,rb[k])
   add('root_pre',env.robot.data.root_state_w.torch);add('joint_q_pre',env.robot.data.joint_pos.torch);add('joint_dq_pre',env.robot.data.joint_vel.torch)
   add('previous_targets',torch.cat((env.executed_leg,env.executed_wheel),-1));add('raw_action',action);add('mean',action);add('actor_valid',student[:,None]);add('controller_pre',owner[:,None])
   switch=on_motion&(prior!=2)&active.new_tensor([True]*scored_envs+[False]*(env.num_envs-scored_envs))
   add('switch_event',switch[:,None]);prior=owner.clone()
   add('prefix_intervals_pre',env.executed_prefix[:,None])
   obs,reward,terminated,truncated,_=env.step(action);done=terminated|truncated
   add('state',env.recovery_snapshot);add('posture',env.standing_snapshot);add('control',env.recovery_control_snapshot);add('geometry',env.wheel_geometry_snapshot);add('root_post',env.handoff_root_post);add('controller',env.handoff_controller[:,None]);add('termination_causes',env.recovery_cause_snapshot);add('motion_clock_s',env.handoff_motion_age[:,None]);add('initial_clock_s',env.handoff_initial_age[:,None]);add('controlled_clock_s',env.recovery_snapshot[:,0:1]);add('motion_previous_mode',env.recovery_snapshot[:,32:33]);add('joint_q_post',env.handoff_joint_q_post);add('joint_dq_post',env.handoff_joint_dq_post)
   valid.append(active.cpu().numpy().copy());active&=~done[:scored_envs]
   if env.recovery_snapshot[:,4].bool().any() or env.recovery_snapshot[:,30].bool().any() or not torch.isfinite(env.recovery_snapshot).all():raise RuntimeError('student Motion probe runtime/initialization fault')
   if not active.any():break
 arrays={k:np.stack(v) for k,v in buffers.items()};arrays['first_episode_valid']=np.stack(valid);arrays['policy_time_s']=np.arange(1,len(valid)+1)*.01
 results=[]
 for e in range(scored_envs):
  mask=arrays['first_episode_valid'][:,e];s=torch.tensor(arrays['state'][mask,e]);p=torch.tensor(arrays['posture'][mask,e]);owner=torch.tensor(arrays['controller'][mask,e,0]);time=torch.tensor(arrays['policy_time_s'][mask],dtype=s.dtype)
  result=score(s,p,owner==2,policy_time_s=time)
  switched=np.flatnonzero((arrays['controller'][:,e,0]==2)&mask)
  ix=int(switched[0]) if len(switched) else None
  result.update(env=e,initial_valid=bool(s[:,29].bool().any()),actual_switched=ix is not None,student_independent_accepted=False,student_controlled_samples=int((owner==3).sum()),motion_controlled_samples=int((owner==2).sum()),termination_causes=arrays['termination_causes'][mask,e][-1].tolist())
  if ix is not None:
   prev=arrays['previous_targets'][ix,e];ctl=arrays['control'][ix,e];target=np.r_[ctl[28:32],ctl[[20,23]]*100]
   result['switch_state']={'policy_time_s':float(arrays['policy_time_s'][ix]),'root_pre':arrays['root_pre'][ix,e].tolist(),'post_height_pitch_roll':np.r_[arrays['state'][ix,e,6],arrays['posture'][ix,e,:2]].tolist(),'physical_targets_delta_fourlegs_twowheels':(target-prev).tolist(),'motion_previous_outside_fraction':float(arrays['motion_previous_outside'][ix,e].mean()),'motion_previous_information_loss':arrays['motion_previous_information_loss'][ix,e].tolist()}
  results.append(result)
 return {'protocol':declaration(),'interface':{'student':'multiskill_mcu_v2','motion':'legacy150D','student_leg_scale_rad':1.5,'motion_leg_scale_rad':.5},'field_schema':{'state':'recovery_policy_trace_v1','posture':'recovery_policy_trace_v1','control':'recovery_policy_trace_v1','root':'pos_w3,quat_xyzw4,linear_velocity_w3,angular_velocity_w3','active_indices':env.ids,'joint_names':env.robot.joint_names,'controller':{'initializing':0,'student':3,'motion':2}},'case':row,'per_env':results,'scored_envs':scored_envs,'passed_envs':sum(x['accepted'] for x in results),'accepted':all(x['accepted'] for x in results),'online_PPO':0,'offline_optimizer':0,'teacher_rescue_not_student_success':True,'simulated_envs':env.num_envs,'scored_env_steps':int(arrays['first_episode_valid'].sum()),'all_simulated_env_steps':len(valid)*env.num_envs},arrays
