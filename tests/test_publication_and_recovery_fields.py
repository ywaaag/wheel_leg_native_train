FROZEN_TEST_SCOPE='PORTABLE'
import json
import pytest
import torch
from native_stand.command_v6.tools.experiment_preparation import publish,verify_publication,digest
from native_stand.recovery.reward_fields import resolve,verify


def test_single_and_multi_marker_checked_before_registration(tmp_path):
    for prefix in ('','A/'):
        root=tmp_path/('single' if not prefix else 'multi')
        publish(root,{prefix+'spec.json':{},prefix+'budget.json':{},'preparation_manifest.json':{}},{},completion_marker=True)
        spec=root/(prefix+'spec.json')
        assert verify_publication(spec)['status']=='VERIFIED'
        spec.write_text('{"tampered":true}')
        with pytest.raises(ValueError,match='SHA'):verify_publication(spec)


def test_authorized_receipt_handles_explicit_spec_change(tmp_path):
    publish(tmp_path/'x',{'spec.json':{},'budget.json':{}},{},completion_marker=True)
    root=tmp_path/'x';s=root/'spec.json';s.write_text('{"authorization":"AUTHORIZED"}')
    (root/'budget.json').write_text(json.dumps({'authorization':'AUTHORIZED','approval_id':'approve','used':{'formal':1}}))
    (root/'authorization_receipt.json').write_text(json.dumps({'spec_sha256':digest(s),'approval_id':'approve'}))
    assert verify_publication(s,authorized=True)['status']=='VERIFIED'
    with pytest.raises(ValueError):verify_publication(s)


def test_reward_field_declaration_and_scope():
    r={'support':1};c={'support_record_reward':{},'settling_reward':{'kind':'pseudo_huber'}}
    # An enabled nonempty declaration activates optional record reward.
    c['support_record_reward']={'beta':.3}
    names=resolve(r,c);assert 'support_record_progress' in names and 'support' in names
    values={k:torch.zeros(2) for k in names};verify(values,values,r,c)
    values.pop('support_record_progress')
    with pytest.raises(ValueError):verify(values,values,r,c)


def test_storage_audit_does_not_read_excluded_tree_or_delete(tmp_path):
    from native_stand.command_v6.tools.audit_storage import audit
    old=tmp_path/'old';old.mkdir();(old/'analysis.json').write_text('{}')
    active=tmp_path/'active';active.mkdir();(active/'analysis.json').write_text('do not inspect')
    result=audit(tmp_path,[active])
    assert len(result['files'])==1 and result['files_deleted']==0
    assert (active/'analysis.json').read_text()=='do not inspect'
    with pytest.raises(ValueError):audit(tmp_path,[])


def test_record_lightweight_audit_reset_baseline_failed_and_budget():
    from native_stand.recovery.support_record_proposal import RecordState
    state=RecordState(2,'cpu');state.reset(torch.arange(2))
    state.before(torch.tensor([.1,.1]),torch.tensor([True,False]))
    state.after(torch.tensor([.2,.9]),torch.tensor([True,False]),beta=.3)
    report=state.audit_summary()
    assert report['reset_count']==2 and report['baseline_established_count']==1
    assert all(report[k]==0 for k in ('failed_step_reward_violations','ineligible_reward_violations','episode_budget_violations'))


def test_storage_profiles_change_estimated_trace_bytes():
    from native_stand.command_v6.tools.storage_budget import estimate
    s={'task':'motion','control':{'policy_dt_s':.01},'budget':{'formal_updates':25},
        'evaluation':{'seconds':30,'diagnostic_profile':'summary'},'ppo':{'envs':64,'steps_per_env':128}}
    small=estimate(s,'formal');s['evaluation']['diagnostic_profile']='full_transition';full=estimate(s,'formal')
    s['evaluation']['diagnostic_profile']='paired_state';paired=estimate(s,'formal')
    assert small['evaluation_bytes']<full['evaluation_bytes']<paired['evaluation_bytes']
    assert small['storage_profiles']==['summary']


def test_record_created_under_inference_resets_outside_it():
    from native_stand.recovery.support_record_proposal import RecordState
    with torch.inference_mode():state=RecordState(2,'cpu')
    state.reset(torch.arange(2))
    state.before(torch.tensor([.1,.1]),torch.tensor([True,False]))
    assert state.audit_summary()['baseline_established_count']==1
