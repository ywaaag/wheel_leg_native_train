"""Recovery adapter; shares scene, physical PD, observation and runtime audit.

This module may only be imported after AppLauncher. All identities, pose data
and the immutable STAND module are injected by the CLI/task assembly boundary.
"""
import torch
from isaaclab.utils.math import quat_apply_inverse,quat_apply
from native_stand.command_v6.runtime.env import CommandEnv
from native_stand.command_v6.domain import contract
from native_stand.recovery.domain import RecoveryFSM,Mode,blend_targets,process_reward,autonomous_stable,ReverseRecoveryCurriculum
from native_stand.recovery.initialization import settlement_joint_indices,zero_initial_velocities
from native_stand.recovery.standing import POSTURE_FIELDS,posture,standing_success_mask,pose_sampling
from native_stand.command_v6.domain.episode_result import recovery_episode_mode


class RecoveryEnv(CommandEnv):
    def __init__(self,cfg,*,recovery_config,pose_library,stand_policy,initialization_only=False,**kwargs):
        self.recovery_config=recovery_config
        self.episode_mode=recovery_episode_mode(recovery_config)
        self.pose_library=pose_library
        from native_stand.recovery.task_protocol import resolve as task_protocol
        self.effective_task_protocol=task_protocol(recovery_config)
        self.initialization_only=initialization_only
        if stand_policy is None and self.episode_mode!='continuous_holding':
            raise ValueError('Recovery handover/autonomous_hold requires frozen STAND dependency')
        self.stand_policy=stand_policy.eval() if stand_policy is not None else None
        if self.stand_policy is not None:
            for parameter in self.stand_policy.parameters():
                parameter.requires_grad_(False)
        self.recovery_ready=False
        self.continuous_evaluation=False
        super().__init__(cfg,**kwargs)
        self.fsm=RecoveryFSM(self.num_envs,self.device,recovery_config['fsm'])
        self.stand_history=torch.zeros_like(self.history)
        self.stand_previous=torch.zeros_like(self.action)
        self.executed_leg=torch.zeros_like(self.leg_target)
        self.executed_wheel=torch.zeros_like(self.wheel_target)
        self.initial_height=torch.zeros(self.num_envs,device=self.device)
        self.success_pulse=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        self.initial_pose_index=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.handover_origin=torch.zeros((self.num_envs,2),device=self.device)
        self.handover_leg=torch.zeros_like(self.leg_target)
        self.handover_wheel=torch.zeros_like(self.wheel_target)
        self.control_jump=torch.zeros(self.num_envs,device=self.device)
        self.wheel_control_jump=torch.zeros_like(self.control_jump)
        self.target_rate=torch.zeros_like(self.action)
        self.handover_target_rate_peak=torch.zeros_like(self.action)
        self.recovery_snapshot=torch.zeros((self.num_envs,39),device=self.device)
        self.recovery_control_snapshot=torch.zeros((self.num_envs,54),device=self.device)
        self.recovery_cause_snapshot=torch.zeros((self.num_envs,6),device=self.device,dtype=torch.bool)
        self.recovery_snapshot_valid=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        self.standing_snapshot=torch.zeros((self.num_envs,10),device=self.device)
        self.holding_episode=None
        if self.episode_mode=='continuous_holding':
            from native_stand.recovery.holding import HoldingEpisode
            self.holding_episode=HoldingEpisode(self.num_envs,self.device,dt=self.step_dt,
                protocol=recovery_config['standing_task']['protocol'])
        self.holding_rollout_counts=torch.zeros(2,device=self.device,dtype=torch.long)
        self.episode_result_snapshot=torch.zeros((self.num_envs,5),device=self.device,dtype=torch.bool)
        self.wheel_longitudinal_offset=torch.zeros(self.num_envs,device=self.device)
        self.wheel_geometry_snapshot=torch.zeros((self.num_envs,13),device=self.device)
        self.wheel_geometry_stats=torch.zeros((),device=self.device)
        self.standing_stats=torch.zeros(10,device=self.device)
        self.episode_origin=torch.zeros((self.num_envs,2),device=self.device)
        self.gate_diagnostic_names=('height','tilt','angular_speed','linear_speed','leg_speed','leg_angle',
            'dual_contact','chassis_clearance','leg_target_jump','wheel_target_jump','stand_leg_envelope')
        self.gate_diagnostic_snapshot=torch.zeros((self.num_envs,20),device=self.device)
        self.initialization_checked=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        self.initial_age=torch.zeros(self.num_envs,device=self.device)
        self.settle_dwell=torch.zeros_like(self.initial_age)
        self.initial_velocity_zeroed=torch.zeros_like(self.initialization_checked)
        self.settlement_joint_ids=settlement_joint_indices(self.robot.joint_names)
        self.initial_attempts=torch.zeros(len(pose_library['poses']),device=self.device,dtype=torch.long)
        self.initial_accepts=torch.zeros_like(self.initial_attempts)
        self.initial_rejects=torch.zeros_like(self.initial_attempts)
        self.rollout_events=torch.zeros(7,device=self.device,dtype=torch.long)
        from native_stand.recovery.episode_metrics import PoseEpisodeMetrics
        self.pose_episode_metrics=PoseEpisodeMetrics(pose_library['poses'],self.device)
        self.split='train'
        self.family=recovery_config['active_family']
        curriculum=recovery_config.get('curriculum',{})
        self.reverse_curriculum=None
        self.curriculum_training=True
        if curriculum.get('automatic_upgrade'):
            self.reverse_curriculum=ReverseRecoveryCurriculum(curriculum['levels'],
                windows_required=curriculum['windows_required'],
                success_rate_min=curriculum['success_rate_min'],
                episodes_per_window=curriculum['episodes_per_window'],
                max_enabled_stage=curriculum.get('max_enabled_stage'),
                full_confirmations_required=curriculum.get('full_confirmations_required',0))
            self.family=self.reverse_curriculum.current_level()['pose_family']
            for level in curriculum['levels']:
                for split in ('train','holdout'):
                    if not any(p['family']==level['pose_family'] and p['split']==split and p['offline_valid']
                               for p in pose_library['poses']):
                        raise ValueError(f"Missing verified pose family: {level['pose_family']}/{split}")
        self.episode_stage=torch.zeros(self.num_envs,device=self.device,dtype=torch.long)
        self.reverse_events=torch.zeros((self.num_envs,3),device=self.device,dtype=torch.long)
        self.reverse_event_valid=torch.zeros(self.num_envs,device=self.device,dtype=torch.bool)
        self.reverse_buffer=torch.zeros((128,self.num_envs,3),device=self.device,dtype=torch.long)
        self.reverse_valid=torch.zeros((128,self.num_envs),device=self.device,dtype=torch.bool)
        self.reverse_cursor=0
        self.height_stats=torch.zeros(3,device=self.device)
        self.height_count=torch.zeros((),device=self.device)
        self.pose_root_bounds=torch.tensor([p.get('initial_root_height_m',recovery_config['initialization']['low_root_height_m'])
            for p in pose_library['poses']],device=self.device)
        self.pose_chassis_bounds=torch.tensor([p.get('initial_chassis_clearance_m',recovery_config['initialization']['chassis_clearance_m'])
            for p in pose_library['poses']],device=self.device)
        self.pose_initial_hold=torch.tensor([p.get('initialization_control')=='hold_initial_targets'
            for p in pose_library['poses']],device=self.device)
        self.pose_direct_reset=torch.tensor([p.get('initialization_control')=='direct_zero_reset'
            for p in pose_library['poses']],device=self.device)
        self.initial_leg_targets=torch.zeros_like(self.leg_target)
        self.geometry=[]
        for shape in pose_library['collision_geometry']:
            if shape['body'] not in self.body_ids:
                raise RuntimeError(f"Missing collision body: {shape['body']}")
            self.geometry.append((shape,self.body_ids[shape['body']],
                torch.tensor(shape['matrix'],device=self.device,dtype=torch.float32)))
        limits=pose_library['joint_limits_rad']
        names=[self.robot.joint_names[i] for i in self.ids]
        self.active_limits=torch.tensor([limits.get(n,[-float('inf'),float('inf')]) for n in names],device=self.device)
        self.joint_limits=torch.tensor([limits.get(n,[-float('inf'),float('inf')]) for n in self.robot.joint_names],device=self.device)
        from native_stand.recovery.domain import support_indices
        self.allowed_sensor,self.restricted_sensor=support_indices(self.sensor.body_names,
            recovery_config['contacts']['allowed_candidate'])
        self.recovery_ready=True

    def select_initial_family(self,family,split):
        if not any(p['family']==family for p in self.pose_library['poses']) or split not in ('train','holdout'):
            raise ValueError('Unknown recovery pose family/split')
        self.family,self.split=family,split

    def _reset_idx(self,env_ids):
        super()._reset_idx(env_ids)
        if not self.recovery_ready:
            return
        ids=torch.arange(self.num_envs,device=self.device) if env_ids is None else env_ids.long()
        if self.reverse_curriculum is not None and self.curriculum_training:
            self.family=self.reverse_curriculum.current_level()['pose_family']
            self.episode_stage[ids]=self.reverse_curriculum.stage
        retained=()
        fraction=0.
        if self.curriculum_training and self.recovery_config.get('rising_task'):
            retained=self.recovery_config['rising_task']['retained_families']
            fraction=self.recovery_config['rising_task']['retained_fraction']
        if self.curriculum_training and self.reverse_curriculum is not None and self.reverse_curriculum.stage:
            stage_config=self.recovery_config['curriculum']['levels'][self.reverse_curriculum.stage]
            retained=stage_config.get('retained_families',())
            fraction=stage_config.get('retained_fraction',0.)
        eligible,weights=pose_sampling(self.pose_library['poses'],self.family,self.split,
                                      retained_families=retained,retained_fraction=fraction)
        if not eligible:
            raise RuntimeError('No valid initial poses; rejected candidates remain in library')
        candidates=torch.tensor(eligible,device=self.device)
        if self.split=='holdout' and self.recovery_config.get('holdout_sampling')=='balanced_pose_cycle':
            choice=candidates[ids % len(candidates)]
        elif self.recovery_config.get('standing_task'):
            weights=torch.tensor(weights,device=self.device)
            choice=candidates[torch.multinomial(weights,len(ids),replacement=True)]
        else:
            choice=candidates[torch.randint(len(eligible),(len(ids),),device=self.device)]
        self.initial_pose_index[ids]=choice
        all_q=torch.tensor([[p['joint_pos'].get(n,0.) for n in self.robot.joint_names]
                           for p in self.pose_library['poses']],device=self.device)
        poses=torch.tensor([[0.,0.,p['root_height_m'],*p['root_quaternion_xyzw']]
                           for p in self.pose_library['poses']],device=self.device)[choice]
        poses[:,:3]+=self.scene.env_origins[ids]
        self.episode_origin[ids]=poses[:,:2]
        self.robot.write_root_pose_to_sim_index(root_pose=poses,env_ids=ids)
        self.robot.write_root_velocity_to_sim_index(root_velocity=torch.zeros((len(ids),6),device=self.device),env_ids=ids)
        self.robot.write_joint_position_to_sim_index(position=all_q[choice],env_ids=ids)
        self.robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(all_q[choice]),env_ids=ids)
        self.initial_height[ids]=poses[:,2]
        self.fsm.reset(ids)
        if self.holding_episode is not None:
            self.holding_episode.reset(ids)
        self.fsm.mode[ids]=int(Mode.INITIALIZING)
        self.initial_age[ids]=0.;self.settle_dwell[ids]=0.
        self.initial_velocity_zeroed[ids]=False
        self.initial_attempts.index_add_(0,choice,torch.ones_like(choice))
        self.stand_history[ids]=0.;self.stand_previous[ids]=0.
        self.executed_leg[ids]=all_q[choice][:,self.ids][:,contract.LEG_COLUMNS]
        self.initial_leg_targets[ids]=self.executed_leg[ids]
        self.executed_wheel[ids]=0.
        self.initialization_checked[ids]=False
        direct=ids[self.pose_direct_reset[choice]]
        self.fsm.mode[direct]=int(Mode.RECOVERY)
        self.initialization_checked[direct]=True
        self.initial_height[direct]=self.recovery_config.get('lift_reference_height_m',.168)
        self.initial_accepts.index_add_(0,choice[self.pose_direct_reset[choice]],torch.ones_like(direct))
        self.handover_target_rate_peak[ids]=0.
        # recovery_snapshot intentionally survives reset: evaluator reads it next.

    def _pre_physics_step(self,actions):
        super()._pre_physics_step(actions)
        student_legs=self.leg_target.clone();student_wheels=self.wheel_target.clone()
        if self.episode_mode=='continuous_holding' or self.recovery_config.get('rising_task'):
            # This task never hands control to STAND. Its checkpoint identity is
            # still validated at assembly, but no unused forward runs each step.
            legs,wheels=student_legs,student_wheels
            blending=standing=torch.zeros_like(self.initialization_checked)
            self.control_jump.zero_();self.wheel_control_jump.zero_()
        else:
            with torch.no_grad():
                teacher_action=self.stand_policy({'policy':self.stand_frame,'history':self.stand_history})
            _,teacher_legs,teacher_wheels=contract.targets(teacher_action,self.reference,
                leg_scale=.5,combined_radius=0.,wheel_scale=100.)
            self.control_jump.copy_((student_legs-teacher_legs).abs().amax(-1))
            self.wheel_control_jump.copy_((student_wheels-teacher_wheels).abs().amax(-1))
            blending=self.fsm.mode==int(Mode.HANDOVER)
            standing=(self.fsm.mode==int(Mode.STAND_VERIFY))|(self.fsm.mode==int(Mode.STAND))
            fraction=torch.where(standing,torch.ones_like(self.fsm.age),
                torch.where(blending,self.fsm.dwell/self.recovery_config['fsm']['blend_s'],0.))
            blend_leg=torch.where(blending[:,None],self.handover_leg,student_legs)
            blend_wheel=torch.where(blending[:,None],self.handover_wheel,student_wheels)
            legs,wheels=blend_targets(blend_leg,blend_wheel,teacher_legs,teacher_wheels,fraction)
        initializing=self.fsm.mode==int(Mode.INITIALIZING)
        hold=initializing & self.pose_initial_hold[self.initial_pose_index]
        legs=torch.where(hold[:,None],self.initial_leg_targets,legs)
        wheels=torch.where(hold[:,None],torch.zeros_like(wheels),wheels)
        before=legs.clone()
        legs=legs.clamp(self.active_limits[list(contract.LEG_COLUMNS),0],self.active_limits[list(contract.LEG_COLUMNS),1])
        self.target_before_joint_limit=before
        self.joint_limit_clip_fraction=(before!=legs).float().mean(-1)
        self.leg_target.copy_(legs);self.wheel_target.copy_(wheels)
        self.target_rate[:,contract.LEG_COLUMNS]=(legs-self.executed_leg)/self.step_dt
        self.target_rate[:,contract.WHEEL_COLUMNS]=(wheels-self.executed_wheel)/self.step_dt
        self.handover_target_rate_peak.copy_(torch.maximum(self.handover_target_rate_peak,
            self.target_rate.abs()*(blending|standing)[:,None]))
        self.executed_leg.copy_(legs);self.executed_wheel.copy_(wheels)
        # Actual executed target encoding, separately normalized for each policy.
        self.action[:,contract.LEG_COLUMNS]=(legs-self.reference[:,contract.LEG_COLUMNS])/self.cfg.leg_position_scale_rad
        self.action[:,contract.WHEEL_COLUMNS]=wheels/self.cfg.wheel_speed_scale_rad_s
        self.action.clamp_(-1.,1.)
        self.stand_previous[:,contract.LEG_COLUMNS]=(legs-self.reference[:,contract.LEG_COLUMNS])/.5
        self.stand_previous[:,contract.WHEEL_COLUMNS]=wheels/100.
        self.stand_previous.clamp_(-1.,1.)
        initializing=self.fsm.mode==int(Mode.INITIALIZING)
        self.action[initializing]=0.;self.stand_previous[initializing]=0.

    def _apply_action(self):
        # Explicit passive-settle phase only. One target write and one PD path.
        if self.pd_counter%self.cfg.pd_interval_steps==0:
            data=self.robot.data
            request,effort=contract.effort(data.joint_pos.torch[:,self.ids],data.joint_vel.torch[:,self.ids],
                self.leg_target,self.wheel_target,leg_kp=self.cfg.leg_kp,leg_kd=self.cfg.leg_kd,wheel_kv=self.cfg.wheel_kv)
            initializing=self.fsm.mode==int(Mode.INITIALIZING)
            initializing=initializing & ~self.pose_initial_hold[self.initial_pose_index]
            if self.initialization_only:initializing=~self.pose_initial_hold[self.initial_pose_index]
            request[initializing]=0.;effort[initializing]=0.
            self.effort_pre.copy_(request);self.effort.copy_(effort)
        self.robot.set_joint_effort_target_index(target=self.effort,joint_ids=self.ids)
        self.pd_counter+=1

    def _geometry_gaps(self):
        data=self.robot.data
        gaps=[];chassis=[]
        z=torch.tensor([[0.,0.,1.]],device=self.device).expand(self.num_envs,-1)
        for shape,body,matrix in self.geometry:
            n=quat_apply_inverse(data.body_quat_w.torch[:,body],z)
            normal=n@matrix[:3,:3]
            center=(n*matrix[:3,3]).sum(-1)+data.body_pos_w.torch[:,body,2]
            if shape['type']=='Cube':
                extent=normal.abs().sum(-1)*float(shape['size'])/2
            elif shape['type']=='Sphere':
                extent=torch.linalg.vector_norm(normal,dim=-1)*float(shape['radius'])
            else:
                axis='XYZ'.index(shape['axis'])
                radial=torch.linalg.vector_norm(normal if shape['type']=='Capsule'
                    else normal[:,[i for i in range(3) if i!=axis]],dim=-1)*float(shape['radius'])
                extent=normal[:,axis].abs()*float(shape['height'])/2+radial
            gap=center-extent-self.cfg.ground_height_m
            gaps.append(gap)
            if shape['body']=='robot':chassis.append(gap)
        return torch.stack(gaps,-1),torch.stack(chassis,-1).amin(-1)

    def _get_dones(self):
        self._motion_state();self._closure()
        data=self.robot.data
        forces=torch.linalg.vector_norm(self.sensor.data.net_forces_w.torch,dim=-1)
        self.contact_force.copy_(forces[:,self.wheel_sensor_ids])
        gaps,chassis=self._geometry_gaps();self.chassis_clearance=chassis
        q=data.joint_pos.torch;dq=data.joint_vel.torch[:,self.ids]
        if self.recovery_config.get('standing_task'):
            angular,gravity=self._motion_state()
            from native_stand.recovery.standing import longitudinal_geometry
            centers=data.body_pos_w.torch[:,self.wheel_body_ids]-data.root_pos_w.torch[:,None,:]
            centers=quat_apply_inverse(data.root_quat_w.torch[:,None,:].expand(-1,2,-1),centers)
            self.wheel_longitudinal_offset.copy_(longitudinal_geometry(centers,gravity).abs())
            self.wheel_geometry_snapshot.copy_(torch.cat((centers.flatten(1),gravity,q[:,self.ids][:,contract.LEG_COLUMNS]),-1))
            anchors=q.new_tensor(self.recovery_config['standing_task']['hip_anchors_root_m'])
            hip=data.root_pos_w.torch[:,None,:]+quat_apply(
                data.root_quat_w.torch[:,None,:].expand(-1,2,-1),anchors.expand(self.num_envs,-1,-1))
            self.standing_snapshot.copy_(posture(gravity,q[:,self.ids],
                dq[:,contract.WHEEL_COLUMNS],hip,data.body_pos_w.torch[:,self.wheel_body_ids],
                data.root_lin_vel_w.torch,angular))
        nonfinite=(~torch.isfinite(data.root_state_w.torch).all(-1)|
            ~torch.isfinite(q).all(-1)|~torch.isfinite(data.joint_vel.torch).all(-1)|
            ~torch.isfinite(self.effort).all(-1))
        if self.recovery_config.get('standing_task'):
            nonfinite |= ~torch.isfinite(self.wheel_longitudinal_offset)
        closure=self.closure_each.amax(-1)>self.cfg.closure_fault_m
        penetration=gaps.amin(-1)<-self.recovery_config['initialization']['severe_penetration_m']
        outside=((q<self.joint_limits[:,0]-1e-3)|(q>self.joint_limits[:,1]+1e-3)).any(-1)
        fault=nonfinite|closure|penetration|outside
        tilt=self.up<self.cfg.minimum_up_cos
        restricted=(forces[:,self.restricted_sensor].amax(-1)>self.recovery_config['contacts']['restricted_force_max_n']
            if self.restricted_sensor else torch.zeros(self.num_envs,dtype=torch.bool,device=self.device))
        gate=self.recovery_config['gate']
        velocity=data.root_lin_vel_w.torch
        initializing=self.fsm.mode==int(Mode.INITIALIZING)
        initial=self.recovery_config['initialization']
        self.initial_age.add_(initializing.float()*self.step_dt)
        # One-time second zero after passive settling, before static validation.
        # A full dwell must still pass afterwards; no zeroing of active episodes.
        second_zero=initializing&~self.initial_velocity_zeroed&(self.initial_age>=initial['settle_min_s'])
        zero_ids=second_zero.nonzero(as_tuple=False).flatten()
        if len(zero_ids):
            zero_initial_velocities(self.robot,zero_ids,len(self.robot.joint_names),self.device)
            self.initial_velocity_zeroed[zero_ids]=True
            self.settle_dwell[zero_ids]=0.
        velocity=data.root_lin_vel_w.torch
        root_bounds=self.pose_root_bounds[self.initial_pose_index]
        chassis_bounds=self.pose_chassis_bounds[self.initial_pose_index]
        settled=((torch.linalg.vector_norm(velocity,dim=-1)<=initial['settled_linear_speed_max_mps'])&
            (torch.linalg.vector_norm(data.root_ang_vel_w.torch,dim=-1)<=initial['settled_angular_speed_max_rad_s'])&
            (data.joint_vel.torch[:,self.settlement_joint_ids].abs().amax(-1)<=initial['settled_joint_speed_max_rad_s'])&
            (torch.acos(self.up.clamp(-1.,1.))<=initial['tilt_max_rad'])&
            (self.root_height>=root_bounds[:,0])&(self.root_height<=root_bounds[:,1])&
            (chassis>=chassis_bounds[:,0])&(chassis<=chassis_bounds[:,1])&~fault&~restricted)
        self.settle_dwell.copy_(torch.where(initializing&self.initial_velocity_zeroed&~second_zero&settled,self.settle_dwell+self.step_dt,0.))
        accepted=initializing&(self.initial_age>=initial['settle_min_s'])&(self.settle_dwell>=initial['settle_dwell_s'])
        rejected=initializing&((self.initial_age>=initial['settle_max_s'])|fault|restricted|tilt)&~accepted
        self.initial_accepts.index_add_(0,self.initial_pose_index,accepted.long())
        self.initial_rejects.index_add_(0,self.initial_pose_index,rejected.long())
        self.initialization_checked |= accepted
        self.initial_height[accepted]=self.root_height[accepted]
        if self.reverse_curriculum is not None:
            self.initial_height[accepted]=self.recovery_config.get('lift_reference_height_m',.168)
        self.fsm.mode[accepted]=int(Mode.RECOVERY)
        physical_eligible=((self.root_height>=gate['height_m'][0])&(self.root_height<=gate['height_m'][1])&
            (torch.acos(self.up.clamp(-1.,1.))<=gate['tilt_max_rad'])&
            (torch.linalg.vector_norm(data.root_ang_vel_w.torch,dim=-1)<=gate['angular_speed_max_rad_s'])&
            (torch.linalg.vector_norm(velocity,dim=-1)<=gate['linear_speed_max_mps'])&
            (dq[:,contract.LEG_COLUMNS].abs().amax(-1)<=gate['joint_speed_max_rad_s'])&
            (q[:,self.ids][:,contract.LEG_COLUMNS].abs().amax(-1)<=gate['joint_abs_max_rad'])&
            (self.contact_force>gate['dual_contact_min_n']).all(-1)&
            (chassis>=gate['chassis_clearance_min_m']))
        eligible=(physical_eligible&(self.control_jump<=gate['target_jump_max_rad'])&
            (self.wheel_control_jump<=gate['wheel_target_jump_max_rad_s'])&
            ((self.executed_leg-self.reference[:,contract.LEG_COLUMNS]).abs().amax(-1)<=.5))
        # Pre-reset evidence only; these mirror existing predicates without changing them.
        if self.recovery_config.get('gate_diagnostics'):
            checks=torch.stack(((self.root_height>=gate['height_m'][0])&(self.root_height<=gate['height_m'][1]),
                torch.acos(self.up.clamp(-1.,1.))<=gate['tilt_max_rad'],
                torch.linalg.vector_norm(data.root_ang_vel_w.torch,dim=-1)<=gate['angular_speed_max_rad_s'],
                torch.linalg.vector_norm(velocity,dim=-1)<=gate['linear_speed_max_mps'],
                dq[:,contract.LEG_COLUMNS].abs().amax(-1)<=gate['joint_speed_max_rad_s'],
                q[:,self.ids][:,contract.LEG_COLUMNS].abs().amax(-1)<=gate['joint_abs_max_rad'],
                (self.contact_force>gate['dual_contact_min_n']).all(-1),chassis>=gate['chassis_clearance_min_m'],
                self.control_jump<=gate['target_jump_max_rad'],
                self.wheel_control_jump<=gate['wheel_target_jump_max_rad_s'],
                (self.executed_leg-self.reference[:,contract.LEG_COLUMNS]).abs().amax(-1)<=.5),-1)
            self.gate_diagnostic_snapshot.copy_(torch.cat((checks.float(),velocity,
                data.root_ang_vel_w.torch,self.control_jump[:,None],self.wheel_control_jump[:,None],
                self.fsm.dwell[:,None]),-1))
            if self.episode_mode=='continuous_holding':
                self.gate_diagnostic_snapshot[:,[8,9,17,18]]=float('nan')
        enter=(self.fsm.mode==int(Mode.RECOVERY))&eligible&(self.fsm.dwell+self.step_dt>=self.fsm.config['gate_dwell_s']-1e-6)
        self.handover_origin[enter]=data.root_pos_w.torch[enter,:2]
        self.handover_leg[enter]=self.executed_leg[enter]
        self.handover_wheel[enter]=self.executed_wheel[enter]
        excursion=torch.linalg.vector_norm(data.root_pos_w.torch[:,:2]-self.handover_origin,dim=-1)
        stable=(physical_eligible & (self.vx.abs()<=gate['stand_vx_abs_max_mps'])&
            (self.vy.abs()<=gate['stand_vy_abs_max_mps'])&
            (self.yaw.abs()<=gate['stand_yaw_abs_max_rad_s'])&(excursion<=gate['stand_excursion_max_m']))
        if self.fsm.config.get('success_mode') == 'autonomous_hold':
            stable=autonomous_stable(self.root_height,torch.acos(self.up.clamp(-1.,1.)),
                velocity,data.root_ang_vel_w.torch,self.contact_force,chassis,
                self.recovery_config['autonomous_stability']) & ~initializing & ~fault & ~restricted
            if self.recovery_config.get('standing_task'):
                protocol=self.recovery_config['standing_task']['protocol']
                stable &= standing_success_mask(self.standing_snapshot,protocol)
            enter=torch.zeros_like(enter)  # No teacher handover in this task.
        previous_mode=self.fsm.mode.clone()
        timeout=torch.zeros_like(fault)
        if self.holding_episode is not None and not self.continuous_evaluation:
            self.fsm.age.add_((~initializing).float()*self.step_dt)
            failed=(tilt|restricted|rejected)&~fault
            self.holding_episode.observe(self.root_height,self.contact_force,self.standing_snapshot[:,:2],
                torch.acos(self.up.clamp(-1.,1.)),self.closure_each.amax(-1),
                (self.effort.abs()>=self.effort.new_tensor(contract.EFFORT_LIMITS)-1e-4).any(-1),
                active=~initializing,valid=self.initialization_checked&~failed&~fault)
            timeout,pulse=self.holding_episode.outcome(failed=failed,fault=fault)
            self.fsm.mode[failed]=int(Mode.RECOVERY_FAILED)
            self.fsm.mode[fault]=int(Mode.RUNTIME_FAULT)
            self.holding_rollout_counts.add_(torch.stack((timeout.long().sum(),(timeout&~pulse).long().sum())))
        else:
            pulse,failed,fault=self.fsm.step(eligible&~accepted,stable,fault,tilt|restricted|rejected,
                dt=self.step_dt,finish_on_success=not self.continuous_evaluation)
        self.success_pulse.copy_(pulse)
        self.initializing_step=initializing
        self.rollout_events.add_(torch.stack((initializing.long().sum(),
            (self.fsm.mode==int(Mode.RECOVERY)).long().sum(),enter.long().sum(),
            pulse.long().sum(),(failed&~fault).long().sum(),fault.long().sum(),rejected.long().sum())))
        self.terminal_causes={'nonfinite':nonfinite,'closure':closure|penetration|outside,
            'height':torch.zeros_like(fault),'tilt':tilt,'body_contact':restricted,'joint_safety':outside}
        terminated=failed|fault
        if self.holding_episode is None:
            terminated |= pulse & (not self.continuous_evaluation)
        certificate_evaluated=(timeout if self.holding_episode is not None and not self.continuous_evaluation
                               else pulse|terminated)
        self.episode_result_snapshot.copy_(torch.stack((terminated,timeout,pulse,fault,certificate_evaluated),-1))
        if self.curriculum_training and not self.continuous_evaluation:
            self.pose_episode_metrics.observe(self.initial_pose_index,done=terminated|timeout,
                success=pulse,timeout=timeout,fault=fault,initial_valid=self.initialization_checked,
                duration=self.episode_length_buf.float()*self.step_dt)
        if self.holding_episode is not None and not self.continuous_evaluation:
            self.holding_episode.record_outcomes(terminated=terminated,truncated=timeout,fault=fault)
        if self.reverse_curriculum is not None and self.curriculum_training:
            self.reverse_events.copy_(torch.stack((self.episode_stage,pulse.long(),fault.long()),-1))
            self.reverse_event_valid.copy_(terminated|timeout)
            if self.reverse_cursor>=len(self.reverse_buffer): raise RuntimeError('Reverse rollout buffer exhausted')
            self.reverse_buffer[self.reverse_cursor].copy_(self.reverse_events)
            self.reverse_valid[self.reverse_cursor].copy_(terminated|timeout)
            self.reverse_cursor+=1
        # One batched pre-reset snapshot. Never read the replacement episode.
        scalar=torch.stack((self.fsm.age,self.fsm.verify,pulse.float(),
            failed.float(),fault.float(),self.initial_pose_index.float(),self.root_height,
            self.vx,self.vy,self.yaw,self.contact_force[:,0],self.contact_force[:,1],
            self.closure_each.amax(-1),chassis,gaps.amin(-1),
            torch.acos(self.up.clamp(-1.,1.)),excursion,
            (self.effort.abs()>=self.effort.new_tensor(contract.EFFORT_LIMITS)-1e-4).any(-1).float(),
            self.fsm.mode.float()),-1)
        self.recovery_snapshot.copy_(torch.cat((scalar,data.root_pos_w.torch,
            data.root_quat_w.torch,self.joint_limit_clip_fraction[:,None],
            self.raw_action.abs().amax(-1,keepdim=True),(self.effort_pre-self.effort).abs().amax(-1,keepdim=True),
            self.initialization_checked.float()[:,None],rejected.float()[:,None],self.reset_count.float()[:,None],
            previous_mode.float()[:,None],self.handover_target_rate_peak),-1))
        self.recovery_cause_snapshot.copy_(torch.stack(tuple(self.terminal_causes.values()),-1))
        self.recovery_control_snapshot.copy_(torch.cat((q[:,self.ids],dq,self.raw_action,self.action,
            self.target_before_joint_limit,self.leg_target,self.effort_pre,self.effort,
            data.applied_torque.torch[:,self.ids],self.closure_each),-1))
        self.recovery_snapshot_valid.copy_(terminated|timeout)
        return terminated,timeout

    def _get_rewards(self):
        q=self.robot.data.joint_pos.torch[:,self.ids]
        margin=(q[:,contract.LEG_COLUMNS].abs()/self.cfg.leg_position_scale_rad).square().mean(-1)
        failure=(self.fsm.mode==int(Mode.RECOVERY_FAILED))|(self.fsm.mode==int(Mode.RUNTIME_FAULT))
        angular,gravity=self._motion_state()
        pitch=torch.atan2(gravity[:,2],-gravity[:,1])
        # Body frame uses +Y as nominal up; this is the canonical roll
        # component orthogonal to the existing pitch definition.
        roll=torch.atan2(gravity[:,0],-gravity[:,1])
        wheel_velocity=self.robot.data.joint_vel.torch[:,self.ids][:,contract.WHEEL_COLUMNS]
        active_q=self.robot.data.joint_pos.torch[:,self.ids]
        # Authored hip axes mirror; active-link axes have the same sign.
        leg_symmetry=torch.stack((active_q[:,0]+active_q[:,3],active_q[:,1]-active_q[:,4]),-1).square().mean(-1)
        support_balance=(self.contact_force[:,0]-self.contact_force[:,1]).abs()/self.contact_force.sum(-1).clamp_min(1.)
        support_region=(self.leg_target-self.reference[:,contract.LEG_COLUMNS]).square().mean(-1)
        wheel_radius=self.recovery_config.get('wheel_radius_m',.06)
        slip_proxy=(wheel_velocity*wheel_radius-self.vx[:,None]).abs().mean(-1)
        total,raw,weighted=process_reward(self.root_height,self.initial_height,
            torch.full_like(self.root_height,self.command_height),self.up,self.effort,
            self.action-self.previous_action,margin,self.success_pulse,failure,
            weights=self.reward_config,dt=self.step_dt,
            settling_config=self.recovery_config.get('settling_reward'),
            linear_velocity=self.robot.data.root_lin_vel_w.torch,
            angular_velocity=(angular if self.recovery_config.get('standing_task') else
                              self.robot.data.root_ang_vel_w.torch),pitch=pitch,roll=roll,
            contact=self.contact_force,wheel_velocity=wheel_velocity,
            leg_symmetry=leg_symmetry,support_balance=support_balance,
            support_region=support_region,slip_proxy=slip_proxy,
            wheel_longitudinal_offset=self.wheel_longitudinal_offset,
            standing_config=self.recovery_config.get('standing_task',{}).get('reward'),
            standing_diagnostics=self.standing_snapshot)
        # Initialization has no agent control; it contributes no task reward.
        total[self.initializing_step]=0.
        for value in raw.values():value[self.initializing_step]=0.
        for value in weighted.values():value[self.initializing_step]=0.
        self.reward_raw=raw;self.reward_weighted=weighted
        controlled=~self.initializing_step
        self.height_stats.add_(torch.stack(((self.root_height*controlled).sum(),
            ((self.root_height-self.command_height).abs()*controlled).sum(),
            (torch.linalg.vector_norm(self.robot.data.root_lin_vel_w.torch,dim=-1)*controlled).sum())))
        self.height_count.add_(controlled.sum())
        self.wheel_geometry_stats.add_((self.wheel_longitudinal_offset*controlled).sum())
        if self.recovery_config.get('standing_task'):
            self.standing_stats.add_((self.standing_snapshot.abs()*controlled[:,None]).sum(0))
        self.extras['native_stand']={'termination':self.terminal_causes,'closure_max':self.closure_each.amax()}
        return total

    def _get_observations(self):
        result=super()._get_observations()
        if self.recovery_ready:
            angular,gravity=self._motion_state();data=self.robot.data
            self.stand_frame=contract.frame(angular,gravity,self.command,
                data.joint_pos.torch[:,self.ids],data.joint_vel.torch[:,self.ids],
                self.stand_previous,self.reference)
            reset=self.episode_length_buf==0
            self.stand_history.copy_(contract.history(self.stand_history,self.stand_frame,reset))
        return result

    def initialization_summary(self):
        packed=torch.stack((self.initial_attempts,self.initial_accepts,self.initial_rejects),-1).cpu().tolist()
        return [{'pose_id':pose['pose_id'],'attempted':row[0],'accepted':row[1],'rejected':row[2],
            'pending':row[0]-row[1]-row[2],'rejection_rate_decided':row[2]/(row[1]+row[2]) if row[1]+row[2] else None}
            for pose,row in zip(self.pose_library['poses'],packed)]

    def begin_task_rollout(self):
        self.rollout_events.zero_()
        self.pose_episode_metrics.reset()
        self.holding_rollout_counts.zero_()
        if self.holding_episode is not None:
            self.holding_episode.begin_rollout()
        self.height_stats.zero_();self.height_count.zero_()
        self.standing_stats.zero_()
        self.wheel_geometry_stats.zero_()
        self.reverse_cursor=0;self.reverse_valid.zero_()

    def collect_reverse_episodes(self):
        if self.reverse_curriculum is None or not self.curriculum_training: return
        rows=self.reverse_buffer[self.reverse_valid].cpu().tolist()
        self.reverse_curriculum.record_episodes(rows)
        self.reverse_event_valid.zero_()

    def recovery_curriculum_checkpoint_state(self):
        if self.reverse_curriculum is None:
            return None
        return self.reverse_curriculum.checkpoint_state()

    def restore_recovery_curriculum(self, state):
        if self.reverse_curriculum is None:
            raise ValueError('checkpoint contains Recovery curriculum but environment has none')
        restored=self.reverse_curriculum.restore_checkpoint_state(state)
        self.family=self.reverse_curriculum.current_level()['pose_family']
        return restored

    def task_rollout_summary(self):
        self.collect_reverse_episodes()
        names=('initialization_env_steps','recovery_env_steps','handover_attempts',
            'complete_successes','task_failures','runtime_faults','initial_rejections')
        height=(self.height_stats/self.height_count.clamp_min(1)).cpu().tolist()
        return {'counts':dict(zip(names,self.rollout_events.cpu().tolist())),
            'episode_summary_version':1,'episodes_by_pose':self.pose_episode_metrics.summary(),
            'effective_task_protocol':self.effective_task_protocol,
            'motion':dict(zip(('mean_height_m','mean_abs_height_error_m','mean_linear_speed_mps'),height)),
            'reverse_curriculum':self.reverse_curriculum.state() if self.reverse_curriculum else None,
            'leg_pair_projection_enabled':False,
            'mean_wheel_longitudinal_offset_m':float((self.wheel_geometry_stats/self.height_count.clamp_min(1)).cpu()),
            'initialization_steps_charge_sample_budget':True,
            'success_requires_frozen_stand_5s':self.fsm.config.get('success_mode')!='autonomous_hold',
            'success_mode':self.fsm.config.get('success_mode','handover'),
            'episode_mode':self.episode_mode,
            'teacher_forward_enabled':self.episode_mode!='continuous_holding' and not bool(self.recovery_config.get('rising_task')),
            'required_stable_s':None if self.holding_episode is not None else self.fsm.config['verify_s'],
            'training_episode':({
                'mode':'fixed_horizon','seconds':self.holding_episode.protocol['seconds'],
                'steady_window_s':self.holding_episode.protocol['steady_window_s'],
                'normal_timeouts':int(self.holding_rollout_counts[0].cpu()),
                'window_failed_timeouts':int(self.holding_rollout_counts[1].cpu()),
                'episode_results':self.holding_episode.rollout_summary(),
                'success_ends_episode':False,'timeout_bootstrap':'installed PPO transition value'}
                if self.holding_episode is not None else None),
            'standing_posture':dict(zip(('mean_abs_'+field for field in POSTURE_FIELDS),
                (self.standing_stats/self.height_count.clamp_min(1)).cpu().tolist()))
                if self.recovery_config.get('standing_task') else None}
