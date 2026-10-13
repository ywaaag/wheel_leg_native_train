"""Actual resolver/evaluator/gate paths, no Isaac import."""
import copy
import json
from pathlib import Path
import torch
import pytest
from native_stand.command_v6.domain.recipe import resolve
from native_stand.command_v6.domain.protocol import score,capability_gate
from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
from native_stand.command_v6.domain.task_curriculum import TaskProgression

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def spec():
    return json.loads((ROOT/'configs/experiments/motion_recheck_20261007/spec.json').read_text())


def retained_batch_fixture(spec, tmp_path):
    """Exercise the real planner without depending on retired candidate runs."""
    candidate=copy.deepcopy(spec)
    for request in candidate['evaluation_requests']:
        request['checkpoint']=candidate['source_checkpoint']
        request['sha256']=candidate['source_sha256']
    path=tmp_path/'spec.json'
    path.write_text(json.dumps(candidate))
    (tmp_path/'budget.json').write_bytes((ROOT/'configs/experiments/motion_recheck_20261007/budget.json').read_bytes())
    return candidate,path


def trace(spec,target,error):
    protocol=protocol_for_spec(spec,30.,True)
    rows=torch.zeros(3000,8,18,dtype=torch.float64)
    rows[:,:,2]=.4;rows[:,:,8:10]=10.
    rows[:,:,3]=target-error if target>0 else target+error
    rows[:,:,6]=target
    valid=torch.ones(3000,8,dtype=torch.bool)
    report=score(rows,valid,torch.zeros_like(valid),torch.zeros(8,6,dtype=torch.bool),
        torch.zeros(8,dtype=torch.bool),dt=.01,target_window=(10.,18.),
        requested_steps=3000,full_trace=True,effective_protocol=protocol)
    report.update(seconds=30.,effective_protocol=protocol)
    return report,protocol


@pytest.mark.parametrize('target',[.5,-.5,4.,-4.])
@pytest.mark.parametrize('error,passed',[(.299,True),(.301,False)])
def test_absolute_boundaries(spec,target,error,passed):
    report,protocol=trace(spec,target,error)
    assert capability_gate(report,(target,0),protocol)['accepted'] is passed


def test_stationary_wrong_direction_missing(spec):
    report,protocol=trace(spec,.5,.5)
    assert not capability_gate(report,(.5,0),protocol)['accepted']
    report['per_env'][0].pop('saturation_fraction')
    assert 'MISSING_EVIDENCE:saturation_fraction' in capability_gate(report,(.5,0),protocol)['per_env'][0]['failed_checks']


def test_zero_mean_absolute_not_signed_cancellation(spec):
    report,protocol=trace(spec,0,0)
    for row in report['per_env']:
        for i,sample in enumerate(row['trace']):sample[3]=.6 if i%2 else -.6
        row['mean_abs_vx_mps']=.6;row['abs_mean_vx_mps']=0.
    assert not capability_gate(report,(0,0),protocol)['accepted']


def test_initial_width_and_conflicts(spec):
    effective,record=resolve(spec)
    assert effective['reward']['linear_error_denominator']==1.
    assert record['command_mode']=='ramp'
    for field,value in [('objective','per_command_adv_norm')]:
        wrong=copy.deepcopy(spec);wrong[field]=value
        with pytest.raises(ValueError):resolve(wrong)
    wrong=copy.deepcopy(spec);wrong['curriculum']['stages'][0]['command_mode']='fixed'
    with pytest.raises(ValueError):resolve(wrong)
    wrong=copy.deepcopy(spec);wrong['reward']['tracking_mode']='separate'
    with pytest.raises(ValueError):resolve(wrong)
    wrong=copy.deepcopy(spec);wrong['reward']['tracking_gap_weight']=1.
    with pytest.raises(ValueError,match='unsupported reward fields'):resolve(wrong)


def test_parking_actual_window(spec):
    report,protocol=trace(spec,1.,0)
    assert protocol['parking_window_s']==[26.,30.]
    assert report['per_env'][0]['stop_vx_abs_mps']==1.


def test_retention_failure_pass_failure():
    guard=TaskProgression({'initial_stage':1,'max_enabled_stage':2,'consecutive_confirmations':3,
        'standing_regression_confirmations':2,'blocked_reason':'test'})
    assert [guard.observe_zero(v) for v in [False,True,False]]==[1,0,1]
    assert guard.observe_zero(None)==2


def test_plan_actual_entry_no_writes(spec,tmp_path):
    from types import SimpleNamespace
    from native_stand.command_v6.tools.evaluate_checkpoint import batch_plan
    output=tmp_path/'absent'
    spec,path=retained_batch_fixture(spec,tmp_path)
    plan=batch_plan(SimpleNamespace(spec=path,
        output=output,attempt_id=None),spec)
    assert plan['preflight']['status']=='PASS'
    assert plan['effective_recipe']['reward']['tracking_mode']=='combined'
    assert not output.exists()


@pytest.mark.parametrize('exit_code,terminal,status',[(0,'COMPLETED','COMPLETED'),
    (1,'FAILED','FAILED'),(124,'STOPPED_BOUNDED','TERMINATED'),
    (0,None,'FAILED'),(124,None,'TERMINATED')])
def test_real_child_terminal_reconciliation(tmp_path,exit_code,terminal,status):
    import subprocess
    import sys
    import time
    from native_stand.command_v6.monitor import reconcile
    output=tmp_path/'run';output.mkdir()
    ledger=tmp_path/'budget.json'
    book={'authorization':'AUTHORIZED','limits':{'evaluate':1},'used':{'evaluate':0},
        'attempts':{'exact':{'phase':'evaluate','status':'RUNNING','updates':0,
            'output_dir':str(output.resolve()),'started_unix_s':time.time()}}}
    ledger.write_text(json.dumps(book))
    code='import json,sys; from pathlib import Path; p=Path(sys.argv[1]); '
    code+=("p.write_text(json.dumps({'status':sys.argv[2],'attempt_id':'exact','completed':['saved']})); " if terminal else '')
    code+='sys.exit(int(sys.argv[3]))'
    child=subprocess.run([sys.executable,'-c',code,str(output/'terminal_report.json'),terminal or '',str(exit_code)])
    result=reconcile(ledger,'exact',output,child.returncode)
    assert result['status']==status
    assert json.loads(ledger.read_text())['used']['evaluate']==1
    again=reconcile(ledger,'exact',output,child.returncode)
    assert not again['reconciled']
    assert json.loads(ledger.read_text())['used']['evaluate']==1


def test_selected_command_phase_counts():
    from types import SimpleNamespace
    from native_stand.command_v6.domain.selected_diagnostics import command_phase_summary
    storage=SimpleNamespace(values=torch.zeros(2,2,1),returns=torch.ones(2,2,1),advantages=torch.ones(2,2,1))
    targets=[torch.tensor([[0.,0.],[1.,0.]])]*2
    ages=[torch.tensor([0.,10.]),torch.tensor([12.,27.])]
    report=command_phase_summary(storage,targets,ages,[2.,8.,8.,8.],'global_rollout')
    assert sum(row['transition_count'] for row in report['groups'])==4
    assert report['normalization']=='global_rollout'


def test_real_schedule_zero_and_full_separate(spec):
    from native_stand.command_v6.config import schedule
    e={**spec['evaluation'],'full_every_updates':50,'zero_every_updates':25}
    assert schedule(25,'formal',e)['zero_only']
    assert not schedule(50,'formal',e)['zero_only']
    assert schedule(50,'formal',e)['full']


def test_course_white_list_and_no_one_direction_promotion():
    config={'initial_stage':2,'max_enabled_stage':15,'consecutive_confirmations':3,
        'standing_regression_confirmations':2,'blocked_reason':'test',
        'required_commands':[[0,0],[1.5,0],[-1.5,0]]}
    manager=TaskProgression(config)
    cases=[{'command':c,'gate':{'accepted':True}} for c in [[0,0],[1.5,0]]]
    for update in [50,100,150]:assert not manager.confirm(update,cases).get('promoted')
    cases.append({'command':[-1.5,0],'gate':{'accepted':True}})
    for update in [200,250]:assert not manager.confirm(update,cases).get('promoted')
    assert manager.confirm(300,cases)['next_stage']==3
    plan=json.loads((ROOT/'configs/experiments/motion_absolute_halfstep_PREPARED_20261007_v2/spec.json').read_text())
    assert all(c[1]==0 for c in plan['curriculum']['stages'][8]['commands'])
    assert max(abs(c[0]) for c in plan['curriculum']['stages'][3]['commands'])==1.5
    assert plan['curriculum']['stages'][9]['boundary']==[[0,.5],[0,-.5]]


def test_setup_cleanup_preserves_original_exception():
    from types import SimpleNamespace
    from native_stand.command_v6.tools.evaluation_state import isolated_evaluation
    class Env:
        cfg=SimpleNamespace(episode_length_s=31.)
        schedule_s=[1.,2.,24.,2.];capture_terminal=False;forced_target=(.5,0.)
        def clear_evaluation_target(self):raise RuntimeError('cleanup')
    @isolated_evaluation
    def evaluate(actor,wrapped,env):
        env.schedule_s=[2.,8.,8.,8.]
        raise ValueError('setup')
    actor=torch.nn.Linear(1,1).train();env=Env()
    before=torch.get_rng_state().clone()
    with pytest.raises(ValueError,match='setup') as captured:evaluate(actor,None,env)
    assert 'cleanup' in captured.value.__notes__[0]
    assert env.schedule_s==[1.,2.,24.,2.]
    assert actor.training and torch.equal(before,torch.get_rng_state())


def test_same_saved_trace_rescore_identical(spec):
    report,protocol=trace(spec,.5,.2)
    original=capability_gate(report,(.5,0),protocol)
    rows=torch.tensor([row['trace'] for row in report['per_env']],dtype=torch.float64).transpose(0,1)
    valid=torch.ones(rows.shape[:2],dtype=torch.bool)
    replay=score(rows,valid,torch.zeros_like(valid),torch.zeros(8,6,dtype=torch.bool),
        torch.zeros(8,dtype=torch.bool),dt=.01,target_window=(10.,18.),requested_steps=3000,
        full_trace=True,effective_protocol=protocol)
    replay['seconds']=30.
    assert capability_gate(replay,(.5,0),protocol)==original


def test_no_isaac_loaded_by_plan(spec,tmp_path):
    import sys
    from types import SimpleNamespace
    from native_stand.command_v6.tools.evaluate_checkpoint import batch_plan
    before={name for name in sys.modules if name.startswith(('isaaclab','isaacsim','agent_world'))}
    spec,path=retained_batch_fixture(spec,tmp_path)
    batch_plan(SimpleNamespace(spec=path,
        output=tmp_path/'absent',attempt_id=None),spec)
    assert {name for name in sys.modules if name.startswith(('isaaclab','isaacsim','agent_world'))}==before


def test_checkpoint_groups_never_splice(spec):
    from native_stand.command_v6.completion import choose_capability
    expected={'capability_commands':[[0,0],[.5,0],[-.5,0]],'scored_envs':8}
    rows=[]
    for i,command in enumerate(expected['capability_commands']):
        rows.append({'checkpoint_sha256':str(i),'role':'candidate','eligible':True,
            'accepted':True,'passed_envs':8,'command':command,'per_env':[],
            'gate':{'per_env':[]}})
    selection=choose_capability(rows,None,expected)
    assert selection['accepted_candidate'] is None
    assert selection['full_eligible_count']==0
