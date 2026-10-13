FROZEN_TEST_SCOPE='PORTABLE'
import json
from pathlib import Path
import pytest
from native_stand.command_v6.domain.trace_schema import STATE,WIDTHS
from native_stand.command_v6.domain.recovery_events import analyze,coverage_from_metrics
from native_stand.command_v6.tools.test_resources import source_file,project_file,scope
from native_stand.recovery.sampling import allocation_plan,coverage


def config():
    return {'active_family':'Swing','sampling':{'version':'fixed_environment_families_v1',
        'family_weights':{'Swing':.5,'Old':.5},'environment_counts':{'Swing':2,'Old':2}},
        'assessment':{'families':['Swing','Old'],'retained_families':['Old']}}


def row(n,entry=None):
    s=[[0.]*WIDTHS['state'] for _ in range(n)];p=[[0.]*WIDTHS['posture'] for _ in range(n)];c=[[0.]*WIDTHS['control'] for _ in range(n)]
    for i,r in enumerate(s):
        r[STATE['recovery_clock_s']]=max(0,(i-1)*.01);r[STATE['initial_valid']]=1
        r[STATE['previous_mode']]=7 if i<2 else 0;r[STATE['height_m']]=.35
        r[STATE['left_contact_n']]=r[STATE['right_contact_n']]=3
    return {'env_id':0,'compact_trace_100hz':s,'posture_trace_100hz':p,'control_diagnostics_100hz':c,
        'entry_confirmation_index':entry,'recovery_s':None if entry is None else (entry-1)*.01,
        'success':False,'standing_failed_checks':['contact'],'termination_reason':['task_failure']}


def test_fixed_quota_preflight_plan_and_env_mapping():
    plan=allocation_plan(config(),4)
    assert [r['family'] for r in plan['environment_to_family']]==['Swing','Swing','Old','Old']
    with pytest.raises(ValueError,match='PPO'):allocation_plan(config(),5)
    c=config();c['sampling']={'version':'family_weights_v1','family_weights':{'Swing':.5,'Old':.5}}
    assert allocation_plan(c,4)['environment_to_family'] is None


def test_counts_have_separate_denominators_and_missing_stays_unknown():
    plan=allocation_plan(config(),4)
    init=[{'family':'Swing','attempted':98},{'family':'Old','attempted':2}]
    phases=[{'family':'Swing','phase':'pre_entry','transition_count':10},
        {'family':'Old','phase':'hold_5_10','transition_count':90}]
    d=coverage(plan,init,phases);s=next(r for r in d['families'] if r['family']=='Swing')
    assert s['declared_slots']==2 and s['initialization_fraction']==.98 and s['valid_transition_fraction']==.1
    assert coverage(plan,None,None)['families'][0]['initialization_fraction'] is None


def test_event_window_categories_and_clock_components():
    kwargs={'dt':.01,'hold_s':.1,'wheel_scale':100}
    assert analyze(row(6),**kwargs)['task_window_category']=='NOT_ENTERED'
    r=analyze(row(8,4),**kwargs)
    assert r['task_window_category']=='EARLY_END_OR_PARTIAL_HOLD'
    assert r['time_scope']['initialization_observed_s']==.02
    assert r['time_scope']['post_entry_hold_observed_s']==.03
    assert analyze(row(15,4),**kwargs)['task_window_category']=='COMPLETE_HOLD_WINDOW'
    incomplete=row(8);incomplete.pop('control_diagnostics_100hz')
    assert analyze(incomplete,**kwargs)['status']=='MISSING_EVIDENCE'
    bad=row(8);bad['compact_trace_100hz'][0].pop()
    with pytest.raises(ValueError):analyze(bad,**kwargs)


def test_training_episode_mean_not_confused_with_eval_recovery():
    m=[{'task_metrics':{'family_phase_coverage':[{'family':'Swing','phase':'pre_entry','transition_count':10}],
        'episodes_by_pose':[{'family':'Swing','completed':2,'mean_duration_s':.71}]}}]
    d=coverage_from_metrics(m,allocation_plan(config(),4))
    assert d['training_episode_summary']['Swing']['mean_completed_episode_s']==.71
    assert d['initialization_attempts_total'] is None


def test_imported_source_location_and_scope(tmp_path):
    path=source_file('recovery/runtime.py');assert path.is_file()
    with pytest.raises(ValueError):source_file('../outside.py')
    p=tmp_path/'test.py';p.write_text('FROZEN_TEST_SCOPE="PROJECT_DATA"\n')
    assert scope(p)=='PROJECT_DATA'
    assert project_file('no_such_resource.json') is None


def test_actual_config_validation_calls_quota_check_without_preparer():
    # Actual config call site invoked in isolation, CPU fixture no historical files.
    import ast,copy
    tree=ast.parse(source_file('recovery/validation.py').read_text())
    fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_recovery')
    block=next(n for n in fun.body if isinstance(n,ast.Try) and any(isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)
        and isinstance(x.value.func,ast.Name) and x.value.func.id=='validate_sampling' for x in n.body))
    from native_stand.recovery.sampling import validate
    ns={'__name__':'native_stand.recovery.validation','__package__':'native_stand.recovery','config':config(),'spec':{'ppo':{'envs':5}},'errors':[],'validate_sampling':validate}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(block)],type_ignores=[])),str(source_file('recovery/validation.py')),'exec'),ns)
    assert any('PPO' in e for e in ns['errors'])


def test_registry_driven_review_handles_nonstandard_updates_and_missing_trace(tmp_path):
    from native_stand.command_v6.tools.review_recovery_events import review
    from native_stand.command_v6.tools.experiment_preparation import digest
    chain=tmp_path/'chain';formal=chain/'formal';(formal/'source_snapshot').mkdir(parents=True)
    (chain/'chain_terminal_report.json').write_text(json.dumps({'status':'COMPLETED'}))
    spec={'recovery':config(),'ppo':{'envs':4},'control':{'policy_dt_s':.01},
        'action':{'wheel_scale_rad_s':100},'asset_sha256':'a'*64}
    spec['recovery']['rising_task']={'post_rise_hold_s':.1}
    sp=formal/'source_snapshot/spec.json';sp.write_text(json.dumps(spec))
    (formal/'manifest.json').write_text(json.dumps({'asset_sha256':'a'*64,'spec_sha256':digest(sp)}))
    e=row(6);e.pop('control_diagnostics_100hz')
    data={'asset_sha256':'a'*64,'spec_sha256':digest(sp),'checkpoint_sha256':'b'*64,
        'evaluation_family':'Swing','per_env':[e]}
    path=formal/'custom_eval.json';path.write_text(json.dumps(data))
    (formal/'candidate_registry.json').write_text(json.dumps([{'update':17,'checkpoint_sha256':'b'*64,
        'evaluation':path.name,'evaluation_sha256':digest(path)}]))
    (formal/'metrics.jsonl').write_text('')
    r=review(chain)
    assert r['cases'][0]['update']==17 and r['cases'][0]['groups'][0]['rows'][0]['status']=='MISSING_EVIDENCE'
    with pytest.raises(ValueError,match='missing'):review(chain,updates=[25])
    assert not (chain/'review.json').exists()


def test_frozen_copy_rejects_unclassified_or_project_data_tests_before_write(tmp_path):
    from native_stand.command_v6.tools.validate_frozen_cpu import validate
    sp=tmp_path/'spec.json';sp.write_text('{}');output=tmp_path/'copy'
    plan=validate(sp,output,tests=['tests/test_recovery_sampling_contract.py'])
    assert plan['test_resource_scopes']['tests/test_recovery_sampling_contract.py']=='PROJECT_DATA'
    with pytest.raises(ValueError,match='PORTABLE'):validate(sp,output,tests=['tests/test_recovery_sampling_contract.py'],write=True)
    assert not output.exists()
