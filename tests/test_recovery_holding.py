import importlib.util
import json
from pathlib import Path

import pytest
import torch

from native_stand.recovery.holding import HoldingEpisode
from native_stand.recovery.standing import score_standing
from test_recovery_standing_balance import perfect_trace

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'configs/experiments/recovery_survival_level_from50_20261006/spec.json'


@pytest.mark.parametrize('bad', [None,'mean_roll','peak_pitch','contact','height','saturation','tilt','closure','nonfinite'])
def test_streaming_window_matches_full_independent_gate(bad):
    spec = json.loads(PARENT.read_text())
    protocol = {**spec['recovery']['standing_task']['protocol'],'initial_xy':[0.,0.]}
    rows, posture = perfect_trace()
    if bad=='mean_roll': posture[:,1] = .13
    if bad=='peak_pitch': posture[50,0] = .16
    if bad=='contact': rows[300:500,10] = 0.
    if bad=='height': rows[300:500,6] = .30
    if bad=='saturation': rows[:100,17] = 1.
    if bad=='tilt': rows[500,15] = .19
    if bad=='closure': rows[500,12] = .006
    if bad=='nonfinite': posture[500,0] = torch.nan
    episode = HoldingEpisode(1,'cpu',dt=.01,protocol=protocol)
    yes = torch.ones(1,dtype=torch.bool); no = ~yes
    with torch.inference_mode():
        for index in range(1000):
            r, p = rows[index:index+1], posture[index:index+1]
            episode.observe(r[:,6],r[:,10:12],p[:,:2],r[:,15],r[:,12],r[:,17].bool(),active=yes,valid=yes)
            timeout, success = episode.outcome(failed=no,fault=no)
            if index<999:
                assert not timeout.any() and not success.any()
    expected = score_standing(rows,posture,dt=.01,requested_s=10.,protocol=protocol,
                             runtime_fault=False,initial_valid=True,terminated=False)
    assert timeout.all() and bool(success[0])==expected['accepted']
    assert bool(success[0])==(bad is None)
    # Ordinary updates/reset outside inference_mode must remain writable.
    episode.reset(torch.tensor([0]))
    assert episode.steps[0]==0


def test_fault_and_fall_override_deadline_and_partial_reset_is_local():
    p = json.loads(PARENT.read_text())['recovery']['standing_task']['protocol']
    e = HoldingEpisode(2,'cpu',dt=.01,protocol=p)
    e.steps[:] = 1000; e.count[:] = 801
    e.sums[:] = torch.tensor([.36,1.,1.,0.,0.])*801
    timeout, success = e.outcome(failed=torch.tensor([True,False]),fault=torch.tensor([False,True]))
    assert not timeout.any() and not success.any()
    e.reset(torch.tensor([0]))
    assert e.steps.tolist()==[0,1000]


def test_fresh_recipe_and_budget_preserve_source_physics(tmp_path):
    definition = importlib.util.spec_from_file_location('prepare_holding',ROOT/'scripts/prepare_recovery_hold.py')
    module = importlib.util.module_from_spec(definition); definition.loader.exec_module(module)
    output = tmp_path/'holding'
    spec = module.prepare(PARENT,output,session='test-session',authorize=False)
    old = json.loads(PARENT.read_text())
    for key in ('action','control','ground','ppo','source_sha256','asset_sha256'):
        assert spec[key]==old[key]
    assert spec['reward']['success_once']==0.
    assert spec['recovery']['curriculum']['max_enabled_stage']==0
    assert spec['budget']['formal_updates']==100 and spec['budget']['smoke_updates']==10
    assert json.loads((output/'budget.json').read_text())['authorization']=='UNAUTHORIZED'
    from native_stand.command_v6.config import schedule,validate
    assert validate(spec)==[]
    for update in (25,50,100):
        assert schedule(update,'formal',spec['evaluation'])['full']
    from native_stand.recovery.validation import validate_recovery
    spec['reward']['success_once']=10.
    assert any('Holding episode' in error for error in validate_recovery(spec))
    with pytest.raises(FileExistsError):module.prepare(PARENT,output,session='test-session')


def test_smoke_certificate_requires_real_horizon_evidence(tmp_path):
    from native_stand.command_v6.wiring import smoke_certificate
    spec=json.loads(PARENT.read_text())
    spec['recovery']['standing_task']['training_episode']={'mode':'fixed_horizon','seconds':10.}
    for name in ('progress.json','terminal_report.json','manifest.json'):
        (tmp_path/name).write_text('{}')
    (tmp_path/'source_snapshot').mkdir()
    (tmp_path/'source_snapshot/spec.json').write_text(json.dumps(spec))
    report=smoke_certificate(tmp_path,spec)
    assert 'required smoke event metrics missing or invalid' in report['errors']
    row={'task_metrics':{'training_episode':{'normal_timeouts':0}},
         'rollout':{'episodes':{'max_duration_s':2.}}}
    (tmp_path/'metrics.jsonl').write_text(json.dumps(row)+'\n')
    assert 'smoke did not observe the required normal_timeout' in smoke_certificate(tmp_path,spec)['errors']
    row['task_metrics']['training_episode']['normal_timeouts']=1
    row['rollout']['episodes']['max_duration_s']=10.
    (tmp_path/'metrics.jsonl').write_text(json.dumps(row)+'\n')
    assert not any('required smoke event' in error or 'required normal_timeout' in error or 'required-duration' in error
                   for error in smoke_certificate(tmp_path,spec)['errors'])


def test_remote_desktop_requires_explicit_shared_mode():
    from native_stand.command_v6.tools.health_check import submission_health
    report={'findings':[],'gpu':{'status':'OK','devices':[{'index':0,'uuid':'GPU-test'}],
        'compute_processes':[{'gpu_uuid':'GPU-test','process_name':'/usr/NX/bin/nxnode.bin'}]}}
    with pytest.raises(ValueError,match='occupied'):
        submission_health(report,current_session='current',target_session='current',physical_gpu=0)
    from native_stand.command_v6.domain.resource_policy import resolve_resources
    policy=resolve_resources({},mode='shared',sharing_authorization='user explicitly allows desktop and training sharing')
    review=submission_health(report,current_session='current',target_session='current',physical_gpu=0,resource_policy=policy)
    assert review['sharing_used'] and review['resource_policy']['authorization_note']
    report['gpu']['compute_processes'].append({'gpu_uuid':'GPU-test','process_name':'python'})
    with pytest.raises(ValueError,match='occupied'):
        submission_health(report,current_session='current',target_session='current',physical_gpu=0)
