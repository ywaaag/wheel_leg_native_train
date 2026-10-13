"""Limits, actual completed work and settled charges are distinct facts."""
def summary(manifest,terminal,progress,book):
    attempt=book.get('attempts',{}).get(manifest.get('attempt_id'),{})
    phase=manifest.get('phase',attempt.get('phase'))
    actual=terminal.get('actual_updates',progress.get('actual_updates'))
    settled=bool(attempt and attempt.get('status')!='RUNNING')
    return {'reserved_phase_limit':book.get('limits',{}).get(phase),
        'reserved_attempt_updates':attempt.get('reserved_updates'),
        'actual_completed':actual,'ledger_charged':attempt.get('updates'),
        'settled':settled,'settled_updates':attempt.get('updates') if settled else None,
        'counts_match':actual==attempt.get('updates') if attempt and actual is not None else None,
        'note':'phase limit is not an attempt reservation or completed count; absent reservation stays UNKNOWN'}
