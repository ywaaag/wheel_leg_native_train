"""Explicit task identity while preserving each recorded legacy protocol."""
from native_stand.command_v6.domain.episode_result import recovery_episode_mode


def resolve(config):
    mode=recovery_episode_mode(config)
    kind='rising' if config.get('rising_task') else 'holding' if mode=='continuous_holding' else mode
    explicit=config.get('task_kind')
    if explicit is not None and explicit!=kind:
        raise ValueError('Recovery task_kind conflicts with existing episode/protocol declaration')
    if kind=='rising':
        protocol=config['rising_task']
        deadline=protocol['recovery_deadline_s']
        hold=protocol['post_rise_hold_s']
        return {'schema_version':1,'task_kind':kind,'window_alignment':'first_eligible_standing_sample',
                'recovery_deadline_s':deadline,'holding_seconds':hold,
                'evaluation_seconds':23.,'success_semantics':'rise event followed by complete same-episode hold',
                'declaration':'explicit' if explicit else 'legacy_adapter'}
    if kind=='holding':
        protocol=config['standing_task']['protocol']
        return {'schema_version':1,'task_kind':kind,'window_alignment':'episode_age',
                'evaluation_seconds':protocol['seconds'],'steady_window_s':list(protocol['steady_window_s']),
                'success_semantics':'full fixed-horizon certificate, separate from time-limit truncation',
                'declaration':'explicit' if explicit else 'legacy_adapter'}
    return {'schema_version':1,'task_kind':kind,'declaration':'explicit' if explicit else 'legacy_adapter',
            'success_semantics':'existing FSM; no reinterpretation'}
