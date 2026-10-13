"""CPU-only DrawBack root-frame target and mirror quality; not runtime wired."""
import torch


def quality(wheels_root,active_q,target_root,*,position_width_m=.25,mirror_width_rad=.10):
    if (wheels_root.shape[-2:]!=(2,3) or active_q.shape!=wheels_root.shape[:-2]+(4,) or target_root.shape!=(2,3)
            or position_width_m<=0 or mirror_width_rad<=0):raise ValueError('Explicit root geometry/active coordinates required')
    if not all(torch.isfinite(v).all() for v in (wheels_root,active_q,target_root)):raise ValueError('Nonfinite proposal inputs')
    distance=(wheels_root-target_root).square().sum(-1)
    # Smooth conservative aggregation emphasizes the worse side without a hard zero.
    cost=torch.logsumexp(distance/position_width_m**2,dim=-1)-torch.log(distance.new_tensor(2.))
    mirror=torch.stack((active_q[...,0]+active_q[...,2],active_q[...,1]-active_q[...,3]),dim=-1)
    position=torch.exp(-cost)
    symmetry=1/(1+(mirror/mirror_width_rad).square().mean(-1))
    return {'position_quality':position,'mirror_quality':symmetry,'quality':position*symmetry,
            'mirror_error_rad':mirror,'wheel_distance_m':distance.sqrt()}


def dense_reward(q,eligible,failed,*,weight_per_s=1.,dt=.01):
    if q.shape!=eligible.shape or q.shape!=failed.shape or weight_per_s<0 or dt<=0:raise ValueError('Explicit reward mask/scales required')
    return weight_per_s*dt*q*eligible*(~failed)


def declaration():
    return {'version':'swing_drawback_mirror_dense_v1','family':'swing_candidate_from_historical_r1',
            'target_root_m':[[.2204998880624771,-.10847419500350952,-.09661871194839478],[-.2204998880624771,-.10847419500350952,-.09661871194839478]],
            'position_width_m':.25,'mirror_width_rad':.10,'weight_per_s':1.,'fade_height_m':[.22,.30],
            'scope':'controlled_Swing_pre_entry','failed_step':'zero','symmetry':'native_hip_sum_active_difference',
            'action_override':False,'strict_symmetry':False}


def validate(spec):
    c=spec.get('recovery',{}).get('drawback_guidance')
    if c is None:return
    r=spec['recovery']
    if (c!=declaration() or spec.get('task')!='recovery' or
        r.get('rising_task',{}).get('version')!='autonomous_rise_min_height_v2' or
        r.get('leg_center_auxiliary') or r.get('wheel_mean_auxiliary') or r.get('exploration_initialization')):
        raise ValueError('Invalid/conflicting DrawBack guidance declaration')


def guided_reward(wheels_root,active_q,height,eligible,failed,*,config,dt):
    q=quality(wheels_root,active_q,wheels_root.new_tensor(config['target_root_m']),
              position_width_m=config['position_width_m'],mirror_width_rad=config['mirror_width_rad'])
    lo,hi=config['fade_height_m'];u=((height-lo)/(hi-lo)).clamp(0,1)
    fade=1-3*u.square()+2*u.pow(3)
    unit=q['quality']*fade
    reward=dense_reward(unit,eligible,failed,weight_per_s=config['weight_per_s'],dt=dt)
    return reward,{**q,'fade':fade,'unit':unit}
