FROZEN_TEST_SCOPE='PORTABLE'
from native_stand.recovery.regression_policy import declaration,should_stop

def test_contact_only_complete_hold_can_be_diagnostic_but_gate_unchanged():
    r=[{'accepted':False,'per_env':[{'success':False,'hold_window_complete':True,'standing_failed_checks':['continuous_contact','terminal_certificate'],'runtime_fault':False}]}]
    assert should_stop(True,r) and not should_stop(True,r,declaration())
    assert r[0]['accepted'] is False

def test_other_or_unknown_failures_and_runtime_fault_still_stop():
    for e in ({'standing_failed_checks':['continuous_contact','roll']},{'hold_window_complete':False},{'runtime_fault':True},{'standing_failed_checks':[]}):
        row={'success':False,'hold_window_complete':True,'standing_failed_checks':['continuous_contact'],'runtime_fault':False,**e}
        assert should_stop(True,[{'accepted':False,'per_env':[row]}],declaration())
    assert should_stop(True,[],declaration())
    assert not should_stop(False,[],declaration())
