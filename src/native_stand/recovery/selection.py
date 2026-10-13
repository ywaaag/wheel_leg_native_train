"""Recovery candidate classification; no standing certification by proxy."""
import math


def rise_rank(entry):
    """Progress ordering is diagnostic; only the full gate can accept a model."""
    rows=entry['per_env']
    retained=entry.get('retained_evaluations',[])
    retained_pass=sum(item.get('passed_envs',0) for item in retained)
    if entry.get('gate',{}).get('effective_protocol',{}).get('protocol_identity')=='autonomous_rise_min_height_v2' or any('diagnostic_hold_prefix_s' in row for row in rows):
        groups=[rows]+[item.get('per_env',[]) for item in retained]
        prefixes=[min((row.get('diagnostic_hold_prefix_s',0.) for row in group),default=0.) for group in groups]
        entries=[sum(row.get('recovery_s') is not None for row in group) for group in groups]
        return (-int(entry['accepted']),-min(entries),-min(prefixes),
                -entry['passed_envs']-retained_pass,entry['checkpoint_sha256'])
    entered=[r for r in rows if r.get('recovery_s') is not None]
    complete=sum(r.get('post_rise_evidence_status')=='COMPLETE' and
                 not r.get('standing_failed_checks') for r in rows)
    falls=sum(r.get('episode_result',{}).get('terminated',False) for r in rows)
    # Failed windows never gain rank merely by collecting more pre-entry time.
    return (-int(entry['accepted']),-entry['passed_envs'],-retained_pass,-complete,
            falls,-len(entered),entry['checkpoint_sha256'])


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
    minimum_v2=bool(continuous and continuous.get('protocol_identity')=='autonomous_rise_min_height_v2')
    required=10. if minimum_v2 else 2. if protocol.get('mode')=='autonomous_hold' else 5.
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
                (row.get('post_rise_observed_s',0.)<10.-1e-3 if minimum_v2 else
                 row.get('continuous_s',0.)<continuous['seconds']-1e-3) or
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
        'result_protocol':('autonomous_rise' if continuous and
            continuous.get('protocol_identity') in ('autonomous_rise_v1','autonomous_rise_min_height_v2') else
            'continuous_standing' if continuous else 'recovery'),
        'objective':continuous.get('objective','stationary') if continuous else 'recovery',
        'evaluation_family':result.get('evaluation_family'),
        'evaluation_curriculum_stage':result.get('evaluation_curriculum_stage',0),
        'retained_evaluations':result.get('retained_evaluations',[]),
        'eligible':not problems,'exclusion_reasons':problems,'accepted':not problems and bool(gate['accepted']),
        'passed_envs':gate['passed_envs'] if gate else 0,'per_env':rows,'gate':gate,
        'gate_evidence':normalized,'means':means}
