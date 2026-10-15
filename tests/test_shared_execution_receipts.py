"""Portable CPU contracts for record-only execution and ledger-owned receipts."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from native_stand.command_v6.tools import submission_receipt as receipts
from native_stand.command_v6.tools import source_identity as sources
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.completion import finalize_report,notify,sha

@pytest.fixture
def declaration(tmp_path):
    cp=tmp_path/'source.pt';cp.write_bytes(b'CPU input fixture')
    spec={'experiment':'fixture','initialization':'random','source_checkpoint':str(cp),'source_sha256':sha(cp),
        'authorization':{'status':'AUTHORIZED','hapi_session':'owner'},'budget':{'evaluation_wall_s':20},
        'device':{'physical_index':0,'uuid':'GPU-fixture','logical':'cuda:0'},'resources':{'mode':'exclusive'},
        'artifacts':{},'evaluation':{}}
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    book={'authorization':'AUTHORIZED','limits':{'evaluate':2},'used':{'evaluate':0},'attempts':{}}
    path.with_name('budget.json').write_text(json.dumps(book))
    return path,spec,tmp_path/'run'


def approved(path,output):
    return receipts.approve({'status':'PASS','spec_sha256':sha(path),'effective_recipe':{'fixture':True}},path,output,'evaluate')


def test_receipt_lock_boundary_and_no_runtime_ancestor_audit(declaration,monkeypatch):
    path,spec,output=declaration
    from native_stand.command_v6.tools import storage_budget,execution_identity,preflight
    monkeypatch.setattr(storage_budget,'check',lambda *a:{'status':'PASS'})
    proof=approved(path,output)
    Ledger(path.with_name('budget.json')).reserve('exact','evaluate',output,approval=proof)
    book=json.loads(path.with_name('budget.json').read_text());row=book['attempts']['exact']
    assert row['submission_receipt']['record']['requested']==spec
    assert not output.exists() and row['updates']==0
    monkeypatch.setattr(execution_identity,'identity',lambda s:{'current_code':'changed'})
    monkeypatch.setattr(preflight,'_check',lambda *a:pytest.fail('Runtime must not repeat ancestor preflight'))
    result=preflight.check(path,output,'evaluate',attempt_id='exact')
    assert result['status']=='PASS' and result['receipt_prerequisites_reused'] and result['execution_identity']=={'current_code':'changed'}
    with pytest.raises(ValueError,match='duplicate'):Ledger(path.with_name('budget.json')).reserve('exact','evaluate',output)
    # Critical corruption still rejects before runtime.
    Path(spec['source_checkpoint']).write_bytes(b'corrupt')
    assert preflight.check(path,output,'evaluate',attempt_id='exact')['status']=='FAIL'


@pytest.mark.parametrize('kind',['spec','checkpoint','budget','plain_dict'])
def test_changed_critical_inputs_or_serialized_approval_rejected(declaration,monkeypatch,kind):
    path,spec,output=declaration
    from native_stand.command_v6.tools import storage_budget
    monkeypatch.setattr(storage_budget,'check',lambda *a:{'status':'PASS'})
    proof=approved(path,output)
    if kind=='spec':path.write_text(path.read_text()+' ')
    elif kind=='checkpoint':Path(spec['source_checkpoint']).write_bytes(b'changed')
    elif kind=='budget':
        book=json.loads(path.with_name('budget.json').read_text());book['limits']['evaluate']=3
        path.with_name('budget.json').write_text(json.dumps(book))
    else:proof=dict(proof)
    before=path.with_name('budget.json').read_bytes()
    with pytest.raises(ValueError):Ledger(path.with_name('budget.json')).reserve('exact','evaluate',output,approval=proof)
    assert path.with_name('budget.json').read_bytes()==before and not output.exists()


def test_identity_reuse_phase_diff_and_configuration_only(tmp_path,monkeypatch):
    source=tmp_path/'package';source.mkdir();module=source/'x.py';module.write_text('x=1')
    def implementation(spec):
        tree,relative=sources.tree_digest(source)
        return {'location_independent_modules_sha256':tree,'relative_modules_sha256':relative,'PPO_path':'fixture PPO','PPO_sha256':'p'}
    from native_stand.command_v6.tools import execution_identity
    monkeypatch.setattr(execution_identity,'identity',implementation)
    path=tmp_path/'spec.json';path.write_text(json.dumps({'experiment':'fixture'}))
    chain=tmp_path/'chain';sources.record_configuration(chain,path)
    phase=chain/'smoke';sources.record_configuration(phase,path)
    record=json.loads((phase/'identity.json').read_text())
    assert record['source_identity_reference'] and 'relative_modules_sha256' not in record
    assert sources.read_identity(phase)['relative_modules_sha256']=={'x.py':sha(module)}
    module.write_text('x=2')
    formal=chain/'formal';sources.record_configuration(formal,path)
    record=json.loads((formal/'identity.json').read_text())
    assert record['phase_source_changes'] and record['strict_same_code_comparison'] is False
    assert not list(chain.rglob('*.py'))
    assert json.loads((formal/'configuration.json').read_text())['source_code_copied_bytes']==0
    with pytest.raises(FileExistsError):sources.record_identity({},chain)


def ended_run(tmp_path):
    run=tmp_path/'ended';run.mkdir();(run/'source_snapshot').mkdir()
    spec={'experiment':'old','notifications':{'enabled':True},'authorization':{'hapi_session':'owner'},'evaluation':{}}
    (run/'source_snapshot/spec.json').write_text(json.dumps(spec))
    (run/'manifest.json').write_text(json.dumps({'attempt_id':'past','hapi_session':'owner','spec_sha256':sha(run/'source_snapshot/spec.json')}))
    (run/'terminal_report.json').write_text(json.dumps({'status':'STOPPED_BOUNDED','actual_updates':3,'samples':24576,'reason':'bounded'}))
    return run


def test_report_error_summary_and_at_most_once_notification(tmp_path,monkeypatch):
    from native_stand.command_v6 import completion
    run=ended_run(tmp_path)
    monkeypatch.setattr(completion,'evaluation_identity',lambda *a:(_ for _ in ()).throw(ValueError('current parser changed')))
    result=finalize_report(run)
    assert result['status']=='STOPPED_BOUNDED' and result['actual_updates']==3 and result['accepted'] is False
    assert result['report_status']=='MISSING_OR_INVALID_EVIDENCE'
    sends=[]
    def send(session,text):sends.append(text);return {'status':'sent'}
    notify(run,send);notify(run,send)
    assert len(sends)==1 and 'STOPPED_BOUNDED' in sends[0]


def test_historical_recorded_identity_survives_live_parser_change(tmp_path,monkeypatch):
    from native_stand.command_v6 import completion
    run=ended_run(tmp_path);manifest=json.loads((run/'manifest.json').read_text())
    manifest['evaluation_identity']={'spec_sha256':'old','evaluator_sha256':'recorded'}
    (run/'manifest.json').write_text(json.dumps(manifest));(run/'metrics.jsonl').write_text('')
    monkeypatch.setattr(completion,'evaluation_identity',lambda *a:pytest.fail('Recorded run must not resolve live protocol'))
    result=finalize_report(run)
    assert result['status']=='STOPPED_BOUNDED' and result.get('report_status') is None
    assert result['candidate_selection']['accepted_candidate'] is None


def test_validation_writes_no_source_or_test_copy(tmp_path,monkeypatch):
    from native_stand.command_v6.tools import validate_cpu as tool
    path=tmp_path/'spec.json';path.write_text('{}');path.with_name('budget.json').write_text('{}')
    calls=[]
    def cpu(command,**kw):
        calls.append(command)
        return SimpleNamespace(returncode=0,stdout='[]' if '-c' in command else json.dumps({'preflight':{'status':'READY_NEEDS_AUTH','cpu_valid':True}}),stderr='')
    monkeypatch.setattr(tool.subprocess,'run',cpu)
    monkeypatch.setattr(sources,'git_info',lambda:{'commit':'fixture','dirty':True})
    output=tmp_path/'validation'
    report=tool.validate(path,output,['tests/test_shared_execution_receipts.py'],write=True)
    assert report['passed'] and report['source_code_copied_bytes']==report['test_copied_bytes']==0
    assert not list(output.rglob('*.py')) and not (output/'source_snapshot').exists() and not (output/'tests').exists()
    assert (output/'identity.json').is_file() and (output/'validation_result.json').is_file()


def test_production_preflight_to_locked_reserve_contract(tmp_path,monkeypatch):
    # Genuine public CPU entry over fixture inputs; simulator never constructed.
    from native_stand.command_v6.tools import preflight,storage_budget,execution_identity
    source=tmp_path/'cp';source.write_text('fixed')
    path=tmp_path/'spec.json'
    spec={'initialization':'random','source_checkpoint':str(source),'source_sha256':sha(source),'budget':{},'evaluation':{}}
    path.write_text(json.dumps(spec));book={'authorization':'AUTHORIZED','limits':{'evaluate':1},'used':{'evaluate':0},'attempts':{}}
    path.with_name('budget.json').write_text(json.dumps(book));output=tmp_path/'run'
    monkeypatch.setattr(preflight,'_check',lambda *a,**kw:{'status':'PASS','spec_sha256':sha(path)})
    monkeypatch.setattr(storage_budget,'check',lambda *a:{'status':'PASS'})
    checked=preflight.check(path,output,'evaluate')
    assert isinstance(checked,receipts.Approval)
    Ledger(path.with_name('budget.json')).reserve('one','evaluate',output,approval=checked)
    monkeypatch.setattr(execution_identity,'identity',lambda s:{})
    assert preflight.check(path,output,'evaluate',attempt_id='one')['receipt_prerequisites_reused']


def test_snapshot_real_entry_writes_only_configuration(tmp_path,monkeypatch):
    from native_stand.command_v6.train import record_run_configuration
    from native_stand.command_v6.tools import execution_identity
    monkeypatch.setattr(execution_identity,'identity',lambda spec:{'location_independent_modules_sha256':'tree','relative_modules_sha256':{'x.py':'sha'},'PPO_path':'fixture','PPO_sha256':'p'})
    path=tmp_path/'spec.json';path.write_text('{}');output=tmp_path/'run';output.mkdir()
    record=record_run_configuration(output,path)
    assert record=={'spec.json':sha(path)}
    assert not list(output.rglob('*.py')) and (output/'source_snapshot/spec.json').is_file()


def test_report_invalid_config_never_certifies(tmp_path):
    run=ended_run(tmp_path)
    path=run/'source_snapshot/spec.json';path.write_text(path.read_text()+' ')
    result=finalize_report(run)
    assert not result['accepted'] and result['report_status']=='MISSING_OR_INVALID_EVIDENCE'
    assert result['status']=='STOPPED_BOUNDED'


def test_reserved_limits_cannot_be_increased(declaration,monkeypatch):
    path,spec,output=declaration
    from native_stand.command_v6.tools import storage_budget,preflight
    monkeypatch.setattr(storage_budget,'check',lambda *a:{'status':'PASS'})
    Ledger(path.with_name('budget.json')).reserve('bound','evaluate',output,approval=approved(path,output))
    book=json.loads(path.with_name('budget.json').read_text());book['limits']['evaluate']=3
    path.with_name('budget.json').write_text(json.dumps(book))
    assert preflight.check(path,output,'evaluate',attempt_id='bound')['status']=='FAIL'


def test_reserved_attempt_without_receipt_is_rejected(declaration):
    path,spec,output=declaration
    book=json.loads(path.with_name('budget.json').read_text())
    book['attempts']['old']={'phase':'evaluate','status':'RUNNING','output_dir':str(output.resolve())}
    path.with_name('budget.json').write_text(json.dumps(book))
    from native_stand.command_v6.tools import preflight
    result=preflight.check(path,output,'evaluate',attempt_id='old')
    assert result['status']=='FAIL' and 'receipt' in str(result['errors'])


def test_concurrent_reservation_uses_one_budget_owner(declaration,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from native_stand.command_v6.tools import storage_budget
    path,spec,output=declaration
    monkeypatch.setattr(storage_budget,'check',lambda *a:{'status':'PASS'})
    targets=[output.with_name('arm0'),output.with_name('arm1')]
    approvals=[approved(path,target) for target in targets]
    def reserve(i):
        try:
            Ledger(path.with_name('budget.json')).reserve('race'+str(i),'evaluate',targets[i],approval=approvals[i])
            return True
        except ValueError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,[0,1]))
    assert sum(results)==1
    book=json.loads(path.with_name('budget.json').read_text())
    assert len(book['attempts'])==1 and book['used']['evaluate']==0
    assert not any(target.exists() for target in targets)
