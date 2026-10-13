"""Isaac Lab task adapter around the existing native physical-joint scene."""
import torch
from gymnasium import spaces
from isaaclab.utils import configclass

from native_stand.env import NativeStandCfg, NativeStandEnv
from native_stand.command_v6.domain import contract, command_schedule, reward
from native_stand.command_v6.domain.tracking_width import linear_width
from native_stand.command_v6.domain.episode_curriculum import EpisodeTracker, EpisodeWindows


@configclass
class CommandEnvCfg(NativeStandCfg):
    episode_length_s = 6.0
    observation_space = {"policy":spaces.Box(-1e6,1e6,shape=(25,)),
                         "history":spaces.Box(-1e6,1e6,shape=(125,))}
    state_space = spaces.Box(-1e6,1e6,shape=(25,))
    episode_curriculum = None


class CommandEnv(NativeStandEnv):
    cfg: CommandEnvCfg

    def __init__(self,cfg,*,stage,command_height,reward_config,schedule_s,**kwargs):
        self.stage_spec = stage
        self.command_height = command_height
        self.reward_config = dict(reward_config)
        self.schedule_s = schedule_s
        self.forced_target = None
        self.capture_terminal = False
        super().__init__(cfg,**kwargs)
        self.history = torch.zeros((self.num_envs,125),device=self.device)
        self.history_needs_init.fill_(True)
        self.target_xy = torch.zeros((self.num_envs,2),device=self.device)
        self.command = torch.zeros((self.num_envs,3),device=self.device)
        self.command[:,2] = command_height
        self.command_counts = torch.zeros(len(stage["commands"]),device=self.device,dtype=torch.long)
        self.training_motion=torch.zeros(self.num_envs,5,device=self.device)
        self.command_index=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.raw_action=torch.zeros_like(self.action)
        self.task_stat_sum=torch.zeros(len(stage['commands']),14,device=self.device,dtype=torch.float64)
        self.task_stat_count=torch.zeros(len(stage['commands']),device=self.device,dtype=torch.long)
        self.width_diagnostics=bool(reward_config.get('width_diagnostics',False))
        self.width_stat_sum=torch.zeros(len(stage['commands']),2,device=self.device,dtype=torch.float64)
        self.channel_stat_sum=torch.zeros(len(stage['commands']),12,device=self.device,dtype=torch.float64)
        self.episode_tracker=None
        self.episode_windows=None
        if cfg.episode_curriculum is not None:
            self.episode_tracker=EpisodeTracker(self.num_envs,self.device,cfg.episode_curriculum,self.step_dt)
            self.episode_windows=EpisodeWindows(cfg.episode_curriculum)

    def set_evaluation_target(self,vx,yaw):
        self.forced_target=(float(vx),float(yaw))

    def measure_posture_geometry(self):
        """Explicit diagnostic call; no reward/action/reset changes."""
        from isaaclab.utils.math import quat_apply
        from native_stand.command_v6.domain.posture_geometry import measure
        data=self.robot.data
        hip_ids=[self.body_ids[side+'_upper_leg'] for side in ('left','right')]
        body=data.body_pos_w.torch
        q=data.root_quat_w.torch
        columns=[quat_apply(q,q.new_tensor(axis).expand(self.num_envs,-1))
                 for axis in ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))]
        return measure(body[:,hip_ids],body[:,self.wheel_body_ids],torch.stack(columns,dim=-1))

    def clear_evaluation_target(self):
        self.forced_target=None

    def change_stage(self, stage, *, linear_denominator=None, yaw_denominator=None):
        self.stage_spec=stage
        if linear_denominator is not None:
            self.reward_config['linear_error_denominator']=linear_denominator
        if yaw_denominator is not None:
            self.reward_config['yaw_error_denominator']=yaw_denominator
        self.command_counts=torch.zeros(len(stage['commands']),device=self.device,dtype=torch.long)
        self.task_stat_sum=torch.zeros(len(stage['commands']),14,device=self.device,dtype=torch.float64)
        self.task_stat_count=torch.zeros(len(stage['commands']),device=self.device,dtype=torch.long)
        self.width_stat_sum=torch.zeros(len(stage['commands']),2,device=self.device,dtype=torch.float64)
        self.channel_stat_sum=torch.zeros(len(stage['commands']),12,device=self.device,dtype=torch.float64)
        # Explicit full reset marks task-switch interruptions, never completed episodes.
        self.reset()

    def begin_task_rollout(self):
        self.task_stat_sum.zero_()
        self.task_stat_count.zero_()
        self.width_stat_sum.zero_()
        self.channel_stat_sum.zero_()

    def task_rollout_summary(self):
        count=self.task_stat_count.cpu().tolist()
        means=(self.task_stat_sum/self.task_stat_count.clamp_min(1)[:,None]).cpu().tolist()
        names=('height_m','height_error_abs_m','vx_error_abs_mps','vy_abs_mps','yaw_error_abs_rad_s',
               'dual_contact','tilt_rad','saturation','action_clip_fraction','leg_projection_fraction',
               'timeout','task_failure','vx_mps','yaw_rad_s')
        result=[{'command':command,'samples':n,'means':dict(zip(names,values)) if n else None,
                 'leg_pair_projection_enabled':self.cfg.leg_pair_radius_rad>0.}
                for command,n,values in zip(self.stage_spec['commands'],count,means)]
        channels=(self.channel_stat_sum/self.task_stat_count.clamp_min(1)[:,None]).cpu().tolist()
        for row,values in zip(result,channels):
            row['action_clip_fraction_by_channel']=values[:6] if row['samples'] else None
            row['effort_saturation_fraction_by_channel']=values[6:] if row['samples'] else None
        if self.width_diagnostics:
            diagnostics=(self.width_stat_sum/self.task_stat_count.clamp_min(1)[:,None]).cpu().tolist()
            for row,values in zip(result,diagnostics):
                row['width_phase_diagnostics']=dict(zip(('linear_denominator','hold_fraction'),values)) if row['samples'] else None
        return result

    def _reset_idx(self,env_ids):
        super()._reset_idx(env_ids)
        ids=torch.arange(self.num_envs,device=self.device) if env_ids is None else env_ids.long()
        if not hasattr(self,"target_xy"):
            return
        if self.forced_target is None:
            from native_stand.command_v6.domain.command_sampling import resolve as sampling_plan
            sampling_plan(self.stage_spec,self.num_envs)
            slots=self.stage_spec.get('sampling_slots')
            if slots is not None:
                slot_tensor=torch.as_tensor(slots,device=self.device,dtype=torch.long)
                chosen=slot_tensor[ids % len(slot_tensor)]
                commands_tensor=self.target_xy.new_tensor(self.stage_spec['commands'])
                values=commands_tensor[chosen]
                counts=torch.bincount(chosen,minlength=len(self.stage_spec['commands']))
            else:
                values,counts=command_schedule.sample(self.stage_spec["commands"],
                    self.stage_spec["weights"],len(ids),device=self.device)
            self.target_xy[ids]=values
            self.command_counts+=counts
            commands=self.target_xy.new_tensor(self.stage_spec['commands'])
            self.command_index[ids]=(values[:,None,:]==commands[None,:,:]).all(-1).long().argmax(-1)
        else:
            self.target_xy[ids]=self.target_xy.new_tensor(self.forced_target)
        self.command[ids]=command_schedule.effective(self.target_xy[ids],
            torch.zeros(len(ids),device=self.device),height=self.command_height,
            entry=self.schedule_s[0],ramp=self.schedule_s[1],
            hold=self.schedule_s[2],exit=self.schedule_s[3])
        self.history_needs_init[ids]=True
        if self.stage_spec.get('enforce_whitelist',False) and self.forced_target is None:
            allowed=self.target_xy.new_tensor(self.stage_spec['commands'])
            if not (self.target_xy[ids,None,:]==allowed[None,:,:]).all(-1).any(-1).all():
                raise RuntimeError('training command outside unlocked stage whitelist')
        if getattr(self,'episode_tracker',None) is not None:
            self.episode_tracker.reset(ids,self.robot.data.root_pos_w.torch[:,:2],self.episode_windows.level)

    def collect_episode_curriculum(self):
        if self.episode_tracker is None:
            return None
        rows=self.episode_tracker.collect()
        windows=self.episode_windows.consume(rows)
        return {'state':self.episode_windows.state(),'windows':windows,
            'completed_episodes':len(rows),'timeout_count':sum(row[1] for row in rows),
            'task_failure_count':sum(row[2] for row in rows),
            'episode_means':{field:sum(row[index] for row in rows)/len(rows) if rows else None
                for index,field in enumerate(('level','timeout','task_failure','duration_s','vx_abs','yaw_abs',
                    'excursion_m','tilt_rad','contact_fraction','height_m','saturation_fraction','closure_m'))}}

    def _pre_physics_step(self,actions):
        self.command.copy_(command_schedule.effective(self.target_xy,
            self.episode_length_buf.float()*self.step_dt,height=self.command_height,
            entry=self.schedule_s[0],ramp=self.schedule_s[1],
            hold=self.schedule_s[2],exit=self.schedule_s[3]))
        self.previous_action.copy_(self.action)
        self.raw_action.copy_(actions)
        clipped,legs,wheels=contract.targets(actions,self.reference,
            leg_scale=self.cfg.leg_position_scale_rad,
            combined_radius=self.cfg.leg_pair_radius_rad,
            wheel_scale=self.cfg.wheel_speed_scale_rad_s)
        self.action.copy_(clipped)
        self.leg_target.copy_(legs)
        self.wheel_target.copy_(wheels)
        self.pd_counter=0

    def _get_observations(self):
        angular,gravity=self._motion_state()
        data=self.robot.data
        q=data.joint_pos.torch[:,self.ids]
        dq=data.joint_vel.torch[:,self.ids]
        # Observation advertises the command that the next action will execute.
        self.command.copy_(command_schedule.effective(self.target_xy,
            self.episode_length_buf.float()*self.step_dt,height=self.command_height,
            entry=self.schedule_s[0],ramp=self.schedule_s[1],hold=self.schedule_s[2],exit=self.schedule_s[3]))
        frame=contract.frame(angular,gravity,self.command,q,dq,self.action,self.reference)
        self.history.copy_(contract.history(self.history,frame,self.history_needs_init))
        self.history_needs_init.fill_(False)
        return {"policy":frame,"history":self.history.clone()}

    def _get_rewards(self):
        q=self.robot.data.joint_pos.torch[:,self.ids]
        total,raw,weighted=reward.compute(self.root_height,self.up,self.vx,self.vy,
            self.yaw,self.command,self.contact_force>2.,self.effort,self.action,
            self.previous_action,q[:,contract.LEG_COLUMNS],self.reset_terminated,
            weights=self.reward_config,height_width=self.reward_config["height_width_m"],
            linear_denominator=linear_width(self.target_xy,self.reward_config),
            yaw_denominator=self.reward_config["yaw_error_denominator"],
            terminal_penalty=self.reward_config["terminal_penalty"],dt=self.step_dt,
            action_delta_wheel_factor=self.reward_config.get('action_delta_wheel_factor',1.),
            posture_config=self.reward_config.get('posture_balance'),
            posture_geometry=(self.measure_posture_geometry() if self.reward_config.get('posture_balance') else None))
        self.reward_raw=raw
        self.reward_weighted=weighted
        # Fault detection remains on the GPU; the trainer checks before PPO.
        self.extras["native_stand"]={"termination":self.terminal_causes,
                                      "closure_max":self.closure_each.amax()}
        return total

    def _get_dones(self):
        if self.capture_terminal:
            return super()._get_dones()
        self._motion_state()
        self._closure()
        data=self.robot.data
        force=torch.linalg.vector_norm(
            self.sensor.data.net_forces_w.torch[:,self.wheel_sensor_ids],dim=-1)
        self.contact_force.copy_(force)
        body_force=torch.linalg.vector_norm(
            self.sensor.data.net_forces_w.torch[:,self.forbidden_sensor_ids],dim=-1).amax(-1)
        q=data.joint_pos.torch[:,self.ids]
        nonfinite=(~torch.isfinite(data.root_state_w.torch).all(-1)|
                   ~torch.isfinite(data.joint_pos.torch).all(-1)|
                   ~torch.isfinite(data.joint_vel.torch).all(-1)|
                   ~torch.isfinite(self.effort).all(-1))
        self.terminal_causes={"nonfinite":nonfinite,
            "closure":self.closure_each.amax(-1)>self.cfg.closure_fault_m,
            "height":data.root_pos_w.torch[:,2]<self.cfg.fall_root_height_m,
            "tilt":self.up<self.cfg.minimum_up_cos,
            "body_contact":body_force>self.cfg.body_contact_max_n,
            "joint_safety":(q[:,contract.LEG_COLUMNS].abs()>self.cfg.active_leg_angle_max_rad).any(-1)}
        terminated=torch.stack(tuple(self.terminal_causes.values())).any(0)
        timeout=(self.episode_length_buf>=self.episode_tracker.deadline_steps if self.episode_tracker is not None
                 else self.episode_length_buf>=self.max_episode_length-1)
        timeout=timeout & ~terminated
        if not self.capture_terminal:
            projected=contract.projection_fraction(self.action,
                leg_scale=self.cfg.leg_position_scale_rad,
                combined_radius=self.cfg.leg_pair_radius_rad)
            stats=torch.stack((self.root_height,(self.root_height-self.command[:,2]).abs(),
                (self.vx-self.command[:,0]).abs(),self.vy.abs(),(self.yaw-self.command[:,1]).abs(),
                (self.contact_force>2).all(-1).float(),torch.acos(self.up.clamp(-1.,1.)),
                (self.effort.abs()>=self.effort.new_tensor(contract.EFFORT_LIMITS)-1e-4).any(-1).float(),
                (self.raw_action.abs()>1).float().mean(-1),projected,timeout.float(),terminated.float(),self.vx,self.yaw),-1)
            self.task_stat_sum.index_add_(0,self.command_index,stats.double())
            self.task_stat_count.index_add_(0,self.command_index,torch.ones_like(self.command_index))
            self.channel_stat_sum.index_add_(0,self.command_index,torch.cat((
                (self.raw_action.abs()>1).double(),
                (self.effort.abs()>=self.effort.new_tensor(contract.EFFORT_LIMITS)-1e-4).double()),-1))
            if self.width_diagnostics:
                width=linear_width(self.target_xy,self.reward_config)
                if not isinstance(width,torch.Tensor):
                    width=torch.full_like(self.vx,width)
                time=self.episode_length_buf.float()*self.step_dt
                start=self.schedule_s[0]+self.schedule_s[1]
                hold=(time>=start)&(time<start+self.schedule_s[2])
                self.width_stat_sum.index_add_(0,self.command_index,
                    torch.stack((width,hold.float()),-1).double())
        if self.episode_tracker is not None:
            self.training_motion.copy_(torch.stack((self.vx.abs(),self.yaw.abs(),self.root_height,
                torch.acos(self.up.clamp(-1.,1.)),
                torch.linalg.vector_norm(data.root_pos_w.torch[:,:2]-self.episode_tracker.origin,dim=-1)),-1))
            self.episode_tracker.observe(data.root_pos_w.torch[:,:2],self.root_height,self.vx,self.yaw,
                self.contact_force>2.,torch.acos(self.up.clamp(-1.,1.)),self.closure_each.amax(-1),
                (self.effort.abs()>=self.effort.new_tensor(contract.EFFORT_LIMITS)-1e-4).any(-1),terminated,timeout)
        return terminated,timeout
