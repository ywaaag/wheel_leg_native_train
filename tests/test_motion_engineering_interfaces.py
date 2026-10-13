import copy,json
from pathlib import Path
import pytest
from native_stand.command_v6.domain.evaluation_config import identities
from native_stand.command_v6.domain.time_axis import window_indices
from native_stand.command_v6.domain.gui_device import resolve as gui
from native_stand.command_v6.domain.command_sampling import resolve as sampling
from native_stand.command_v6.tools.compare_motion import compare
from native_stand.command_v6.tools.experiment_preparation import digest


def test_scoring_identity_ignores_metadata_preserves_thresholds():
    a={'requested_seconds':30,'motion_window_s':[10,18],'seed':104,'scored_envs':8,'vx_error_max_mps':.3,
        'full_every_updates':25,'motion_commands':[[.5,0]],'diagnostics':{'enabled':True}}
    b={**a,'full_every_updates':50,'motion_commands':[[1,0]],'diagnostics':{'enabled':False}}
    assert identities(a)['scoring_sha256']==identities(b)['scoring_sha256']
    assert identities(a)['schedule_sha256']!=identities(b)['schedule_sha256']
    assert identities(a)['storage_sha256']!=identities(b)['storage_sha256']
    assert identities(a)['scoring_sha256']!=identities({**b,'motion_window_s':[10,17]})['scoring_sha256']
    assert identities(a)['scoring_sha256']!=identities({**b,'vx_error_max_mps':.4})['scoring_sha256']


def test_windows_version_and_early_end():
    p=window_indices(3000,dt=.01,window_s=[10,18])
    assert p['index_half_open']==[999,1800] and p['required_samples']==801
    assert not window_indices(1030,dt=.01,window_s=[10,18])['complete']
    assert window_indices(3000,dt=.01,window_s=[26,30])['index_half_open']==[2599,3000]
    with pytest.raises(ValueError):window_indices(3000,dt=.01,window_s=[10,18],version='unknown')


def test_sampling_and_gui_semantics():
    stage={'commands':[[0,0],[.5,0]],'weights':[.25,.75]}
    assert sampling(stage,64)['mode']=='categorical_weights'
    assert sampling(stage,64)['nominal_expected_reset_allocations']==[16,48]
    with pytest.raises(ValueError):sampling({**stage,'sampling_mode':'fixed_slots'},64)
    with pytest.raises(ValueError):sampling({**stage,'sampling_mode':'categorical_weights','sampling_slots':[0]*64},64)
    for gpu in (0,1):assert gui(gpu,str(gpu))['app_options']['device']=='cuda:0'
    with pytest.raises(ValueError):gui(1,'0')


def fixture(tmp_path):
    cp=tmp_path/'model.pt';cp.write_bytes(b'fixture identity only')
    request={'models':[]}
    for name in ('source','candidate'):
        folder=tmp_path/name;folder.mkdir();manifest={'asset_sha256':'a'*64,'spec_sha256':'b'*64}
        (folder/'manifest.json').write_text(json.dumps(manifest));items=[]
        for target in (0,.5,-.5):
            rows=[]
            for env in range(2):
                vx=target*.9;trace=[[.01*(i+1),0,.4,vx,0,0,0,0] for i in range(3000)]
                rows.append({'env_id':env,'continuous_s':30,'trace':trace,'termination_reason':[]})
            data={**manifest,'checkpoint_sha256':digest(cp),'target':[target,0],'dt':.01,
                'per_env':rows,'capability_gate':{'per_env':[{'env_id':i,'failed_checks':[]} for i in range(2)]},
                'effective_protocol':{'requested_seconds':30,'scored_envs':2,'steady_window_s':[2,30],
                'motion_window_s':[10,18],'seed':104,'sample_rate_hz':100,'vx_error_max_mps':.3,'full_every_updates':25 if name=='source' else 50}}
            path=folder/(str(target)+'.json');path.write_text(json.dumps(data));items.append({'path':str(path),'sha256':digest(path)})
        request['models'].append({'name':name,'checkpoint':str(cp),'checkpoint_sha256':digest(cp),'evaluations':items})
    return request


def test_explicit_models_compare_and_partial_gain_is_missing(tmp_path):
    r=fixture(tmp_path);answer=compare(r)
    assert answer['models']['source']['pairs']['0:0.5']['gain']==pytest.approx(.9)
    item=r['models'][1]['evaluations'][1];path=Path(item['path']);data=json.loads(path.read_text())
    data['per_env'][0].update(continuous_s=10.3,trace=data['per_env'][0]['trace'][:1030],termination_reason=['joint_safety'])
    path.write_text(json.dumps(data));item['sha256']=digest(path)
    answer=compare(r);p=answer['models']['candidate']['pairs']['0:0.5']
    assert p['gain'] is None and p['scope']=='MISSING_OR_PARTIAL'
    assert any(not c['complete'] for c in answer['models']['candidate']['commands'].values())
    item['sha256']='0'*64
    with pytest.raises(ValueError,match='SHA'):compare(r)


def test_submission_summary_source_handshake_does_not_imply_formal(tmp_path):
    from native_stand.command_v6.tools.submission_summary import summarize
    s=tmp_path/'spec.json';s.write_text(json.dumps({'source_sha256':'a'*64,'budget':{'formal_updates':50},
        'curriculum':{'active_stage':1},'authorization':{'hapi_session':'owner'}}))
    r=tmp_path/'receipt.json';r.write_text(json.dumps({'spec_sha256':digest(s)}))
    h=tmp_path/'handshake.json';h.write_text(json.dumps({'status':'SUBMITTED','run_state':'SOURCE_EVAL'}))
    assert summarize(s,r,h)['formal_first_update_verified'] is False
    r.write_text(json.dumps({'spec_sha256':'0'*64}))
    with pytest.raises(ValueError):summarize(s,r,h)


def test_online_summary_and_gate_use_same_float64_window():
    import torch
    from native_stand.command_v6.domain.protocol import score,FIELDS
    n=3000;rows=torch.zeros(n,1,len(FIELDS));rows[:,0,2]=.4
    rows[:,0,3]=.5;rows[999,0,3]=1.5;rows[:,0,6]=.5
    valid=torch.ones(n,1,dtype=torch.bool);done=torch.zeros_like(valid)
    causes=torch.zeros(1,6,dtype=torch.bool);timeout=torch.zeros(1,dtype=torch.bool)
    r=score(rows,valid,done,causes,timeout,dt=.01,target_window=(10,18),requested_steps=n,
        full_trace=True,effective_protocol={'steady_window_s':[10,18]})
    row=r['per_env'][0]
    assert row['window_time_axis']['observed_samples']==801
    assert row['mean_abs_vx_error_mps']==pytest.approx(1/801)


def test_thin_keyboard_script_does_not_define_independent_defaults():
    import ast
    path=Path(__file__).resolve().parents[1]/'scripts/play_motion_keyboard.py'
    tree=ast.parse(path.read_text())
    assert not any(isinstance(n,ast.Attribute) and n.attr in ('add_argument','execve') for n in ast.walk(tree))


def test_preparer_uses_categorical_semantics_and_effective_budget_text(inputs):
    from test_motion_preparer import call
    _,_,request,_=inputs
    request.write_text(json.dumps({'mode':'course','retained_commands':[[0,0],[.5,0],[-.5,0]],
        'current_commands':[[1,0],[-1,0]],'weights':[.25,.125,.125,.25,.25],
        'online_updates':51,'smoke_updates':1,'full_every_updates':25,
        'wall_s':{'source_eval':600,'smoke':300,'formal':1200}}))
    result=call(inputs)
    assert result['spec']['curriculum']['stages'][1]['sampling_mode']=='categorical_weights'
    assert '50 updates' in result['spec']['curriculum']['task_progression']['blocked_reason']
    assert result['preparation_manifest']['sampling_plan'][1]['counts_scope'].startswith('command allocations')

# Fixture returns temporary files, never an active budget.
from test_motion_preparer import inputs


def test_zero_oscillation_does_not_cancel_mean_absolute(tmp_path):
    r=fixture(tmp_path);item=r['models'][0]['evaluations'][0];path=Path(item['path'])
    data=json.loads(path.read_text())
    for row in data['per_env']:
        for i,sample in enumerate(row['trace']):sample[3]=.6 if i%2 else -.6
    path.write_text(json.dumps(data));item['sha256']=digest(path)
    answer=compare(r)
    zero=next(c for c in answer['models']['source']['commands'].values() if c['target']==[0,0])
    assert all(row['window_metrics']['mean_absolute']==pytest.approx(.6) for row in zero['per_env'])
    assert all(abs(row['window_metrics']['mean'])<.001 for row in zero['per_env'])
