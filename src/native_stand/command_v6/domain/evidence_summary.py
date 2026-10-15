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


def ledger_summary(book,*,reference,sha256):
    """Accounting stays explicit; immutable receipt bodies live in the original ledger."""
    attempts={}
    for key,row in book.get('attempts',{}).items():
        summary={name:item for name,item in row.items() if name!='submission_receipt'}
        if row.get('submission_receipt'):
            summary['submission_receipt_reference']={'ledger':reference,'attempt_id':key,
                'sha256':row['submission_receipt']['sha256']}
        attempts[key]=summary
    return {**{k:v for k,v in book.items() if k!='attempts'},'attempts':attempts,
            'raw_ledger_reference':{'path':reference,'sha256':sha256}}


def selection_summary(value):
    """Retain model identity/counts, not repeated per-environment certificate bodies."""
    if isinstance(value,dict):
        return {key:selection_summary(item) for key,item in value.items()
                if key not in ('per_env','evaluations','cases','conditions','gate_evidence','per_command')}
    if isinstance(value,list):return [selection_summary(item) for item in value]
    return value
