FROZEN_TEST_SCOPE='PORTABLE'
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from native_stand.command_v6.tools import storage_budget
from native_stand.command_v6.domain.evidence_summary import compact,result
from native_stand.command_v6.domain.metrics import motion_reward_fields,RolloutMetrics
from native_stand.command_v6.domain.reward import compute


def test_storage_gate_accounts_peak_and_terminal_reserve(tmp_path,monkeypatch):
    spec={'budget':{'formal_updates':50},'evaluation':{'seconds':30,'full_every_updates':25},
        'ppo':{'envs':64,'steps_per_env':128},'control':{'policy_dt_s':.01}}
    monkeypatch.setattr(storage_budget.shutil,'disk_usage',lambda p:SimpleNamespace(free=0))
    r=storage_budget.check(spec,tmp_path/'new','formal')
    assert r['status']=='INSUFFICIENT_STORAGE' and r['atomic_temp_peak_bytes']>0 and r['terminal_reserve_bytes']>0
    assert not (tmp_path/'new').exists()
    monkeypatch.setattr(storage_budget.shutil,'disk_usage',lambda p:SimpleNamespace(free=r['required_bytes']))
    assert storage_budget.check(spec,tmp_path/'new','formal')['status']=='PASS'


def test_reserve_rechecks_storage_before_attempt_mutation(tmp_path,monkeypatch):
    from native_stand.command_v6.ledger import Ledger
    (tmp_path/'spec.json').write_text(json.dumps({'budget':{}}))
    path=tmp_path/'budget.json';path.write_text(json.dumps({'authorization':'AUTHORIZED','limits':{'source_eval':1},
        'used':{'source_eval':0},'attempts':{}}));before=path.read_bytes()
    monkeypatch.setattr(storage_budget,'check',lambda *a:{'status':'INSUFFICIENT_STORAGE'})
    with pytest.raises(ValueError,match='storage'):Ledger(path).reserve('exact','source_eval',tmp_path/'run')
    assert path.read_bytes()==before


def test_recursive_summary_removes_arrays_not_geometry_metrics():
    data={'per_env':[{'trace':[[0]*18]*1000,'mean_roll':.02}],
        'retained_evaluations':[{'per_env':[{'compact_trace_100hz':[[0]*39]*1000}],
          'control_diagnostics':{'rows':[[[0]*54]*8]*1000}}],
        'paired_state':{'rows':[[[0]*197]*8]*1000}}
    summary=result(data,reference='evaluation.json',sha256='a'*64)
    assert len(json.dumps(summary))<2000 and summary['per_env'][0]['mean_roll']==.02
    assert summary['raw_evidence']['sha256']=='a'*64
    assert len(data['per_env'][0]['trace'])==1000
    assert compact(summary)==summary


def test_real_posture_reward_metrics_summary_share_declaration():
    n=2;zero=torch.zeros(n);one=torch.ones(n);z6=torch.zeros(n,6)
    cfg={'version':'bounded_geometry_v1','weight':-.1,
        'deadbands':{'roll_rad':.02,'wheel_heading_offset_m':.02,'leg_length_difference_m':.02},
        'denominators':{'roll_rad':.01,'wheel_heading_offset_m':.01,'leg_length_difference_m':.01}}
    from native_stand.command_v6.domain.posture_geometry import validate_balance
    # Use actual field names from the shared validated declaration.
    validate_balance(cfg)
    weights={k:1. for k in motion_reward_fields({})}
    geometry={'roll_rad':zero,'wheel_heading_offset_m':zero,'leg_length_difference_m':zero,'valid':torch.ones(n,dtype=torch.bool)}
    _,raw,weighted=compute(one,one,zero,zero,zero,torch.stack((zero,zero,one),-1),
        torch.ones(n,2,dtype=torch.bool),z6,z6,z6,torch.zeros(n,4),torch.zeros(n,dtype=torch.bool),
        weights=weights,height_width=.1,linear_denominator=.04,yaw_denominator=.09,terminal_penalty=-1,
        posture_config=cfg,posture_geometry=geometry)
    stats=RolloutMetrics(motion_reward_fields({'posture_balance':cfg}),['fault'],n,'cpu')
    stats.add(raw,weighted,{'fault':torch.zeros(n,dtype=torch.bool)},torch.ones(n,2,dtype=torch.bool),
        torch.zeros(n,4),z6,[40,40,5.5,40,40,5.5])
    assert 'posture_balance' in stats.summary()['weighted_mean']


def test_source_reuse_certificate_identity_complete_and_missing(tmp_path,monkeypatch):
    from native_stand.command_v6.tools import source_evidence as tool
    from native_stand.command_v6.tools import evaluate_checkpoint as evaluator
    from native_stand.command_v6.tools.experiment_preparation import digest
    folder=tmp_path/'source';(folder/'source_snapshot').mkdir(parents=True)
    checkpoint=tmp_path/'model.pt';checkpoint.write_bytes(b'frozen')
    s={'source_checkpoint':str(checkpoint),'source_sha256':digest(checkpoint),'asset_sha256':'a'*64}
    sp=folder/'source_snapshot/spec.json';sp.write_text(json.dumps(s))
    identity={'execution_dependencies':{'sha256':'taskcode'},'location_independent_modules_sha256':'code','PPO_sha256':'ppo','dependencies':{'torch':'frozen'}}
    (folder/'manifest.json').write_text(json.dumps({'spec_sha256':digest(sp),'asset_sha256':'a'*64,'execution_identity':identity,'evaluator_sha256':'evaluator'}))
    (folder/'terminal_report.json').write_text(json.dumps({'status':'COMPLETED','actual_updates':0}))
    protocol={'requested_seconds':30,'scored_envs':1,'steady_window_s':[2,30],'motion_window_s':[10,18]}
    payload={'checkpoint_sha256':digest(checkpoint),'spec_sha256':digest(sp),'asset_sha256':'a'*64,
        'target':[0,0],'seconds':30,'effective_protocol':protocol,'per_env':[{'env_id':0,'continuous_s':30,'outcome':'completed'}]}
    path=folder/'evaluation_source.json';path.write_text(json.dumps(payload))
    entry={'role':'source','checkpoint_sha256':digest(checkpoint),'evaluation':path.name,'evaluation_sha256':digest(path)}
    (folder/'candidate_registry.json').write_text(json.dumps([entry]))
    monkeypatch.setattr(tool,'recipe',lambda spec:spec)
    monkeypatch.setattr(tool,'identity',lambda spec:identity)
    monkeypatch.setattr(evaluator,'protocol_for_spec',lambda *a:protocol)
    assert tool.check(s,folder)['status']=='REUSABLE'
    other={**s,'asset_sha256':'c'*64}
    assert tool.check(other,folder)['status']=='CONFLICTING'
    payload['per_env'][0]['continuous_s']=10;path.write_text(json.dumps(payload));entry['evaluation_sha256']=digest(path)
    (folder/'candidate_registry.json').write_text(json.dumps([entry]))
    assert tool.check(s,folder)['status']=='MISSING'


def test_actual_chain_and_registry_compaction_are_wired():
    from native_stand.command_v6.tools.test_resources import source_file
    import ast
    for relative in ('command_v6/train.py','command_v6/stand_chain.py','command_v6/completion.py'):
        text=source_file(relative).read_text();ast.parse(text)
        assert 'compact(' in text
    text=source_file('command_v6/stand_chain.py').read_text()
    assert "if certificate['status']!='REUSABLE'" in text and "historical_wall_not_charged_as_new" in text
