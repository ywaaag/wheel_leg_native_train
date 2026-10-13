import ast
import json
from pathlib import Path

import pytest
import torch

from native_stand.command_v6.completion import notify,write,sha
from native_stand.command_v6.domain.evaluation_config import scoring,split
from native_stand.recovery.min_height import RiseHold,PhaseCoverage,protocol,score,ProgressGuard


def test_notification_conflicting_frozen_owner_never_sends(tmp_path):
    (tmp_path/'source_snapshot').mkdir()
    write(tmp_path/'manifest.json',{'hapi_session':'wrong'})
    write(tmp_path/'source_snapshot/spec.json',{'authorization':{'hapi_session':'owner'}})
    (tmp_path/'completion_report.md').write_text('ready')
    write(tmp_path/'report_ready.json',{'event_id':'event','report_sha256':sha(tmp_path/'completion_report.md')})
    result=notify(tmp_path,lambda *_:pytest.fail('routing conflict sent'))
    assert result['status']=='notification_route_conflict'
    assert notify(tmp_path,lambda *_:pytest.fail('duplicate send'))==result


def test_complete_failed_hold_is_not_incomplete():
    s=torch.zeros(1220,39,dtype=torch.float64);a=torch.zeros(1220,10)
    s[:,0]=torch.arange(1,1221)*.01;s[:,6]=.168;s[200:,6]=.42
    s[:,10:12]=3;s[:,13]=.01;s[:,29]=1
    s[500,10]=0
    result=score(s,a,dt=.01,p=protocol(),initial_valid=True,terminated=True,terminal_success=False)
    assert not result['accepted'] and result['post_rise_evidence_status']=='COMPLETE'
    assert result['checks']['continuous'] and 'continuous' not in result['failed_checks']
    assert 'continuous_contact' in result['failed_checks']


def test_persistent_inference_allocation_reset_second_rollout_training():
    with torch.inference_mode():
        f=RiseHold(1,'cpu',dt=.01,p=protocol());coverage=PhaseCoverage(1,'cpu')
        for _ in range(30):
            f.observe(torch.tensor([.42]),torch.zeros(1,2),torch.zeros(1),torch.full((1,2),3.),
                torch.full((1,),.01),torch.zeros(1),torch.zeros(1),active=torch.ones(1,dtype=torch.bool),
                valid=torch.ones(1,dtype=torch.bool),safety_failed=torch.zeros(1,dtype=torch.bool),fault=torch.zeros(1,dtype=torch.bool))
        coverage.observe(torch.tensor([0]),torch.tensor([0]),torch.ones(1,dtype=torch.bool),
            {'r':torch.ones(1)},{'r':torch.ones(1)},torch.zeros(1,6))
    f.reset(torch.tensor([0]));coverage.reset()
    with torch.inference_mode():coverage.observe(torch.tensor([0]),torch.tensor([0]),torch.ones(1,dtype=torch.bool),{'r':torch.ones(1)},{'r':torch.ones(1)},torch.zeros(1,6))
    coverage.reset();f.reset(torch.tensor([0]))
    parameter=torch.tensor(1.,requires_grad=True);parameter.square().backward();assert parameter.grad==2


def test_actual_train_call_sites_split_source_milestone_and_final_protocol():
    path=Path(__file__).resolve().parents[1]/'src/native_stand/command_v6/train.py'
    tree=ast.parse(path.read_text());found=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call):continue
        for field in node.keywords:
            if field.arg=='standing_protocol':
                if not isinstance(node.func,ast.Name) or node.func.id!='evaluate_actor':continue
                expression=field.value.body if isinstance(field.value,ast.IfExp) else field.value
                assert isinstance(expression,ast.Call) and expression.func.id=='scoring_configuration'
                found.append(field)
    assert len(found)>=4
    cfg={'seconds':30,'full_trace_updates':[25],'full_every_updates':25,'diagnostic_profile':'summary'}
    assert scoring(cfg)=={'seconds':30}
    assert split(cfg)['storage']['full_trace_updates']==[25]
    with pytest.raises(ValueError):scoring({**cfg,'unknown_threshold':7})


def test_raw_source_save_registry_compression_guard_init(tmp_path):
    from native_stand.command_v6.tools.recovery_progress_baseline import load
    rows=[{'entry_confirmation_index':19,'recovery_s':.2,'control_diagnostics_100hz':torch.zeros(300,54).tolist()}]
    raw={'spec_sha256':'spec','checkpoint_sha256':'model','per_env':rows}
    write(tmp_path/'evaluation_source.json',raw)
    write(tmp_path/'manifest.json',{'spec_sha256':'spec','source_sha256':'model','asset_sha256':'asset'})
    entry={'role':'source','evaluation':'evaluation_source.json','checkpoint_sha256':'model',
        'result':{'per_env':[{'entry_confirmation_index':19,'recovery_s':.2}]}}
    loaded,evidence=load(tmp_path,entry,spec_sha256='spec',source_sha256='model',asset_sha256='asset')
    guard=ProgressGuard(loaded,{'delta_min_rad_s':1,'alternation_fraction_min':.8,'limit_fraction_min':.8,'entry_count_drop':1,'confirmations':2})
    assert guard.source_entries==1 and evidence['sha256']==sha(tmp_path/'evaluation_source.json')
    entry['evaluation']='../escape.json'
    with pytest.raises(ValueError):load(tmp_path,entry,spec_sha256='spec',source_sha256='model',asset_sha256='asset')


def test_recovery_retry_default_zero_write_and_no_quota_transfer(tmp_path):
    from native_stand.command_v6.tools.prepare_recovery_retry import prepare
    root=Path(__file__).resolve().parents[1]
    spec=json.loads((root/'configs/experiments/2026_10_7-23_29__recovery_min_height_p1_guardfix_from_s50/spec.json').read_text())
    run=tmp_path/'failed';(run/'source_snapshot').mkdir(parents=True)
    write(run/'source_snapshot/spec.json',spec)
    write(run/'manifest.json',{'attempt_id':'exact','spec_sha256':sha(run/'source_snapshot/spec.json')})
    write(run/'terminal_report.json',{'status':'FAILED','actual_updates':9,'reason':'fixture reader error'})
    ledger=tmp_path/'budget.json';book={'limits':{'smoke':20,'formal':100},'attempts':{'exact':{'status':'FAILED','updates':9,'wall_s':30.,'output_dir':str(run)}}}
    write(ledger,book);before=ledger.read_bytes();out=tmp_path/'2026_10_8-00_00__retry_fixture'
    result=prepare(run,ledger,out,session='current')
    assert not out.exists() and result['budget']['authorization']=='UNAUTHORIZED'
    assert result['budget']['historical_actual_updates']==9
    assert all(v==0 for v in result['budget']['limits'].values())
    prepare(run,ledger,out,session='current',write=True)
    assert ledger.read_bytes()==before
    with pytest.raises(FileExistsError):prepare(run,ledger,out,session='current')
    book['attempts']['exact']['updates']=10;write(ledger,book)
    with pytest.raises(ValueError,match='accounting'):prepare(run,ledger,tmp_path/'2026_10_8-00_01__retry_bad',session='current')
