"""Explicit stop decision independent from immutable capability scoring."""

def declaration():
    return {'version':'recovery_retention_contact_diagnostic_v1','trigger':'continuous_contact_only',
            'action':'record_only','scope':'retained_families','all_other_regression':'stop'}


def contact_only_failure(results):
    failed=[r for r in results if not r.get('accepted',False)]
    if not failed:return False
    for r in failed:
        rows=r.get('per_env')
        if not rows:return False
        for e in rows:
            if e.get('success'):continue
            checks=set(e.get('standing_failed_checks') or [])
            if (not e.get('hold_window_complete') or not checks or 'continuous_contact' not in checks
                or not checks<= {'continuous_contact','terminal_certificate'} or e.get('runtime_fault')):return False
    return True


def should_stop(regressed,results,config=None):
    if config is not None and config!=declaration():raise ValueError('Unknown regression policy')
    return bool(regressed and not (config is not None and contact_only_failure(results)))
