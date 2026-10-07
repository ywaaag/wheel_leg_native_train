"""Pure sample accounting and event-sized wiring smoke requirements."""
import math


def samples_per_update(spec):
    ppo = spec['ppo']
    dimensions = (ppo['envs'], ppo['steps_per_env'])
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
           for value in dimensions):
        raise ValueError('PPO envs and steps_per_env must be positive integers')
    return dimensions[0] * dimensions[1]


def samples_for_updates(spec, updates):
    if isinstance(updates, bool) or not isinstance(updates, int) or updates < 0:
        raise ValueError('actual updates must be a nonnegative integer')
    return samples_per_update(spec) * updates


def smoke_plan(spec):
    """Report a minimum, without changing declared updates or granting a budget."""
    declaration = spec.get('wiring_smoke', {})
    if not isinstance(declaration, dict):
        raise ValueError('wiring_smoke must be an object')
    allowed = {'required_event', 'required_event_duration_s', 'event_offset_s',
               'minimum_event_count'}
    unknown = set(declaration) - allowed
    if unknown:
        raise ValueError('unknown wiring_smoke fields: ' + ', '.join(sorted(unknown)))
    recovery = spec.get('recovery', {})
    episode = recovery.get('standing_task', {}).get('training_episode')
    inferred = bool(episode)
    duration = declaration.get('required_event_duration_s',
                               episode['seconds'] if inferred else None)
    event = declaration.get('required_event', 'normal_timeout' if inferred else None)
    offset = declaration.get('event_offset_s',
                             recovery.get('initialization', {}).get('settle_max_s', 0.)
                             if inferred else 0.)
    count = declaration.get('minimum_event_count', 1)
    if event not in (None, 'normal_timeout', 'completed_episode'):
        raise ValueError('unsupported wiring_smoke required_event')
    if (isinstance(count, bool) or not isinstance(count, int) or count < 1 or
            isinstance(offset, bool) or not isinstance(offset, (int, float)) or
            not math.isfinite(offset) or offset < 0):
        raise ValueError('invalid wiring smoke event count or offset')
    if event is None and duration is not None or event is not None and duration is None:
        raise ValueError('wiring smoke event and duration must be declared together')
    result = {'required_event': event, 'required_event_duration_s': duration,
              'event_offset_s': offset, 'minimum_event_count': count,
              'declared_updates': spec.get('budget', {}).get('smoke_updates'),
              'minimum_updates': None, 'minimum_samples': None,
              'planned_samples': None, 'planned_seconds_per_env': None,
              'budget_sufficient': None, 'declaration_source':
              'wiring_smoke' if declaration else 'training_episode' if inferred else 'legacy_no_event'}
    if duration is not None:
        if (isinstance(duration, bool) or not isinstance(duration, (int, float)) or
                not math.isfinite(duration) or duration <= 0):
            raise ValueError('wiring smoke event duration must be positive and finite')
    if 'ppo' not in spec:
        if event is not None:
            raise ValueError('event-sized wiring smoke requires frozen PPO dimensions')
        return result
    per_update = samples_per_update(spec)
    dt = spec.get('control', {}).get('policy_dt_s')
    if dt is not None and (isinstance(dt, bool) or not isinstance(dt, (int, float)) or
                          not math.isfinite(dt) or dt <= 0):
        raise ValueError('policy period must be positive and finite')
    updates = result['declared_updates']
    if updates is not None:
        result['planned_samples'] = samples_for_updates(spec, updates)
        if dt is not None:
            result['planned_seconds_per_env'] = updates * spec['ppo']['steps_per_env'] * dt
    if event is not None:
        if dt is None:
            raise ValueError('event-sized wiring smoke requires a policy period')
        minimum_steps = math.ceil((duration * count + offset) / dt - 1e-9)
        minimum_updates = math.ceil(minimum_steps / spec['ppo']['steps_per_env'])
        result.update(minimum_updates=minimum_updates,
                      minimum_samples=minimum_updates * per_update,
                      budget_sufficient=updates is not None and updates >= minimum_updates)
    return result
