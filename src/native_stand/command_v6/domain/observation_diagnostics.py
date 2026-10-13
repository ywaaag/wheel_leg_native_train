"""Pure statistics of explicitly supplied pre-action 150D actor inputs.

No simulator, actor forward, RNG, gradients, or file IO. Variance describes
observed excitation; it does not establish observability or policy sensitivity.
"""
import torch


def labels():
    frame=[*['angular_body_'+a for a in 'xyz'],*['gravity_body_'+a for a in 'xyz'],
        'command_vx','command_yaw','command_height',
        'leg_offset_left_hip','leg_offset_left_active','leg_offset_right_hip','leg_offset_right_active',
        *['active_velocity_'+str(i) for i in range(6)],*['previous_clipped_action_'+str(i) for i in range(6)]]
    return ['current/'+x for x in frame]+[f'history_{i}_oldest_to_newest/'+x for i in range(5) for x in frame]


def summarize(inputs,*,episode_ids,near_zero_variance=1e-10):
    """Rows are valid pre-action samples for ONE family and ONE phase.

    episode_ids must identify env+episode uniquely. No concatenated-episode
    temporal variance; reset mixtures must be grouped by the calling boundary.
    """
    if inputs.ndim!=2 or inputs.shape[1]!=150 or len(episode_ids)!=len(inputs):
        raise ValueError('Expected N x 150 inputs and N unique episode identifiers')
    if near_zero_variance<0:raise ValueError('Negative diagnostic variance threshold')
    values=inputs.detach().to(dtype=torch.float64,device='cpu')
    if not torch.isfinite(values).all():raise ValueError('Nonfinite actor inputs cannot be summarized as valid')
    if not len(values):
        return {'sample_count':0,'dimensions':None,'status':'NO_SAMPLES'}
    mean=values.mean(0);var=values.var(0,unbiased=False)
    groups={}
    for i,key in enumerate(episode_ids):groups.setdefault(key,[]).append(i)
    temporal=[];means=[];used=0
    for indices in groups.values():
        group=values[indices];means.append(group.mean(0))
        if len(indices)>1:
            temporal.append((group.var(0,unbiased=False),len(indices)));used+=len(indices)
    time_var=sum((v*n for v,n in temporal),torch.zeros(150,dtype=torch.float64))/used if used else None
    between=torch.stack(means).var(0,unbiased=False) if len(means)>1 else None
    dimensions=[]
    for i,name in enumerate(labels()):
        dimensions.append({'index':i,'name':name,'mean':float(mean[i]),'variance':float(var[i]),
            'min':float(values[:,i].min()),'max':float(values[:,i].max()),
            'p05':float(torch.quantile(values[:,i],.05)),'p95':float(torch.quantile(values[:,i],.95)),
            'within_episode_time_variance':float(time_var[i]) if time_var is not None else None,
            'between_episode_mean_variance':float(between[i]) if between is not None else None,
            'near_constant_in_observed_samples':bool(var[i]<=near_zero_variance)})
    return {'sample_count':len(values),'episode_count':len(groups),'dimensions':dimensions,
        'near_zero_variance_threshold':near_zero_variance,'variance_space':'actual scaled actor input',
        'temporal_variance_samples':used,'between_episode_scope':'equally weighted episode means; may mix environment and pose differences',
        'interpretation':'Near-constant input is not proof of missing wiring, lack of observability, or policy insensitivity'}
