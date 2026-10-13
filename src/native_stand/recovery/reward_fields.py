"""One declaration for Recovery runtime reward outputs and rollout consumers."""
BASE=('lift','upright','effort','action_delta','joint_margin')
OPTIONAL=('height_overshoot','pitch_level','roll_level','support','low_height_wheel_spin',
          'leg_symmetry','support_balance','support_region','slip_proxy','wheel_longitudinal_offset')


def resolve(reward,config):
    fields=list(BASE);settling=config.get('settling_reward')
    if settling:
        fields+=['settling_linear','settling_angular'] if settling.get('kind')=='pseudo_huber' else ['settling_motion']
        if 'settling_yaw_weight' in settling:fields.append('settling_yaw')
    fields += [n for n in OPTIONAL if n in reward]
    if config.get('standing_task'):
        from .standing import REWARD_FIELDS
        fields+=list(REWARD_FIELDS)
    if config.get('support_record_reward'):fields.append('support_record_progress')
    if config.get('drawback_guidance'):fields.append('drawback_mirror_guidance')
    return tuple(fields)


def verify(raw,weighted,reward,config):
    expected=set(resolve(reward,config))
    if set(raw)!=expected or set(weighted)!=expected:raise ValueError('Recovery reward output/declaration differs: '+str(set(raw)^expected))
