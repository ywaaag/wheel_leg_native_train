"""Explicit CPU-only native-target schedule and measurement contracts.

Not imported by CommandEnv or policy factory; never grants runtime permission.
"""
import numpy as np

VERSION='recovery_native_dynamic_diagnostic_draft_v1'
LEG_ORDER=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')


def smooth_clock(time_s,duration_s,delay_s=0.):
    if not np.isfinite([time_s,duration_s,delay_s]).all() or duration_s<=0 or delay_s<0:raise ValueError('Invalid schedule time')
    t=np.clip((time_s-delay_s)/duration_s,0.,1.)
    return t**3*(10-15*t+6*t*t)


def target(initial_q,time_s,*,contraction_rad,rotation_rad,duration_s,contraction_delay_s):
    q=np.asarray(initial_q,dtype=np.float64)
    if q.shape!=(4,) or not np.isfinite(q).all() or not np.isfinite([contraction_rad,rotation_rad]).all():raise ValueError('Expected explicit finite4leg targets')
    a=contraction_rad*smooth_clock(time_s,duration_s,contraction_delay_s)
    b=rotation_rad*smooth_clock(time_s,duration_s)
    return q+np.array([a-b,a+b,-a+b,a+b])


def encode_native(leg_target,reference,*,leg_scale=1.6):
    values=(np.asarray(leg_target)-np.asarray(reference))/leg_scale
    if values.shape!=(4,) or not np.isfinite(values).all() or (abs(values)>1+1e-7).any():
        raise ValueError('Target outside existing native action envelope; never silently clip diagnostic')
    return values


def validate_sample(sample,*,joint_names,body_names,rate):
    expected={'time_s','episode_id','initial_valid','action_origin','override_mask','joint_q','joint_dq',
              'root_state','target6','PD_requested6','PD_clipped6','PD_applied6'}
    if rate=='physics':expected|={'contact_force_world_by_body','contact_dt_s'}
    elif rate!='PD':raise ValueError('Unknown measurement rate')
    if set(sample)!=expected:raise ValueError('Missing/unknown diagnostic fields')
    if sample['action_origin'] not in ('initialization','explicit_diagnostic','frozen_actor'):raise ValueError('Unknown action origin')
    shapes={'joint_q':(len(joint_names),),'joint_dq':(len(joint_names),),'root_state':(13,),
            'target6':(6,),'PD_requested6':(6,),'PD_clipped6':(6,),'PD_applied6':(6,),'override_mask':(6,)}
    if rate=='physics':shapes['contact_force_world_by_body']=(len(body_names),3)
    for key,shape in shapes.items():
        a=np.asarray(sample[key])
        if a.shape!=shape or not np.isfinite(a).all():raise ValueError('Invalid measurement '+key)
    if not np.isfinite(sample['time_s']) or sample['time_s']<0:raise ValueError('Invalid clock')
    if rate=='physics' and sample['contact_dt_s']!=.001:raise ValueError('Contact dt must be explicit physics1ms')
    return True
