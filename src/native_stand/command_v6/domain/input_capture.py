"""Explicit bounded tensor recorder; no actor, simulator, RNG or file IO."""
import torch

VERSION='recovery_input_action_reward_v1'


def validate(spec):
    c=spec.get('input_capture')
    if c is None:return None
    if c!={'version':VERSION,'enabled':True,'max_storage_bytes':268435456}:
        raise ValueError('Unknown input capture declaration')
    if (spec.get('task')!='recovery' or not spec.get('evaluation_only') or
            spec['evaluation']['scored_envs']!=8 or spec['evaluation']['envs']!=64 or
            spec['budget']['smoke_updates'] or spec['budget']['formal_updates'] or
            spec.get('wheel_envelope_conversion')):
        raise ValueError('Capture requires Recovery PPO0,64env/8scored,scalar Gaussian with no conversion')
    requests=spec.get('evaluation_requests',[])
    if len(requests)!=3 or any(r['seconds']!=23 or r['sha256']!=spec['source_sha256'] for r in requests):
        raise ValueError('Capture requires three same-source 23s requests')
    return c


class Recorder:
    def __init__(self,steps,envs,device,*,std,active_indices,joint_names,dt):
        if steps>2300 or envs!=8 or dt!=.01:raise ValueError('Capture size/frequency outside declaration')
        if std.shape!=(6,) or not torch.isfinite(std).all() or not (std>0).all():
            raise ValueError('Capture needs six positive scalar std parameters')
        self.steps=steps;self.envs=envs;self.dt=dt;self.std=std.detach().clone()
        self.active_indices=list(active_indices);self.joint_names=list(joint_names)
        self.arrays={};self.count=0;self.reward_names=None
        self.device=device

    def _put(self,name,value):
        value=value[:self.envs].detach()
        if name not in self.arrays:
            self.arrays[name]=torch.zeros((self.steps,*value.shape),device=self.device,dtype=value.dtype)
        self.arrays[name][self.count].copy_(value)

    def before(self,*,observation,mean,root,joint_pos,joint_vel,command,reference,
               previous_action,contact,metadata,active):
        if self.count>=self.steps:raise ValueError('Capture exceeds declared steps')
        if observation.shape[-1]!=150 or mean.shape[-1]!=6:raise ValueError('Actor capture shape differs')
        for name,value in locals().copy().items():
            if name!='self':self._put('pre_'+name,value)
        self._put('distribution_std',self.std.expand(self.envs,6))

    def after(self,*,state,control,reward_total,reward_raw,reward_weighted,initializing,support_record=None):
        names=list(reward_raw)
        if self.reward_names is None:self.reward_names=names
        if self.reward_names!=names or set(names)!=set(reward_weighted):raise ValueError('Reward capture layout changed')
        self._put('post_state',state);self._put('post_control',control)
        self._put('post_reward_total',reward_total)
        self._put('post_reward_raw',torch.stack([reward_raw[k] for k in names],-1))
        self._put('post_reward_weighted_dt',torch.stack([reward_weighted[k] for k in names],-1))
        self._put('post_initializing',initializing)
        if support_record is not None:self._put('support_record_transition',support_record)
        self.count+=1

    def finish(self):
        return {k:v[:self.count].detach().cpu().numpy().copy() for k,v in self.arrays.items()}

    def metadata(self):
        return {'version':VERSION,'policy_dt_s':self.dt,'steps_observed':self.count,'scored_envs':self.envs,
            'joint_names':self.joint_names,'active_indices':self.active_indices,'reward_names':self.reward_names,
            'pre_metadata_columns':['pose_index','episode_id','initialization_valid','fsm_mode','recovery_clock_s','task_phase'],
            'pre_action_scope':'actor(obs) deterministic output exactly once; std parameter direct read, no distribution update or sampling',
            'post_scope':'pre-reset snapshots and actual runtime reward dict; total includes once events',
            'pre_contact_scope':'last recorded contact-force resultant; initial/reset sample may be zero or previous sensor update,not independently refreshed',
            'pre_root_layout':'root_state_w: xyz,quaternion_xyzw,linear_velocity_world,angular_velocity_world',
            'random_trajectory_collected':False,'optimizer_updates':0}
