"""Recovery candidate classification; no standing certification by proxy."""
import math


def classify_recovery(entry,expected):
    result=entry['result'];rows=result.get('per_env',[])
    problems=[]
    from native_stand.command_v6.domain.evidence import resolve_gate
    normalized=resolve_gate(result,'recovery',expected_envs=expected['scored_envs'],
        expected_protocol=expected.get('effective_protocols',{}).get('zero'))
    if not normalized['candidate_eligible']:problems.append(normalized['status'])
    if entry.get('identity')!=expected:problems.append('identity_mismatch')
    if entry.get('kind')!='full':problems.append('light_only')
    if len(rows)!=expected['scored_envs']:problems.append('missing_environments')
    fields=('continuous_s','verify_s','height_min_m','height_final_m',
            'dual_contact_fraction','closure_max_m','tilt_peak_rad','saturation_fraction_policy')
    if any(row.get(key) is None or not math.isfinite(float(row[key])) for row in rows for key in fields):
        problems.append('missing_metrics')
    if any(row.get('outcome') not in ('success','task_failure') for row in rows):
        problems.append('runtime_fault_or_incomplete')
    gate=result.get('recovery_gate')
    if gate is None:problems.append('missing_recovery_gate')
    protocol=result.get('success_protocol',{'mode':'handover','required_stable_s':5.})
    continuous=protocol.get('standing_protocol')
    required=2. if protocol.get('mode')=='autonomous_hold' else 5.
    if protocol.get('required_stable_s')!=required:problems.append('success_protocol_mismatch')
    if not continuous and any(row.get('success') and row.get('verify_s',0.)<required-1e-5 for row in rows):
        problems.append('insufficient_stand_verification')
    if continuous:
        metric_fields=('net_drift_m','max_excursion_m','mean_abs_vx_mps','mean_abs_vy_mps',
            'mean_abs_yaw_rad_s','mean_abs_pitch_rad','mean_abs_roll_rad','mean_mirror_error_rad',
            'mean_leg_length_difference_m','mean_support_difference','dual_contact_fraction')
        if any(row.get('standing_metrics',{}).get(key) is None or
               not math.isfinite(float(row['standing_metrics'][key])) for row in rows for key in metric_fields):
            problems.append('missing_standing_metrics')
        if protocol.get('continuous_seconds',0.)<continuous['seconds']:
            problems.append('short_standing_window')
        if any('standing_metrics' not in row or 'standing_failed_checks' not in row for row in rows):
            problems.append('missing_standing_metrics')
        if any(row.get('success') and (not row.get('continuous_window_completed') or
                row.get('continuous_s',0.)<continuous['seconds']-1e-3 or
                row.get('standing_failed_checks')) for row in rows):
            problems.append('invalid_standing_certificate')
        if gate and (gate.get('passed_envs')!=sum(bool(row.get('success')) for row in rows) or
                bool(gate.get('accepted'))!=bool(rows and all(row.get('success') for row in rows))):
            problems.append('inconsistent_standing_gate')
        if continuous.get('objective')=='survival_level':
            retained=result.get('retained_evaluations',[])
            if any(row.get('accepted') and any(not check.get('accepted') for check in retained) for row in rows):
                problems.append('retained_family_failure')
    means={key:sum(row[key] for row in rows)/len(rows) if rows and
        all(row.get(key) is not None for row in rows) else None for key in fields}
    times=[row['recovery_s'] for row in rows if row.get('success') and row.get('recovery_s') is not None]
    means['recovery_s']=sum(times)/len(times) if times else None
    if continuous:
        for key in ('net_drift_m','max_excursion_m','mean_abs_vx_mps','mean_abs_yaw_rad_s',
                    'mean_abs_pitch_rad','mean_abs_roll_rad','mean_mirror_error_rad',
                    'mean_leg_length_difference_m','dual_contact_fraction'):
            values=[row.get('standing_metrics',{}).get(key) for row in rows]
            means[key]=sum(values)/len(values) if values and all(v is not None for v in values) else None
    return {**{key:value for key,value in entry.items() if key!='result'},'task':'recovery',
        'result_protocol':'continuous_standing' if continuous else 'recovery',
        'objective':continuous.get('objective','stationary') if continuous else 'recovery',
        'evaluation_family':result.get('evaluation_family'),
        'evaluation_curriculum_stage':result.get('evaluation_curriculum_stage',0),
        'retained_evaluations':result.get('retained_evaluations',[]),
        'eligible':not problems,'exclusion_reasons':problems,'accepted':not problems and bool(gate['accepted']),
        'passed_envs':gate['passed_envs'] if gate else 0,'per_env':rows,'gate':gate,
        'gate_evidence':normalized,'means':means}
