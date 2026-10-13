"""Versioned actor probability coordinates; no simulator or file access."""

def declaration():
    return {'version':'recovery_wheel_bounded_mean_gaussian_v1','channels':[2,5],
        'mean':'tanh_raw_mlp_wheels','std':'source_scalar_unchanged',
        'sample':'Gaussian_in_action_coordinates','log_prob':'ordinary_Gaussian',
        'deterministic':'same_bounded_mean','environment_clip':'unchanged_minus1_plus1',
        'warmstart':'strict_parameters_Adam_not_behavior_preserving'}


def validate(spec):
    c=spec.get('action_distribution')
    if c is None:return
    if (c!=declaration() or spec.get('task')!='recovery' or spec.get('wheel_envelope_conversion') or
        spec.get('source_input_dim')!=150 or spec['action'].get('wheel_scale_rad_s')!=100 or
        spec['recovery'].get('wheel_mean_auxiliary') or spec['recovery'].get('exploration_initialization')):
        raise ValueError('Unknown/conflicting bounded wheel mean distribution')
