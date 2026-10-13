"""Pure submission metadata validation; a declaration never grants new permission."""


def authorization(spec):
    value = spec.get('authorization')
    if value is None:
        return {'status': 'UNKNOWN'}
    if isinstance(value, str):
        value = {'status': value}
    if not isinstance(value, dict):
        raise ValueError('authorization must be an object or legacy status string')
    result = dict(value)
    result.setdefault('status', 'UNKNOWN')
    if result['status'] not in ('AUTHORIZED', 'UNAUTHORIZED', 'UNKNOWN'):
        raise ValueError('authorization.status must be AUTHORIZED, UNAUTHORIZED or UNKNOWN')
    session = result.get('hapi_session')
    if session is not None and (not isinstance(session, str) or not session.strip()):
        raise ValueError('authorization.hapi_session must be a nonempty string')
    return result


def metadata(spec, *, target_session, current_session, physical_gpu,
             output_available=True, duplicate_submission=False):
    """No I/O. UNKNOWN legacy declarations still require authorized ledger preflight."""
    errors = []
    try:
        effective = authorization(spec)
    except ValueError as exc:
        return {'status': 'NOT_READY', 'errors': [str(exc)], 'reason_code': 'CONFIG_ERROR',
                'effective_authorization': None}
    if effective['status'] == 'UNAUTHORIZED':
        errors.append('spec explicitly declares UNAUTHORIZED')
    if not target_session or not current_session or target_session != current_session:
        errors.append('explicit HAPI target must match current session')
    if effective.get('hapi_session') and effective['hapi_session'] != target_session:
        errors.append('HAPI target differs from the authorized spec')
    if physical_gpu not in (0, 1) or isinstance(physical_gpu, bool):
        errors.append('explicit physical GPU is required for submission')
    elif spec.get('device', {}).get('physical_index', physical_gpu) != physical_gpu:
        errors.append('physical GPU differs from spec')
    if not output_available:
        errors.append('output path already exists')
    if duplicate_submission:
        errors.append('chain submission already exists; duplicate submission forbidden')
    reason = ('AUTHORIZATION_MISSING' if any('UNAUTHORIZED' in e or 'HAPI' in e for e in errors)
              else 'CONFIG_ERROR' if errors else 'OK')
    return {'status': 'NOT_READY' if errors else 'READY_METADATA',
            'reason_code': reason, 'errors': errors, 'effective_authorization': effective}
