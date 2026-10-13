"""Measured wheel/hip geometry in world coordinates; no control or runtime I/O."""
import torch


def diagnostic_window(protocol, target, *, total_samples, dt):
    """Light diagnostics use their declared steady window, never a full hold gate."""
    from .time_axis import window_indices
    motion=protocol.get('motion_window_s') if any(target) else None
    window=motion if motion is not None else protocol['steady_window_s']
    axis=window_indices(total_samples,dt=dt,window_s=window)
    return {**axis,'scope':'motion_window' if motion is not None else 'steady_window',
            'full_motion_window_declared':motion is not None}


def measure(hip_world, wheel_world, world_from_CAD):
    """Two Euclidean hip-pivot→wheel-center lengths, heading offset and roll.

    Shapes: [N,2,3], [N,2,3], [N,3,3]; left first. Native up=CAD+y,
    forward=CAD-z, left=CAD-x. Heading is forward projected onto the ground.
    Invalid heading is explicitly flagged, not silently treated as aligned.
    """
    if hip_world.shape != wheel_world.shape or hip_world.ndim!=3 or hip_world.shape[1:]!=(2,3):
        raise ValueError('expected left/right hip and wheel centers [N,2,3]')
    if world_from_CAD.shape!=(hip_world.shape[0],3,3):
        raise ValueError('expected world_from_CAD [N,3,3]')
    forward=-world_from_CAD[:,:,2]
    heading=torch.cat((forward[:,:2],torch.zeros_like(forward[:,:1])),dim=-1)
    norm=torch.linalg.vector_norm(heading,dim=-1)
    valid=(norm>1e-6)&torch.isfinite(hip_world).all(dim=(1,2))&torch.isfinite(wheel_world).all(dim=(1,2))&torch.isfinite(world_from_CAD).all(dim=(1,2))
    heading=heading/norm.clamp_min(1e-6)[:,None]
    lengths=torch.linalg.vector_norm(wheel_world-hip_world,dim=-1)
    offset=((wheel_world[:,0]-wheel_world[:,1])*heading).sum(-1)
    roll=torch.atan2(-world_from_CAD[:,2,0],world_from_CAD[:,2,1])
    return {'left_leg_length_m':lengths[:,0],'right_leg_length_m':lengths[:,1],
        'leg_length_difference_m':lengths[:,0]-lengths[:,1],
        'wheel_heading_offset_m':offset,'wheel_height_difference_m':wheel_world[:,0,2]-wheel_world[:,1,2],
        'roll_rad':roll,'valid':valid}


def validate_balance(config):
    import math
    if not isinstance(config,dict) or set(config)!={'version','weight','deadbands','denominators'}:
        raise ValueError('posture_balance fields differ')
    if config['version']!='bounded_geometry_v1':raise ValueError('unknown posture_balance version')
    if type(config['weight']) not in (int,float) or not math.isfinite(config['weight']) or config['weight']>=0:
        raise ValueError('posture weight must be negative finite')
    names={'wheel_heading_offset_m','leg_length_difference_m','roll_rad'}
    for field in ('deadbands','denominators'):
        if not isinstance(config[field],dict) or set(config[field])!=names:
            raise ValueError('posture '+field+' fields differ')
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 or
               (field=='denominators' and v==0) for v in config[field].values()):
            raise ValueError('invalid posture '+field)
    return config


def bounded_cost(geometry, config):
    """Mean of three bounded physical-state costs, no actuator-space symmetry."""
    validate_balance(config)
    components={}
    for name in config['denominators']:
        error=torch.relu(geometry[name].abs()-config['deadbands'][name])
        components[name]=1-torch.exp(-error.square()/config['denominators'][name])
    total=torch.stack(tuple(components.values())).mean(0)
    return torch.where(geometry['valid'],total,torch.full_like(total,float('nan'))),components


def validate_task(spec):
    config=spec['motion_posture']
    if spec.get('task')=='recovery':raise ValueError('motion posture is not Recovery')
    if set(config)!={'version','assessment_commands','acceptance','chain_wall_s'} or config['version']!='native_posture_v1':
        raise ValueError('unknown motion posture task schema')
    commands=config['assessment_commands']
    if commands!=[[0,0],[.5,0],[-.5,0],[1,0],[-1,0],[1.5,0],[-1.5,0],[2,0],[-2,0]]:
        raise ValueError('posture task preserves full B250 old-endpoint assessment')
    rule=config['acceptance']
    if set(rule)!={'minimum_relative_improvement','required_confirmations','maximum_component_regression_fraction','minimum_confirmation_spacing_updates'}:
        raise ValueError('posture acceptance fields differ')
    if not 0<rule['minimum_relative_improvement']<1 or rule['required_confirmations']!=2 or not 0<=rule['maximum_component_regression_fraction']<=.2 or rule['minimum_confirmation_spacing_updates']<1:
        raise ValueError('invalid posture acceptance thresholds')
    if type(config['chain_wall_s']) not in (int,float) or not 120<config['chain_wall_s']<=10800:
        raise ValueError('posture chain exceeds3hour authorization')
    validate_balance(spec['reward']['posture_balance'])
