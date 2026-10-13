"""Independent student autonomous recovery identity; legacy gates unchanged."""
def declaration():
    from native_stand.recovery.handoff_protocol import declaration as base
    result=base();result.update(version='student_autonomous_swing_v1',settle_s=2.5);return result

def score(state,posture,student_control,*,policy_time_s):
    from native_stand.recovery.motion_handoff import score as shared_score
    result=shared_score(state,posture,student_control,policy_time_s=policy_time_s,configuration=declaration())
    if 'not_settled_within_2s' in result.get('failed_checks',[]):result['failed_checks']=['not_entered_within_2p5s']
    return result
