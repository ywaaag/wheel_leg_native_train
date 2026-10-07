"""Pure event-aligned autonomous rise scoring; no simulator or IO."""
import math
import torch
from native_stand.recovery.standing import score_standing


def validate_rise(config):
    expected = {'version':'autonomous_rise_v1','recovery_deadline_s':11.5,
                'post_rise_hold_s':10.,'retained_families':['R0'],
                'retained_fraction':.4}
    if config != expected:
        raise ValueError('autonomous rise requires explicit11.5s deadline/10s hold/40%R0 rehearsal')
    return config


def rise_protocol(protocol, config):
    validate_rise(config)
    return {**protocol, 'seconds':23., 'steady_window_s':[0.,23.],
            'recovery_deadline_s':11.5, 'post_rise_hold_s':10.,
            'window_alignment':'first_eligible_standing_sample',
            'protocol_identity':'autonomous_rise_v1'}


def score_rise(series, posture, *, dt, protocol, runtime_fault, initial_valid, terminated):
    """First standing-entry window, never stitch episodes or retry a failed hold."""
    hold = protocol['post_rise_hold_s']
    deadline = protocol['recovery_deadline_s']
    expected = round(hold/dt)
    base = {**protocol,'seconds':hold,'steady_window_s':[0.,hold]}
    fallback = score_standing(series,posture,dt=dt,requested_s=hold,protocol=base,
        runtime_fault=runtime_fault,initial_valid=initial_valid,terminated=terminated)
    metadata = {'recovery_s':None,'post_rise_window_s':None,
                'post_rise_observed_s':0.,'height_peak_m':None,'height_gain_m':None}
    if not len(series) or posture.shape != (len(series),10) or not math.isfinite(dt) or dt<=0:
        return {**fallback,**metadata,'accepted':False,'failed_checks':['missing_metrics']}
    metadata.update(height_peak_m=float(series[:,6].max()),
                    height_gain_m=float(series[:,6].max()-series[0,6]))
    if not torch.isfinite(series).all() or not torch.isfinite(posture).all():
        return {**fallback,**metadata,'accepted':False}
    low, high = protocol['height_m']
    eligible = ((series[:,6]>=low)&(series[:,6]<=high)&
                (series[:,15]<=protocol['peak_tilt_max_rad'])&
                (posture[:,:2].abs()<=protocol['level_mean_max_rad']).all(-1)&
                (series[:,10:12]>2.).all(-1)&series[:,29].bool())
    candidates = torch.nonzero(eligible,as_tuple=False).flatten()
    if not len(candidates):
        return {**fallback,**metadata,'accepted':False,
                'checks':{**fallback['checks'],'standing_entry':False},
                'failed_checks':list(dict.fromkeys([*fallback['failed_checks'],'standing_entry']))}
    start = int(candidates[0])
    recovery_s = float(series[start,0])
    finish = start+expected
    metadata.update(recovery_s=recovery_s,
        post_rise_window_s=[start*dt,finish*dt],
        post_rise_observed_s=min(expected,len(series)-start)*dt)
    result = score_standing(series[start:finish],posture[start:finish],dt=dt,
        requested_s=hold,protocol=base,runtime_fault=runtime_fault,
        initial_valid=initial_valid,terminated=terminated)
    result['checks']['recovery_deadline'] = recovery_s<=deadline+1e-5
    result['checks']['continuous_height'] = (finish<=len(series) and
        bool(((series[start:finish,6]>=low)&(series[start:finish,6]<=high)).all()))
    result['checks']['continuous_contact'] = (finish<=len(series) and
        bool((series[start:finish,10:12]>2.).all()))
    result['checks']['recovery_safety'] = bool((series[:,12]<=protocol['closure_max_m']).all())
    result['failed_checks'] = [k for k,v in result['checks'].items() if not v]
    result['accepted'] = all(result['checks'].values())
    return {**result,**metadata}
