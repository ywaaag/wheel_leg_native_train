"""Explicit diagnostic subclass using RecoveryEnv's shared physics/PD/safety.
Import only after AppLauncher. No actor call inside env; evaluator selects one.
"""
import torch
from isaaclab.utils.math import quat_apply_inverse
from .runtime import RecoveryEnv
from .domain import Mode
from .motion_handoff import motion_frame,physical_targets,encode_executed
from .min_height import protocol,entry_mask
from .handoff_protocol import declaration,prefix_steps
from native_stand.command_v6.domain import contract

from .handoff_clock import HandoffClock

class HandoffEnv(RecoveryEnv):
    def __init__(self,*args,**kwargs):
        self.handoff_ready=False
        super().__init__(*args,**kwargs)
        self.rise_hold=HandoffClock(self.num_envs,self.device)
        self.motion_history=torch.zeros_like(self.history);self.motion_obs=None
        self.controller=torch.zeros(self.num_envs,device=self.device,dtype=torch.long)
        self.executed_prefix=torch.zeros_like(self.controller)
        self.switch_steps=0;self.handoff_ready=True
    def configure_case(self,row):
        self.switch_steps=prefix_steps(row['switch_s']);self.case_kind=row['kind']
    def configure_protocol(self,configuration):
        self.rise_hold=HandoffClock(self.num_envs,self.device,configuration)
    def configure_randomization(self,configuration):
        self.handoff_randomization=configuration
    def _reset_idx(self,ids):
        super()._reset_idx(ids)
        if getattr(self,'handoff_ready',False):
            ids=torch.arange(self.num_envs,device=self.device) if ids is None else ids
            self.motion_history[ids]=0;self.executed_prefix[ids]=0;self.controller[ids]=0
            randomization=getattr(self,'handoff_randomization',None)
            if randomization and self.case_kind!='normal_motion_baseline':
                from .handoff_ownership import yaw_randomize
                root=self.robot.data.root_state_w.torch[ids,:7].clone()
                sample=torch.rand(len(ids),device=self.device)
                root[:,3:7]=yaw_randomize(root[:,3:7],sample,randomization['root_yaw_rad'])
                self.robot.write_root_pose_to_sim_index(root_pose=root,env_ids=ids)
    def _pre_physics_step(self,actions):
        self.command[:]=self.command.new_tensor([0.,0.,.36])
        self.previous_action.copy_(self.action);self.raw_action.copy_(actions)
        initializing=self.fsm.mode==int(Mode.INITIALIZING)
        motion=(~initializing)&(self.executed_prefix>=self.switch_steps)
        self.controller.copy_(torch.where(initializing,0,torch.where(motion,2,1)))
        self.rise_hold.motion.copy_(motion)
        # Only one policy was evaluated for each controlled env in evaluator.
        clipped=actions.clamp(-1,1)
        scale=torch.where(motion,.5,getattr(self,'prefix_leg_scale',1.6))[:,None]
        legs=self.reference[:,list(contract.LEG_COLUMNS)]+clipped[:,list(contract.LEG_COLUMNS)]*scale
        wheels=clipped[:,[2,5]]*100.
        hold=initializing&self.pose_initial_hold[self.initial_pose_index]
        legs=torch.where(hold[:,None],self.initial_leg_targets,legs);wheels=torch.where(initializing[:,None],0.,wheels)
        self.target_before_joint_limit=legs.clone();legs=legs.clamp(self.active_limits[list(contract.LEG_COLUMNS),0],self.active_limits[list(contract.LEG_COLUMNS),1])
        self.joint_limit_clip_fraction=(self.target_before_joint_limit!=legs).float().mean(-1)
        self.leg_target.copy_(legs);self.wheel_target.copy_(wheels);self.executed_leg.copy_(legs);self.executed_wheel.copy_(wheels)
        self.action.copy_(encode_executed(legs,wheels,self.reference,leg_scale=1.6,wheel_scale=100.)['clipped']);self.action[initializing]=0
        self.stand_previous.zero_();self.target_rate.zero_();self.control_jump.zero_();self.wheel_control_jump.zero_();self.pd_counter=0
        self.executed_prefix+=(~initializing)&~motion
    def _get_dones(self):
        result=super()._get_dones()
        self.handoff_root_post=self.robot.data.root_state_w.torch.clone()
        self.handoff_motion_age=self.rise_hold.motion_age.clone()
        self.handoff_initial_age=self.initial_age.clone()
        self.handoff_controller=self.controller.clone()
        self.handoff_joint_q_post=self.robot.data.joint_pos.torch.clone()
        self.handoff_joint_dq_post=self.robot.data.joint_vel.torch.clone()
        return result
    def _get_rewards(self):
        # Diagnostic only: no reward/optimizer consumer. Shared safety/dones still run.
        return torch.zeros(self.num_envs,device=self.device)
    def _get_observations(self):
        result=super()._get_observations()
        if getattr(self,'handoff_ready',False):
            angular,gravity=self._motion_state();data=self.robot.data;reset=self.episode_length_buf==0
            initial=self.fsm.mode==int(Mode.INITIALIZING)
            previous_legs=torch.where(initial[:,None],self.reference[:,list(contract.LEG_COLUMNS)],self.executed_leg)
            previous_wheels=torch.where(initial[:,None],0.,self.executed_wheel)
            m=motion_frame(angular,gravity,data.joint_pos.torch[:,self.ids],data.joint_vel.torch[:,self.ids],previous_legs,previous_wheels,self.reference,self.motion_history,reset,command=getattr(self,'motion_command',None))
            self.motion_history.copy_(m['history']);self.motion_obs=m
        return result
