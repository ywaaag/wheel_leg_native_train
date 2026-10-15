"""Student-only execution over shared RecoveryEnv physics/PD, after AppLauncher."""
import torch
from native_stand.recovery.runtime import RecoveryEnv
from native_stand.recovery.domain import Mode
from native_stand.recovery.handoff_clock import HandoffClock
from .interface import History,frame,task,targets,critic_input
from .protocol import declaration

class StudentEnv(RecoveryEnv):
    def __init__(self,*args,student_role='RecoveryStudent',interface_version='multiskill_student_v1',student_command_height=.40,critic_privileged_version=None,**kwargs):
        self.student_ready=False;self.student_role=student_role;self.interface_version=interface_version
        self.student_command_height=float(student_command_height)
        if critic_privileged_version not in (None,'standing_privileged49_v1'):raise ValueError('unknown runtime Critic privileged version')
        self.critic_privileged_version=critic_privileged_version
        super().__init__(*args,**kwargs)
        self.student_history=History(self.num_envs,self.device)
        self.student_clock=torch.zeros(self.num_envs,device=self.device,dtype=torch.float64)
        self.rise_hold=HandoffClock(self.num_envs,self.device,declaration());self.student_ready=True
        self.student_obs=None
        from .mcu_interface import PolicyClock
        self.mcu_clock=PolicyClock(self.num_envs,self.device)
    def _reset_idx(self,ids):
        super()._reset_idx(ids)
        if getattr(self,'student_ready',False):
            ids=torch.arange(self.num_envs,device=self.device) if ids is None else ids
            self.student_history.reset(ids);self.student_clock[ids]=0
            if hasattr(self,"mcu_clock"):self.mcu_clock.reset(ids)
            perturb=getattr(self,'student_yaw_amplitude',0.)
            if perturb:
                from native_stand.recovery.handoff_ownership import yaw_randomize
                root=self.robot.data.root_state_w.torch[ids,:7].clone()
                root[:,3:7]=yaw_randomize(root[:,3:7],torch.rand(len(ids),device=self.device),perturb)
                self.robot.write_root_pose_to_sim_index(root_pose=root,env_ids=ids)
    def _pre_physics_step(self,actions):
        initial=self.fsm.mode==int(Mode.INITIALIZING)
        self.student_actor_valid=(~initial)&self.initialization_checked
        self.previous_action.copy_(self.action);self.raw_action.copy_(actions)
        t=targets(actions,self.reference,self.active_limits)
        hold=initial&self.pose_initial_hold[self.initial_pose_index]
        legs=torch.where(hold[:,None],self.initial_leg_targets,t['leg_executed'])
        wheels=torch.where(initial[:,None],0.,t['wheel_executed'])
        self.target_before_joint_limit=t['leg_requested'];self.joint_limit_clip_fraction=t['joint_limit_clipped'].float().mean(-1)
        self.leg_target.copy_(legs);self.wheel_target.copy_(wheels);self.executed_leg.copy_(legs);self.executed_wheel.copy_(wheels)
        self.action.copy_(t['clipped_action']);self.action[initial]=0
        self.control_jump.zero_();self.wheel_control_jump.zero_();self.stand_previous.zero_();self.target_rate.zero_();self.pd_counter=0
        self.rise_hold.motion.copy_(~initial)
    def _get_dones(self):
        result=super()._get_dones()
        self.student_root_post=self.robot.data.root_state_w.torch.clone()
        self.student_q_post=self.robot.data.joint_pos.torch.clone();self.student_dq_post=self.robot.data.joint_vel.torch.clone()
        self.student_controlled_post=self.student_actor_valid.clone()
        return result
    def _get_observations(self):
        legacy=super()._get_observations()
        if not getattr(self,'student_ready',False):return legacy
        if getattr(self,'motion_training_enabled',False):
            # Legacy history has its own clock; only the explicit Motion branch
            # restores the single controlled-age command before student encoding.
            self.command.copy_(self.motion_observation_command)
        angular,gravity=self._motion_state();d=self.robot.data;initial=self.fsm.mode==int(Mode.INITIALIZING)
        # Passive initialization has no executed actor target; native zero semantics.
        mcu=getattr(self,'interface_version','multiskill_student_v1')=='multiskill_mcu_v2'
        prev_legs=self.executed_leg if mcu else torch.where(initial[:,None],self.reference[:,(0,1,3,4)],self.executed_leg)
        prev_wheels=torch.where(initial[:,None],0.,self.executed_wheel)
        f=frame(angular,gravity,d.joint_pos.torch[:,self.ids],d.joint_vel.torch[:,self.ids],prev_legs,prev_wheels,self.reference)
        time_s=self.episode_length_buf.to(torch.float64)*self.step_dt
        update=(~self.student_history.valid[:,-1]) | ((self.student_history.times[:,-1]-time_s).abs()>1e-8)
        if getattr(self,'motion_training_enabled',False) and getattr(self,'student_obs',None) is not None:
            update |= (self.student_obs['student_actor'][:,22:25]-self.command/self.command.new_tensor([4.,4.,.5])).abs().amax(-1)>1e-8
        if not update.any():return self.student_obs
        if mcu:
            self.mcu_clock.check(time_s)
        else:self.student_history.append(f,time_s,update)
        skill='Recovery' if self.student_role=='RecoveryStudent' else 'Motion'
        command=f.new_tensor([0.,0.,.36 if skill=='Recovery' else .40,0.,0.]).expand(self.num_envs,-1)
        if mcu:
            from .mcu_interface import actor_input,task as mcu_task
            commands=f.new_tensor([0.,0.,self.student_command_height]).expand(self.num_envs,-1)
            if getattr(self,'motion_training_enabled',False):commands=self.command
            if getattr(self,'motion_validation',False):
                from .motion_validation import command_tensor
                commands=command_tensor(self.student_motion_command,f,self.student_role)
            actor=actor_input(f,mcu_task(skill,commands))
        else:actor=self.student_history.encode(task(skill,command))
        from isaaclab.utils.math import quat_apply_inverse
        velocity=quat_apply_inverse(d.root_quat_w.torch,d.root_lin_vel_w.torch)
        native_velocity=torch.stack((-velocity[:,2],-velocity[:,0],velocity[:,1]),-1)
        dwell=self.rise_hold.dwell.float()*self.step_dt
        if mcu:
            from .mcu_interface import critic_input as critic_encoder
        else:critic_encoder=critic_input
        critic=critic_encoder(actor,self.root_height,native_velocity,self.contact_force,self.rise_hold.age,dwell,self.rise_hold.count.float()*self.step_dt)
        if getattr(self,'critic_privileged_version',None):
            from .standing_zero_privileged import critic_input as privileged_encoder
            critic=privileged_encoder(critic,d.root_lin_vel_w.torch[:,2],d.applied_torque.torch[:,self.ids],d.joint_vel.torch[:,self.ids][:,(2,5)],native_velocity[:,0],radius=self.recovery_config['wheel_radius_m'])
        self.student_obs={'student_actor':actor,'student_critic':critic};return self.student_obs
    def _get_rewards(self):
        # PPO0 only. Future reward must be a separately declared experiment.
        return torch.zeros(self.num_envs,device=self.device)

class TrainingStudentEnv(StudentEnv):
    """Public recipe adapter: physical path unchanged, nonzero post/reset reward."""
    def __init__(self,*args,**kwargs):
        self.task_ready=False
        self.standing_rehearsal=kwargs.pop('standing_rehearsal_configuration',None)
        from .recovery_task import configuration
        self.student_reward_configuration=kwargs.pop('student_reward_configuration',configuration())
        if self.student_reward_configuration!=configuration(self.student_reward_configuration.get('version')):raise ValueError('student runtime reward differs')
        super().__init__(*args,**kwargs)
        from .recovery_task import Certificate
        self.rise_hold=Certificate(self.num_envs,self.device)
        if self.student_reward_configuration.get('version')in ('student_recovery_reward_standing_mirror_huber_v11','student_standing_alignment_reward_v12','student_standing_zero_privileged49_reward_v13'):
            from .standing_certificate import StandingCertificate
            self.rise_hold=StandingCertificate(self.num_envs,self.device)
            if self.student_reward_configuration.get('version') in ('student_standing_alignment_reward_v12','student_standing_zero_privileged49_reward_v13'):
                from .standing_certificate import AlignmentCertificate
                self.rise_hold=AlignmentCertificate(self.num_envs,self.device)
            self.student_fault_diagnostics_enabled=True
        if self.student_reward_configuration.get('version')=='student_standing_survival_quality_reward_v14':
            from .standing_survival_task import Clock
            self.rise_hold=Clock(self.num_envs,self.device);self.student_fault_diagnostics_enabled=True
        self.student_h0=torch.zeros(self.num_envs,device=self.device)
        self.student_h0_valid=torch.zeros(self.num_envs,device=self.device,dtype=torch.bool)
        self.student_previous_physical=torch.zeros(self.num_envs,6,device=self.device)
        self.student_reward_result=None;self.task_ready=True
        self.standing_rehearsal_pose_mask=torch.tensor([p['family']=='motion_native_normal' for p in self.pose_library['poses']],device=self.device)
    def _reset_idx(self,ids):
        super()._reset_idx(ids)
        if getattr(self,'task_ready',False):
            ids=torch.arange(self.num_envs,device=self.device) if ids is None else ids
            self.student_h0[ids]=0;self.student_h0_valid[ids]=False
            if self.standing_rehearsal:
                normal=ids[self.standing_rehearsal_pose_mask[self.initial_pose_index[ids]]]
                if len(normal):
                    from .rehearsal import angular_reset
                    root=self.robot.data.root_state_w.torch[normal].clone()
                    perturbed=angular_reset(root,torch.rand(len(normal),2,device=self.device),self.standing_rehearsal['angular_velocity_max_rad_s'])
                    self.robot.write_root_velocity_to_sim_index(root_velocity=perturbed[:,7:13],env_ids=normal)
    def _pre_physics_step(self,actions):
        controlled=(self.fsm.mode!=int(Mode.INITIALIZING))&self.initialization_checked
        first=controlled&~self.student_h0_valid
        self.student_h0[first]=self.robot.data.root_pos_w.torch[first,2]
        self.student_h0_valid|=first
        self.student_previous_physical[:,[0,1,3,4]]=self.executed_leg
        self.student_previous_physical[:,[2,5]]=self.executed_wheel
        super()._pre_physics_step(actions)
    def _get_dones(self):
        if not getattr(self,'task_ready',False):return super()._get_dones()
        if hasattr(self.rise_hold,'set_joint'):self.rise_hold.set_joint(self.robot.data.joint_pos.torch[:,self.ids][:,[0,1,3,4]])
        if hasattr(self.rise_hold,'set_offset'):
            from native_stand.recovery.standing import longitudinal_geometry
            from isaaclab.utils.math import quat_apply_inverse
            data=self.robot.data
            centers=data.body_pos_w.torch[:,self.wheel_body_ids]-data.root_pos_w.torch[:,None,:]
            centers=quat_apply_inverse(data.root_quat_w.torch[:,None,:].expand(-1,2,-1),centers)
            _,gravity=self._motion_state()
            self.rise_hold.set_offset(longitudinal_geometry(centers,gravity))
        self._motion_state()
        self.rise_hold.set_velocity(torch.stack((self.vx,self.vy,self.yaw),-1))
        result=super()._get_dones()
        from .recovery_task import reward
        executed=torch.zeros_like(self.student_previous_physical)
        executed[:,[0,1,3,4]]=self.executed_leg;executed[:,[2,5]]=self.executed_wheel
        angular,_=self._motion_state()
        s=self.recovery_snapshot;p=self.standing_snapshot;clock=self.rise_hold
        if self.student_reward_configuration.get('version')=='student_standing_survival_quality_reward_v14':
            from .standing_survival_reward import reward as survival_reward
            if not getattr(self,'motion_training_enabled',False):
             self.student_reward_result=survival_reward(height=s[:,6],angles=p[:,:2],velocity_xy=self.robot.data.root_lin_vel_w.torch[:,:2],yaw=s[:,9],contacts=s[:,10:12],leg_q=self.robot.data.joint_pos.torch[:,self.ids][:,[0,1,3,4]],wheel_offset=clock.offset,leg_lengths=p[:,2:4],angular_pitch_roll=angular[:,[0,2]],applied_torque=self.robot.data.applied_torque.torch[:,self.ids],previous_targets=self.student_previous_physical,executed_targets=executed,controlled=self.student_actor_valid,valid=s[:,29].bool(),physical_failure=s[:,3].bool(),fault=s[:,4].bool())
             clock.record_quality(s,p,self.wheel_geometry_snapshot,self.robot.data.root_lin_vel_w.torch,self.student_actor_valid)
            self.student_terminal_critic=None
            if clock.normal_timeout.any():
                self.student_terminal_critic=self._get_observations()['student_critic'].detach().clone()
            result=(result[0],clock.normal_timeout.clone())
            self.episode_result_snapshot[:,1]=clock.normal_timeout
            self.episode_result_snapshot[:,2]=clock.certificate_passed
            self.episode_result_snapshot[:,4]=result[0]|result[1]
        else:
            self.student_reward_result=reward(s[:,6],self.student_h0,p[:,:2],s[:,10:12],s[:,13],self.robot.data.applied_torque.torch[:,self.ids],self.student_previous_physical,executed,angular,
          torch.stack((self.vx,self.vy,torch.zeros_like(self.vx)),-1),self.yaw,clock.entry>=0,self.student_actor_valid,s[:,4].bool(),
          clock.entry_confirmed,clock.certificate_passed,clock.task_failure,reward_configuration=self.student_reward_configuration,
          active_leg_q=self.robot.data.joint_pos.torch[:,self.ids][:,[0,1,3,4]],wheel_heading_offset=getattr(self.rise_hold,'offset',None))
        self.student_event_snapshot=torch.stack((clock.entry_confirmed,clock.hold_window_complete,clock.certificate_passed,clock.task_failure,clock.runtime_fault),-1).clone()
        self.student_hold_prefix_snapshot=clock.prefix.clone()
        return result
    def _get_rewards(self):
        if not getattr(self,'task_ready',False) or self.student_reward_result is None:return super()._get_rewards()
        return self.student_reward_result['total']
