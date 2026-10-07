import json
from pathlib import Path

import pytest

from native_stand.command_v6 import submission, supervisor
from native_stand.command_v6.tools import health_check as health


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def project_fixture(tmp_path, monkeypatch):
    root=tmp_path/'project'
    root.mkdir()
    for name in ('README.md','STATUS.md','TOOL_INDEX.md'):
        (root/name).write_text('Current entry\n')
    source=root/'source.pt';source.write_bytes(b'source')
    asset=root/'asset.usd';asset.write_bytes(b'asset')
    spec=root/'configs/spec.json'
    config={'source_checkpoint':str(source),'source_sha256':health.digest(source),
        'source_update':50,'source_spec_sha256':'source-spec','source_input_dim':150,
        'asset_path':str(asset),'asset_sha256':health.digest(asset),
        'evaluation':{'scored_envs':2}}
    write_json(spec,config)
    write_json(spec.with_name('budget.json'),{'authorization':'AUTHORIZED','attempts':{},
        'limits':{'source_eval':1,'smoke':3,'formal':50},'used':{}})
    metadata={'update':50,'asset_sha256':health.digest(asset),'spec_sha256':'source-spec',
        'actor_input_shape':[256,150],'critic_input_shape':[256,150],
        'std':[1.]*6,'optimizer_lr':[3e-5]}
    monkeypatch.setattr(health,'checkpoint_metadata',lambda path:dict(metadata))
    return root,spec,config,metadata


def test_exact_process_identity_rejects_substrings_reuse_and_duplicate_flags(tmp_path,monkeypatch):
    output=tmp_path/'run';spec=tmp_path/'spec.json'
    argv=['python','/src/train.py','--output-dir',str(output),'--attempt-id','exact',
          '--spec',str(spec)]
    row={'pid':7,'argv':argv,'command':' '.join(argv),'started_unix_s':10.,
         'environment':{'CUDA_VISIBLE_DEVICES':'1'}}
    monkeypatch.setattr(health,'process_snapshot',lambda pid:row)
    kw={'output_dir':output,'attempt_id':'exact','command_token':'train.py',
        'started_unix_s':10.,'spec_path':spec,'physical_gpu':1}
    assert health.process_identity(7,**kw)['status']=='OK'
    assert health.process_identity(7,**{**kw,'started_unix_s':4.})['status']=='PROCESS_IDENTITY_MISMATCH'
    assert health.process_identity(7,**{**kw,'started_unix_s':None})['status']=='MISSING_EVIDENCE'
    argv[1]='/src/not_train.py'
    assert health.process_identity(7,**kw)['status']=='PROCESS_IDENTITY_MISMATCH'
    argv[1]='/src/train.py';argv.extend(['--attempt-id','exact'])
    assert health.process_identity(7,**kw)['status']=='PROCESS_IDENTITY_MISMATCH'


def test_internal_source_spec_and_shape_are_checked(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    assert health.inspect_project(root,spec_path=spec)['status']=='OK'
    metadata['spec_sha256']='wrong'
    metadata['critic_input_shape']=[256,149]
    report=health.inspect_project(root,spec_path=spec)
    assert any('spec_sha256 differs' in str(row['detail']) for row in report['findings'])
    assert any('critic_input_shape differs' in str(row['detail']) for row in report['findings'])


def add_run(root,spec,config,metadata):
    run=root/'run';run.mkdir()
    checkpoint=run/'model_update_25.pt';checkpoint.write_bytes(b'candidate')
    metadata.update(update=25,spec_sha256=health.digest(spec))
    manifest={'attempt_id':'a','spec_sha256':health.digest(spec),'phase':'formal'}
    progress={'attempt_id':'a','status':'COMPLETED','actual_updates':25,'samples':204800,
        'latest_checkpoint':{'path':str(checkpoint),'sha256':health.digest(checkpoint),'update':25},
        'evaluations':[{'cases':[{'path':'evaluation_25.json'}]}]}
    terminal={key:progress[key] for key in ('attempt_id','status','actual_updates','samples')}
    terminal['exit_code']=0
    write_json(run/'manifest.json',manifest);write_json(run/'progress.json',progress)
    write_json(run/'terminal_report.json',terminal)
    write_json(run/'source_snapshot/spec.json',config)
    gate={'accepted':True,'passed_envs':2,'per_env':[{'env_id':0,'accepted':True},
        {'env_id':1,'accepted':True}]}
    evaluation={'checkpoint_sha256':health.digest(checkpoint),'spec_sha256':health.digest(spec),
        'standing_gate':gate,'per_env':[{'env_id':0},{'env_id':1}]}
    write_json(run/'evaluation_25.json',evaluation)
    candidate={'checkpoint':str(checkpoint),'checkpoint_sha256':health.digest(checkpoint),
        'update':25,'eligible':True,'accepted':True,'role':'candidate','evaluation':'evaluation_25.json'}
    selection={'latest_checkpoint':progress['latest_checkpoint'],'best_new_evaluated_candidate':candidate,
        'accepted_candidate':candidate,'fallback_checkpoint':candidate,'accepted_by_stage':{'L1':candidate}}
    write_json(run/'candidate_selection.json',selection)
    write_json(run/'analysis.json',{'status':'COMPLETED','actual_updates':25,'samples':204800,
        'candidate_selection':selection})
    (run/'completion_report.md').write_text('Terminal: COMPLETED\n')
    book={'authorization':'AUTHORIZED','attempts':{'a':{'status':'COMPLETED','phase':'formal',
        'output_dir':str(run),'updates':25,'started_unix_s':1.}},
        'limits':{'formal':50},'used':{'formal':25}}
    write_json(spec.with_name('budget.json'),book)
    return run,evaluation,selection,progress


def test_all_candidate_roles_require_same_checkpoint_raw_evidence(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    run,evaluation,selection,progress=add_run(root,spec,config,metadata)
    report=health.inspect_project(root,spec_path=spec,run=run)
    assert not any('accepted_by_stage' in str(row['detail']) for row in report['findings'])
    evaluation['standing_gate']['accepted']=False
    evaluation['standing_gate']['passed_envs']=1
    evaluation['standing_gate']['per_env'][1]['accepted']=False
    write_json(run/'evaluation_25.json',evaluation)
    report=health.inspect_project(root,spec_path=spec,run=run)
    assert any('accepted_by_stage.L1 lacks complete passed raw gates' in str(row['detail']) for row in report['findings'])
    assert any(row['reason_code']=='BEHAVIOR_GATE_FAILED' for row in report['findings'])


def test_report_and_progress_raw_conflicts_are_detected(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    run,evaluation,selection,progress=add_run(root,spec,config,metadata)
    progress['evaluations'][0]['cases'][0]['standing_gate']={'accepted':False}
    write_json(run/'progress.json',progress)
    (run/'completion_report.md').write_text('Terminal: FAILED\n')
    write_json(run/'report_ready.json',{'report_sha256':'wrong'})
    report=health.inspect_project(root,spec_path=spec,run=run)
    details=' '.join(str(row['detail']) for row in report['findings'])
    assert 'progress/raw standing_gate conflict' in details
    assert 'Markdown/terminal status conflict' in details
    assert 'report_ready/report SHA conflict' in details


def test_stage_acceptance_requires_all_declared_commands(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    run,evaluation,selection,progress=add_run(root,spec,config,metadata)
    selection['accepted_candidate']['identity']={'capability_commands':[[0,0],[1,0],[-1,0]]}
    write_json(run/'candidate_selection.json',selection)
    report=health.inspect_project(root,spec_path=spec,run=run)
    assert any('missing_command_evaluations' in str(row['detail']) for row in report['findings'])


def test_health_zero_writes_and_unsettled_unknown_attempt(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    book=json.loads(spec.with_name('budget.json').read_text())
    book['attempts']={'a':{'status':'UNKNOWN','output_dir':str(root/'absent'),'started_unix_s':1}}
    write_json(spec.with_name('budget.json'),book)
    before={str(path):path.read_bytes() for path in root.rglob('*') if path.is_file()}
    report=health.inspect_project(root,spec_path=spec)
    assert any(row['reason_code']=='UNSETTLED_ATTEMPT' for row in report['findings'])
    assert report['files_written']==report['ppo']==report['simulation']==0
    assert before=={str(path):path.read_bytes() for path in root.rglob('*') if path.is_file()}


def test_standalone_evaluation_does_not_replace_trainer_run(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    run,evaluation,selection,progress=add_run(root,spec,config,metadata)
    standalone=root/'durability_100s.json'
    write_json(standalone,evaluation)
    write_json(standalone.with_name('durability_100s.terminal.json'),{'attempt_id':'evaluation',
        'status':'COMPLETED'})
    book=json.loads(spec.with_name('budget.json').read_text())
    book['attempts']['evaluation']={'phase':'evaluate','status':'COMPLETED',
        'started_unix_s':2.,'output_dir':str(standalone),'updates':0}
    write_json(spec.with_name('budget.json'),book)
    report=health.inspect_project(root,spec_path=spec)
    assert not any('durability_100s.json/' in row['path'] for row in report['findings'])
    assert str(run/'manifest.json') in report['inputs']


def test_source_raw_evaluation_uses_explicit_baseline_run(tmp_path,monkeypatch):
    root,spec,config,metadata=project_fixture(tmp_path,monkeypatch)
    run,evaluation,selection,progress=add_run(root,spec,config,metadata)
    source_run=root/'source_eval'
    baseline={**evaluation,'checkpoint_sha256':config['source_sha256']}
    write_json(source_run/'evaluation_source.json',baseline)
    manifest=json.loads((run/'manifest.json').read_text())
    manifest['source_baseline_run']=str(source_run)
    write_json(run/'manifest.json',manifest)
    selection['source_baseline']={'checkpoint':config['source_checkpoint'],
        'checkpoint_sha256':config['source_sha256'],'evaluation':'evaluation_source.json','role':'source'}
    write_json(run/'candidate_selection.json',selection)
    report=health.inspect_project(root,spec_path=spec,run=run)
    assert not any('source_baseline lacks same-checkpoint' in str(row['detail']) for row in report['findings'])
    assert str(source_run/'evaluation_source.json') in report['inputs']


def test_active_phase_health_gate_and_gpu_occupancy():
    report={'findings':[{'reason_code':'BUDGET_EXHAUSTED','detail':'smoke'},
        {'reason_code':'BEHAVIOR_GATE_FAILED','detail':'source'}],
        'gpu':{'status':'OK','devices':[{'index':1,'uuid':'GPU-1'}],'compute_processes':[]}}
    health.submission_health(report,current_session='current',target_session='current',phase='formal',physical_gpu=1)
    with pytest.raises(ValueError):
        health.submission_health(report,current_session='current',target_session='current',phase='smoke',physical_gpu=1)
    report['gpu']['compute_processes']=[{'gpu_uuid':'GPU-1','pid':7}]
    with pytest.raises(ValueError,match='occupied'):
        health.submission_health(report,current_session='current',target_session='current',phase='formal',physical_gpu=1)
    with pytest.raises(ValueError,match='HAPI target'):
        health.submission_health({'findings':[]},current_session='current',target_session='historical')


def test_gpu_physical_uuid_inventory(monkeypatch):
    class Result:
        returncode=0;stderr=''
        def __init__(self,stdout):self.stdout=stdout
    calls=[]
    def query(command,**kwargs):
        calls.append(command)
        return Result('0, GPU-zero, device zero\n1, GPU-one, device one\n' if '--query-gpu=index,uuid,name' in command
            else '7, GPU-one, trainer, 1024\n')
    monkeypatch.setattr(health.subprocess,'run',query)
    result=health.gpu_snapshot()
    assert result['devices'][1]['uuid']=='GPU-one'
    assert result['compute_processes'][0]['pid']==7
    assert len(calls)==2


def test_handshake_marks_unknown_never_started(tmp_path,monkeypatch):
    spec=tmp_path/'spec.json';spec.write_text('{}')
    manifest={'spec_sha256':health.digest(spec),'attempt_id':'a','pid':7,'process_started_unix_s':10.}
    progress={'attempt_id':'a','status':'RUNNING','actual_updates':1}
    write_json(tmp_path/'manifest.json',manifest);write_json(tmp_path/'progress.json',progress)
    message={'status':'RUNNING','attempt_id':'a','output_dir':str(tmp_path),'trainer_pid':7}
    monkeypatch.setattr(submission,'process_identity',lambda *args,**kwargs:{'status':'OK'})
    result=submission.validate_handshake(message,spec_path=spec,output=tmp_path,
        attempt_id='a',monitor_pid=8,monitor_started_unix_s=10.)
    assert result['started'] and result['identity_verified']
    progress['actual_updates']=0;write_json(tmp_path/'progress.json',progress)
    result=submission.validate_handshake(message,spec_path=spec,output=tmp_path,
        attempt_id='a',monitor_pid=8,monitor_started_unix_s=10.)
    assert result['status']=='UNKNOWN' and not result['started'] and not result['identity_verified']


def test_supervisor_launch_blocks_health_before_any_child(tmp_path,monkeypatch):
    import sys
    spec=tmp_path/'spec.json';spec.write_text('{}')
    monkeypatch.setattr(sys,'argv',['supervisor','--spec',str(spec),'--output-dir',str(tmp_path/'new'),
        '--launch','--physical-gpu','1','--hapi-session','current'])
    monkeypatch.setenv('HAPI_SESSION_ID','current')
    monkeypatch.setattr(supervisor,'check',lambda *args:{'status':'PASS'})
    monkeypatch.setattr(supervisor,'inspect_project',lambda *args,**kwargs:{'findings':[
        {'reason_code':'IDENTITY_ERROR','detail':'fixture conflict'}]})
    with pytest.raises(ValueError,match='health prerequisite'):
        supervisor.main()
    assert not (tmp_path/'new').exists()


def test_supervisor_default_plan_does_not_request_processes_or_write(tmp_path,monkeypatch,capsys):
    import sys
    spec=tmp_path/'spec.json';spec.write_text('{}')
    monkeypatch.setattr(sys,'argv',['supervisor','--spec',str(spec),'--output-dir',str(tmp_path/'new')])
    monkeypatch.setattr(supervisor,'check',lambda *args:{'status':'PASS'})
    def inspect(*args,**kwargs):
        assert kwargs['include_processes'] is False
        return {'findings':[]}
    monkeypatch.setattr(supervisor,'inspect_project',inspect)
    supervisor.main()
    report=json.loads(capsys.readouterr().out)
    assert report['files_written']==0 and not (tmp_path/'new').exists()
