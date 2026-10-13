"""Explicit execution recipe; legacy declarations are disclosed, never rewritten."""
import copy


def resolve(spec):
    result = copy.deepcopy(spec)
    if spec.get('receiver_training'):
        return result, {'mode':'receiver_motion_recipe','reward':result['receiver_reward'],
            'actor_scope':'receiver_only','critic_context':result['receiver_training']['critic_context'],
            'changes':[],'control_scales':result['action']}
    if spec.get('task') == 'recovery':
        from native_stand.recovery.effective import disclose
        return result, {'mode': 'recovery_owned', 'changes': [],'effective_recovery':disclose(spec)}
    strict = spec.get('effective_recipe_version') == 1
    conflicts = []
    reward = result['reward']
    if strict:
        supported={'upright','height','velocity_tracking','two_wheel_contact','effort','action_delta',
            'joint_margin','height_width_m','linear_error_denominator','yaw_error_denominator',
            'terminal_penalty','stage_linear_denominators','stage_yaw_denominators',
            'action_delta_wheel_factor','action_delta_semantics','tracking_mode','width_diagnostics',
            'linear_cohort_width','posture_balance'}
        unknown=set(reward)-supported
        if unknown:raise ValueError('unsupported reward fields: '+', '.join(sorted(unknown)))
    if reward.get('posture_balance') is not None:
        from .posture_geometry import validate_balance
        validate_balance(reward['posture_balance'])
    if reward.get('tracking_mode','combined') not in ('combined','separate'):
        raise ValueError('unknown tracking_mode')
    if reward.get('tracking_mode', 'combined') != 'combined':
        conflicts.append('reward.tracking_mode: execution supports combined')
    if any(key in reward for key in ('linear_velocity_tracking', 'yaw_velocity_tracking')):
        conflicts.append('independent tracking weights are unsupported by combined reward')
    for stage in result['curriculum']['stages']:
        if stage.get('command_mode','ramp') not in ('ramp','fixed'):
            raise ValueError('unknown stage command_mode')
        if stage.get('command_mode', 'ramp') != 'ramp':
            conflicts.append('stage command_mode: execution supports ramp')
    if result.get('objective', 'global_adv_norm') != 'global_adv_norm':
        conflicts.append('objective: execution supports global_adv_norm')
    if result.get('objective','global_adv_norm') not in ('global_adv_norm','per_command_adv_norm'):
        raise ValueError('unknown actor objective')
    if result['evaluation'].get('command_mode', 'ramp') != 'ramp':
        conflicts.append('evaluation command_mode: execution supports ramp')
    if result['evaluation'].get('tracking_mode', 'combined') != 'combined':
        conflicts.append('evaluation tracking_mode: execution supports combined')
    if result['evaluation'].get('motion_protocol','ramp') != 'ramp':
        conflicts.append('evaluation motion_protocol: execution supports ramp')
    declared_root=result.get('execution_source_root')
    if declared_root and '/isolated/' in declared_root:
        conflicts.append('execution_source_root: shared src executes; old isolated declaration is not loaded')
    if strict and conflicts:
        raise ValueError('; '.join(conflicts))
    active = result['curriculum']['active_stage']
    for field in ('linear_error_denominator', 'yaw_error_denominator'):
        table = reward.get('stage_' + ('linear' if field.startswith('linear') else 'yaw') + '_denominators')
        if table is not None:
            reward[field] = table[str(active)]
    return result, {
        'version': 1, 'strict': strict, 'legacy_ignored_declarations': conflicts,
        'command_mode': 'ramp', 'training_schedule_s': result['curriculum']['schedule_s'],
        'episode_length_s': result['curriculum']['episode_length_s'], 'active_stage': active,
        'reward': {**reward, 'tracking_mode': 'combined'},
        'reward_formula': 'exp(-((vx-cvx)^2+vy^2)/linear_d-(yaw-cyaw)^2/yaw_d); weighted sum * policy_dt once + terminal',
        'advantage_normalization': 'installed PPO global rollout normalization',
        'ppo': result['ppo'], 'changes': ['initial active-stage denominators resolved'],
    }
