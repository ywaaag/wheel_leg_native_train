import torch
from native_stand.recovery.rising import score_rise


PROTOCOL = dict(seconds=22.,steady_window_s=[0.,22.],height_m=[.34,.38],
    height_fraction_min=.9,dual_contact_min=.95,level_mean_max_rad=.1,
    level_peak_max_rad=.15,peak_tilt_max_rad=.18,saturation_max=.05,
    closure_max_m=.005,objective='survival_level',initial_xy=[0.,0.],
    recovery_deadline_s=11.5,post_rise_hold_s=10.)


def trajectory(entry=3.):
    s=torch.zeros(2200,39);p=torch.zeros(2200,10)
    s[:,0]=torch.arange(1,2201)*.01
    s[:,6]=.2;s[round(entry*100):,6]=.36
    s[:,10:12]=3.;s[:,29]=1
    return s,p


def score(s,p,**kw):
    return score_rise(s,p,dt=.01,protocol=PROTOCOL,
        runtime_fault=kw.get('fault',False),initial_valid=kw.get('valid',True),
        terminated=kw.get('terminated',False))


def test_delayed_rise_scores_own_full_hold():
    s,p=trajectory();r=score(s,p)
    assert r['accepted'] and r['post_rise_window_s']==[3.,13.]
    assert r['metrics']['height_min_m']>.34


def test_late_entry_does_not_shorten_hold():
    s,p=trajectory(13.);r=score(s,p)
    assert not r['accepted'] and 'recovery_deadline' in r['failed_checks']


def test_transient_entry_cannot_restart_or_stitch_hold():
    s,p=trajectory();s[350:450,6]=.2
    assert 'continuous_height' in score(s,p)['failed_checks']


def test_early_termination_missing_initialization_and_fault_fail():
    s,p=trajectory()
    assert not score(s[:500],p[:500],terminated=True)['accepted']
    assert not score(s,p,valid=False)['accepted']
    assert not score(s,p,fault=True)['accepted']


def test_no_standing_entry_and_nonfinite_cannot_pass():
    s,p=trajectory();s[:,6]=.2
    assert not score(s,p)['accepted']
    s[1,6]=float('nan')
    assert not score(s,p)['accepted']


def test_prepared_rise_protocol_smoke_and_sampling_contract():
    import json
    from pathlib import Path
    from native_stand.command_v6.config import validate,evaluation_seconds
    from native_stand.command_v6.domain.execution_plan import smoke_plan
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    root=Path(__file__).resolve().parents[1]
    # Read-only prepared declaration, never its mutable ledger.
    s=json.loads((root/'configs/experiments/2026_10_7-15_51__recovery_rise_low_from50/spec.json').read_text())
    assert not validate(s)
    p=protocol_for_spec(s,23.)
    assert p['recovery_deadline_s']==11.5 and p['post_rise_hold_s']==10.
    assert p['window_alignment']=='first_eligible_standing_sample'
    assert smoke_plan(s)['budget_sufficient'] and evaluation_seconds(s,full=True)==23.
    assert s['recovery']['rising_task']['retained_fraction']==.4


def test_frozen_worker_receipt_rejects_tampering(tmp_path):
    import hashlib,json,pytest
    from native_stand.command_v6.tools.execution_identity import verify_frozen_root
    root=tmp_path/'source_snapshot/native_stand';root.mkdir(parents=True)
    (root/'a.py').write_text('value=1\n')
    spec={'execution_source_root':'/declared/src'}
    data=json.dumps(spec).encode();(root.parent/'spec.json').write_bytes(data)
    manifest={'spec_sha256':hashlib.sha256(data).hexdigest(),
        'declared_execution_source_root':'/declared/src',
        'execution_modules_sha256':{'a.py':hashlib.sha256((root/'a.py').read_bytes()).hexdigest()}}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    assert verify_frozen_root(root,'/declared/src',spec)['declared_source_root']=='/declared/src'
    (root/'a.py').write_text('value=2\n')
    with pytest.raises(ValueError,match='module identities'):verify_frozen_root(root,'/declared/src',spec)


def test_completed_episode_receipt_correction_preserves_history(tmp_path,complete_smoke_fixture):
    import copy,hashlib,json
    from native_stand.command_v6.wiring import smoke_certificate,completed_smoke
    from native_stand.command_v6.stand_chain import correct_smoke_receipt
    spec={'experiment':'old','source_sha256':'source','budget':{'smoke_updates':10},
        'ppo':{'envs':64,'steps_per_env':128},'control':{'policy_dt_s':.01},
        'wiring_smoke':{'required_event':'completed_episode','required_event_duration_s':2.,
                        'minimum_event_count':1,'event_offset_s':1.}}
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    folder=tmp_path/'smoke';complete_smoke_fixture(folder,path,10)
    (folder/'metrics.jsonl').write_text(json.dumps({'rollout':{'episodes':{
        'completed':550,'max_duration_s':2.18}}})+'\n')
    actual=smoke_certificate(folder,spec);assert actual['status']=='PASSED'
    prior={**actual,'status':'FAILED','errors':['smoke did not observe the required completed_episode']}
    original=folder/'wiring_certificate.json';original.write_text(json.dumps(prior))
    before=original.read_bytes();corrected=tmp_path/'corrected.json'
    correct_smoke_receipt(path,folder,corrected)
    assert original.read_bytes()==before
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    book={'attempts':{'old':{'phase':'smoke','status':'COMPLETED','output_dir':str(folder),
        'evidence_spec_path':str(path),'evidence_spec_sha256':digest(path),
        'evidence_certificate_path':str(corrected),'evidence_certificate_sha256':digest(corrected)}}}
    new=copy.deepcopy(spec);new['experiment']='new'
    assert completed_smoke(book,new)
    new['control']['policy_dt_s']=.02
    assert not completed_smoke(book,new)
    corrected.write_text('{}')
    assert not completed_smoke(book,spec)
