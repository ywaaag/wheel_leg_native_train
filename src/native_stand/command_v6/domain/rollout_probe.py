"""Explicit bounded frozen-policy diagnostic declaration; no runtime imports."""
VERSION='recovery_frozen_stochastic_rollout_v1'

def declaration():
    return {'version':VERSION,'rollouts':2,'steps_per_rollout':128,'envs':64,
        'optimizer_updates':0,'max_storage_bytes':67108864,'sampling':'existing_ppo_act',
        'return_semantics':'rsl_compute_returns_global_advantage_normalization'}

def validate(spec):
    c=spec.get('rollout_probe')
    if c is None:return
    if spec.get('rollout_full_joint_capture') not in (None,True):raise ValueError('Unknown full joint capture option')
    from native_stand.recovery.support_record_proposal import declaration as record_declaration
    if (c!=declaration() or spec.get('task')!='recovery' or not spec.get('evaluation_only') or
        spec.get('input_capture') or spec.get('evaluation_requests') or
        spec['ppo']['envs']!=64 or spec['ppo']['steps_per_env']!=128 or
        spec['budget'].get('smoke_updates') or spec['budget'].get('formal_updates') or
        spec.get('recovery',{}).get('wheel_mean_auxiliary') or
        spec.get('recovery',{}).get('exploration_initialization') or
        spec.get('recovery',{}).get('support_record_reward')!=record_declaration() or
        spec.get('recovery',{}).get('sampling',{}).get('environment_counts')!={
            'swing_candidate_from_historical_r1':26,'drawback_manual0001':25,'R0':13}):
        raise ValueError('Unknown/conflicting frozen stochastic rollout declaration')
