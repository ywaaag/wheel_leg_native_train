"""Explicit reset sampling semantics; allocations are not transition counts."""

def resolve(stage,envs):
    slots=stage.get('sampling_slots');mode=stage.get('sampling_mode','fixed_slots' if slots is not None else 'categorical_weights')
    if mode not in ('categorical_weights','fixed_slots'):raise ValueError('unsupported command sampling mode')
    if (mode=='categorical_weights' and slots is not None) or (mode=='fixed_slots' and slots is None):
        raise ValueError('sampling mode conflicts with slots')
    if slots is not None and (len(slots)!=envs or any(type(i) is not int or not 0<=i<len(stage['commands']) for i in slots)):
        raise ValueError('fixed slots must cover environment indices')
    return {'mode':mode,'nominal_expected_reset_allocations':[envs*w for w in stage['weights']],
        'counts_scope':'command allocations at reset; not actual transitions',
        'fixed_slots':slots,'transition_counts_source':'task_stat_count; command_counts counts allocations'}
