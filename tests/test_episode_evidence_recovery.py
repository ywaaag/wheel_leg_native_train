import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import torch

from native_stand.command_v6.domain.episode_summary import normalize,build
from native_stand.command_v6.tools import engineering_recovery as recovery
from native_stand.command_v6.wiring import smoke_certificate,completed_smoke
from native_stand.recovery.episode_metrics import PoseEpisodeMetrics
from native_stand.recovery.task_protocol import resolve

ROOT=Path(__file__).resolve().parents[1]


def test_versioned_episode_schema_legacy_and_conflict():
    value={'completed':550,'max_duration_s':2.18}
    assert normalize(value)['completed_episodes']==550
    assert normalize({'completed_episodes':2,'max_duration_s':2.})['completed']==2
    with pytest.raises(ValueError,match='conflict'):normalize({**value,'completed_episodes':0})
    with pytest.raises(ValueError):normalize({'completed':2})
    with pytest.raises(ValueError):normalize({'schema_version':2,'completed':0})


def test_markdown_compaction_does_not_mutate_raw_evidence():
    from native_stand.command_v6.completion import compact_report_value
    raw={'accepted':False,'per_env':[{'env_id':0,'trace_100hz':[[1.,2.]]*100}],
         'failed_checks':['roll']}
    before=copy.deepcopy(raw)
    summary=compact_report_value(raw)
    assert raw==before and summary['accepted'] is False
    assert summary['per_env'][0]['trace_100hz']['omitted_from_markdown']


def test_pose_metrics_keep_geometry_initialization_and_recovery_distinct():
    poses=[{'pose_id':'low','family':'R1','offline_valid':True},
           {'pose_id':'old','family':'R0','offline_valid':True}]
    metrics=PoseEpisodeMetrics(poses,'cpu')
    rng=torch.get_rng_state().clone()
    metrics.observe(torch.tensor([0,0,1]),done=torch.tensor([1,1,1],dtype=torch.bool),
        success=torch.tensor([0,0,1],dtype=torch.bool),timeout=torch.tensor([0,1,0],dtype=torch.bool),
        fault=torch.zeros(3,dtype=torch.bool),initial_valid=torch.tensor([0,1,1],dtype=torch.bool),
        duration=torch.tensor([.5,2.,10.]))
    rows=metrics.summary()
    assert rows[0]['completed']==2 and rows[0]['runtime_initial_valid_episodes']==1
    assert rows[0]['successes']==0 and rows[0]['policy_recoverable'] is None
    assert rows[1]['successes']==1 and rows[1]['max_duration_s']==10.
    assert torch.equal(rng,torch.get_rng_state())
    metrics.reset();assert metrics.summary()[0]['completed']==0


def test_holding_rising_protocols_and_conflicts():
    for name,kind in [('recovery_r0_hold10_from50_20261007','holding'),
                      ('2026_10_7-15_58__recovery_rise_low_from50','rising')]:
        config=json.loads((ROOT/'configs/experiments'/name/'spec.json').read_text())['recovery']
        before=copy.deepcopy(config)
        result=resolve(config)
        assert result['task_kind']==kind and config==before
        assert resolve({**config,'task_kind':kind})['declaration']=='explicit'
        with pytest.raises(ValueError):resolve({**config,'task_kind':'other'})


def test_grouped_smoke_cannot_use_old_cohort_totals(tmp_path,complete_smoke_fixture):
    spec={'source_sha256':'source','budget':{'smoke_updates':1},'ppo':{'envs':8,'steps_per_env':128},
          'control':{'policy_dt_s':.01},'wiring_smoke':{'required_groups':[
              {'family':'R1','minimum_duration_s':1.,'require_runtime_initial_valid':True},
              {'family':'R0','minimum_completed':1}]}}
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    folder=tmp_path/'smoke';complete_smoke_fixture(folder,path,1)
    def metrics(rows):
        (folder/'metrics.jsonl').write_text(json.dumps({'task_metrics':{'episodes_by_pose':rows}})+'\n')
    old=build(10,10.,10.,family='R0',pose_id='old',runtime_initial_valid_episodes=10)
    metrics([old]);assert smoke_certificate(folder,spec)['status']=='FAILED'
    low=build(1,2.,2.,family='R1',pose_id='low',runtime_initial_valid_episodes=1)
    metrics([old,low]);assert smoke_certificate(folder,spec)['status']=='PASSED'
    low['runtime_initial_valid_episodes']=0
    metrics([old,low]);assert smoke_certificate(folder,spec)['status']=='FAILED'


def recovery_fixture(tmp_path,complete_smoke_fixture):
    source=tmp_path/'source.pt';source.write_bytes(b'actor checkpoint')
    asset=tmp_path/'asset.usd';asset.write_bytes(b'asset fixture')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    spec={'experiment':'old','source_checkpoint':str(source),'source_sha256':sha(source),
          'asset_path':str(asset),'asset_sha256':sha(asset),'budget':{'smoke_updates':2},
          'ppo':{'envs':8,'steps_per_env':128},'control':{'policy_dt_s':.01},
          'wiring_smoke':{'required_event':'completed_episode','required_event_duration_s':1.}}
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    folder=tmp_path/'smoke';complete_smoke_fixture(folder,path,2)
    (folder/'metrics.jsonl').write_text(json.dumps({'rollout':{'episodes':{'completed':2,'max_duration_s':2.}}})+'\n')
    original={**smoke_certificate(folder,spec),'status':'FAILED',
              'errors':['smoke did not observe the required completed_episode']}
    (folder/'wiring_certificate.json').write_text(json.dumps(original))
    for directory,updates,key in [(folder,2,'smoke-id'),(tmp_path/'source_eval',0,'source-id')]:
        directory.mkdir(exist_ok=True)
        (directory/'source_snapshot').mkdir(exist_ok=True)
        (directory/'source_snapshot/spec.json').write_text(json.dumps(spec))
        (directory/'terminal_report.json').write_text(json.dumps({'status':'COMPLETED','actual_updates':updates}))
        (directory/'manifest.json').write_text(json.dumps({'attempt_id':key,'spec_sha256':sha(path),
                                                          'source_sha256':spec['source_sha256']}))
    original={**smoke_certificate(folder,spec),'status':'FAILED',
              'errors':['smoke did not observe the required completed_episode']}
    (folder/'wiring_certificate.json').write_text(json.dumps(original))
    book={'authorization':'AUTHORIZED','limits':{'source_eval':1,'smoke':2,'formal':10},
          'used':{'source_eval':1,'smoke':2,'formal':0},'attempts':{
              'source-id':{'phase':'source_eval','status':'COMPLETED','updates':0,'output_dir':str(tmp_path/'source_eval')},
              'smoke-id':{'phase':'smoke','status':'COMPLETED','updates':2,'output_dir':str(folder)}}}
    (tmp_path/'budget.json').write_text(json.dumps(book))
    return path,folder,tmp_path/'2026_10_7-17_00__recovery'


def test_recovery_plan_zero_write_apply_preserves_ids_usage_and_requires_authorization(tmp_path,complete_smoke_fixture):
    spec,folder,target=recovery_fixture(tmp_path,complete_smoke_fixture)
    before={p:p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    planned=recovery.plan(spec,folder,target)
    assert not target.exists() and planned['files_written']==0
    assert all(p.read_bytes()==data for p,data in before.items())
    result=recovery.apply(planned,planned['plan_sha256'])
    assert result['status']=='PREPARED_UNAUTHORIZED'
    book=json.loads((target/'budget.json').read_text())
    assert book['used']==planned['used'] and book['limits']==planned['limits']
    assert set(book['attempts'])==set(planned['imported_attempt_ids'])
    assert completed_smoke(book,json.loads((target/'spec.json').read_text()))
    assert all(p.read_bytes()==data for p,data in before.items())
    with pytest.raises(FileExistsError):recovery.plan(spec,folder,target)
    with pytest.raises(ValueError,match='already have a recovery publication'):
        recovery.plan(spec,folder,target.with_name('2026_10_7-17_01__duplicate'))


def test_recovery_rejects_changed_budget_and_wrong_failure(tmp_path,complete_smoke_fixture):
    spec,folder,target=recovery_fixture(tmp_path,complete_smoke_fixture)
    planned=recovery.plan(spec,folder,target)
    book=json.loads(spec.with_name('budget.json').read_text());book['used']['smoke']=1
    spec.with_name('budget.json').write_text(json.dumps(book))
    with pytest.raises(ValueError):recovery.apply(planned,planned['plan_sha256'])
    assert not target.exists()


def test_recovery_never_rebinds_failed_receipt_to_changed_evidence(tmp_path,complete_smoke_fixture):
    spec,folder,target=recovery_fixture(tmp_path,complete_smoke_fixture)
    (folder/'metrics.jsonl').write_text(json.dumps({'rollout':{'episodes':{'completed':3,'max_duration_s':2.}}})+'\n')
    with pytest.raises(ValueError,match='cannot rebind history'):recovery.plan(spec,folder,target)
    assert not target.exists()


def test_actual_frozen_preflight_cpu_import_and_identity(tmp_path):
    snapshot=tmp_path/'source_snapshot';snapshot.mkdir()
    copied=snapshot/'native_stand';shutil.copytree(ROOT/'src/native_stand',copied,ignore=shutil.ignore_patterns('__pycache__'))
    source=ROOT/'configs/experiments/2026_10_7-15_58__recovery_rise_low_from50/spec.json'
    spec=json.loads(source.read_text());(snapshot/'spec.json').write_bytes(source.read_bytes())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (tmp_path/'manifest.json').write_text(json.dumps({'spec_sha256':digest(source),
        'declared_execution_source_root':spec['execution_source_root'],
        'execution_modules_sha256':{str(p.relative_to(copied)):digest(p) for p in copied.rglob('*.py')}}))
    # Execute the real preflight imported from its relocated frozen package, without AppLauncher.
    script=('import sys,json;sys.path.insert(0,sys.argv[1]);'
            'from native_stand.command_v6.tools.preflight import check;'
            'r=check(sys.argv[2],sys.argv[3],"source_eval");'
            'print(json.dumps({"execution":r["execution_identity"],"errors":r["errors"],'
            '"isaac_imported":any(k.startswith("isaaclab") for k in sys.modules)}))')
    import os
    child=subprocess.run([sys.executable,'-c',script,str(snapshot),str(source),str(tmp_path/'UNCREATED')],
                         env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=60)
    assert child.returncode==0,child.stderr
    result=json.loads(child.stdout)
    assert result['execution']['actual_execution_root']==str(snapshot)
    assert result['execution']['declared_source_root']==spec['execution_source_root']
    assert result['isaac_imported'] is False and not (tmp_path/'UNCREATED').exists()
    assert not any('receipt identity' in e or 'source_root differs' in e for e in result['errors'])
