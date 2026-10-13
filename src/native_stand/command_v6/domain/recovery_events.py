"""Pure first-episode event alignment; explicit frozen clock/scales, no simulator IO."""
import numpy as np
from .trace_schema import STATE,POSTURE,CONTROL,WIDTHS,VERSION,PHASE_CODES,validate_rows
from .time_axis import event,sustained_events


def analyze(row,*,dt,hold_s,wheel_scale):
    base={'env_id':row['env_id'],'passed':row.get('success'),
        'failed_checks':row.get('standing_failed_checks'),'termination_reason':row.get('termination_reason'),
        'trace_schema':VERSION,'control_scope':'100Hz held PD values; not full 5ms effort audit'}
    required={'state':row.get('compact_trace_100hz'),'posture':row.get('posture_trace_100hz'),
              'control':row.get('control_diagnostics_100hz')}
    missing=[k for k,v in required.items() if v is None]
    if missing:return {**base,'status':'MISSING_EVIDENCE','missing':missing}
    for key,value in required.items():validate_rows(value,key)
    s,p,c=(np.asarray(required[k],dtype=float).reshape(-1,WIDTHS[k]) for k in ('state','posture','control'))
    if len(s)!=len(p) or len(s)!=len(c):raise ValueError('Aligned trace lengths differ')
    if not len(s):return {**base,'status':'MISSING_EVIDENCE','missing':['nonempty_trace']}
    if not all(np.isfinite(v).all() for v in (s,p,c)):return {**base,'status':'NONFINITE_TRACE'}
    if len(np.unique(s[:,STATE['episode_id']]))!=1:raise ValueError('Trace stitches multiple episodes')
    active=(s[:,STATE['recovery_clock_s']]>0)&s[:,STATE['initial_valid']].astype(bool)&(s[:,STATE['previous_mode']]!=PHASE_CODES['initializing'])
    init=s[:,STATE['previous_mode']]==PHASE_CODES['initializing']
    def at(i):
        if i is None:return None
        i=int(i);clipped=c[i,CONTROL['clipped_action']];dq=c[i,CONTROL['joint_dq']]
        return {**event(i,dt=dt,recovery_seconds=float(s[i,STATE['recovery_clock_s']])),
            'height_m':float(s[i,STATE['height_m']]),'tilt_rad':float(s[i,STATE['tilt_rad']]),
            'pitch_roll_rad':[float(p[i,POSTURE[f]]) for f in ('pitch_rad','roll_rad')],
            'contact_n':[float(s[i,STATE[f]]) for f in ('left_contact_n','right_contact_n')],
            'leg_target_rad':c[i,CONTROL['leg_target_after_limit']].tolist(),
            'wheel_target_rad_s':(clipped[[2,5]]*wheel_scale).tolist(),'wheel_actual_rad_s':dq[[2,5]].tolist(),
            'requested_nm':c[i,CONTROL['requested_torque']].tolist(),
            'clipped_nm':c[i,CONTROL['physical_clipped_torque']].tolist(),
            'applied_nm':c[i,CONTROL['applied_torque']].tolist()}
    def first(mask):
        ids=np.flatnonzero(active&mask);return at(ids[0]) if len(ids) else None
    ids=np.flatnonzero(active);entry=row.get('entry_confirmation_index')
    if entry is not None and (type(entry) is not int or not 0<=entry<len(s)):raise ValueError('Invalid entry index')
    if entry is None:
        entry_s=row.get('recovery_s')
        if entry_s is not None:
            # Use actual recovery clock rather than assuming index=seconds/dt.
            found=np.flatnonzero(active&(s[:,STATE['recovery_clock_s']]>=entry_s-1e-6))
            entry=int(found[0]) if len(found) else None
    expected=round(hold_s/dt);hold_start=entry+1 if entry is not None else None
    observed=min(expected,max(0,len(s)-hold_start)) if hold_start is not None else 0
    complete=observed>=expected
    category='NOT_ENTERED' if entry is None else 'COMPLETE_HOLD_WINDOW' if complete else 'EARLY_END_OR_PARTIAL_HOLD'
    pre=active.copy()
    if hold_start is not None:pre[hold_start:]=False
    early=ids[s[ids,STATE['recovery_clock_s']]<=.5]
    return {**base,'status':'MEASURED','task_window_category':category,
        'time_scope':{'initialization_observed_s':float(init.sum()*dt),
            'recovery_pre_entry_observed_s':float(pre.sum()*dt),
            'post_entry_hold_observed_s':observed*dt,'required_hold_s':hold_s,
            'trace_observed_s':len(s)*dt,'clock_note':'initialization/pre-entry/hold counted separately; trace includes setup if present',
            'includes_evaluation_reset':False,'scope':'first evaluation episode; not training mean episode duration'},
        'entry_event':at(entry),'entry_s':row.get('recovery_s'),'hold_prefix_s':row.get('diagnostic_hold_prefix_s'),
        'initial_valid':row.get('initial_valid'),'height_peak_m':float(s[:,STATE['height_m']].max()),
        'first_control':at(ids[0]) if len(ids) else None,'last_control':at(ids[-1]) if len(ids) else None,
        'first_contact_loss':first((s[:,[STATE['left_contact_n'],STATE['right_contact_n']]]<=2).any(1)),
        'contact_loss_intervals':sustained_events((active&(s[:,[STATE['left_contact_n'],STATE['right_contact_n']]]<=2).any(1)).tolist(),dt=dt),
        'first_pitch_0p1':first(abs(p[:,POSTURE['pitch_rad']])>.1),
        'first_tilt_0p5':first(s[:,STATE['tilt_rad']]>.5),
        'first_height_0p3':first(s[:,STATE['height_m']]>=.3),
        'first_half_second_peak':at(early[np.argmax(s[early,STATE['height_m']])]) if len(early) else None}


def coverage_from_metrics(metrics,plan):
    from native_stand.recovery.sampling import coverage
    phases=[];episodes={};initializations=None
    for metric in metrics:
        task=metric.get('task_metrics',{})
        phases.extend(task.get('family_phase_coverage') or [])
        for row in task.get('episodes_by_pose') or []:
            f=row['family'];count=row['completed'];record=episodes.setdefault(f,[0,0.])
            record[0]+=count;record[1]+=count*(row.get('mean_duration_s') or 0.)
        # Historical logs often omit reset counters; do not infer them from episode count.
        if task.get('initialization_by_pose') is not None:initializations=task['initialization_by_pose']
    output=coverage(plan,initializations,phases if phases else None)
    output['training_episode_summary']={f:{'completed':v[0],'mean_completed_episode_s':v[1]/v[0] if v[0] else None,
        'scope':'training completed episodes; initialization/recovery/hold components not independently reconstructable from this mean'} for f,v in episodes.items()}
    return output
