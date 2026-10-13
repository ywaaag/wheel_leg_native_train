"""Explicit Recovery wheel std initialization, no RNG, IO or optimizer mutations."""
import math
import torch

VERSION='wheel_std_initial_multiplier_v1'


def validate(spec):
    config=spec.get('recovery',{}).get('exploration_initialization')
    if config is None:return
    expected={'version','wheel_std_multiplier','channels','apply_phases','optimizer_moments','std_parameterization'}
    if (spec.get('task')!='recovery' or spec.get('initialization')!='warmstart' or
            spec.get('source_input_dim')!=150 or spec.get('wheel_envelope_conversion') or
            set(config)!=expected or config['version']!=VERSION or
            config['wheel_std_multiplier'] not in (1.,.5) or isinstance(config['wheel_std_multiplier'],bool) or
            config['channels']!=[2,5] or config['apply_phases']!=['smoke','formal'] or
            config['optimizer_moments']!='preserve_all' or config['std_parameterization']!='positive_scalar' or
            spec['action']['wheel_scale_rad_s']!=100. or spec['ppo'].get('clear_adam_first_moment',False)):
        raise ValueError('Invalid Recovery wheel std initialization declaration')


def initialize(actor,config,*,wheel_scale_rad_s,leg_scale_rad=None):
    """Called once after strict warmstart and Adam restore, before first act()."""
    distribution=actor.distribution
    if getattr(distribution,'std_type',None)!='scalar':raise ValueError('Wheel std intervention requires scalar std')
    parameter=distribution.std_param
    if parameter.shape!=(6,) or not torch.isfinite(parameter).all() or not (parameter>0).all():
        raise ValueError('Wheel std initialization requires finite positive6D std')
    if config['version']!=VERSION or config['channels']!=[2,5] or config['wheel_std_multiplier'] not in (1.,.5):raise ValueError('Unknown wheel std intervention')
    factor=getattr(distribution,'output_factor',torch.ones_like(parameter))
    if not torch.equal(factor,torch.ones_like(parameter)):raise ValueError('Unexpected std output calibration')
    before=parameter.detach().clone()
    with torch.no_grad():parameter[[2,5]]=parameter[[2,5]]*config['wheel_std_multiplier']
    from native_stand.command_v6.domain.action_std import readback
    kwargs={'parameterization':'scalar','output_factor':factor,'leg_scale_rad':leg_scale_rad or 1.,'wheel_scale_rad_s':wheel_scale_rad_s}
    return {'version':VERSION,'before_normalized_std':before.cpu().tolist(),
        'after_normalized_std':parameter.detach().cpu().tolist(),
        'before_physical_wheel_std_rad_s':(before[[2,5]]*wheel_scale_rad_s).cpu().tolist(),
        'after_physical_wheel_std_rad_s':(parameter.detach()[[2,5]]*wheel_scale_rad_s).cpu().tolist(),
        'std_before':readback(before,**kwargs),'std_after':readback(parameter,**kwargs),
        'leg_physical_units_known':leg_scale_rad is not None,
        'optimizer_moments':'preserved','application':'initialization only,not freeze/schedule/action scale change'}
