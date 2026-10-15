import json
from pathlib import Path
import pytest
from native_stand.command_v6.domain.time_axis import interval,event,sustained_events
from native_stand.command_v6.domain.diagnostic_profiles import storage_plan
from native_stand.command_v6.tools.audit_terminal import audit
from native_stand.command_v6.tools.validate_cpu import validate


def test_clocks_half_open_poststep_and_unknown_initialization():
    row=interval(20,1020,dt=.01,total_samples=1020)
    assert row['duration_s']==10 and row['boundary_seconds']==pytest.approx([.2,10.2])
    assert row['first_post_step_seconds']==.21
    assert event(20,dt=.01,recovery_seconds=.1)['initialization_duration_s'] is None
    assert [e['duration_s'] for e in sustained_events([False,True,True,False,True],dt=.01)]==[.02,.01]
    with pytest.raises(ValueError):interval(0,4,dt=.01,total_samples=3)


def test_one_storage_plan_profiles_and_legacy():
    spec={'control':{'policy_dt_s':.01},'evaluation':{'full_trace_updates':[25]}}
    assert storage_plan(spec,update=25,full=True)['full_trace']
    assert not storage_plan(spec,update=50,full=True)['full_trace']
    explicit=storage_plan(spec,request={'diagnostic_profile':'full_transition'},full=True)
    assert explicit['full_trace'] and explicit['diagnostics']
    with pytest.raises(ValueError):storage_plan(spec,update=25,full=True,request={'diagnostic_profile':'summary'})
    spec['task']='recovery';spec['recovery']={'rising_task':{'version':'autonomous_rise_min_height_v2'}}
    assert storage_plan(spec,update=50,full=True)['runtime_kwargs']['diagnostic_profile']=='full_transition'


def test_terminal_audit_counts_events_and_missing_not_zero(tmp_path):
    run=tmp_path/'run';run.mkdir();ledger=tmp_path/'budget.json'
    for name,data in [('manifest.json',{'attempt_id':'a','phase':'smoke'}),
                      ('terminal_report.json',{'status':'FAILED','actual_updates':9}),
                      ('progress.json',{'actual_updates':8})]:
        (run/name).write_text(json.dumps(data))
    ledger.write_text(json.dumps({'limits':{'smoke':10},'attempts':{'a':{'updates':10,'status':'FAILED'}}}))
    trace=[[0.]*39 for _ in range(4)];trace[0][10:12]=[3,3];trace[3][10:12]=[3,3]
    (run/'evaluation_source.json').write_text(json.dumps({'per_env':[{'env_id':0,'compact_trace_100hz':trace}]}))
    before=ledger.read_bytes();result=audit(run,ledger)
    assert result['updates']['actual_completed']==9 and not result['updates']['counts_match']
    assert result['updates']['reserved_phase_limit']==10
    assert result['evaluations'][0]['per_env'][0]['contact_loss_longest_s']==.02
    assert result['evaluations'][0]['per_env'][0]['torque_limit_channels_policy_rate'] is None
    assert ledger.read_bytes()==before
    from native_stand.command_v6.tools.summarize_run import summarize
    assert summarize(run,ledger)['update_accounting']==result['updates']
    assert result['updates']['settled_updates']==10
    assert result['updates']['reserved_attempt_updates'] is None


def test_frozen_validation_default_no_copy_or_runtime(tmp_path):
    spec=tmp_path/'spec.json';spec.write_text('{}');out=tmp_path/'copy'
    result=validate(spec,out)
    assert result['files_written']==0 and not result['validation_executed'] and not out.exists()
    assert result['simulation']==0
    with pytest.raises(ValueError):validate(spec,out,['scripts/train.py'])


def test_effective_recovery_inventory_covers_every_declared_leaf():
    from native_stand.recovery.effective import disclose
    spec={'control':{'height_command_m':.36},'reward':{'lift':2.,'upright':1.},
        'recovery':{'rising_task':{'version':'autonomous_rise_min_height_v2','recovery_deadline_s':11.5,'post_rise_hold_s':10.},
            'fsm':{'timeout_s':11.5},'standing_task':{'protocol':{'height_m':[.34,.38]}},'initialization':{'settle_max_s':1.}}}
    d=disclose(spec);rows={r['field']:r for r in d['complete_field_inventory']}
    assert 'recovery.initialization.settle_max_s' in rows
    assert rows['recovery.standing_task.protocol.height_m']['status']=='TASK_PROTOCOL_OVERRIDE'
    assert rows['recovery.standing_task.protocol.height_m']['effective'] is None
    assert rows['recovery.fsm.timeout_s']['status']=='LEGACY_COMPATIBILITY_NOT_TASK_CERTIFICATE'
    assert not d['changes_to_recipe']


def test_actual_training_storage_calls_share_plan():
    import ast
    path=Path(__file__).resolve().parents[1]/'src/native_stand/command_v6/train.py'
    nodes=[n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name) and n.func.id=='storage_plan']
    assert len(nodes)>=4
