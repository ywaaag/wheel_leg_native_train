"""Small pure helpers for versioned evaluation and gate evidence."""
from __future__ import annotations

import hashlib
import json
import math

GATE_STATES = ("PASSED", "FAILED", "NOT_RUN", "MISSING_EVIDENCE", "CONFLICTING_EVIDENCE")
PROTOCOL_FIELDS = frozenset('''checkpoint_every_updates closure_max_m command_mode direction_fraction_min
dual_contact_min durability_only_for_selected durability_seconds durability_steady_window_s envs
evaluation_schedule_s final_evaluation_seeds full_at_final full_every_updates gate_identity
height_steady_fraction_min hold_seconds light_every_updates light_seconds light_window_s motion_commands
motion_protocol motion_vx_error_cap_mps motion_vx_error_floor_mps motion_vx_error_fraction
motion_vx_error_max_mps motion_vx_min_speed_enabled motion_vx_min_speed_fraction motion_window_s
motion_yaw_error_cap_rad_s motion_yaw_error_floor_rad_s motion_yaw_error_fraction
motion_yaw_error_max_rad_s motion_yaw_min_speed_enabled motion_yaw_min_speed_fraction peak_tilt_max_rad
protocol_identity relative_motion_error_fraction run_final_durability saturation_fraction_max
scored_envs seconds seed standing_drift_max_m standing_excursion_max_m standing_height_m steady_window_s
stop_window_s tracking_mode unlock_full_updates vx_error_max_mps vy_abs_max_mps yaw_drift_max_m
yaw_error_max_rad_s yaw_excursion_max_m zero_mean_abs_vx_max_mps zero_mode excursion_max_m
height_fraction_min height_m leg_length_difference_max_m level_mean_max_rad level_peak_max_rad
mirror_error_max_rad objective saturation_max support_difference_max version vx_abs_max_mps
yaw_abs_max_rad_s parking_window_s requested_seconds actual_duration_seconds sample_rate_hz
termination_semantics metric_scope effective_protocol_sha256 diagnostics
observed_duration_per_env_s scoring_protocol_sha256 yaw_translation_max_mps
straight_yaw_max_rad_s field_boundary_max_m zero_every_updates
recovery_deadline_s post_rise_hold_s window_alignment'''.split())


def effective_protocol(protocol, *, requested_seconds, actual_duration_seconds=None,
                       steady_window_s=None, motion_window_s=None, parking_window_s=None,
                       sample_rate_hz, scored_envs, termination_semantics):
    """Return an immutable-by-convention protocol record for the scoring actually run."""
    if not isinstance(protocol, dict):
        raise TypeError("evaluation protocol must be an object")
    unknown=set(protocol)-PROTOCOL_FIELDS
    if unknown:raise ValueError('unknown evaluation protocol fields: '+', '.join(sorted(unknown)))
    if protocol.get('protocol_identity') == 'motion_absolute_v3':
        required=('motion_window_s','steady_window_s','parking_window_s','standing_height_m',
            'closure_max_m','peak_tilt_max_rad','saturation_fraction_max','dual_contact_min',
            'vy_abs_max_mps','zero_mean_abs_vx_max_mps','motion_vx_error_max_mps',
            'motion_yaw_error_max_rad_s','direction_fraction_min','straight_yaw_max_rad_s',
            'yaw_translation_max_mps','yaw_drift_max_m','yaw_excursion_max_m','field_boundary_max_m')
        absent=[key for key in required if key not in protocol]
        if absent:raise ValueError('absolute protocol missing fields: '+', '.join(absent))
        if protocol.get('command_mode') != 'ramp':
            raise ValueError('absolute_v3 recheck explicitly requires ramp command mode')
        for key in required:
            if key.endswith('_s') or key=='standing_height_m':continue
            value=protocol[key]
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
                raise ValueError('invalid absolute protocol threshold: '+key)
    duration = float(requested_seconds if actual_duration_seconds is None else actual_duration_seconds)
    requested = float(requested_seconds)
    rate = float(sample_rate_hz)
    if not (math.isfinite(duration) and 0 <= duration <= requested and
            all(math.isfinite(v) and v > 0 for v in (requested, rate))):
        raise ValueError("protocol duration and sample rate must be finite and positive")
    if type(scored_envs) is not int or scored_envs < 1:
        raise ValueError("scored_envs must be positive")
    def window(value, label):
        if value is None:
            return None
        if len(value) != 2:
            raise ValueError(f"{label} must have two endpoints")
        start, end = map(float, value)
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= requested):
            raise ValueError(f"{label} must be within the actual duration")
        return [start, end]
    result = dict(protocol)
    result.update({
        "requested_seconds": requested,
        "actual_duration_seconds": duration,
        "steady_window_s": window(steady_window_s, "steady_window_s"),
        "motion_window_s": window(motion_window_s, "motion_window_s"),
        "parking_window_s": window(parking_window_s, "parking_window_s"),
        "sample_rate_hz": rate,
        "scored_envs": int(scored_envs),
        "termination_semantics": str(termination_semantics),
        "metric_scope": {
            "steady_metrics": "steady_window",
            "survival_metrics": "full_episode",
            "parking_metrics": "parking_window",
        },
    })
    result["protocol_identity"] = result.get("protocol_identity", "effective_v1")
    identity_payload = {k: v for k, v in result.items() if k != "effective_protocol_sha256"}
    result["effective_protocol_sha256"] = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return result


def protocol_contract(record):
    """Scoring identity excludes observed duration and collection-only diagnostics."""
    return {key:value for key,value in record.items() if key not in (
        'actual_duration_seconds','observed_duration_per_env_s','effective_protocol_sha256',
        'scoring_protocol_sha256','diagnostics')}


def protocol_hash(record):
    return hashlib.sha256(json.dumps(protocol_contract(record),sort_keys=True,
        separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def observed_protocol(record,durations):
    durations=[float(value) for value in durations]
    if len(durations)!=record['scored_envs']:raise ValueError('observed duration environment count differs')
    if any(not math.isfinite(value) or value<0 or value>record['requested_seconds']+1e-5 for value in durations):
        raise ValueError('observed duration outside requested scoring window')
    updated={**record,'observed_duration_per_env_s':durations,
             'scoring_protocol_sha256':protocol_hash(record)}
    return effective_protocol(updated,requested_seconds=record['requested_seconds'],
        actual_duration_seconds=min(record['requested_seconds'],max(durations,default=0.)),
        steady_window_s=record['steady_window_s'],motion_window_s=record.get('motion_window_s'),
        parking_window_s=record.get('parking_window_s'),sample_rate_hz=record['sample_rate_hz'],
        scored_envs=record['scored_envs'],termination_semantics=record['termination_semantics'])


def validate_effective_protocol(record):
    rebuilt=effective_protocol(record,requested_seconds=record['requested_seconds'],
        actual_duration_seconds=record['actual_duration_seconds'],steady_window_s=record['steady_window_s'],
        motion_window_s=record.get('motion_window_s'),parking_window_s=record.get('parking_window_s'),
        sample_rate_hz=record['sample_rate_hz'],scored_envs=record['scored_envs'],
        termination_semantics=record['termination_semantics'])
    if rebuilt!=record:raise ValueError('effective protocol contents or SHA differ')
    if record.get('scoring_protocol_sha256') and record['scoring_protocol_sha256']!=protocol_hash(record):
        raise ValueError('scoring protocol SHA differs')
    return record


def resolve_gate(result, task, *, expected_protocol_sha256=None, expected_envs=None,expected_protocol=None):
    """Normalize task-specific gate evidence without treating missing data as a pass."""
    gate_key = {"standing": "standing_gate", "recovery": "recovery_gate",
                "capability": "capability_gate", "motion": "motion_gate"}.get(task)
    if gate_key is None:
        raise ValueError(f"unknown gate task: {task}")
    raw = result.get(gate_key) if isinstance(result, dict) else None
    if isinstance(result, dict) and result.get('status')=='NOT_RUN':
        return {'raw_gate':raw,'status':'NOT_RUN','missing_fields':[],
                'conflicts':[],'candidate_eligible':False}
    if raw is None:
        return {"raw_gate": None, "status": "MISSING_EVIDENCE", "missing_fields": [gate_key],
                "conflicts": [], "candidate_eligible": False}
    if not isinstance(raw, dict):
        return {"raw_gate": raw, "status": "MISSING_EVIDENCE", "missing_fields": ["gate_object"],
                "conflicts": [], "candidate_eligible": False}
    if raw.get('status')=='NOT_RUN':
        return {'raw_gate':raw,'status':'NOT_RUN','missing_fields':[],'conflicts':[],
                'candidate_eligible':False}
    conflicts = []
    missing = [key for key in ("accepted", "passed_envs", "per_env") if key not in raw]
    rows=raw.get('per_env')
    if type(raw.get('accepted')) is not bool:missing.append('accepted_boolean')
    if type(raw.get('passed_envs')) is not int:missing.append('passed_envs_integer')
    if not isinstance(rows,list) or not rows or any(not isinstance(row,dict) for row in rows):
        missing.append('per_env_nonempty_records')
        rows=[]
    if missing:
        return {'raw_gate':raw,'status':'MISSING_EVIDENCE','missing_fields':missing,
                'conflicts':[],'candidate_eligible':False}
    if any(type(row.get('accepted')) is not bool and not isinstance(row.get('failed_checks'),list) for row in rows):
        return {'raw_gate':raw,'status':'MISSING_EVIDENCE','missing_fields':['per_env_gate_decision'],
                'conflicts':[],'candidate_eligible':False}
    if any(type(row.get('accepted')) is bool and isinstance(row.get('failed_checks'),list) and
           row['accepted']!=(not row['failed_checks']) for row in rows):
        conflicts.append('per_env_decision_conflict')
    if not 0<=raw['passed_envs']<=len(rows):conflicts.append('passed_envs_range')
    if 'scored_envs' in raw and (type(raw['scored_envs']) is not int or raw['scored_envs']!=len(rows)):
        conflicts.append('raw_scored_env_count')
    if expected_envs is not None and raw.get("scored_envs", expected_envs) != expected_envs:
        conflicts.append("scored_envs")
    if expected_envs is not None and isinstance(raw.get("per_env"), list) and len(raw["per_env"]) != expected_envs:
        conflicts.append("per_env_count")
    if raw.get('accepted') is True and isinstance(raw.get('per_env'),list) and raw.get('passed_envs')!=len(raw['per_env']):
        conflicts.append('accepted_passed_count')
    rows=raw.get('per_env',[])
    if isinstance(rows,list) and rows and all(isinstance(row,dict) and 'accepted' in row for row in rows):
        if sum(row['accepted'] is True for row in rows)!=raw.get('passed_envs'):
            conflicts.append('per_env_passed_count')
        if raw.get('accepted')!=(all(row['accepted'] is True for row in rows)):
            conflicts.append('per_env_accepted_conflict')
    if isinstance(rows,list) and rows and all(isinstance(row,dict) and 'failed_checks' in row for row in rows):
        if sum(not row['failed_checks'] for row in rows)!=raw.get('passed_envs'):
            conflicts.append('per_env_failed_checks_count')
        if raw.get('accepted')!=(all(not row['failed_checks'] for row in rows)):
            conflicts.append('per_env_failed_checks_accepted')
    if isinstance(rows,list) and rows and all(isinstance(row,dict) and 'env_id' in row for row in rows):
        if len({row['env_id'] for row in rows})!=len(rows):conflicts.append('duplicate_env_id')
    if 'accepted' in result and result['accepted']!=raw.get('accepted'):
        conflicts.append('report_raw_gate')
    protocol = result.get("effective_protocol", {})
    if protocol:
        try:validate_effective_protocol(protocol)
        except (ValueError,KeyError,TypeError):conflicts.append('invalid_effective_protocol')
    if expected_protocol is not None:
        if not protocol:missing.append('effective_protocol')
        elif protocol_contract(protocol)!=protocol_contract(expected_protocol):conflicts.append('protocol_contract')
    if expected_protocol_sha256 and protocol.get("effective_protocol_sha256") != expected_protocol_sha256:
        conflicts.append("protocol_identity")
    if conflicts:
        status = "CONFLICTING_EVIDENCE"
    elif missing:
        status = "MISSING_EVIDENCE"
    elif raw.get("accepted") is True and int(raw.get("passed_envs", 0)) == len(raw["per_env"]):
        status = "PASSED"
    else:
        status = "FAILED"
    return {"raw_gate": raw, "status": status, "missing_fields": missing,
            "conflicts": conflicts, "candidate_eligible": status in ("PASSED", "FAILED")}


def diagnostic_field(value, *, requested, enabled, sample_count=0, scope="policy_step", missing_reason=None):
    valid = bool(enabled and sample_count > 0 and value is not None)
    return {"value": value if valid else None, "requested": bool(requested), "enabled": bool(enabled),
            "valid": valid, "sample_count": int(sample_count),
            "missing_reason": None if valid else (missing_reason or
                ("not_requested" if not requested else "runtime_not_enabled" if not enabled else "field_unavailable")),
            "scope": scope}


def field_validity(names,*,requested,enabled,sample_count,scope,available=True):
    return {name:diagnostic_field(True if available else None,requested=requested,enabled=enabled,
        sample_count=sample_count,scope=scope) for name in names}


def tensor_field_validity(rows,valid,names,*,requested,enabled,scope):
    """One aggregate transfer after collection; uncollected/invalid values stay null."""
    if not enabled or rows is None:
        return field_validity(names,requested=requested,enabled=enabled,sample_count=0,scope=scope,available=False)
    import torch
    if rows.shape[:-1]!=valid.shape or rows.shape[-1]!=len(names):
        raise ValueError('diagnostic field names and tensor dimensions differ')
    finite=torch.isfinite(rows)
    masked=valid[...,None].expand_as(finite)
    counts=(finite & masked).reshape(-1,len(names)).sum(0)
    bad=(~finite & masked).reshape(-1,len(names)).sum(0)
    packed=torch.stack((counts,bad)).cpu().tolist()
    return {name:diagnostic_field(True if failures==0 else None,requested=requested,enabled=enabled,
        sample_count=count,scope=scope,missing_reason='nonfinite_samples' if failures else None)
        for name,count,failures in zip(names,*packed)}
