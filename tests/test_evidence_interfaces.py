import json
import pytest
import torch
from native_stand.command_v6.domain.evidence import effective_protocol,resolve_gate,diagnostic_field,validate_effective_protocol
from native_stand.command_v6.domain.selected_diagnostics import selected,summarize_tensor
from native_stand.command_v6.tools.preflight import classify_errors
from native_stand.command_v6.wiring import smoke_certificate


@pytest.mark.parametrize('seconds,start',[(10,2),(100,2),(1,.5)])
def test_effective_protocol(seconds,start):
    kwargs=dict(requested_seconds=seconds,steady_window_s=[start,seconds],sample_rate_hz=100,
                scored_envs=8,termination_semantics='first episode')
    first=effective_protocol({},**kwargs)
    assert first==effective_protocol({},**kwargs)
    validate_effective_protocol(first)
    with pytest.raises(ValueError):effective_protocol({'unknown_protocol_field':True},**kwargs)
    assert first['actual_duration_seconds']==seconds
    assert first['metric_scope']['survival_metrics']=='full_episode'
    with pytest.raises(TypeError):effective_protocol({},unknown_field=True,**kwargs)
    with pytest.raises(ValueError):effective_protocol({},**{**kwargs,'steady_window_s':[0,seconds+1]})


def test_gate_status():
    assert resolve_gate({'status':'NOT_RUN'},'recovery')['status']=='NOT_RUN'
    assert resolve_gate({},'recovery')['status']=='MISSING_EVIDENCE'
    result={'recovery_gate':{'accepted':True,'passed_envs':8,'per_env':[{'failed_checks':[]}]*8}}
    assert resolve_gate(result,'recovery',expected_envs=8)['status']=='PASSED'
    assert resolve_gate(result,'recovery',expected_envs=7)['status']=='CONFLICTING_EVIDENCE'
    result['recovery_gate']['accepted']=False
    result['recovery_gate']['passed_envs']=0
    result['recovery_gate']['per_env']=[{'failed_checks':['continuous']}]*8
    assert resolve_gate(result,'recovery')['status']=='FAILED'


def test_diagnostic_zero_not_missing():
    assert diagnostic_field(0.,requested=True,enabled=True,sample_count=1)['valid']
    missing=diagnostic_field(0.,requested=True,enabled=False)
    assert missing['value'] is None and missing['missing_reason']=='runtime_not_enabled'
    assert not selected({},1)
    assert selected({'diagnostics':{'enabled':True,'record_updates':[2]}},2)
    assert summarize_tensor(torch.tensor([0.,1.,2.]))['mean']==1


@pytest.mark.parametrize('errors,code',[([], 'OK'),(['phase budget exhausted'],'BUDGET_EXHAUSTED'),
    (['new simulation/PPO budget has not been authorized'],'AUTHORIZATION_MISSING'),
    (['source SHA differs'],'IDENTITY_ERROR'),(['budget already occupied'],'UNSETTLED_ATTEMPT'),
    (['preceding phase has not completed'],'MISSING_EVIDENCE'),(['bad config'],'CONFIG_ERROR'),
    (['process identity mismatch'],'PROCESS_IDENTITY_MISMATCH'),(['behavior gate failed'],'BEHAVIOR_GATE_FAILED')])
def test_preflight_reasons(errors,code):assert classify_errors(errors)[0]==code


def test_smoke_not_fixed_filename_or_ten_updates(tmp_path):
    records={'progress.json':{'actual_updates':3,'actor_parameters_changed':True,
        'evaluations':[{'cases':[{'path':'evaluation_3_0_0.json'}]}]},
        'terminal_report.json':{'status':'COMPLETED','actual_updates':3},
        'manifest.json':{'source_sha256':'source'},
        'evaluation_3_0_0.json':{'per_env':[{}],'outcome_counts':{'runtime_fault':0}}}
    for name,value in records.items():(tmp_path/name).write_text(json.dumps(value))
    spec={'source_sha256':'source','budget':{'smoke_updates':3}}
    (tmp_path/'source_snapshot').mkdir()
    (tmp_path/'source_snapshot/spec.json').write_text(json.dumps(spec))
    import hashlib
    records['manifest.json']['spec_sha256']=hashlib.sha256((tmp_path/'source_snapshot/spec.json').read_bytes()).hexdigest()
    (tmp_path/'manifest.json').write_text(json.dumps(records['manifest.json']))
    assert smoke_certificate(tmp_path,{'source_sha256':'source','budget':{'smoke_updates':3}})['status']=='PASSED'
    records['terminal_report.json']['actual_updates']=2
    (tmp_path/'terminal_report.json').write_text(json.dumps(records['terminal_report.json']))
    assert smoke_certificate(tmp_path,{'source_sha256':'source','budget':{'smoke_updates':3}})['status']=='FAILED'


def test_formal_requires_persisted_certificate_and_rejects_stale_evidence(tmp_path,complete_smoke_fixture):
    from native_stand.command_v6.wiring import completed_smoke
    spec_path=tmp_path/'spec.json';spec={'source_sha256':'source','budget':{'smoke_updates':3}}
    spec_path.write_text(json.dumps(spec));folder=tmp_path/'smoke';folder.mkdir()
    complete_smoke_fixture(folder,spec_path,3)
    book={'attempts':{'s':{'phase':'smoke','status':'COMPLETED','output_dir':str(folder)}}}
    assert completed_smoke(book,spec)
    certificate=(folder/'wiring_certificate.json').read_bytes()
    (folder/'wiring_certificate.json').unlink()
    assert not completed_smoke(book,spec)
    (folder/'wiring_certificate.json').write_bytes(certificate)
    (folder/'evaluation_fixture.json').write_text('{}')
    assert not completed_smoke(book,spec)


@pytest.mark.parametrize('seconds', [1.,10.,100.])
def test_recovery_cpu_runtime_diagnostics_and_timing(seconds):
    from types import SimpleNamespace
    from native_stand.recovery.recipe import evaluate_actor
    class Env:
        device='cpu';num_envs=8;step_dt=.01;family='R0';split='train'
        curriculum_training=True;continuous_evaluation=False;reverse_curriculum=None
        recovery_config={'gate_diagnostics':False,'stand_sha256':'fixture','runtime_initialization_validated':True}
        fsm=SimpleNamespace(config={'timeout_s':120.,'verify_s':2.,'success_mode':'autonomous_hold'})
        pose_library={'poses':[{'family':'R0','seed':104,'pose_id':'fixture'}]}
        terminal_causes={name:torch.zeros(8,dtype=torch.bool) for name in
                         ('nonfinite','closure','height','tilt','body_contact','joint_safety')}
        gate_diagnostic_names=tuple('fixture_'+str(i) for i in range(11))
        episode_origin=torch.zeros(8,2)
        recovery_snapshot=torch.zeros(8,39)
        recovery_control_snapshot=torch.zeros(8,54)
        recovery_cause_snapshot=torch.zeros(8,6,dtype=torch.bool)
        gate_diagnostic_snapshot=torch.zeros(8,20)
        def reset(self):
            self.age=0
            self.recovery_snapshot[:,29]=1
            self.recovery_snapshot[:,6]=.36
            return torch.zeros(8,150),{}
        def select_initial_family(self,family,split):self.family,self.split=family,split
        def initialization_summary(self):return {'fixture':True}
        def step(self,action):
            self.age+=1
            self.recovery_snapshot[:,0]=self.age*self.step_dt
            if self.recovery_config['gate_diagnostics']:self.gate_diagnostic_snapshot.fill_(7)
            return torch.zeros(8,150),None,torch.zeros(8,dtype=torch.bool),None,None
    env=Env()
    result=evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=seconds,seed=104,diagnostics=True)
    assert result['effective_protocol']['steady_window_s']==[.5,seconds]
    assert result['effective_protocol']['actual_duration_seconds']==seconds
    assert result['per_env'][0]['gate_diagnostics_100hz'][-1][0]==7
    assert result['diagnostics_validity']['gate_diagnostics_100hz']['valid']
    assert env.recovery_config['gate_diagnostics'] is False
    with pytest.raises(TypeError):evaluate_actor(None,None,env,seconds=seconds,seed=104,typo=True)


def test_gradient_capture_does_not_change_update():
    import copy
    from native_stand.command_v6.domain.selected_diagnostics import GradientSummary
    torch.manual_seed(7)
    actor=torch.nn.Linear(3,6);critic=torch.nn.Linear(3,1)
    other=copy.deepcopy(actor)
    x=torch.randn(4,3)
    optimizer=torch.optim.SGD(actor.parameters(),lr=.01)
    observer=GradientSummary(actor,critic,optimizer)
    actor(x).square().mean().backward();optimizer.step();observer.close()
    comparison=torch.optim.SGD(other.parameters(),lr=.01)
    other(x).square().mean().backward();comparison.step()
    for a,b in zip(actor.parameters(),other.parameters()):torch.testing.assert_close(a,b,rtol=0,atol=0)
    assert observer.summary()['actor']>0
    assert observer.summary()['critic'] is None


def test_readonly_health_and_corrected_output(tmp_path):
    from native_stand.command_v6.tools.health_check import inspect_project,process_identity
    from native_stand.command_v6.tools.correct_evidence import audit_run
    project=tmp_path/'project';project.mkdir()
    for name in ('README.md','STATUS.md','TOOL_INDEX.md'):(project/name).write_text('[missing](absent.json)')
    before={p.name:p.read_bytes() for p in project.iterdir()}
    report=inspect_project(project)
    assert report['files_written']==0 and report['findings'][0]['reason_code']=='MISSING_EVIDENCE'
    assert before=={p.name:p.read_bytes() for p in project.iterdir()}
    assert process_identity(None,output_dir=project,attempt_id='absent')['status']=='MISSING_EVIDENCE'
    output=tmp_path/'corrected'
    audit_run(project,output)
    with pytest.raises(FileExistsError):audit_run(project,output)
    assert before=={p.name:p.read_bytes() for p in project.iterdir()}


@pytest.mark.parametrize('cause,timeout,steps,expected',[(None,False,100,'completed'),
    (None,True,100,'completed'),(None,True,20,'UNKNOWN'),('tilt',False,20,'task_failure'),
    ('closure',False,20,'runtime_fault'),(None,False,20,'UNKNOWN')])
def test_termination_and_effective_metric_scope(cause,timeout,steps,expected):
    from native_stand.command_v6.domain.protocol import score,FIELDS,CAUSES
    rows=torch.zeros(steps,1,len(FIELDS));rows[:,:,2]=.4
    rows[:min(20,steps),:,3]=10
    valid=torch.ones(steps,1,dtype=torch.bool)
    done=torch.zeros_like(valid)
    if cause or timeout:done[-1]=True
    causes=torch.zeros(1,len(CAUSES),dtype=torch.bool)
    if cause:causes[0,CAUSES.index(cause)]=True
    protocol=effective_protocol({},requested_seconds=1.,steady_window_s=[.5,.8],
        parking_window_s=[.9,1.],sample_rate_hz=100,scored_envs=1,termination_semantics='fixture')
    result=score(rows,valid,done,causes,torch.tensor([timeout]),dt=.01,
        target_window=protocol['steady_window_s'],requested_steps=100,effective_protocol=protocol)
    row=result['per_env'][0]
    assert row['outcome']==expected
    if steps==100:
        assert row['height_steady_mean_m']==pytest.approx(.4)
        assert row['mean_abs_vx_mps']==0 and row['stop_vx_abs_mps']==0


def test_handshake_unknown_without_identity(tmp_path):
    from native_stand.command_v6.submission import validate_handshake
    result=validate_handshake({'status':'RUNNING'},spec_path=tmp_path/'spec.json',
        output=tmp_path,attempt_id='fixture',monitor_pid=None)
    assert result['status']=='UNKNOWN'


def test_cli_effective_durability_uses_recovery_thresholds():
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    spec={'task':'recovery','control':{'policy_dt_s':.01},
        'evaluation':{'scored_envs':8,'durability_seconds':100},
        'recovery':{'standing_task':{'protocol':{'seconds':10,'steady_window_s':[2,10],'level_mean_max_rad':.1}}}}
    result=protocol_for_spec(spec,100,True)
    assert result['steady_window_s']==[2,100] and result['level_mean_max_rad']==.1
    assert result['diagnostics']['enabled']
