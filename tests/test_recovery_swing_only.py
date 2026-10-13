FROZEN_TEST_SCOPE='PORTABLE'
import pytest
from native_stand.command_v6.domain.recovery_course import parse_request
from native_stand.recovery.sampling import validate_explicit
from native_stand.recovery.controlled_ppo import declaration

def test_single_swing_empty_retained_and_missing_active_not_vacuous_success():
    f='swing_candidate_from_historical_r1';r={'purpose':'test','level_id':'Level3','current_family':f,'retained_families':[],'family_weights':{f:1.},'environment_counts':{f:64},'smoke_updates':10,'formal_updates':100,'evaluation_updates':[25,50,100],'wall_s':{'source_eval':900,'smoke':900,'formal':3500},'swing_only':True,'actor_update_scope':declaration()}
    assert parse_request(r)['retained_families']==[]
    r['family_weights']={}
    with pytest.raises(ValueError):parse_request(r)

def test_bilateral_diagnostic_50ms_reset_and_not_gate():
    import torch
    from native_stand.recovery.swing_training_diagnostics import SwingDiagnostics
    d=SwingDiagnostics(2,'cpu');state=torch.zeros(2,39);pose=torch.zeros(2,10);pose[:,2:4]=.33;geo=torch.zeros(2,13);geo[:,7]=-1;geo[:,:6]=torch.tensor([1.,-1,0.,-1,-1,0.]);anchors=torch.zeros(2,3)
    for _ in range(5):
        d.pre(torch.tensor([True,False]),torch.zeros(2,6),torch.zeros(2,6),torch.zeros(2,6));d.post(state,pose,torch.zeros(2,6),torch.tensor([False,False]),geo,anchors)
    assert d.summary()['bilateral_short_034_50ms_events']==1
    assert d.summary()['milestone_is_not_accepted']

def test_swing_smoke_proves_completed_episode_without_requiring_115s_success():
    from native_stand.command_v6.domain.recovery_course import swing_smoke_contract
    from native_stand.command_v6.domain.execution_plan import smoke_plan
    f='swing_candidate_from_historical_r1';c=swing_smoke_contract(.01,1.,f)
    s={'wiring_smoke':c,'budget':{'smoke_updates':10},'ppo':{'envs':64,'steps_per_env':128},'control':{'policy_dt_s':.01},'recovery':{}}
    p=smoke_plan(s);assert p['budget_sufficient'] and p['required_event']=='completed_episode'
    assert p['required_event_duration_s']==.01
    assert c['required_groups'][0]['require_runtime_initial_valid']
    assert .7>=p['required_event_duration_s'] # real short task-failure episode qualifies engineering duration
    assert 0<p['required_event_duration_s'] # empty/no episode never qualifies
