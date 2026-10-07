"""Explicit episode evidence, separate from value-bootstrap or reward decisions."""


EPISODE_MODES = ('handover', 'autonomous_hold', 'continuous_holding')
STAND_DEPENDENCY_FIELDS = ('stand_checkpoint', 'stand_sha256', 'stand_spec',
                           'stand_spec_sha256', 'stand_frozen')


def recovery_episode_mode(config):
    """Resolve legacy declarations without changing their termination semantics."""
    training = config.get('standing_task', {}).get('training_episode')
    if training is not None:
        if training.get('mode') != 'fixed_horizon':
            raise ValueError('Unknown Recovery training episode mode')
        if config['fsm'].get('success_mode') != 'autonomous_hold':
            raise ValueError('Continuous holding cannot use teacher handover')
        return 'continuous_holding'
    mode = config['fsm'].get('success_mode', 'handover')
    if mode not in ('handover', 'autonomous_hold'):
        raise ValueError('Unknown Recovery success mode')
    return mode


def requires_stand(config):
    """Declared historical dependencies keep their existing identity checks."""
    return (recovery_episode_mode(config) != 'continuous_holding' or
            any(name in config for name in STAND_DEPENDENCY_FIELDS))


def episode_result(*, terminated, truncated, certificate_passed, runtime_fault,
                   task_mode, termination_reason=()):
    """Normalize scalar evidence; certificate failure is not an absorbing state."""
    if task_mode not in EPISODE_MODES:
        raise ValueError('Unknown episode task mode')
    if any(type(value) is not bool for value in (terminated, truncated, runtime_fault)):
        raise ValueError('Episode terminal flags must be explicit booleans')
    if certificate_passed is not None and type(certificate_passed) is not bool:
        raise ValueError('Episode certificate must be boolean or missing')
    if terminated and truncated:
        raise ValueError('An episode cannot terminate and time-limit truncate together')
    if runtime_fault and (not terminated or certificate_passed):
        raise ValueError('Runtime fault must terminate and cannot pass a certificate')
    if not isinstance(termination_reason, (tuple, list)) or any(
            not isinstance(reason, str) for reason in termination_reason):
        raise ValueError('Episode termination reasons must be strings')
    return {'version': 1, 'task_mode': task_mode, 'terminated': terminated,
            'truncated': truncated, 'certificate_passed': certificate_passed,
            'runtime_fault': runtime_fault, 'termination_reason': list(termination_reason)}
