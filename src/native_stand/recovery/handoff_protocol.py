"""Single finite-time protocol for online clock, planner and offline scorer."""
import math
VERSION='recovery_motion_zero_handoff_v2'
SCHEMA='recovery_policy_trace_v1'

def declaration():
    return {'version':VERSION,'schema':SCHEMA,'dt':.01,'settle_s':2.,'entry_dwell_s':.20,'hold_s':10.,'vx_max':.5,'strict_vx':.02,'vy_max':.02,'yaw_max':.03}

def validate_protocol(value):
    expected=declaration()
    if set(value)!=set(expected):raise ValueError('Unknown handoff protocol fields')
    if value.get('version')=='student_autonomous_swing_v1':
        if any(value[k]!=v for k,v in expected.items() if k not in ('version','settle_s')) or value['settle_s']!=2.5:
            raise ValueError('Student recovery protocol must use2.5s deadline')
        return value
    if value!=expected:
        if value.get('version')!='recovery_motion_extended_diagnostic_v1':raise ValueError('Unsupported protocol')
        if any(value[k]!=v for k,v in expected.items() if k not in ('version','settle_s')) or not 2.<value['settle_s']<=5.:
            raise ValueError('Diagnostic may only extend settle time up to5s')
    return value

def duration(prefix_s,initialization_s,protocol=None):
    prefix_steps(prefix_s)
    if not math.isfinite(initialization_s) or initialization_s<0:raise ValueError('Invalid initialization duration')
    cfg=validate_protocol(protocol) if protocol is not None else declaration()
    return initialization_s+prefix_s+cfg['settle_s']+cfg['hold_s']+.02

def prefix_steps(seconds):
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<=seconds<=5 or abs(seconds/.01-round(seconds/.01))>1e-8:raise ValueError('Switch must be a finite10ms interval in[0,5]')
    return round(seconds/declaration()['dt'])
