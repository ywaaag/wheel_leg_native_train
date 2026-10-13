"""Strong named-axis access for persisted native Motion control diagnostics."""
import numpy as np

VERSION='motion_policy_control_v1'
AXES=('policy_time','scored_env','channel')
GROUPS={'q':[0,6],'dq':[6,12],'raw_action':[12,18],'clipped_action':[18,24],
        'leg_target_before_projection':[24,28],'leg_target_after_projection':[28,32],
        'leg_position_error':[32,36],'PD_requested_nm':[36,42],
        'physical_clipped_nm':[42,48],'actuator_applied_nm':[48,54]}


def _tensor(result,key,groups,version,channels,*,allow_legacy_axes=False):
    control=result[key];envs=result['effective_protocol']['scored_envs']
    if type(envs) is not int or envs<1:raise ValueError('Positive scored env count required')
    declared=control.get('axes');declared_version=control.get('schema_version')
    if declared is not None and tuple(declared)!=AXES:raise ValueError('Control trace axis order differs')
    if declared_version is not None and declared_version!=version:raise ValueError('Control trace schema differs')
    if declared is None or declared_version is None:
        if not allow_legacy_axes:raise ValueError('Trace axis/schema metadata missing')
        origin='explicit_legacy_producer_contract; not inferred from shape'
    else:
        if tuple(declared)!=AXES or declared_version!=version:raise ValueError('Control trace axis/schema differs')
        origin='producer_declared'
    if control.get('groups')!=groups:raise ValueError('Control trace channel schema differs')
    rows=control['rows'];valid=np.asarray(control['valid'],dtype=bool)
    if valid.shape!=(len(rows),envs):raise ValueError('Control validity axes differ')
    array=np.full((len(rows),envs,channels),np.nan,dtype=np.float64)
    for t,step in enumerate(rows):
        if len(step)!=envs:raise ValueError('Time/env axes or env count differ')
        for e,value in enumerate(step):
            if value is None:
                if valid[t,e]:raise ValueError('Valid control sample missing channels')
                continue
            if len(value)!=channels:raise ValueError('Control channel count differs')
            array[t,e]=value
            if valid[t,e] and not np.isfinite(array[t,e]).all():raise ValueError('Valid control sample nonfinite')
    return {'values':array,'valid':valid,'axes':AXES,'schema_version':version,
        'axis_identity_origin':origin,'groups':groups,'shape':list(array.shape),
        'measurement_scope':'policy end; held preceding PD torque; terminal controls may be unavailable'}


def group(trace,name):
    if name not in trace['groups']:raise ValueError('Unknown channel group')
    start,stop=trace['groups'][name]
    return trace['values'][:,:,start:stop]


def control_tensor(result,*,allow_legacy_axes=False):
    return _tensor(result,'control_diagnostics',GROUPS,VERSION,54,allow_legacy_axes=allow_legacy_axes)


def paired_tensor(result):
    from ..domain.paired_state import VERSION as version,GROUPS as groups,CHANNELS
    return _tensor(result,'paired_state',groups,version,CHANNELS)
