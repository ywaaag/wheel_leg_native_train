"""Explicit task identity while preserving each recorded legacy protocol."""
from native_stand.command_v6.domain.episode_result import recovery_episode_mode


def batch_seconds(spec):
    """Single duration authority for Recovery batch, including legacy hold requests."""
    config=spec.get('recovery',{})
    from .sampling import scoring_config
    if config.get('rising_task'):
        from native_stand.recovery.rising import validate_rise
        validate_rise(scoring_config(config['rising_task']))
        return resolve(config)['evaluation_seconds']
    if config.get('standing_task',{}).get('training_episode'):
        return float(resolve(config)['evaluation_seconds'])
    return 10.


def resolve(config):
    if 'sampling' in config or 'assessment' in config:
        from .sampling import validate_explicit
        validate_explicit(config)
    mode=recovery_episode_mode(config) if not config.get('rising_task') else 'autonomous_hold'
    kind='rising' if config.get('rising_task') else 'holding' if mode=='continuous_holding' else mode
    explicit=config.get('task_kind')
    if explicit is not None and explicit!=kind:
        raise ValueError('Recovery task_kind conflicts with existing episode/protocol declaration')
    if kind=='rising':
        from .sampling import scoring_config
        protocol=scoring_config(config['rising_task'])
        deadline=protocol['recovery_deadline_s']
        hold=protocol['post_rise_hold_s']
        minimum=protocol.get('version')=='autonomous_rise_min_height_v2'
        import math
        seconds=math.ceil(deadline+hold+config.get('initialization',{}).get('settle_max_s',1.)+.01) if minimum else 23.
        return {'schema_version':1,'task_kind':kind,'window_alignment':('first_confirmed_entry_then_next1000_samples' if minimum else 'first_eligible_standing_sample'),
                'recovery_deadline_s':deadline,'holding_seconds':hold,
                'evaluation_seconds':float(seconds),'success_semantics':'rise event followed by complete same-episode hold',
                'declaration':'explicit' if explicit else 'legacy_adapter'}
    if kind=='holding':
        protocol=config['standing_task']['protocol']
        return {'schema_version':1,'task_kind':kind,'window_alignment':'episode_age',
                'evaluation_seconds':protocol['seconds'],'steady_window_s':list(protocol['steady_window_s']),
                'success_semantics':'full fixed-horizon certificate, separate from time-limit truncation',
                'declaration':'explicit' if explicit else 'legacy_adapter'}
    return {'schema_version':1,'task_kind':kind,'declaration':'explicit' if explicit else 'legacy_adapter',
            'success_semantics':'existing FSM; no reinterpretation'}
