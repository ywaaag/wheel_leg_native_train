"""Owned-child chain interface fixtures; no Isaac or online PPO."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from native_stand.command_v6.domain.execution_plan import samples_for_updates,smoke_plan
from native_stand.command_v6 import stand_chain
from native_stand.command_v6.wiring import validate_persisted_certificate


def holding_spec(updates=9):
    return {'source_sha256':'fixture','ppo':{'envs':64,'steps_per_env':128},
            'control':{'policy_dt_s':.01},'budget':{'smoke_updates':updates},
            'recovery':{'initialization':{'settle_max_s':1.},'standing_task':{
                'training_episode':{'seconds':10.}}}}


def test_smoke_minimum_uses_event_duration_offset_and_spec_dimensions():
    spec=holding_spec()
    plan=smoke_plan(spec)
    assert plan['minimum_updates']==9 and plan['minimum_samples']==9*64*128
    assert plan['planned_seconds_per_env']==pytest.approx(11.52)
    assert plan['budget_sufficient'] is True
    assert smoke_plan(holding_spec(3))['budget_sufficient'] is False
    assert holding_spec(3)['budget']['smoke_updates']==3
    assert samples_for_updates({'ppo':{'envs':8,'steps_per_env':32}},3)==768
    with pytest.raises(ValueError):samples_for_updates({'ppo':{'envs':8,'steps_per_env':32}},True)


def test_smoke_requirement_explicit_shorter_or_longer_than_ten_seconds():
    spec=holding_spec(1)
    spec['wiring_smoke']={'required_event':'completed_episode','required_event_duration_s':.5,'event_offset_s':0.}
    assert smoke_plan(spec)['minimum_updates']==1
    spec['wiring_smoke']['required_event_duration_s']=30.
    assert smoke_plan(spec)['minimum_updates']==24
    spec['wiring_smoke']['unknown']=0
    with pytest.raises(ValueError,match='unknown wiring_smoke'):smoke_plan(spec)


def event_message(events, *, wait_for_formal=False):
    reader,writer=os.pipe()
    try:
        for event in events:stand_chain.chain_event(writer,event)
        os.close(writer)
        writer=None
        return stand_chain.read_startup_events(reader,wait_s=.01,wait_for_formal=wait_for_formal)
    finally:
        os.close(reader)
        if writer is not None:os.close(writer)


def test_submission_first_stage_is_separate_from_formal_proof():
    result=event_message([{'event_type':'stage_started','phase':'source_eval'}])
    assert result['status']=='SUBMITTED' and result['current_stage']=='source_eval'
    assert result['started'] is False and result['formal_first_update_verified'] is False
    assert result['identity_verified'] is False


def test_optional_formal_wait_consumes_owned_events_before_first_update():
    result=event_message([
        {'event_type':'stage_started','phase':'source_eval'},
        {'event_type':'stage_finished','phase':'source_eval','exit_code':0},
        {'event_type':'stage_started','phase':'smoke'},
        {'event_type':'stage_finished','phase':'smoke','exit_code':0},
        {'event_type':'stage_started','phase':'formal'},
        {'status':'RUNNING','actual_updates':1,'trainer_pid':42}],wait_for_formal=True)
    assert result['status']=='RUNNING' and result['current_stage']=='formal'
    # Process/spec/progress verification still belongs to validate_handshake.
    assert result['formal_first_update_verified'] is False and result['started'] is False


def test_failed_owned_phase_and_malformed_event_never_report_started():
    result=event_message([{'event_type':'stage_finished','phase':'source_eval','exit_code':1}])
    assert result['status']=='FAILED' and result['started'] is False
    reader,writer=os.pipe()
    try:
        os.write(writer,b'invalid JSON\n')
        result=stand_chain.read_startup_events(reader,wait_s=.01)
        assert result['status']=='UNKNOWN' and result['started'] is False
    finally:os.close(reader);os.close(writer)


def test_startup_pipe_closed_is_only_a_notification_failure():
    reader,writer=os.pipe()
    os.close(reader)
    try:stand_chain.chain_event(writer,{'event_type':'stage_started','phase':'source_eval'})
    finally:os.close(writer)


def test_run_phase_is_single_certificate_generation_owner(tmp_path,monkeypatch,complete_smoke_fixture):
    spec_path=tmp_path/'spec.json'
    spec={'source_sha256':'fixture','budget':{'smoke_updates':3}}
    spec_path.write_text(json.dumps(spec))
    output=tmp_path/'smoke'
    from native_stand.command_v6.tools.submission_receipt import Approval
    monkeypatch.setattr(stand_chain,'check',lambda *args,**kwargs:Approval({'status':'PASS'}))
    monkeypatch.setattr(stand_chain,'Ledger',lambda *args:SimpleNamespace(reserve=lambda *args,**kwargs:None))
    def spawn(*args,**kwargs):
        output.mkdir()
        complete_smoke_fixture(output,spec_path,3)
        (output/'wiring_certificate.json').unlink()
        return SimpleNamespace(pid=42,wait=lambda:0)
    monkeypatch.setattr(stand_chain.subprocess,'Popen',spawn)
    row=stand_chain.run_phase(spec_path,'smoke',output)
    assert row['exit_code']==0
    evidence=output/'wiring_certificate.json'
    before=evidence.read_bytes()
    assert validate_persisted_certificate(output,spec)['status']=='PASSED'
    assert evidence.read_bytes()==before
    changed=json.loads((output/'progress.json').read_text());changed['actual_updates']=2
    (output/'progress.json').write_text(json.dumps(changed))
    assert validate_persisted_certificate(output,spec)['status']=='FAILED'
    assert evidence.read_bytes()==before


def test_smoke_insufficient_event_budget_fails_before_reservation(tmp_path,monkeypatch):
    spec_path=tmp_path/'spec.json';spec_path.write_text(json.dumps(holding_spec(3)))
    monkeypatch.setattr(stand_chain,'Ledger',lambda *args:pytest.fail('no reservation before sufficient sampling'))
    with pytest.raises(ValueError,match='cannot cover'):
        stand_chain.run_phase(spec_path,'smoke',tmp_path/'smoke')
