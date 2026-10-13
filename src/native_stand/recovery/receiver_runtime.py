"""Train only the Motion receiver; frozen Recovery prefix uses shared PD."""
import torch
from tensordict import TensorDict
from .handoff_runtime import HandoffEnv
from .domain import Mode
from .handoff_ownership import ownership
from native_stand.command_v6.domain import reward as motion_reward
from native_stand.command_v6.domain import contract

class ReceiverEnv(HandoffEnv):
    def __init__(self,*args,receiver_config,recovery_actor,motion_reward_config,**kwargs):
        self.receiver_config=receiver_config
        self.prefix_actor=recovery_actor.eval();self.prefix_actor.requires_grad_(False)
        self.receiver_reward_config=motion_reward_config
        self.receiver_ready=False
        super().__init__(*args,**kwargs)
        self.switch_steps=50;self.case_kind='receiver_training'
        self.configure_protocol(receiver_config['protocol'])
        self.receiver_ready=True
        self.ownership_counts=torch.zeros(6,device=self.device,dtype=torch.long)
        self.ownership_by_family=torch.zeros((2,3),device=self.device,dtype=torch.long)
        self.receiver_previous_action=torch.zeros_like(self.action)
    def _reset_idx(self,ids):
        super()._reset_idx(ids)
        if getattr(self,'receiver_ready',False):
            ids=torch.arange(self.num_envs,device=self.device) if ids is None else ids
            self.receiver_previous_action[ids]=0
    def actor_valid_pre(self):
        threshold=torch.where(self.pose_direct_reset[self.initial_pose_index],0,50)
        _,valid=ownership(self.fsm.mode==int(Mode.INITIALIZING),self.initialization_checked,self.executed_prefix,threshold)
        original=getattr(self,'return_to_original',torch.zeros_like(valid))
        return valid&~original
    def compose_training_action(self,requested):
        # Requested receiver samples remain in PPO storage, never replaced by prefix actions.
        valid=self.actor_valid_pre();initial=self.fsm.mode==int(Mode.INITIALIZING)
        original=getattr(self,'return_to_original',torch.zeros_like(valid))&~initial&self.initialization_checked
        executing=requested.clone();executing[~valid&~original]=0
        prefix=~valid&~initial&~original
        if prefix.any():
            observation=TensorDict(self.recovery_observation,batch_size=[self.num_envs])
            executing[prefix]=self.prefix_actor(observation[prefix],stochastic_output=False)
        return executing
    def _pre_physics_step(self,actions):
        threshold=torch.where(self.pose_direct_reset[self.initial_pose_index],0,50)
        self.switch_steps=threshold
        valid=self.actor_valid_pre()
        self.receiver_control_pre=valid.clone()
        self.receiver_previous_action.copy_(self.motion_obs['previous_action_readback']['clipped'])
        super()._pre_physics_step(actions)
        original=getattr(self,'return_to_original',torch.zeros_like(valid))&(self.fsm.mode!=int(Mode.INITIALIZING))&self.initialization_checked
        self.controller[original]=4
        self.ownership_counts[5]+=original.sum()
        self.ownership_counts[:3]+=torch.stack(((self.controller==0).sum(),(self.controller==1).sum(),(self.controller==2).sum()))
        normal=self.pose_direct_reset[self.initial_pose_index]
        for group,mask in enumerate((~normal,normal)):
            self.ownership_by_family[group]+=torch.stack(tuple(((self.controller==stage)&mask).sum() for stage in (0,1,2)))
    def _get_observations(self):
        recovery=super()._get_observations()
        self.recovery_observation=recovery
        if not getattr(self,'handoff_ready',False):return recovery
        # Policy/critic see the receiver's native .40 command and continuous history.
        return {'policy':self.motion_obs['policy'],'history':self.motion_obs['history']}
    def _get_dones(self):
        result=super()._get_dones()
        if getattr(self,'receiver_ready',False):
            self.ownership_counts[3]+=(self.handoff_controller==2).logical_and(result[0]|result[1]).sum()
            self.ownership_counts[4]+=(self.handoff_controller==2).logical_and(self.handoff_motion_age<=.010001).sum()
        return result
    def _get_rewards(self):
        if not getattr(self,'receiver_ready',False):return torch.zeros(self.num_envs,device=self.device)
        c=self.receiver_reward_config
        command=self.command.clone();command[:]=command.new_tensor([0.,0.,.40])
        receiver_action=self.motion_obs['previous_action_readback']['clipped']
        # _get_rewards precedes post-step observation refresh: encode targets now.
        from .motion_handoff import encode_executed
        receiver_action=encode_executed(self.executed_leg,self.executed_wheel,self.reference,leg_scale=.5,wheel_scale=100.)['clipped']
        reward,raw,weighted=motion_reward.compute(self.root_height,self.up,self.vx,self.vy,self.yaw,
            command,self.contact_force>2.,self.effort,receiver_action,self.receiver_previous_action,
            self.robot.data.joint_pos.torch[:,self.ids][:,list(contract.LEG_COLUMNS)],
            self.recovery_snapshot[:,3].bool()|self.recovery_snapshot[:,4].bool(),
            weights={k:c[k] for k in motion_reward.fields(c)},height_width=c['height_width_m'],
            linear_denominator=c.get('linear_cohort_width',{}).get('retained_denominator',c['linear_error_denominator']),yaw_denominator=c['yaw_error_denominator'],
            terminal_penalty=c['terminal_penalty'],dt=self.step_dt,
            action_delta_wheel_factor=c.get('action_delta_wheel_factor',1.))
        valid=self.receiver_control_pre
        self.reward_raw={k:v*valid for k,v in raw.items()};self.reward_weighted={k:v*valid for k,v in weighted.items()}
        return reward*valid
    def receiver_summary(self):
        c=self.ownership_counts.cpu().tolist()
        groups=self.ownership_by_family.cpu().tolist();total=sum(row[2] for row in groups)
        return dict(initialization=c[0],frozen_recovery=c[1],receiver=c[2],receiver_episode_ends=c[3],
                    real_handoffs=c[4],frozen_original_motion=c[5],critic_context=self.receiver_config['critic_context'],
                    by_family={name:dict(initialization=row[0],frozen_prefix=row[1],receiver=row[2],
                        receiver_effective_fraction=row[2]/max(sum(row),1),
                        valid_actor_share=row[2]/max(total,1)) for name,row in zip(('Swing','normal_zero'),groups)})
