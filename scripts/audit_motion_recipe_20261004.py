"""Read-only CPU audit of immutable motion recipes and recorded metrics."""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import types

import torch


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def audit_run(relative):
    run = ROOT / relative
    snapshot = run / 'source_snapshot'
    manifest = read_json(run / 'manifest.json')
    mismatches = []
    for name, expected in manifest['source_snapshot_sha256'].items():
        actual = hashlib.sha256((snapshot / name).read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append(name)
    spec = read_json(snapshot / 'spec.json')
    stage_id = spec['curriculum']['active_stage']
    stage = spec['curriculum']['stages'][stage_id]
    tree = ast.parse((snapshot / 'train.py').read_text())
    initialized_width = any(
        isinstance(node, ast.Assign)
        and any(ast.unparse(target) == "spec['reward']['linear_error_denominator']"
                for target in node.targets)
        for node in ast.walk(tree)
    )
    runtime = (snapshot / 'runtime_env.py').read_text()
    fixed_supported = 'command_mode' in runtime
    rows = [json.loads(line) for line in (run / 'metrics.jsonl').read_text().splitlines()]
    keys = rows[0]['rollout']['raw_mean'].keys()
    ignored = [key for key in ('linear_velocity_tracking', 'yaw_velocity_tracking')
               if key in spec['reward'] and key not in keys]
    windows = []
    intervals = ((1, 50), (100, 200), (300, 400), (448, 497)) if 'speed1' in relative else ()
    metric_names = ('vx_mps', 'vx_error_abs_mps', 'yaw_rad_s', 'yaw_error_abs_rad_s',
                    'dual_contact', 'tilt_rad')
    for lo, hi in intervals:
        selected = [row for row in rows if lo <= row['update'] <= hi]
        groups = {}
        for row in selected:
            for group in row['task_metrics']:
                if not group['samples']:
                    continue
                key = str(group['command'])
                aggregate = groups.setdefault(key, {'samples': 0, 'sums': {}})
                aggregate['samples'] += group['samples']
                for name, value in group['means'].items():
                    if name not in metric_names:
                        continue
                    aggregate['sums'][name] = aggregate['sums'].get(name, 0.) + value * group['samples']
        windows.append({'updates': [lo, hi], 'groups': {
            key: {'samples': value['samples'], 'means': {
                name: total / value['samples'] for name, total in value['sums'].items()}}
            for key, value in groups.items()}})
    terminal = read_json(run / 'terminal_report.json')
    last = [{'command': group['command'], 'samples': group['samples'], 'means': {
        name: value for name, value in (group['means'] or {}).items() if name in metric_names}}
        for group in rows[-1]['task_metrics']] if 'speed1' in relative else []
    return {'run': relative, 'snapshot_files_verified': len(manifest['source_snapshot_sha256']),
            'snapshot_hash_mismatches': mismatches, 'fixed_requested': stage.get('command_mode') == 'fixed',
            'fixed_supported_in_snapshot': fixed_supported,
            'initial_stage_width_applied': initialized_width,
            'base_linear_denominator': spec['reward']['linear_error_denominator'],
            'configured_stage_linear_denominator': spec['reward']['stage_linear_denominators'][str(stage_id)],
            'ignored_tracking_weights': ignored, 'recorded_reward_terms': list(keys),
            'task_progression_configured': bool(spec['curriculum'].get('task_progression')),
            'terminal': {name: terminal.get(name) for name in (
                'status', 'actual_updates', 'samples', 'early_stop_reason')},
            'full_evaluation_count': len(terminal.get('evaluations', [])), 'windows': windows,
            'last_task_metrics': last}


def reproduce_speed1():
    snapshot = ROOT / 'runs/motion_speed1_20261003/formal/source_snapshot'
    spec = read_json(snapshot / 'spec.json')
    package = types.ModuleType('motion_audit_snapshot')
    package.__path__ = [str(snapshot)]
    sys.modules[package.__name__] = package
    load_module(package.__name__ + '.contract', snapshot / 'domain_contract.py')
    reward = load_module(package.__name__ + '.reward', snapshot / 'domain_reward.py')
    schedule = load_module(package.__name__ + '.schedule', snapshot / 'domain_schedule.py')
    times = torch.tensor([0., 1.5, 3., 6.5, 8.], dtype=torch.float64)
    target = torch.tensor([[1., 0.]], dtype=torch.float64).repeat(len(times), 1)
    commands = schedule.effective(target, times, height=.4, entry=1., ramp=1., hold=4., exit=1.)
    n = len(times)
    zeros = torch.zeros(n, dtype=torch.float64)
    args = (zeros + .4, zeros + 1., zeros, zeros, zeros, commands,
            torch.ones(n, 2, dtype=torch.bool), torch.zeros(n, 6, dtype=torch.float64),
            torch.zeros(n, 6, dtype=torch.float64), torch.zeros(n, 6, dtype=torch.float64),
            torch.zeros(n, 4, dtype=torch.float64), torch.zeros(n, dtype=torch.bool))
    kwargs = dict(weights=spec['reward'], height_width=.06, linear_denominator=.01,
                  yaw_denominator=.09, terminal_penalty=-1., dt=.01,
                  action_delta_wheel_factor=spec['reward']['action_delta_wheel_factor'])
    total, raw, weighted = reward.compute(*args, **kwargs)
    modified = dict(spec['reward'], linear_velocity_tracking=400., yaw_velocity_tracking=400.)
    altered, _, _ = reward.compute(*args, **dict(kwargs, weights=modified))
    assert torch.equal(total, altered), 'Unexpected independent tracking weight effect'
    assert torch.allclose(commands[:, 0], torch.tensor([0., .5, 1., .5, 0.], dtype=torch.float64))
    assert math.isclose(raw['velocity_tracking'][2].item(), math.exp(-100.), rel_tol=1e-12)
    return {'times_s': times.tolist(), 'effective_vx_command': commands[:, 0].tolist(),
            'stationary_raw_tracking': raw['velocity_tracking'].tolist(),
            'stationary_weighted_tracking': weighted['velocity_tracking'].tolist(),
            'independent_weights_100x_change_total_reward_max_delta': (altered-total).abs().max().item(),
            'hold_tracking_at_vx_0p4_yaw0': math.exp(-(.4-1.)**2/.01),
            'scope': 'CPU function reproduction; no Isaac, PPO, simulation or runtime changes'}


def main():
    runs = ['runs/motion_gpu1_20261002/formal', 'runs/motion_fixed_20261003/formal',
            'runs/motion_warmup_retention_20261003/formal', 'runs/motion_speed1_20261003/formal']
    result = {'runs': [audit_run(run) for run in runs], 'speed1_cpu_reproduction': reproduce_speed1()}
    assert not any(run['snapshot_hash_mismatches'] for run in result['runs'])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
