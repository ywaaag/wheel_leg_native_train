import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from native_stand.command_v6.domain.submission_contract import authorization, metadata
from native_stand.command_v6 import supervisor


@pytest.mark.parametrize('value', ['AUTHORIZED', 'UNAUTHORIZED', {'status':'AUTHORIZED'},
                                  {'hapi_session':'current'}, None])
def test_legacy_authorization_is_normalized_without_rewriting(value):
    spec={'authorization':value}
    original=deepcopy(spec)
    effective=authorization(spec)
    assert isinstance(effective,dict)
    assert effective['status'] in ('AUTHORIZED','UNAUTHORIZED','UNKNOWN')
    assert spec==original


@pytest.mark.parametrize('value', [True, [], 1, 'YES', {'status':False},
                                  {'hapi_session':''}, {'hapi_session':7}])
def test_invalid_authorization_rejected(value):
    with pytest.raises(ValueError):authorization({'authorization':value})


def args_for(tmp_path):
    return SimpleNamespace(spec=tmp_path/'spec.json',output_dir=tmp_path/'new',
        formal_only=False,evaluation_only=False,hapi_session='current',physical_gpu=1,
        resource_policy={'mode':'exclusive'})


def health():
    return {'findings':[],'gpu':{'status':'OK','devices':[{'index':1,'uuid':'gpu1'}],
                               'compute_processes':[]}}


def test_readiness_needs_resource_evidence_and_preflight(tmp_path,monkeypatch):
    monkeypatch.setenv('HAPI_SESSION_ID','current')
    args=args_for(tmp_path)
    spec={'authorization':'AUTHORIZED','device':{'physical_index':1,'uuid':'gpu1'}}
    result=supervisor.submission_readiness(args,spec,{'status':'PASS'})
    assert result['status']=='READY_METADATA' and not result['submit_ready']
    assert supervisor.submission_readiness(args,spec,{'status':'PASS'},health())['submit_ready']
    rejected=supervisor.submission_readiness(args,spec,{'status':'READY_NEEDS_AUTH',
        'reason_code':'BUDGET_EXHAUSTED'},health())
    assert not rejected['submit_ready'] and rejected['reason_code']=='BUDGET_EXHAUSTED'
    spec['device']['uuid']='wrong'
    assert not supervisor.submission_readiness(args,spec,{'status':'PASS'},health())['submit_ready']
    assert not args.output_dir.exists()


@pytest.mark.parametrize('changes', [dict(target_session=None),dict(current_session=None),
    dict(target_session='historical'),dict(physical_gpu=None),dict(physical_gpu=0),
    dict(output_available=False),dict(duplicate_submission=True)])
def test_submission_metadata_blocks_incomplete_command(changes):
    kwargs=dict(target_session='current',current_session='current',physical_gpu=1)
    kwargs.update(changes)
    result=metadata({'authorization':{'status':'AUTHORIZED','hapi_session':'current'},
                     'device':{'physical_index':1}},**kwargs)
    assert result['status']=='NOT_READY'


def test_unauthorized_declaration_cannot_be_promoted_by_session():
    assert metadata({'authorization':'UNAUTHORIZED'},target_session='current',
        current_session='current',physical_gpu=1)['status']=='NOT_READY'


def test_cli_submission_check_is_zero_write_and_nonzero_when_incomplete(tmp_path,monkeypatch,capsys):
    path=tmp_path/'spec.json';path.write_text(json.dumps({'authorization':'AUTHORIZED'}))
    before=path.read_bytes()
    monkeypatch.setenv('HAPI_SESSION_ID','current')
    monkeypatch.setattr(supervisor,'check',lambda *a:{'status':'PASS'})
    monkeypatch.setattr(supervisor,'inspect_project',lambda *a,**k:health())
    monkeypatch.setattr('sys.argv',['supervisor','--spec',str(path),'--output-dir',str(tmp_path/'new'),
                                  '--check-submission'])
    assert supervisor.main()==2
    report=json.loads(capsys.readouterr().out)
    assert report['preflight']['status']=='PASS'
    assert report['submission_contract']['status']=='NOT_READY'
    assert report['files_written']==0 and path.read_bytes()==before
    assert list(tmp_path.iterdir())==[path]


def test_cli_resource_check_reports_ready_without_launch(tmp_path,monkeypatch,capsys):
    path=tmp_path/'spec.json';path.write_text(json.dumps({'authorization':'AUTHORIZED'}))
    monkeypatch.setenv('HAPI_SESSION_ID','current')
    monkeypatch.setattr(supervisor,'check',lambda *a:{'status':'PASS'})
    monkeypatch.setattr(supervisor,'inspect_project',lambda *a,**k:health())
    monkeypatch.setattr('sys.argv',['supervisor','--spec',str(path),'--output-dir',str(tmp_path/'new'),
        '--check-submission','--physical-gpu','1','--hapi-session','current'])
    assert supervisor.main()==0
    assert json.loads(capsys.readouterr().out)['submission_contract']['submit_ready']
    assert list(tmp_path.iterdir())==[path]


def test_readonly_submission_check_rejects_launch_flag(tmp_path,monkeypatch):
    monkeypatch.setattr('sys.argv',['supervisor','--spec',str(tmp_path/'absent'),
        '--output-dir',str(tmp_path/'new'),'--check-submission','--launch'])
    with pytest.raises(SystemExit) as failure:supervisor.main()
    assert failure.value.code==2 and not list(tmp_path.iterdir())


def test_evaluation_plan_also_checks_session_without_reserving(tmp_path,monkeypatch,capsys):
    from native_stand.command_v6.tools import evaluate_checkpoint
    path=tmp_path/'spec.json';path.write_text(json.dumps({'authorization':'AUTHORIZED'}))
    monkeypatch.setattr(evaluate_checkpoint,'batch_plan',lambda *a:{'preflight':{'status':'PASS'}})
    monkeypatch.setattr(supervisor,'inspect_project',lambda *a,**k:health())
    monkeypatch.setenv('HAPI_SESSION_ID','current')
    monkeypatch.setattr('sys.argv',['supervisor','--spec',str(path),'--output-dir',str(tmp_path/'new'),
        '--evaluation-only','--check-submission','--physical-gpu','1'])
    assert supervisor.main()==2
    assert not json.loads(capsys.readouterr().out)['submission_contract']['submit_ready']
    assert list(tmp_path.iterdir())==[path]
