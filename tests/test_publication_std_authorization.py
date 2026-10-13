import json
from pathlib import Path
import pytest
import torch
from native_stand.command_v6.tools.experiment_preparation import publish,digest
from native_stand.command_v6.domain.action_std import readback
from native_stand.command_v6.tools import register_authorization as auth
from test_motion_preparer import inputs


def test_nested_publication_marker_and_failure_cleanup(tmp_path,monkeypatch):
    root=tmp_path/'ab';payload={'A/spec.json':{},'B/spec.json':{},'preparation_manifest.json':{}}
    publish(root,payload,{},completion_marker=True)
    marker=json.loads((root/'publication_complete.json').read_text())
    assert set(marker['files'])==set(payload)
    assert all(digest(root/p)==h for p,h in marker['files'].items())
    for name in ('../escape.json','/abs.json','A/B/spec.json'):
        with pytest.raises(ValueError):publish(tmp_path/'invalid',{name:{}},{})
    original=Path.open
    def fail(path,*args,**kwargs):
        if path.name=='publication_complete.json':raise OSError('disk full')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',fail)
    with pytest.raises(OSError):publish(tmp_path/'failed',payload,{},completion_marker=True)
    assert not (tmp_path/'failed').exists()


def test_std_scalar_log_factor_and_preclip_units():
    std=torch.tensor([.1,.2,.3,.4,.5,.6])
    args={'output_factor':[1,1,.06,1,1,.06],'leg_scale_rad':.5,'wheel_scale_rad_s':100}
    a=readback(std,parameterization='scalar',**args);b=readback(std.log(),parameterization='log',**args)
    assert a['physical_target_std']==pytest.approx(b['physical_target_std'])
    assert a['physical_target_std'][2]==pytest.approx(1.8)
    assert 'before clipping' in a['scope']
    with pytest.raises(ValueError):readback(-std,parameterization='scalar',**args)


def test_authorization_zero_write_budget_rejection_and_duplicate(tmp_path,monkeypatch):
    # Files use project-root shape; no real project declaration is edited.
    module_root=tmp_path/'src/native_stand/command_v6/tools/register_authorization.py'
    module_root.parent.mkdir(parents=True);module_root.write_text('fixture')
    monkeypatch.setattr(auth,'__file__',str(module_root));monkeypatch.setattr(auth,'validate',lambda s:[])
    arm=tmp_path/'configs/experiments/fresh/A';arm.mkdir(parents=True)
    spec=arm/'spec.json';book=arm/'budget.json'
    spec.write_text(json.dumps({'budget':{'smoke_updates':1,'formal_updates':9,'smoke_wall_s':300,'formal_wall_s':600}}))
    book.write_text(json.dumps({'authorization':'UNAUTHORIZED','attempts':{},'used':{'smoke':0,'formal':0},'limits':{'smoke':1,'formal':9}}))
    request={'approval_id':'approval','user_scope':'explicit test approval','session':'current','physical_gpu':1,
        'gpu_uuid':'GPU-test','max_online_updates':10,'max_phase_wall_s':900,'arms':[{'spec':str(spec),'spec_sha256':digest(spec),'budget_sha256':digest(book)}]}
    before=(spec.read_bytes(),book.read_bytes())
    assert auth.register(request,current_session='current')['files_written']==0
    assert (spec.read_bytes(),book.read_bytes())==before
    with pytest.raises(ValueError):auth.register({**request,'max_online_updates':9},current_session='current')
    with pytest.raises(ValueError):auth.register(request,current_session='other')
    assert auth.register(request,current_session='current',write=True)['files_written']==3
    assert json.loads(book.read_text())['authorization']=='AUTHORIZED'
    with pytest.raises(ValueError):auth.register(request,current_session='current',write=True)


def test_authorization_publication_error_rolls_back_spec_and_book(tmp_path,monkeypatch):
    module_root=tmp_path/'src/native_stand/command_v6/tools/register_authorization.py'
    module_root.parent.mkdir(parents=True);module_root.write_text('fixture')
    monkeypatch.setattr(auth,'__file__',str(module_root));monkeypatch.setattr(auth,'validate',lambda s:[])
    arm=tmp_path/'configs/experiments/fresh';arm.mkdir(parents=True)
    spec=arm/'spec.json';ledger=arm/'budget.json'
    spec.write_text(json.dumps({'budget':{'smoke_updates':1,'formal_updates':1,'smoke_wall_s':300,'formal_wall_s':600}}))
    ledger.write_text(json.dumps({'authorization':'UNAUTHORIZED','used':{'smoke':0,'formal':0},'limits':{'smoke':1,'formal':1},'attempts':{}}))
    request={'approval_id':'fixture','user_scope':'fixture only','session':'now','physical_gpu':1,'gpu_uuid':'GPU-fixture',
        'max_online_updates':2,'max_phase_wall_s':900,'arms':[{'spec':str(spec),'spec_sha256':digest(spec),'budget_sha256':digest(ledger)}]}
    before=(spec.read_bytes(),ledger.read_bytes());original=Path.open
    def failure(path,*args,**kwargs):
        if path.name=='authorization_receipt.json':raise OSError('fixture publication failure')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',failure)
    with pytest.raises(OSError):auth.register(request,current_session='now',write=True)
    assert (spec.read_bytes(),ledger.read_bytes())==before
    assert not (arm/'authorization_receipt.json').exists()


def test_cpu_initialization_strict_and_adam_unchanged(inputs):
    from native_stand.command_v6.tools.checkpoint_initialization import audit
    parent,checkpoint,request,out=inputs
    spec=json.loads(parent.read_text());saved=torch.load(checkpoint,weights_only=False)
    state=torch.get_rng_state().clone();result=audit(spec,saved)
    assert result['Adam_preserved'] and result['optimizer_steps_executed']==0
    assert all(r['max_abs_difference']==0 for r in result['parameter_differences'])
    assert torch.equal(state,torch.get_rng_state())


def test_finished_comparison_common_source_and_distinct_learned_std(tmp_path):
    from native_stand.command_v6.tools.compare_arms import compare
    source=tmp_path/'source.pt';torch.save({'actor':{'distribution.std_param':torch.ones(6)*.1}},source)
    runs=[]
    for arm,factor in [('A',1.),('B',.5)]:
        run=tmp_path/arm;(run/'source_snapshot').mkdir(parents=True);runs.append(run)
        spec={'source_checkpoint':str(source),'source_sha256':digest(source),'evaluation':{'seed':104},
            'action':{'leg_scale_rad':.5,'wheel_scale_rad_s':100.},'recovery':{'exploration_initialization':{'wheel_std_multiplier':factor}}}
        (run/'source_snapshot/spec.json').write_text(json.dumps(spec));(run/'manifest.json').write_text('{}')
        (run/'terminal_report.json').write_text('{"status":"COMPLETED","actual_updates":100}')
        model=run/'model.pt';torch.save({'actor':{'distribution.std_param':torch.ones(6)*.08}},model)
        (run/'candidate_selection.json').write_text(json.dumps({'candidates':[{'checkpoint':str(model),'checkpoint_sha256':digest(model),'accepted':False}]}))
    result=compare(runs)
    assert result['arms'][1]['declared_initialization']['wheel_std_multiplier']==.5
    assert result['arms'][1]['candidates'][0]['checkpoint_std']['physical_target_std'][2]==pytest.approx(8.)
    assert result['arms'][1]['initialization_readback'] is None
    (runs[1]/'terminal_report.json').write_text('{"status":"RUNNING"}')
    with pytest.raises(ValueError,match='finished'):compare(runs)
