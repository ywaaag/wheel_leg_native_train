"""Small result representation; raw arrays live only in identity-bound evaluations."""
import hashlib,json
RAW_KEYS={'trace','compact_trace_100hz','posture_trace_100hz','control_diagnostics_100hz',
    'gate_diagnostics_100hz','wheel_geometry_trace_100hz','failure_window_100hz',
    'failure_posture_window_100hz','failure_geometry_window_100hz','control_diagnostics','paired_state',
    'posture_geometry_trace_100hz','actor_input_trace_100hz'}


def compact(value,key=''):
    if isinstance(value,dict) and value.get('raw_array_omitted') is True:return value
    if key in RAW_KEYS and value is not None:
        return {'raw_array_omitted':True,'evidence_field':key,
            'item_count':len(value) if isinstance(value,(dict,list)) else None}
    if isinstance(value,dict):return {k:compact(v,k) for k,v in value.items()}
    if isinstance(value,list):return [compact(v,key) for v in value]
    return value


def result(value,*,reference,sha256):
    return {**compact(value),'raw_evidence':{'path':reference,'sha256':sha256,
        'scope':'load full data via identity-bound evaluation_loader; summary never substitutes for arrays'}}
