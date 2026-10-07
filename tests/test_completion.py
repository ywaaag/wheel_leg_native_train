import copy
import json
from pathlib import Path
import subprocess
import sys
import os

import pytest

from native_stand.command_v6.completion import (acknowledge, choose, evaluation_identity,
    finalize_report, notify, plan, read_metrics, sha, write)
from native_stand.command_v6.domain.protocol import standing_gate
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.monitor import reconcile

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/'configs/experiments/stand_plane.json').read_text())
EXPECTED=evaluation_identity(SPEC,'fixture_evaluator')


def candidate(name='candidate',drift=.05,seconds=10,accepted=True,role='candidate'):
    rows=[{'env_id':index,'outcome':'completed' if seconds==10 else 'task_failure',
        'termination_reason':'timeout' if seconds==10 else 'tilt','continuous_s':seconds,
        'net_drift_m':drift,'max_excursion_m':drift,'dual_contact_fraction':.95,
        'mean_abs_vx_error_mps':.01,'mean_abs_yaw_error_rad_s':.01,'height_steady_mean_m':.363,
        'peak_tilt_rad':.01,'closure_max_m':.001,'saturation_fraction':0.} for index in range(8)]
    result={'per_env':rows,'effective_protocol':EXPECTED['effective_protocols']['zero']}
    result['standing_gate']=standing_gate(result,SPEC['evaluation'])
    if not accepted:
        result['standing_gate']['accepted']=False
    return {'checkpoint':name,'checkpoint_sha256':name,'update':100,'identity':EXPECTED,
        'kind':'full','role':role,'result':result}


def test_source_can_beat_all_and_latest_is_not_best():
    source=candidate('source',drift=.01,role='source')
    selection=choose([candidate('latest',drift=.15),source],{'sha256':'latest'},EXPECTED)
    assert selection['best_observed_candidate']['checkpoint']=='source'
    assert selection['accepted_candidate']['role']=='source'


def test_all_unaccepted_survival_precedes_small_drift():
    selection=choose([candidate('early',drift=0,seconds=1),
                      candidate('alive',drift=.5,accepted=False)],None,EXPECTED)
    assert selection['accepted_candidate'] is None
    assert selection['best_observed_candidate']['checkpoint']=='alive'


@pytest.mark.parametrize('problem',['missing','protocol','light','runtime'])
def test_invalid_evidence_never_certifies(problem):
    entry=candidate()
    if problem=='missing':
        entry['result']['per_env'][0]['height_steady_mean_m']=None
    elif problem=='protocol':
        entry['identity']={**EXPECTED,'protocol_sha256':'other'}
    elif problem=='light':
        entry['kind']='light'
    else:
        entry['result']['per_env'][0]['outcome']='runtime_fault'
    selection=choose([entry],{'sha256':'candidate'},EXPECTED)
    assert selection['accepted_candidate'] is None
    assert selection['best_observed_candidate'] is None
    assert selection['unreviewed_checkpoints']


def test_jsonl_truncated_tail(tmp_path):
    file=tmp_path/'metrics.jsonl'
    file.write_text('{"actual_update":1}\n{"actual_update":')
    rows,issues=read_metrics(file)
    assert len(rows)==1 and issues==[{'line':2,'kind':'truncated_tail'}]


def ready_run(tmp_path,session='fixture_session'):
    write(tmp_path/'manifest.json',{'hapi_session':session})
    (tmp_path/'completion_report.md').write_text('fixture')
    write(tmp_path/'report_ready.json',{'event_id':'event','report_sha256':sha(tmp_path/'completion_report.md')})
    write(tmp_path/'analysis.json',{'status':'COMPLETED'})
    write(tmp_path/'candidate_selection.json',{})


def test_at_most_once_and_review_ack(tmp_path):
    ready_run(tmp_path)
    calls=[]
    def send(session,message):
        calls.append((session,message))
        return {'status':'sent'}
    assert notify(tmp_path,send)['status']=='sent'
    assert notify(tmp_path,send)['status']=='sent'
    assert len(calls)==1
    acknowledge(tmp_path)
    assert notify(tmp_path,send)['status']=='reviewed'
    assert len(calls)==1


@pytest.mark.parametrize('mode',['failed','unknown_delivery','not_configured'])
def test_delivery_failure_does_not_repeat(tmp_path,mode):
    ready_run(tmp_path,None if mode=='not_configured' else 'fixture_session')
    calls=[]
    def send(session,message):
        calls.append(session)
        if mode=='unknown_delivery':
            raise subprocess.TimeoutExpired('fake',1)
        return {'status':'failed','returncode':1}
    expected='notification_not_configured' if mode=='not_configured' else mode
    assert notify(tmp_path,send)['status']==expected
    assert notify(tmp_path,send)['status']==expected
    assert len(calls)==(0 if mode=='not_configured' else 1)


def test_report_required_before_notification(tmp_path):
    with pytest.raises(ValueError,match='not ready'):
        notify(tmp_path,lambda *_:pytest.fail('unexpected transport'))


@pytest.mark.parametrize('status,code',[('COMPLETED',0),('TERMINATED',143),('STOPPED_BOUNDED',124)])
def test_fake_terminal_accounting_and_report(tmp_path,status,code):
    run=tmp_path/'run'
    run.mkdir()
    (run/'source_snapshot').mkdir()
    write(run/'source_snapshot/spec.json',SPEC)
    checkpoint=run/'model.pt'
    checkpoint.write_bytes(b'fixture model')
    entry=candidate(str(checkpoint))
    entry['checkpoint_sha256']=sha(checkpoint)
    write(run/'candidate_registry.json',[entry])
    write(run/'manifest.json',{'attempt_id':'own','evaluator_sha256':'fixture_evaluator','hapi_session':None})
    write(run/'terminal_report.json',{'status':status,'actual_updates':2,'samples':16384,'wall_s':10,
        'latest_checkpoint':{'path':str(checkpoint),'sha256':sha(checkpoint)}})
    write(run/'progress.json',{'actual_updates':2})
    (run/'metrics.jsonl').write_text(json.dumps({'rollout_s':2,'ppo_s':1,'evaluation_s':1,'serialization_s':.1})+'\n')
    ledger=tmp_path/'budget.json'
    write(ledger,{'authorization':'AUTHORIZED','limits':{'formal':10},'used':{'formal':2},
        'attempts':{'own':{'phase':'formal','output_dir':str(run.resolve()),'status':'RUNNING',
            'updates':2,'started_unix_s':0},'other':{'phase':'formal','output_dir':'/other','status':'COMPLETED','updates':4}}})
    reconcile(ledger,'own',run,code)
    analysis=finalize_report(run,code)
    assert analysis['actual_updates']==2
    assert analysis['status']==status
    assert json.loads(ledger.read_text())['attempts']['other']['updates']==4
    assert analysis['candidate_selection']['accepted_candidate']
    assert notify(run)['status']=='notification_not_configured'
    assert finalize_report(run,code)==analysis


def test_plan_preserves_frozen_schedule():
    result=plan(SPEC,'formal')
    assert result['updates']==200 and result['samples']==1638400
    assert result['checkpoints']==2
    assert result['light_evaluations']==1 and result['full_evaluations']==1


def test_latest_unreviewed_inventory_and_nonfinite():
    entry=candidate()
    inventory=[{'sha256':'candidate'},{'sha256':'latest'}]
    selection=choose([entry],inventory[-1],EXPECTED,inventory)
    assert selection['unreviewed_checkpoints']==[inventory[-1]]
    entry['result']['per_env'][0]['net_drift_m']=float('nan')
    invalid=choose([entry],None,EXPECTED)
    assert invalid['best_observed_candidate'] is None
    json.dumps(invalid,allow_nan=False)


def test_unknown_delivery_after_interrupted_sender(tmp_path):
    ready_run(tmp_path)
    write(tmp_path/'hapi_notification.json',{'status':'sending','event_id':'event'})
    assert notify(tmp_path,lambda *_:pytest.fail('must not resend'))['status']=='unknown_delivery'


def test_exit_conflict_is_not_silently_success(tmp_path):
    (tmp_path/'source_snapshot').mkdir()
    write(tmp_path/'source_snapshot/spec.json',SPEC)
    write(tmp_path/'manifest.json',{'attempt_id':'test','evaluator_sha256':'fixture_evaluator'})
    write(tmp_path/'terminal_report.json',{'status':'COMPLETED','actual_updates':1,'samples':8192,'wall_s':10})
    analysis=finalize_report(tmp_path,1)
    assert analysis['terminal_exit_conflict']
    assert analysis['accounted_updates_without_metrics']==1
    assert analysis['candidate_selection']['accepted_candidate'] is None


@pytest.mark.parametrize('mode',['normal','sigterm','hard_timeout'])
def test_real_cpu_child_exit_reconciles_own_attempt(tmp_path,mode):
    command=[sys.executable,'-c', 'pass' if mode=='normal' else
        'import os,signal; os.kill(os.getpid(),signal.SIGTERM)' if mode=='sigterm' else 'raise SystemExit(124)']
    child=subprocess.run(command,timeout=5)
    run=tmp_path/'run'
    run.mkdir()
    path=tmp_path/'budget.json'
    write(path,{'limits':{'formal':10},'used':{'formal':3},'attempts':{
        'current':{'output_dir':str(run.resolve()),'phase':'formal','status':'RUNNING','updates':3,'started_unix_s':0}}})
    if mode=='normal':
        write(run/'terminal_report.json',{'status':'COMPLETED','actual_updates':3})
    result=reconcile(path,'current',run,child.returncode)
    assert result['status']==('COMPLETED' if mode=='normal' else 'TERMINATED')
    assert json.loads(path.read_text())['used']['formal']==3


def test_monitor_fake_trainer_full_completion_chain(tmp_path,monkeypatch):
    from native_stand.command_v6 import monitor
    spec_path=tmp_path/'spec.json'
    write(spec_path,SPEC)
    run=tmp_path/'run'
    ledger=tmp_path/'budget.json'
    write(ledger,{'authorization':'AUTHORIZED','limits':{'source_eval':1},'used':{'source_eval':0},
        'source_eval_wall_used_s':0,'attempts':{'fake':{'output_dir':str(run.resolve()),
            'phase':'source_eval','status':'RUNNING','updates':0,'started_unix_s':0}}})
    fake_root=tmp_path/'fake'/'nested'/'kernel'
    fake_root.mkdir(parents=True)
    (fake_root/'train.py').write_text('raise SystemExit(7)\n')
    monkeypatch.setattr(monitor,'ROOT',fake_root)
    received=[]
    monkeypatch.setattr(monitor,'notify',lambda path:received.append(json.loads((path/'report_ready.json').read_text())))
    reader,writer=os.pipe()
    monkeypatch.setattr(sys,'argv',['monitor','--spec',str(spec_path),'--phase','source_eval',
        '--output-dir',str(run),'--attempt-id','fake','--handshake-fd',str(writer)])
    assert monitor.main()==7
    os.close(reader)
    assert received[0]['status']=='report_ready'
    assert json.loads((run/'analysis.json').read_text())['status']=='FAILED'
    book=json.loads(ledger.read_text())
    assert book['used']['source_eval']==1
    assert book['attempts']['fake']['status']=='FAILED'


def test_episode_summary_uses_fixed_shape_done_mask():
    import torch
    from native_stand.command_v6.domain.metrics import RolloutMetrics
    metrics=RolloutMetrics(['reward'],['tilt'],2,'cpu')
    for done in (torch.tensor([True,False]),torch.tensor([False,False])):
        metrics.add({'reward':torch.ones(2)},{'reward':torch.ones(2)},
            {'tilt':torch.zeros(2,dtype=torch.bool)},torch.ones(2,2,dtype=torch.bool),
            torch.zeros(2,4),torch.zeros(2,6),[40,40,5.5,40,40,5.5],
            torch.tensor([2.,5.],dtype=torch.float64),done)
    assert metrics.summary()['episodes']=={'schema_version':1,'completed':1,'completed_episodes':1,
                                           'mean_duration_s':2.,'max_duration_s':2.}
