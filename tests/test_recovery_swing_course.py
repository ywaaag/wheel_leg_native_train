import pytest
from native_stand.recovery.rising import validate_rise
from native_stand.recovery.sampling import scoring_config
from native_stand.recovery.standing import pose_sampling,StandingRegression

def declaration():
    return {'version':'autonomous_rise_min_height_v2','recovery_deadline_s':11.5,
        'post_rise_hold_s':10.,'entry_dwell_s':.2,'minimum_height_m':.3,
        'sampling_version':'explicit_retained_pose_weights_v1',
        'retained_families':['drawback_manual0001','R0'],'retained_fraction':.6}

def test_curriculum_changes_sampling_not_protocol():
    d=declaration();pure=scoring_config(d);assert validate_rise(pure)==pure
    d['minimum_height_m']=.25
    with pytest.raises(ValueError):validate_rise(scoring_config(d))

@pytest.mark.parametrize('change',[{'retained_families':['drawback_manual0001']},
    {'retained_families':['R0','R0']},{'retained_fraction':.2},{'retained_fraction':float('nan')},
    {'sampling_version':'unknown'}])
def test_invalid_rehearsal_rejected(change):
    d=declaration();d.update(change)
    with pytest.raises(ValueError):validate_rise(scoring_config(d))

def test_family_mass_independent_of_pose_count_and_split():
    poses=[{'family':f,'split':split,'offline_valid':True,'sample_weight':w}
        for split in ('train','holdout') for f,n,w in [('swing',1,1.),('drawback',1,2.),('R0',4,.25)] for _ in range(n)]
    for split in ('train','holdout'):
        ids,w=pose_sampling(poses,'swing',split,retained_families=['drawback','R0'],retained_fraction=.6)
        mass={f:sum(v for i,v in zip(ids,w) if poses[i]['family']==f) for f in ('swing','drawback','R0')}
        assert mass==pytest.approx({'swing':.4,'drawback':.4,'R0':.2})

def test_unlearned_current_group_does_not_block_old_skill_guard():
    guard=StandingRegression(confirmed=True)
    assert not guard.observe(accepted=False,full=True,continuous_s=23.)
    assert not guard.observe(accepted=True,full=True,continuous_s=23.)
    assert not guard.observe(accepted=False,full=True,continuous_s=23.)
    assert guard.observe(accepted=False,full=True,continuous_s=23.)

def test_frozen_disabled_notifications_never_call_transport(tmp_path):
    import json
    from native_stand.command_v6.completion import notify,sha
    (tmp_path/'source_snapshot').mkdir()
    (tmp_path/'source_snapshot/spec.json').write_text(json.dumps({'notifications':{'enabled':False}}))
    (tmp_path/'completion_report.md').write_text('Completed report')
    (tmp_path/'report_ready.json').write_text(json.dumps({'event_id':'swing','report_sha256':sha(tmp_path/'completion_report.md')}))
    (tmp_path/'manifest.json').write_text(json.dumps({'hapi_session':'owner'}))
    def forbidden(*args):raise AssertionError('External delivery not authorized')
    assert notify(tmp_path,send=forbidden)['status']=='notification_disabled'
