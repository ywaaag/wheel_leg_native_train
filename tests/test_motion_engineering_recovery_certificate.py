"""CPU regression for real failed Motion + PPO0 evidence and public consumers.

Historical files are strictly read-only. Test reviews are temporary fixture
reviews, never publication authority. The actual signed review is a separate artifact.
"""
FROZEN_TEST_SCOPE='PROJECT_DATA'
import copy
import json
from pathlib import Path
import pytest
from native_stand.command_v6.tools import motion_recovery_certificate as cert
from native_stand.command_v6.tools import prepare_engineering_recovery as prepare
from native_stand.command_v6.tools.experiment_preparation import differences,digest
from native_stand.command_v6.tools.execution_identity import execution_dependencies

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'runs/2026_10_8-22_51__motion_b250_posture_storage_retry'
SUP=ROOT/'runs/2026_10_9-09_11__motion_posture_smoke_light_ppo0'
PARENT=ROOT/'configs/experiments'/OLD.name/'spec.json'

@pytest.fixture(scope='module')
def real_contract(tmp_path_factory):
    tmp=tmp_path_factory.mktemp('motion-recovery-contract')
    spec=json.loads(PARENT.read_text())
    req=prepare.request(OLD/'smoke',SUP,PARENT.with_name('budget.json'),tmp/'review.json')
    original=json.loads((OLD/'smoke/manifest.json').read_text())['execution_identity']
    supplemental=json.loads((SUP/'manifest.json').read_text())['execution_identity']
    target=cert.code_contract(spec)
    a=cert.changes(original,target)
    b=differences(execution_dependencies(original['relative_modules_sha256'],'motion')['modules_sha256'],
                  execution_dependencies(supplemental['relative_modules_sha256'],'motion')['modules_sha256'])
    review={'version':1,'status':'REVIEWED','reviewer':'CPU test fixture only','reason':'Exercise identity-bound rejection contracts',
        'target_changes':a,'supplement_changes':b,'decisions':[{'module':x,'disposition':'engineering_only',
        'reason':'Temporary CPU fixture, not authority to publish real evidence'} for x in sorted({r['field'] for r in a+b})]}
    Path(req['change_review']).write_text(json.dumps(review))
    result=cert.audit(req,spec)
    assert result['status']=='READY',result['missing']
    return req,spec,result


def test_real_failure_light_repair_and_budget_are_distinct(real_contract):
    req,spec,result=real_contract
    assert result['facts']['optimizer_wiring']['actual_updates']==1
    assert result['facts']['optimizer_wiring']['update_proof']['actor_parameters_changed']
    assert result['facts']['fault_path_repair']['status']=='PROVEN_ENGINEERING_ONLY'
    assert not result['new_candidate_capability_certified']
    assert all(not c['capability_accepted'] and c['valid_samples_per_env']==151 for c in result['facts']['fault_path_repair']['cases'])
    assert len(result['facts']['source_capability']['evaluations'])==9
    b=result['facts']['accounting']
    assert b['consumed_wall_s']==pytest.approx(5834.829444408417)
    assert b['remaining_wall_s']==pytest.approx(4965.170555591583)
    assert b['new_smoke_updates']==0 and b['consumed_smoke_updates']==1 and b['new_formal_limit']==50


@pytest.mark.parametrize('kind', ['checkpoint','env_missing','short','runtime_fault','window','capability','unfixed'])
def test_incompatible_light_evidence_rejected_without_losing_other_facts(real_contract,monkeypatch,kind):
    req,spec,result=real_contract
    path=SUP/'evaluation_01.json';text=Path.read_text
    data=json.loads(text(path))
    if kind=='checkpoint':data['checkpoint_sha256']='f'*64
    elif kind=='env_missing':data['per_env'].pop()
    elif kind=='short':data['per_env'][0]['continuous_s']=3.
    elif kind=='runtime_fault':data['per_env'][0]['outcome']='runtime_fault'
    elif kind=='window':data['per_env'][0]['posture_geometry']['complete_window']=False
    elif kind=='capability':data['capability_gate'].update(status='PASSED',accepted=True)
    elif kind=='unfixed':data['effective_protocol']['steady_window_s']=[10.,18.]
    replacement=json.dumps(data)
    monkeypatch.setattr(Path,'read_text',lambda self,*a,**kw:replacement if self.resolve()==path.resolve() else text(self,*a,**kw))
    checked=cert.audit(req,spec)
    assert checked['status']!='READY'
    assert any('fault_path_repair:' in e for e in checked['missing'])
    assert checked['facts']['accounting']==result['facts']['accounting']
    assert checked['facts']['optimizer_wiring']['status']=='PROVEN'
    assert checked['facts']['source_capability']['status']=='PROVEN_ORIGINAL_SOURCE'


@pytest.mark.parametrize('kind',['unreviewed','stale','behavior_disposition'])
def test_per_file_review_required(real_contract,tmp_path,kind):
    req,spec,result=real_contract;req=copy.deepcopy(req)
    review=json.loads(Path(req['change_review']).read_text())
    if kind=='unreviewed':review['status']='NOT_APPROVED'
    elif kind=='stale':review['target_changes'][0]['after']='f'*64
    else:review['decisions'][0]['disposition']='behavior_changed'
    path=tmp_path/'review.json';path.write_text(json.dumps(review));req['change_review']=str(path)
    checked=cert.audit(req,spec)
    assert checked['status']=='MISSING' and any('code_migration:' in e for e in checked['missing'])
    assert checked['facts']['accounting']['remaining_wall_s']>0


@pytest.mark.parametrize('field',['reward','control','ppo','seed','restore_source_rng','rollout_probe'])
def test_unreviewed_recipe_changes_rejected(real_contract,field):
    req,spec,result=real_contract;spec=copy.deepcopy(spec)
    if isinstance(spec.get(field),dict):spec[field]['unexpected']=42
    else:spec[field]='changed'
    checked=cert.audit(req,spec)
    assert checked['status']=='CONFLICTING' and checked['conflicts']


def test_plan_zero_writes(real_contract,tmp_path):
    req,spec,result=real_contract
    output=ROOT/'configs/experiments/2026_10_9-22_00__motion_recovery_cpu_fixture'
    assert not output.exists()
    before={p:digest(p) for p in result['inputs_sha256']}
    planned=prepare.prepare(OLD/'smoke',SUP,PARENT,PARENT.with_name('budget.json'),req['change_review'],output)
    assert planned['status']=='READY' and planned['files_written']==0 and not output.exists()
    assert planned['budget']['attempts']=={} and all(v==0 for v in planned['budget']['used'].values())
    assert planned['spec']['source_checkpoint']==spec['source_checkpoint']
    assert planned['budget']['authorization']=='UNAUTHORIZED'
    assert all(digest(p)==sha for p,sha in before.items())


def test_single_publication_and_recovery_reservation(real_contract,tmp_path,monkeypatch):
    req,spec,result=real_contract
    # Keep all publication/submission claims inside a disposable project fixture.
    project=tmp_path/'project';folder=project/'configs/experiments';folder.mkdir(parents=True)
    supplement_config=folder/SUP.name;supplement_config.mkdir()
    (supplement_config/'budget.json').symlink_to(ROOT/'configs/experiments'/SUP.name/'budget.json')
    monkeypatch.setattr(prepare,'__file__',str(project/'src/native_stand/command_v6/tools/prepare_engineering_recovery.py'))
    from native_stand.command_v6 import ledger as ledger_module
    monkeypatch.setattr(ledger_module,'__file__',str(project/'src/native_stand/command_v6/ledger.py'))
    from native_stand.command_v6.tools import storage_budget
    monkeypatch.setattr(storage_budget,'check',lambda *a,**kw:{'status':'PASS'})
    # Actual loading remains this project; publication relocation is metadata only.
    prepared=prepare.prepare(OLD/'smoke',SUP,PARENT,PARENT.with_name('budget.json'),req['change_review'],
        folder/'2026_10_9-22_01__motion_recovery_cpu_fixture',write=True)
    output=Path(prepared['output']);new_spec=prepared['spec'];new_spec['execution_source_root']=str(ROOT/'src')
    (output/'spec.json').write_text(json.dumps(new_spec))
    marker=output/'publication_complete.json';publication=json.loads(marker.read_text())
    publication['files']['spec.json']=digest(output/'spec.json');marker.write_text(json.dumps(publication))
    from native_stand.command_v6.tools import register_authorization as authorization
    monkeypatch.setattr(authorization,'__file__',str(project/'src/native_stand/command_v6/tools/register_authorization.py'))
    auth_request={'approval_id':'CPU-fixture-only','user_scope':'Temporary fixture only','session':'fixture-session',
        'physical_gpu':new_spec['device']['physical_index'],'gpu_uuid':new_spec['device']['uuid'],
        'max_online_updates':50,'max_phase_wall_s':new_spec['budget']['formal_wall_s'],
        'arms':[{'spec':str(output/'spec.json'),'spec_sha256':digest(output/'spec.json'),'budget_sha256':digest(output/'budget.json')}]}
    authorization.register(auth_request,current_session='fixture-session',write=True)
    new_spec=json.loads((output/'spec.json').read_text());book=json.loads((output/'budget.json').read_text())
    assert cert.validate(new_spec,book)['status']=='READY'
    from native_stand.command_v6.wiring import completed_smoke
    assert completed_smoke(book,new_spec)
    from native_stand.command_v6.tools import preflight
    monkeypatch.setattr(preflight,'__file__',str(project/'src/native_stand/command_v6/tools/preflight.py'))
    assert preflight.check(output/'spec.json',tmp_path/'new-run/formal','formal')['status']=='PASS'
    from native_stand.command_v6 import supervisor
    monkeypatch.setattr('sys.argv',['supervisor','--spec',str(output/'spec.json'),'--output-dir',str(tmp_path/'planned-run')])
    supervisor.main() # actual zero-write dispatcher selects formal-only automatically
    assert not (tmp_path/'planned-run').exists()
    ledger_module.Ledger(output/'budget.json').reserve('fixture-exact','formal',tmp_path/'new-run/formal')
    assert preflight.check(output/'spec.json',tmp_path/'new-run/formal','formal',attempt_id='fixture-exact')['status']=='PASS'
    assert preflight.check(output/'spec.json',tmp_path/'duplicate-run/formal','formal')['status']=='FAIL'
    settled=json.loads((output/'budget.json').read_text())
    assert list(settled['attempts'])==['fixture-exact'] and settled['used']['smoke']==0
    with pytest.raises(ValueError,match='already reserved'):
        ledger_module.Ledger(output/'budget.json').reserve('duplicate','formal',tmp_path/'another-run/formal')
    with pytest.raises(ValueError,match='already published'):
        prepare.prepare(OLD/'smoke',SUP,PARENT,PARENT.with_name('budget.json'),req['change_review'],
            folder/'2026_10_9-22_02__motion_recovery_cpu_fixture',write=True)


def test_certificate_revalidation_and_budget_not_reset(real_contract,tmp_path):
    req,spec,record=real_contract;path=tmp_path/'certificate.json';path.write_text(json.dumps(record))
    spec=copy.deepcopy(spec);b=record['facts']['accounting']
    spec['budget'].update(smoke_updates=0,formal_updates=50)
    spec['engineering_recovery']={'version':cert.VERSION,'certificate':str(path),'sha256':digest(path),
        'single_use_id':cert.stable_hash({'failed_attempt':record['facts']['optimizer_wiring']['attempt_id'],
            'terminal_sha256':record['facts']['optimizer_wiring']['terminal_sha256']})}
    book={'limits':{'source_eval':0,'smoke':0,'formal':50},'used':{'smoke':0,'formal':0},'attempts':{},'historical_usage':b}
    assert cert.validate(spec,book)['status']=='READY'
    book['limits']['smoke']=1
    with pytest.raises(ValueError,match='zero new smoke'):cert.validate(spec,book)
    path.write_text(path.read_text()+' ')
    with pytest.raises(ValueError,match='input SHA differs'):cert.validate(spec)


def test_frozen_location_and_unrelated_snapshot_do_not_change_reviewed_contract(real_contract,monkeypatch):
    req,spec,record=real_contract
    actual_identity=cert.identity
    def relocated(value):
        data=actual_identity(value)
        data['declared_source_root']=str(ROOT/'src')
        data['source_root']='/fixture/run/source_snapshot'
        data['location_independent_modules_sha256']='unrelated-recovery-snapshot-change'
        data['execution_dependencies']['excluded_modules']['recovery/new.py']={'sha256':'fixture','reason':'Recovery only'}
        return data
    monkeypatch.setattr(cert,'identity',relocated)
    audited=cert.audit(req,spec)
    assert audited['status']=='READY'
    assert audited['inputs_sha256']==record['inputs_sha256']
    assert audited['facts']['code_migration']['target_changes']==record['facts']['code_migration']['target_changes']


def test_runtime_exception_does_not_erase_accounting_or_repair(real_contract,monkeypatch):
    req,spec,record=real_contract
    def broken(*a,**kw):raise RuntimeError('fixture checkpoint readback error')
    monkeypatch.setattr(cert,'actor_proof',broken)
    audited=cert.audit(req,spec)
    assert audited['status']=='MISSING'
    assert audited['facts']['accounting']==record['facts']['accounting']
    assert audited['facts']['source_capability']['status']=='PROVEN_ORIGINAL_SOURCE'
    assert any('fixture checkpoint readback error' in e for e in audited['missing'])


def test_historical_report_uses_recorded_execution_not_new_permission():
    from native_stand.command_v6.tools.motion_recovery_certificate import historical_report_certificate
    import json,copy
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    run=root/'runs/2026_10_9-10_14__motion_posture_engineering_recovery/formal'
    if not run.exists():
        import pytest
        pytest.skip('PROJECT_DATA: completed formal run unavailable')
    spec=json.loads((run/'source_snapshot/spec.json').read_text())
    manifest=json.loads((run/'manifest.json').read_text())
    assert historical_report_certificate(spec,manifest,run/'source_snapshot')['status']=='READY'
    import pytest
    wrong=copy.deepcopy(manifest);wrong['execution_identity']['PPO_sha256']='0'*64
    with pytest.raises(ValueError,match='dependency'):
        historical_report_certificate(spec,wrong,run/'source_snapshot')
