"""Freeze two same-source motion specs and independent exact-attempt ledgers."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'runs/motion_retention_reeval_20261005/spec.json'
REF = ROOT / 'runs/motion_retention_reference_20261006_audit/reference.pt'
OUT = ROOT / 'configs/experiments/motion_retention_ab_20261006'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    from native_stand.command_v6.tools.entrypoints import historical_cli_guard
    historical_cli_guard('scripts/create_motion_retention_ab_20261006.py')
    if OUT.exists():
        raise FileExistsError(OUT)
    source = json.loads(BASE.read_text())
    reference_sha = sha(REF)
    for arm, coefficient in (('off', 0.0), ('on', 0.01)):
        spec = copy.deepcopy(source)
        spec['experiment'] = f'motion_retention_ab_20261006_{arm}'
        spec.pop('diagnostic_identity_only', None)
        spec.pop('zero_mode', None)
        spec.pop('zero_mean_abs_vx_max_mps', None)
        spec['retention'] = {'enabled': True, 'lambda': coefficient,
            'reference_path': str(REF), 'reference_sha256': reference_sha,
            'samples_per_command': 512}
        spec['curriculum']['task_progression']['max_enabled_stage'] = 1
        spec['curriculum']['task_progression']['consecutive_confirmations'] = 99
        spec['evaluation'].pop('zero_mode', None)
        spec['evaluation'].pop('zero_mean_abs_vx_max_mps', None)
        spec['evaluation']['steady_window_s'] = [2.0, 6.0]
        spec['evaluation']['motion_window_s'] = [2.0, 6.0]
        spec['evaluation']['stop_window_s'] = 1.0
        spec['evaluation']['full_every_updates'] = 25
        spec['evaluation']['checkpoint_every_updates'] = 25
        spec['budget'].update(smoke_updates=1, formal_updates=49,
            smoke_wall_s=300, formal_wall_s=1250,
            sample_limit=409600, formal_samples=401408)
        folder = OUT / arm
        folder.mkdir(parents=True)
        (folder / 'spec.json').write_text(json.dumps(spec, indent=2) + '\n')
        ledger = {'authorization': 'AUTHORIZED',
            'limits': {'source_eval': 0, 'smoke': 1, 'formal': 49, 'evaluate': 0, 'play': 0},
            'used': {'source_eval': 0, 'smoke': 0, 'formal': 0, 'evaluate': 0, 'play': 0},
            'attempts': {}, 'source_eval_wall_used_s': 0.0}
        (folder / 'budget.json').write_text(json.dumps(ledger, indent=2) + '\n')
        print(arm, 'spec_sha256', sha(folder / 'spec.json'), 'reference_sha256', reference_sha)


if __name__ == '__main__':
    main()
