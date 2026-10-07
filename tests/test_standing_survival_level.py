import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from native_stand.command_v6.config import schedule, validate
from native_stand.command_v6.completion import choose
from native_stand.recovery.domain import autonomous_stable, ReverseRecoveryCurriculum, RecoveryFSM
from native_stand.recovery.standing import score_standing, standing_success_mask, pose_sampling
from test_recovery_standing_balance import perfect_trace, FakeStandingEnv

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'runs/standing_scissor_20261006/formal/model_update_50.pt'
PARENT = SOURCE.parent/'source_snapshot/spec.json'


@pytest.fixture
def recipe(tmp_path):
    definition = importlib.util.spec_from_file_location('prepare_level', ROOT/'scripts/prepare_standing_balance.py')
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    folder = tmp_path/'survival_level'
    module.prepare_survival_level(PARENT, SOURCE, folder)
    return json.loads((folder/'spec.json').read_text()), module, folder


def score(rows, d, spec, **overrides):
    return score_standing(rows, d, dt=.01, requested_s=10.,
        protocol={**spec['recovery']['standing_task']['protocol'], 'initial_xy':[0.,0.]},
        runtime_fault=overrides.get('runtime_fault',False), initial_valid=True,
        terminated=overrides.get('terminated',False))


def test_new_recipe_preserves_physics_and_source_and_new_budget(recipe):
    spec, _, folder = recipe
    old = json.loads(PARENT.read_text())
    assert validate(spec) == []
    for field in ('ground','control','action','termination','ppo','asset_sha256'):
        assert spec[field] == old[field]
    assert spec['source_update'] == 50 and spec['source_input_dim'] == 150
    assert spec['budget']['formal_updates'] + spec['budget']['smoke_updates'] == 10000
    assert spec['budget']['sample_limit'] == 81920000
    assert spec['budget']['formal_wall_s']+300+300+1200+60 == 36000
    assert json.loads((folder/'budget.json').read_text())['authorization'] == 'UNAUTHORIZED'
    with pytest.raises(FileExistsError):
        recipe[1].prepare_survival_level(PARENT, SOURCE, folder)


def test_frozen_source_strict_load_and_adam(recipe):
    from test_recovery_standing_balance import test_actual_source1500_strict_actor_critic_adam_and_learning_rate
    test_actual_source1500_strict_actor_critic_adam_and_learning_rate(recipe[0])


def test_motion_and_geometry_only_diagnostics(recipe):
    spec = recipe[0]
    rows, d = perfect_trace()
    rows[:,7:10] = torch.tensor([.8, .2, .5])
    rows[:,19] = torch.linspace(0., 8., 1000)
    d[:,4:6] = .8
    d[:,3] = .35
    d[:,0:2] = .07
    result = score(rows, d, spec)
    assert result['accepted'] and result['metrics']['net_drift_m'] == 8.
    assert not set(('vx','vy','yaw','excursion','mirror','leg_length','support_balance')) & result['checks'].keys()
    old = json.loads(PARENT.read_text())
    assert not score(rows,d,old)['accepted']


@pytest.mark.parametrize('bad', ['pitch','roll','height','contact','closure','saturation','fall','nonfinite'])
def test_retained_physical_and_level_gates(recipe, bad):
    rows, d = perfect_trace()
    args = {}
    if bad in ('pitch','roll'): d[:, 0 if bad=='pitch' else 1] = .16
    if bad=='height': rows[:,6] = .3
    if bad=='contact': rows[:,10] = 0.
    if bad=='closure': rows[:,12] = .006
    if bad=='saturation': rows[:,17] = .2
    if bad=='fall': args['terminated'] = True
    if bad=='nonfinite': rows[100,7] = float('nan')
    assert not score(rows,d,recipe[0],**args)['accepted']


def test_online_success_and_hold_ignore_speed_not_level(recipe):
    spec = recipe[0]
    yes = torch.ones(1,dtype=torch.bool)
    cfg = spec['recovery']['autonomous_stability']
    stable = autonomous_stable(torch.tensor([.36]),torch.tensor([.08]),
        torch.tensor([[2.,1.,0.]]),torch.tensor([[0.,2.,0.]]),torch.ones(1,2)*50.,
        torch.tensor([.3]),cfg)
    d = torch.zeros(1,10); d[:,4:6] = 1.; d[:,3] = .3
    assert stable.all() and standing_success_mask(d,spec['recovery']['standing_task']['protocol']).all()
    fsm = RecoveryFSM(1,'cpu',spec['recovery']['fsm'])
    pulses = 0
    for _ in range(200):
        pulse, _, _ = fsm.step(yes,stable,~yes,~yes,dt=.01)
        pulses += int(pulse.sum())
    assert pulses == 1
    d[:,0] = .16
    assert not standing_success_mask(d,spec['recovery']['standing_task']['protocol']).any()


def test_curriculum_two_windows_and_confirmations_then_R1_only(recipe):
    cfg = recipe[0]['recovery']['curriculum']
    manager = ReverseRecoveryCurriculum(cfg['levels'],max_enabled_stage=cfg['max_enabled_stage'],
                                       full_confirmations_required=2)
    manager.record_episodes([[0,True,False]]*256)
    assert manager.stage == 0
    manager.confirm_evaluation(stage=0,accepted=True,continuous_s=10.)
    assert manager.stage == 0
    manager.confirm_evaluation(stage=0,accepted=True,continuous_s=10.)
    assert manager.stage == 1 and manager.current_level()['pose_family'] == 'R0_perturbed'
    manager.record_episodes([[1,True,False]]*256)
    for _ in range(2):manager.confirm_evaluation(stage=1,accepted=True,continuous_s=10.)
    assert manager.stage == 1


def test_sampling_preserves_40_percent_R0_and_train_holdout_separation(recipe):
    spec = recipe[0]
    poses = json.loads(Path(spec['recovery']['pose_library']).read_text())['poses']
    level = spec['recovery']['curriculum']['levels'][1]
    for split in ('train','holdout'):
        ids, weights = pose_sampling(poses,level['pose_family'],split,
            retained_families=level['retained_families'],retained_fraction=level['retained_fraction'])
        assert sum(weights) == pytest.approx(1.)
        assert sum(w for i,w in zip(ids,weights) if poses[i]['family']=='R0') == pytest.approx(.4)
        assert all(poses[i]['split']==split and poses[i]['offline_valid'] for i in ids)


@pytest.mark.parametrize('bad', ['online_speed','reward_speed','reward_geometry','old_gate'])
def test_mismatched_goal_rejected_before_Isaac(recipe, bad):
    spec = copy.deepcopy(recipe[0])
    if bad=='online_speed':spec['recovery']['autonomous_stability']['linear_speed_max_mps']=.05
    if bad=='reward_speed':spec['recovery']['settling_reward']['settling_linear_weight']=-.6
    if bad=='reward_geometry':spec['recovery']['standing_task']['reward']['weights']['mirror_posture']=-.02
    if bad=='old_gate':spec['recovery']['standing_task']['protocol']['excursion_max_m']=.2
    assert validate(spec)


def test_actual_saved_trace_reclassified_without_overwriting(recipe):
    old = json.loads(SOURCE.with_name('evaluation_50_0_0.json').read_text())
    assert old['passed_envs'] == 0
    for row in old['per_env']:
        result = score(torch.tensor(row['compact_trace_100hz']),torch.tensor(row['posture_trace_100hz']),recipe[0])
        assert result['accepted']
    assert json.loads(SOURCE.with_name('evaluation_50_0_0.json').read_text())['passed_envs'] == 0


def test_low_frequency_evaluations_and_exact_initial_confirmations(recipe):
    cfg = recipe[0]['evaluation']
    assert not any(schedule(i,'formal',cfg)['full'] for i in range(1,100))
    assert schedule(100,'formal',cfg)['full'] and schedule(200,'formal',cfg)['full']
    assert not schedule(300,'formal',cfg)['full'] and schedule(500,'formal',cfg)['full']
    assert not any(schedule(i,'formal',cfg)['light'] for i in range(1,10001))


def test_retained_R0_failure_blocks_certification_and_state_restores(recipe):
    from native_stand.recovery.recipe import evaluate_actor
    cfg = recipe[0]
    class Env(FakeStandingEnv):
        def step(self, action):
            out = super().step(action)
            if self.family=='R0':self.standing_snapshot[:,0] = .2
            else:self.standing_snapshot[:,0] = 0.
            return out
    env = Env(cfg)
    env.family = 'R0_perturbed'
    env.reverse_curriculum = SimpleNamespace(stage=1)
    result = evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=10.,seed=104)
    assert not result['accepted'] and result['evaluation_curriculum_stage']==1
    assert len(result['retained_evaluations'])==1 and not result['retained_evaluations'][0]['accepted']
    assert all('retained_family' in row['standing_failed_checks'] for row in result['per_env'])
    assert env.curriculum_training and env.family=='R0_perturbed' and env.split=='train'


def test_candidate_ranking_prefers_level_not_drift(recipe):
    from native_stand.recovery.recipe import evaluate_actor
    env = FakeStandingEnv(recipe[0],drift=True);env.reverse_curriculum=None
    result = evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=10.,seed=104)
    better = copy.deepcopy(result)
    for row in result['per_env']:
        row['standing_metrics']['mean_abs_roll_rad'] = .08
    for row in better['per_env']:
        row['standing_metrics']['net_drift_m'] = 10.
        row['standing_metrics']['mean_abs_roll_rad'] = .01
    identity={'scored_envs':8}
    entries=[{'identity':identity,'kind':'full','result':r,'checkpoint_sha256':name,'checkpoint':name}
             for r,name in ((result,'low_drift'),(better,'level'))]
    assert choose(entries,None,identity)['accepted_candidate']['checkpoint']=='level'
