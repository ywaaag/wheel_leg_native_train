import json
import os
from pathlib import Path
from types import SimpleNamespace

from native_stand.command_v6 import stand_chain
from native_stand.command_v6.completion import write


def test_ordinary_baseline_failure_does_not_block_training(tmp_path,monkeypatch):
    spec=tmp_path/'spec.json'
    write(spec,{'experiment':'fixture','budget':{'smoke_updates':3}})
    write(tmp_path/'budget.json',{'limits':{'formal':3000},'used':{'source_eval':1,'smoke':3,'formal':2}})
    chain=tmp_path/'chain'
    chain.mkdir()
    write(chain/'manifest.json',{'attempt_id':'fixture','hapi_session':None})
    phases=[]
    def run_phase(spec_path,phase,output,handshake_fd=None):
        phases.append(phase)
        output.mkdir()
        write(output/'candidate_selection.json',{})
        if phase=='smoke':
            write(output/'progress.json',{'actual_updates':3,'actor_parameters_changed':True,
                'evaluations':[{'cases':[{'path':'evaluation_fixture.json'}]}]})
            write(output/'terminal_report.json',{'status':'COMPLETED','actual_updates':3})
            write(output/'manifest.json',{'source_sha256':None})
            (output/'source_snapshot').mkdir()
            (output/'source_snapshot/spec.json').write_bytes(spec_path.read_bytes())
            import hashlib
            write(output/'manifest.json',{'source_sha256':None,'spec_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest()})
            write(output/'evaluation_fixture.json',{'per_env':[{}],'outcome_counts':{}})
        return {'phase':phase,'run':str(output),'exit_code':0,'status':'COMPLETED',
            'terminal':{'actual_updates':3,'source_pass':False},
            'progress':{'actor_parameters_changed':True},'analysis':'fixture'}
    monkeypatch.setattr(stand_chain,'run_phase',run_phase)
    notified=[]
    monkeypatch.setattr(stand_chain,'notify',lambda path:notified.append(path))
    reader,writer=os.pipe()
    assert stand_chain.worker(SimpleNamespace(output_dir=chain,spec=spec,handshake_fd=writer))==0
    os.close(reader)
    assert phases==['source_eval','smoke','formal']
    assert notified==[chain]
    assert json.loads((chain/'chain_terminal_report.json').read_text())['durability']['status']=='NOT_RUN'


def test_runtime_fault_stops_following_phases_and_reports(tmp_path,monkeypatch):
    spec=tmp_path/'spec.json'
    write(spec,{})
    write(tmp_path/'budget.json',{'limits':{'formal':3000},'used':{'source_eval':1,'smoke':0,'formal':0}})
    chain=tmp_path/'chain'
    chain.mkdir()
    write(chain/'manifest.json',{'attempt_id':'fixture','hapi_session':None})
    phases=[]
    def run_phase(spec_path,phase,output,handshake_fd=None):
        phases.append(phase)
        output.mkdir()
        return {'phase':phase,'run':str(output),'exit_code':1,'status':'FAILED',
            'terminal':{'failure':'closure'},'progress':{}}
    monkeypatch.setattr(stand_chain,'run_phase',run_phase)
    monkeypatch.setattr(stand_chain,'notify',lambda path:None)
    reader,writer=os.pipe()
    assert stand_chain.worker(SimpleNamespace(output_dir=chain,spec=spec,handshake_fd=writer))==1
    os.close(reader)
    assert phases==['source_eval']
    assert (chain/'report_ready.json').exists()
