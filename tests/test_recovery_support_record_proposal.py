FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.recovery.support_record_proposal import quality,record_step,RecordState,declaration,validate

def test_length_slope_nonzero_at_actual_long_start_and_both_sides_contribute():
    length=torch.tensor([[.375,.376]],requires_grad=True)
    q=quality(length,torch.ones_like(length)*.28)['quality'];q.backward()
    assert (length.grad<0).all() and q.item()>0
    shortened=quality(torch.tensor([[.365,.376]]),torch.ones(1,2)*.28)['quality']
    assert shortened>q

def test_stall_oscillation_failure_and_cap():
    best=torch.tensor([.2]);total=0.
    for v in [.2,.3,.2,.3,.25,.4,.4]:
        r,best=record_step(torch.tensor([v]),best,eligible=torch.tensor([True]),failed=torch.tensor([False]))
        total+=r.item()
    assert abs(total-.3*(.4-.2))<1e-7
    r,best=record_step(torch.tensor([.8]),best,eligible=torch.tensor([True]),failed=torch.tensor([True]))
    assert r.item()==0 and best.item()>.79

def test_ineligible_old_group_or_after_entry_reward_zero():
    r,b=record_step(torch.tensor([.9]),torch.tensor([.2]),eligible=torch.tensor([False]),failed=torch.tensor([False]))
    assert r.item()==0 and torch.allclose(b,torch.tensor([.2]))

def test_pure_rotation_without_down_improvement_cannot_claim_height_bonus():
    initial=quality(torch.ones(1,2)*.375,torch.ones(1,2)*.28)['quality']
    r,_=record_step(initial,initial,eligible=torch.tensor([True]),failed=torch.tensor([False]))
    assert r.item()==0 # no height input, height alone cannot switch off cost.

def test_exact_precontrol_baseline_partial_reset_failure_and_snapshot_survives():
    s=RecordState(2,'cpu');s.before(torch.tensor([.2,.8]),torch.tensor([True,False]))
    r=s.after(torch.tensor([.3,.9]),torch.tensor([False,False]),beta=.3)
    assert torch.allclose(r,torch.tensor([.03,0.]))
    old=s.snapshot.clone();s.reset(torch.tensor([0]));assert torch.equal(old,s.snapshot)
    s.before(torch.tensor([.6,.8]),torch.tensor([True,False]))
    assert s.best[0]==.6
    assert (s.after(torch.tensor([.9,.9]),torch.tensor([True,False]),beta=.3)==0).all()

def test_oldgroup_afterentry_no_bonus_and_declared_episode_units():
    s=RecordState(1,'cpu');s.before(torch.tensor([.2]),torch.tensor([True]));s.after(torch.tensor([.3]),torch.tensor([False]),beta=.3)
    s.before(torch.tensor([.3]),torch.tensor([False]));assert s.after(torch.tensor([1.]),torch.tensor([False]),beta=.3)==0
    spec={'task':'recovery','recovery':{'support_record_reward':declaration(),'rising_task':{'version':'autonomous_rise_min_height_v2'}}}
    validate(spec);spec['recovery']['wheel_mean_auxiliary']={'enabled':True}
    import pytest
    with pytest.raises(ValueError):validate(spec)

def test_course_declares_record_only_and_rejects_aux_combination():
    from native_stand.command_v6.domain.recovery_course import parse_request
    import pytest
    f=declaration()['family']
    r={'purpose':'test','level_id':'Level3','current_family':f,'retained_families':['R0'],
       'family_weights':{f:.5,'R0':.5},'smoke_updates':10,'formal_updates':25,
       'evaluation_updates':[10,25],'wall_s':{'source_eval':900,'smoke':900,'formal':3600},
       'support_record_reward':declaration()}
    assert parse_request(r)['support_record_reward']==declaration()
    r['wheel_mean_auxiliary']={}
    with pytest.raises(ValueError,match='conflicting'):parse_request(r)


def test_smoke_requires_real_positive_record_not_update_count(tmp_path):
    import json,hashlib
    from native_stand.command_v6.wiring import smoke_certificate
    spec={'source_sha256':'source','budget':{'smoke_updates':10},'recovery':{'support_record_reward':declaration()}}
    records={'progress.json':{'actual_updates':10,'actor_parameters_changed':True,
        'evaluations':[{'cases':[{'path':'evaluation.json'}]}]},
        'terminal_report.json':{'status':'COMPLETED','actual_updates':10},
        'evaluation.json':{'per_env':[{}],'outcome_counts':{'runtime_fault':0}}}
    (tmp_path/'source_snapshot').mkdir();b=json.dumps(spec).encode();(tmp_path/'source_snapshot/spec.json').write_bytes(b)
    records['manifest.json']={'source_sha256':'source','spec_sha256':hashlib.sha256(b).hexdigest()}
    for k,v in records.items():(tmp_path/k).write_text(json.dumps(v))
    for value in (None,0.,float('nan'),-.1):
        (tmp_path/'metrics.jsonl').write_text(json.dumps({'rollout':{'weighted_mean':{'support_record_progress':value}}})+'\n')
        assert smoke_certificate(tmp_path,spec)['status']=='FAILED'
    (tmp_path/'metrics.jsonl').write_text(json.dumps({'rollout':{'weighted_mean':{'support_record_progress':.0001}},'task_metrics':{'support_record_audit':{'reset_count':2,'baseline_established_count':1,'failed_step_reward_violations':0,'ineligible_reward_violations':0,'episode_budget_violations':0}}})+'\n')
    assert smoke_certificate(tmp_path,spec)['status']=='PASSED'

def test_policy_readback_masks_samples_without_touching_rng_or_inputs():
    from native_stand.recovery.support_record_proposal import PolicyReadback
    mean=torch.zeros(2,6);mean[0,2]=2.;mean[1,2]=99
    std=torch.ones_like(mean)*.1;sample=mean.clone();before=mean.clone();rng=torch.get_rng_state().clone()
    r=PolicyReadback('cpu');r.add(mean,std,sample,torch.tensor([True,False]));s=r.summary()
    assert s['eligible_count']==1 and s['sample_clip_fraction']==[1.,0.]
    assert s['abs_mean_normalized']==[2.,0.]
    assert torch.equal(mean,before) and torch.equal(rng,torch.get_rng_state())
