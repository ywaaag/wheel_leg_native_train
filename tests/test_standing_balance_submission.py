"""CPU/fake-process gates for the authorized immutable execution snapshot."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

from native_stand.command_v6 import stand_chain
from native_stand.command_v6.completion import write,plan
from native_stand.command_v6.tools.preflight import check

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/recovery_standing_balance_20261006/spec.json'


def test_authorized_total_is_not_10000_plus_smoke():
    spec=json.loads(SPEC.read_text())
    book=json.loads(SPEC.with_name('budget.json').read_text())
    assert spec['budget']['smoke_updates']+spec['budget']['formal_updates']==10000
    assert book['sample_limit']==10000*64*128
    assert sum(spec['budget'][key] for key in ('source_eval_wall_s','smoke_wall_s',
        'formal_wall_s','durability_wall_s'))+60==36000
    assert spec['recovery']['curriculum']['max_enabled_stage']==0
    assert book['authorization']=='AUTHORIZED'
    assert spec['evaluation']['checkpoint_every_updates']==100
    assert plan(spec,'formal')['updates']==9997


def test_authorized_preflight_plan_has_no_writes(tmp_path):
    output=tmp_path/'source_eval'
    before=SPEC.with_name('budget.json').read_bytes()
    result=check(SPEC,output,'source_eval')
    assert result['status'] in ('PASS','READY_NEEDS_AUTH') and result['cpu_valid']
    if result['status']=='READY_NEEDS_AUTH':assert result['reason_code']=='BUDGET_EXHAUSTED'
    assert not output.exists() and before==SPEC.with_name('budget.json').read_bytes()


def test_snapshot_is_used():
    source=Path(stand_chain.__file__).read_text()
    assert "shutil.copytree(ROOT.parent,chain/'source_snapshot/native_stand'" in source
    assert "chain/'source_snapshot/native_stand/command_v6/stand_chain.py'" in source
    assert "start_new_session=True" in source
    assert "chain_wall_s" in source and "validate_handshake" in source


def test_fake_chain_runs_once_notifies_once(tmp_path,monkeypatch,complete_smoke_fixture):
    spec=tmp_path/'spec.json'
    config=json.loads(SPEC.read_text());write(spec,config)
    write(tmp_path/'budget.json',{'limits':{'formal':9997},
        'used':{'source_eval':1,'smoke':3,'formal':42}})
    chain=tmp_path/'chain';chain.mkdir()
    write(chain/'manifest.json',{'attempt_id':'fixture','hapi_session':None})
    phases=[]
    def run_phase(spec_path,phase,output,handshake_fd=None):
        phases.append(phase);output.mkdir()
        write(output/'candidate_selection.json',{})
        if phase=='smoke':
            write(output/'progress.json',{'actual_updates':3,'actor_parameters_changed':True,
                'evaluations':[{'cases':[{'path':'evaluation_fixture.json'}]}]})
            write(output/'terminal_report.json',{'status':'COMPLETED','actual_updates':3})
            write(output/'manifest.json',{'source_sha256':config['source_sha256']})
            (output/'source_snapshot').mkdir()
            (output/'source_snapshot/spec.json').write_bytes(spec_path.read_bytes())
            import hashlib
            write(output/'manifest.json',{'source_sha256':config['source_sha256'],
                'spec_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest()})
            write(output/'evaluation_fixture.json',{'per_env':[{}]*8,'outcome_counts':{}})
            complete_smoke_fixture(output,spec_path,3)
        return {'phase':phase,'run':str(output),'exit_code':0,'status':'COMPLETED',
            'terminal':{'actual_updates':3 if phase=='smoke' else 42},
            'progress':{'actor_parameters_changed':True}}
    monkeypatch.setattr(stand_chain,'run_phase',run_phase)
    notified=[];monkeypatch.setattr(stand_chain,'notify',lambda p:notified.append(p))
    reader,writer=os.pipe()
    assert stand_chain.worker(SimpleNamespace(output_dir=chain,spec=spec,handshake_fd=writer))==0
    os.close(reader)
    assert phases==['source_eval','smoke','formal'] and notified==[chain]
    result=json.loads((chain/'chain_terminal_report.json').read_text())
    assert result['formal_updates']==42 and result['remaining_formal_updates']==9955
    assert result['durability']['status']=='NOT_RUN'


def test_incomplete_smoke_never_starts_formal(tmp_path,monkeypatch):
    config=json.loads(SPEC.read_text());spec=tmp_path/'spec.json';write(spec,config)
    write(tmp_path/'budget.json',{'limits':{'formal':9997},
        'used':{'source_eval':1,'smoke':1,'formal':0}})
    chain=tmp_path/'chain';chain.mkdir()
    write(chain/'manifest.json',{'attempt_id':'fixture','hapi_session':None})
    phases=[]
    def run_phase(spec_path,phase,output,handshake_fd=None):
        phases.append(phase);output.mkdir()
        write(output/'candidate_selection.json',{})
        return {'phase':phase,'run':str(output),'exit_code':0,'status':'COMPLETED',
            'terminal':{'actual_updates':1},'progress':{'actor_parameters_changed':True}}
    monkeypatch.setattr(stand_chain,'run_phase',run_phase)
    monkeypatch.setattr(stand_chain,'notify',lambda p:None)
    reader,writer=os.pipe()
    assert stand_chain.worker(SimpleNamespace(output_dir=chain,spec=spec,handshake_fd=writer))==1
    os.close(reader)
    assert phases==['source_eval','smoke']
    assert (chain/'report_ready.json').exists()
