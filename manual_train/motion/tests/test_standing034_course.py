"""PORTABLE: real Motion contract/model/owner boundaries; no simulator."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy,json,os,random
from pathlib import Path
import pytest,torch
from tensordict import TensorDict
from native_stand.motion_course import domain,io
from native_stand.command_v6.domain.protocol import score,FIELDS,capability_gate
from native_stand.command_v6.domain.evidence import effective_protocol
from native_stand.command_v6.domain.warmstart import initialize_state,initialize_adam,preserve_rng_state
from native_stand.command_v6.learning import model
PROJECT=io.PROJECT

def result(target,passed=8):
    return {'target':target,'per_env':[dict(env_id=i,height_steady_mean_m=.34,saturation_fraction=.01,hold_mean_abs_error=.01) for i in range(8)],'capability_gate':{'passed_envs':passed,'accepted':passed==8}}

def registry(update=100,checkpoint='cp',passed=8):
    return [dict(kind='full',update=update,checkpoint=checkpoint,checkpoint_sha256='a'*64,result=result(cmd,passed)) for cmd in domain.COMMANDS]

def test_joint_same_model_all_three_commands():
    assert domain.aggregate(registry())[0]['accepted']
    rows=registry();rows[2]['checkpoint']='other'
    assert not domain.aggregate(rows)
    assert not domain.aggregate(registry()[:2])

def test_missing_height_cannot_accept():
    rows=registry();rows[0]['result']['per_env'][0]['height_steady_mean_m']=None
    assert not domain.aggregate(rows)[0]['accepted']

def test_duplicate_command_rejected():
    rows=registry()
    with pytest.raises(ValueError,match='duplicate'):domain.aggregate(rows+rows[:1])

def test_fail_pass_fail_resets_confirmation():
    book={'totals':{'formal_updates':300},'confirmations':1}
    candidates=domain.aggregate(registry(passed=7));latest=candidates[-1]
    assert domain.decide(book,candidates,latest)['action']=='RESUME'
    assert book['confirmations']==0
    assert domain.decide(book,domain.aggregate(registry()),latest)['action']=='RESUME'
    assert book['confirmations']==1
    domain.decide(book,candidates,latest);assert book['confirmations']==0

def test_two_full_joint_assessments_accept_one_complete_model():
    rows=registry(100,'first')+registry(200,'second');book={'totals':{'formal_updates':300}}
    d=domain.decide(book,domain.aggregate(rows),domain.aggregate(rows)[-1])
    assert d['action']=='ACCEPT' and d['candidate']['checkpoint']=='second'

def test_unlimited_is_not_fake_high_numeric_cap_and_rollback_once():
    row=domain.aggregate(registry(passed=5))[0];book={'totals':{'formal_updates':5100},'best':row,'stagnant_blocks':2}
    assert domain.decide(book,[row],row)['action']=='RESUME'
    assert book['rollbacks']==1
    book['stagnant_blocks']=2
    assert domain.decide(book,[row],row)['action']=='STOP'

def test_new_height_membership_and_legacy_scoring_unchanged():
    rows=torch.zeros(3000,8,len(FIELDS));rows[:,:,2]=.34;rows[:,:,8:10]=3.
    valid=torch.ones(3000,8,dtype=torch.bool);done=torch.zeros_like(valid);causes=torch.zeros(8,6,dtype=torch.bool);timeout=torch.zeros(8,dtype=torch.bool)
    args=dict(dt=.01,requested_steps=3000,full_trace=True,target_window=(10.,20.))
    new=score(rows,valid,done,causes,timeout,effective_protocol={'gate_identity':'motion_standing034_v1','standing_height_m':[.32,.36],'steady_window_s':[10.,20.]},**args)
    old=score(rows,valid,done,causes,timeout,**args)
    assert all(r['height_steady_fraction']==1. for r in new['per_env'])
    assert all(r['height_steady_fraction']==0. for r in old['per_env'])

def test_real_checkpoint_strict_actor_critic_adam_restore():
    torch.set_num_threads(2)
    original_sha=io.sha(io.SOURCE)
    source=torch.load(io.SOURCE,map_location='cpu',weights_only=False)
    obs=TensorDict({'policy':torch.zeros(4,25),'history':torch.zeros(4,125)},batch_size=[4])
    parent=json.loads((io.SOURCE.parent/'source_snapshot/spec.json').read_text())
    actor=model(obs,actor=True,spec=parent);critic=model(obs,actor=False,spec=parent)
    actor.load_state_dict(initialize_state(source['actor'],actor.state_dict(),input_dim=150))
    critic.load_state_dict(initialize_state(source['critic'],critic.state_dict(),input_dim=150))
    names=[('actor.'+n,p) for n,p in actor.named_parameters()]+[('critic.'+n,p) for n,p in critic.named_parameters()]
    optimizer=torch.optim.Adam([p for _,p in names],lr=3e-5)
    initialize_adam(source['optimizer'],optimizer,names,names,learning_rate=3e-5,input_dim=150)
    loaded=optimizer.state_dict();saved=source['optimizer']
    for a,b in zip(loaded['param_groups'][0]['params'],saved['param_groups'][0]['params']):
        for key in ('step','exp_avg','exp_avg_sq'):assert torch.equal(loaded['state'][a][key],saved['state'][b][key])
    assert all(torch.equal(actor.state_dict()[k],v) for k,v in source['actor'].items())
    assert all(torch.equal(critic.state_dict()[k],v) for k,v in source['critic'].items())
    assert original_sha==io.sha(io.SOURCE)

def test_extra_rng_restore_and_missing_identity_fail():
    import numpy as np
    a=random.getstate();b=np.random.get_state()
    spec={'motion_course':{'resume':True,'task_manifest_sha256':'x'}}
    source={'motion_course_checkpoint':{'task_manifest_sha256':'x'},'python_rng':a,'numpy_rng':b}
    random.seed(99);np.random.seed(99);io.restore_extra_rng(source,spec)
    assert random.getstate()==a
    assert np.array_equal(np.random.get_state()[1],b[1])
    with pytest.raises(ValueError):io.restore_extra_rng({},spec)

def test_stop_file_and_storage_do_not_launch_watcher(tmp_path):
    task=tmp_path/'task_manifest.json';task.write_text('{}');out=tmp_path/'run/formal';out.mkdir(parents=True)
    spec={'motion_course':{'task_manifest':str(task),'artifact_limit_bytes':2*1024**3}}
    assert not io.stop_requested(spec,out)
    task.with_name('STOP').touch();assert io.stop_requested(spec,out)
    task.with_name('STOP').unlink();spec['motion_course']['artifact_limit_bytes']=1
    with pytest.raises(RuntimeError,match='storage'):io.stop_requested(spec,out)

def test_finish_engineering_failure_no_dispatch(tmp_path,monkeypatch):
    task=tmp_path/'task_manifest.json';task.write_text('{}');ledger=task.with_name('task_ledger.json')
    spec=tmp_path/'spec.json';spec.write_text(json.dumps({'motion_course':{'task_manifest':str(task)}}))
    ledger.write_text(json.dumps({'active_spec':str(spec),'blocks':[],'totals':dict(updates=0,formal_updates=0,samples=0,wall_s=0.,score_episodes=0)}))
    spec.with_name('budget.json').write_text(json.dumps({'used':{'smoke':0,'formal':0}}))
    chain=tmp_path/'run';chain.mkdir();(chain/'chain_terminal_report.json').write_text(json.dumps({'chain_wall_s':1.,'phase_results':[]}))
    monkeypatch.setattr(io,'project_root',lambda s:tmp_path)
    monkeypatch.setattr(io,'prepare',lambda *a,**k:pytest.fail('must not resubmit on engineering failure'))
    io.finish(spec,chain,'FAILED','fixture runtime fault')
    assert json.loads(ledger.read_text())['status']=='ENGINEERING_STOP'
    with pytest.raises(ValueError,match='owner'):io.finish(spec,chain,'FAILED','fixture')

def test_settlement_failure_records_exact_reason(tmp_path):
    task=tmp_path/'task_manifest.json';task.write_text('{}');ledger=task.with_name('task_ledger.json');ledger.write_text('{}')
    spec=tmp_path/'spec.json';spec.write_text(json.dumps({'motion_course':{'task_manifest':str(task)}}))
    io.settlement_failure(spec,ValueError('identity differs'))
    d=json.loads(ledger.read_text());assert d['status']=='ENGINEERING_STOP' and 'identity differs' in d['next_decision']['reason']

def test_source_behavior_failure_allowed_faults_rejected(tmp_path):
    spec={'source_sha256':'b'*64}
    for i,cmd in enumerate(domain.COMMANDS):
        r=result(cmd,0);r.update(checkpoint_sha256='b'*64,effective_protocol={'gate_identity':'motion_standing034_v1'})
        for row in r['per_env']:row.update(outcome='task_failure',continuous_s=.3)
        (tmp_path/f'evaluation_source_{i}.json').write_text(json.dumps(r))
    proof=io.verify_source_evidence(spec,tmp_path)
    assert proof['engineering_valid'] and not proof['behavior_passed']
    p=tmp_path/'evaluation_source_1.json';r=json.loads(p.read_text());r['per_env'][0]['outcome']='runtime_fault';p.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='runtime fault'):io.verify_source_evidence(spec,tmp_path)

def test_episode_count_from_atomic_actual_results(tmp_path):
    for stage in ('source_eval','smoke','formal'):
        d=tmp_path/stage;d.mkdir()
        (d/'evaluation_1_0_0.json').write_text(json.dumps({'per_env':[{}]*8}))
        (d/'progress.json').write_text('{}')
    assert io.score_episode_count(tmp_path)==24

def test_checkpoint_counts_smoke_separately_from_formal(tmp_path,monkeypatch):
    task=tmp_path/'task/task_manifest.json';task.parent.mkdir();task.write_text('{}')
    task.with_name('task_ledger.json').write_text(json.dumps({'totals':{'updates':325,'formal_updates':300}}))
    d=tmp_path/'configs/experiments/example';d.mkdir(parents=True)
    (d/'budget.json').write_text(json.dumps({'used':{'smoke':25,'formal':0}}))
    s={'experiment':'example','motion_course':dict(task_manifest=str(task),task_manifest_sha256='x',block_index=1,cumulative_formal_updates=300)}
    monkeypatch.setattr(io,'PROJECT',tmp_path);monkeypatch.setattr(io,'module_hashes',lambda p:{})
    m=io.checkpoint_metadata(s,25)['motion_course_checkpoint']
    assert m['cumulative_formal_updates']==300 and m['cumulative_online_updates']==350
    (d/'budget.json').write_text(json.dumps({'used':{'smoke':25,'formal':100}}))
    m=io.checkpoint_metadata(s,100)['motion_course_checkpoint']
    assert m['cumulative_formal_updates']==400 and m['cumulative_online_updates']==450

def test_real_public_train_failure_writes_original_terminal(tmp_path,monkeypatch):
    """Execute real main+ledger+finally, inject failure before AppLauncher; no Isaac."""
    import sys
    from native_stand.command_v6 import train
    original=json.loads((io.SOURCE.parent/'source_snapshot/spec.json').read_text())
    original['source_checkpoint']=str(io.SOURCE)
    p=tmp_path/'spec.json';p.write_text(json.dumps(original));out=tmp_path/'run'
    p.with_name('budget.json').write_text(json.dumps(dict(authorization='AUTHORIZED',limits=dict(source_eval=1,smoke=25,formal=300,evaluate=0,play=0),used=dict(source_eval=0,smoke=0,formal=0,evaluate=0,play=0),attempts={},source_eval_wall_used_s=0.)))
    monkeypatch.setattr(train,'STOP',False)
    monkeypatch.setattr(train,'check',lambda *a,**k:{'status':'PASS'})
    def fail(*a,**k):raise RuntimeError('CPU injected failure before AppLauncher')
    monkeypatch.setattr(train,'_snapshot',fail)
    monkeypatch.setattr(sys,'argv',['train','--spec',str(p),'--output-dir',str(out),'--phase','source_eval','--run'])
    with pytest.raises(RuntimeError,match='CPU injected failure'):train.main()
    terminal=json.loads((out/'terminal_report.json').read_text())
    assert terminal['status']=='FAILED' and terminal['stop_kind']=='exception'
    assert 'CPU injected failure' in terminal['failure']['exception']
    assert terminal['actual_updates']==0
