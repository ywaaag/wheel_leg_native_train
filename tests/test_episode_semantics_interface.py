import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
import torch

from native_stand.command_v6.domain.episode_result import (
    episode_result, recovery_episode_mode, requires_stand, STAND_DEPENDENCY_FIELDS)
from native_stand.recovery.holding import HoldingEpisode


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT/'configs/experiments/recovery_r0_hold10_from50_20261007/spec.json'


def test_modes_preserve_legacy_and_require_explicit_holding():
    assert recovery_episode_mode({'fsm': {}}) == 'handover'
    assert recovery_episode_mode({'fsm': {'success_mode': 'autonomous_hold'}}) == 'autonomous_hold'
    config = {'fsm': {'success_mode': 'autonomous_hold'},
              'standing_task': {'training_episode': {'mode': 'fixed_horizon'}}}
    assert recovery_episode_mode(config) == 'continuous_holding'
    config['fsm']['success_mode'] = 'handover'
    with pytest.raises(ValueError, match='cannot use teacher'):
        recovery_episode_mode(config)
    config['standing_task']['training_episode']['mode'] = 'unknown'
    with pytest.raises(ValueError, match='Unknown'):
        recovery_episode_mode(config)


def test_only_explicit_holding_can_omit_stand_declaration():
    config = json.loads(SPEC.read_text())['recovery']
    assert requires_stand(config)
    for key in STAND_DEPENDENCY_FIELDS:
        config.pop(key)
    assert not requires_stand(config)
    spec = json.loads(SPEC.read_text())
    spec['recovery'] = config
    from native_stand.recovery.validation import validate_recovery
    assert validate_recovery(spec) == []
    config['stand_frozen'] = True
    assert requires_stand(config)
    assert 'recovery missing stand_checkpoint' in validate_recovery(spec)
    config.pop('stand_frozen')
    config['standing_task'].pop('training_episode')
    assert requires_stand(config)
    assert 'recovery missing stand_checkpoint' in validate_recovery(spec)


def test_optional_stand_dependency_preflight_and_snapshot_are_cpu_only(tmp_path):
    from native_stand.command_v6.tools.preflight import check
    from native_stand.command_v6.train import _snapshot
    spec=json.loads(SPEC.read_text())
    for key in STAND_DEPENDENCY_FIELDS:spec['recovery'].pop(key,None)
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    book={'authorization':'UNAUTHORIZED','limits':{'source_eval':1,'smoke':10,'formal':100},
        'used':{'source_eval':0,'smoke':0,'formal':0},'attempts':{},'source_eval_wall_used_s':0}
    (tmp_path/'budget.json').write_text(json.dumps(book))
    result=check(path,tmp_path/'run','source_eval')
    assert not any('stand_checkpoint' in error or 'stand_spec' in error for error in result['errors'])
    from native_stand.recovery.preflight import check as recovery_check
    recovery_result=recovery_check(path,tmp_path/'run')
    assert recovery_result['stand_sha256'] is None and recovery_result['files_written']==0
    folder=tmp_path/'snapshot_run';folder.mkdir()
    _snapshot(folder,path)
    assert not (folder/'source_snapshot/frozen_stand_spec.json').exists()
    assert (folder/'source_snapshot/episode_result.py').is_file()


@pytest.mark.parametrize('passed', [True, False])
def test_normal_timeout_is_separate_from_certificate(passed):
    result = episode_result(terminated=False, truncated=True, certificate_passed=passed,
                            runtime_fault=False, task_mode='continuous_holding')
    assert result['truncated'] and not result['terminated']
    assert result['certificate_passed'] is passed


def test_result_rejects_contradictions_and_preserves_unknown():
    kwargs = dict(terminated=True, truncated=False, certificate_passed=False,
                  runtime_fault=True, task_mode='handover')
    assert episode_result(**kwargs)['runtime_fault']
    with pytest.raises(ValueError, match='cannot terminate'):
        episode_result(**{**kwargs, 'truncated': True})
    with pytest.raises(ValueError, match='cannot pass'):
        episode_result(**{**kwargs, 'certificate_passed': True})
    assert episode_result(**{**kwargs, 'terminated': False, 'runtime_fault': False,
                             'certificate_passed': None})['certificate_passed'] is None


def filled_holding(n=2):
    protocol = json.loads(SPEC.read_text())['recovery']['standing_task']['protocol']
    holding = HoldingEpisode(n, 'cpu', dt=.01, protocol=protocol)
    holding.steps[:] = 1000
    holding.count[:] = 801
    holding.sums[:] = torch.tensor([.36, 1., 1., 0., 0.])*801
    return holding


def test_failed_gate_summary_preserves_timeout_and_reports_key_metrics():
    holding = filled_holding()
    holding.sums[1, 4] = .13*801
    no = torch.zeros(2, dtype=torch.bool)
    timeout, passed = holding.outcome(failed=no, fault=no)
    assert timeout.tolist() == [True, True]
    assert passed.tolist() == [True, False]
    holding.record_outcomes(terminated=no, truncated=timeout, fault=no)
    summary = holding.rollout_summary()
    assert summary['counts'] == dict(completed_episodes=2, normal_timeouts=2,
                                     certificate_passed=1, physical_failures=0, runtime_faults=0)
    assert summary['failed_gate_counts']['mean_roll'] == 1
    assert summary['metrics']['duration_s']['mean'] == 10.
    assert 'stochastic training' in summary['scope']
    holding.reset(torch.tensor([0]))
    assert holding.rollout_summary() == summary  # Local reset cannot erase terminal evidence.
    holding.begin_rollout()
    assert holding.rollout_summary()['metrics']['duration_s']['mean'] is None


def test_fault_end_is_not_a_failed_timeout_certificate():
    holding = filled_holding()
    holding.peaks[1, 2] = float('nan')
    terminated = torch.ones(2, dtype=torch.bool)
    fault = torch.tensor([False, True])
    holding.record_outcomes(terminated=terminated, truncated=~terminated, fault=fault)
    summary = holding.rollout_summary()
    assert summary['counts']['physical_failures'] == 1
    assert summary['counts']['runtime_faults'] == 1
    assert summary['certificate_evaluated_episodes'] == 0
    assert not any(summary['failed_gate_counts'].values())
    assert summary['metrics']['peak_tilt_rad']['sample_count'] == 1


@pytest.mark.parametrize('fall_step', [None, 300])
def test_evaluator_episode_results_separate_window_from_fall(fall_step):
    from test_recovery_standing_balance import FakeStandingEnv
    from native_stand.recovery.recipe import evaluate_actor
    spec = json.loads(SPEC.read_text())
    env = FakeStandingEnv(spec, fall_step=fall_step)
    env.reverse_curriculum = None
    result = evaluate_actor(lambda obs: torch.zeros(8, 6), None, env, seconds=10., seed=321)
    for row in result['per_env']:
        flags = row['episode_result']
        assert flags['task_mode'] == 'continuous_holding'
        assert flags['terminated'] == (fall_step is not None)
        assert flags['truncated'] == (fall_step is None)
        assert flags['certificate_passed'] == row['success']
        assert not flags['runtime_fault']
    assert result['success_protocol']['episode_mode'] == 'continuous_holding'
    assert result['success_protocol']['certificate_mode'] == 'full_window'


def runtime_module(monkeypatch):
    class Base:
        def _pre_physics_step(self, actions):
            self.leg_target.copy_(actions[:, [0, 1, 3, 4]])
            self.wheel_target.copy_(actions[:, [2, 5]])
    monkeypatch.setitem(sys.modules, 'native_stand.command_v6.runtime.env', SimpleNamespace(CommandEnv=Base))
    monkeypatch.setitem(sys.modules, 'isaaclab.utils.math', SimpleNamespace(quat_apply=lambda *a: None,
                                                                         quat_apply_inverse=lambda *a: None))
    module_spec = importlib.util.spec_from_file_location('episode_runtime_fixture',
                                                       ROOT/'src/native_stand/recovery/runtime.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('mode, expected_calls', [('continuous_holding', 0), ('handover', 1),
                                                ('autonomous_hold', 1)])
def test_holding_skips_teacher_forward_legacy_paths_preserved(monkeypatch, mode, expected_calls):
    module = runtime_module(monkeypatch)
    from native_stand.recovery.domain import Mode
    env = object.__new__(module.RecoveryEnv)
    env.episode_mode = mode
    env.step_dt = .01
    env.leg_target = torch.zeros(2, 4); env.wheel_target = torch.zeros(2, 2)
    env.reference = torch.zeros(2, 6)
    env.initialization_checked = torch.ones(2, dtype=torch.bool)
    env.control_jump = torch.zeros(2); env.wheel_control_jump = torch.zeros(2)
    env.fsm = SimpleNamespace(mode=torch.full((2,), int(Mode.RECOVERY)), age=torch.zeros(2),
                              dwell=torch.zeros(2))
    env.recovery_config = {'fsm': {'blend_s': .3}}
    env.stand_frame = torch.zeros(2, 25); env.stand_history = torch.zeros(2, 125)
    calls = []
    def teacher(obs):
        calls.append(obs)
        return torch.zeros(2, 6)
    env.stand_policy = teacher
    env.handover_leg = env.leg_target.clone(); env.handover_wheel = env.wheel_target.clone()
    env.pose_initial_hold = torch.zeros(1, dtype=torch.bool)
    env.initial_pose_index = torch.zeros(2, dtype=torch.long)
    env.initial_leg_targets = env.leg_target.clone()
    env.active_limits = torch.tensor([[-10., 10.]]*6)
    env.target_rate = torch.zeros(2, 6)
    env.executed_leg = env.leg_target.clone(); env.executed_wheel = env.wheel_target.clone()
    env.handover_target_rate_peak = torch.zeros(2, 6)
    env.action = torch.zeros(2, 6); env.stand_previous = torch.zeros(2, 6)
    env.cfg = SimpleNamespace(leg_position_scale_rad=1.6, wheel_speed_scale_rad_s=100.)
    actions = torch.tensor([[.1, .2, .3, .4, .5, .6]]).repeat(2, 1)
    env._pre_physics_step(actions)
    assert len(calls) == expected_calls
    assert torch.equal(env.leg_target, actions[:, [0, 1, 3, 4]])
    assert torch.equal(env.wheel_target, actions[:, [2, 5]])
