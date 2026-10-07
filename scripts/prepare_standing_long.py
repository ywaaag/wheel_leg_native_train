"""Create a fresh formal authorization while referencing immutable verification evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification-run', type=Path, required=True)
    parser.add_argument('--parent-spec', type=Path, required=True)
    parser.add_argument('--config-dir', type=Path, required=True)
    parser.add_argument('--updates', type=int, default=500)
    parser.add_argument('--wall-s', type=int, default=7200)
    args = parser.parse_args()
    if args.config_dir.exists() or args.updates <= 0 or args.wall_s < 60:
        raise ValueError('fresh config directory and positive bounded budget required')
    spec = json.loads(args.parent_spec.read_text())
    parent_book = json.loads(args.parent_spec.with_name('budget.json').read_text())
    attempts = {}
    for phase in ('source_eval', 'smoke'):
        folder = (args.verification_run / phase).resolve()
        rows = [(key, row) for key, row in parent_book['attempts'].items()
                if row['phase'] == phase and row['output_dir'] == str(folder) and
                row['status'] == 'COMPLETED']
        if len(rows) != 1:
            raise ValueError(f'exact completed {phase} evidence missing')
        key, row = rows[0]
        manifest = json.loads((folder / 'manifest.json').read_text())
        snapshot = folder / 'source_snapshot/spec.json'
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != manifest['spec_sha256']:
            raise ValueError('evidence snapshot identity differs')
        attempts['reused_' + key] = {
            **row, 'updates': 0, 'wall_s': 0,
            'evidence_spec_path': str(snapshot), 'reused_evidence': True,
            'original_ledger': str(args.parent_spec.with_name('budget.json').resolve()),
            'original_attempt_id': key, 'evidence_updates': row['updates'],
            'evidence_wall_s': row['wall_s'],
            'accounting_note': 'Evidence only; original consumption remains in original ledger.'}
    spec['experiment'] = args.config_dir.name
    spec['artifacts']['run_name'] = args.config_dir.name
    spec['budget'].update(formal_updates=args.updates, formal_wall_s=args.wall_s,
                          sample_limit=args.updates * spec['ppo']['envs'] * spec['ppo']['steps_per_env'],
                          chain_wall_s=args.wall_s)
    spec['authorization']['user_scope'] = '2026-10-06 direct bounded long formal authorized after completed source/smoke wiring; ordinary behavior failure does not block learning.'
    spec['authorization_note'] = spec['authorization']['user_scope']
    spec['phase_initialization'] = 'Strict source update1500 actor/critic/Adam; configured LR3e-5; new environment reset.'
    book = {'authorization': 'AUTHORIZED', 'authorization_evidence': spec['authorization_note'],
            'experiment': spec['experiment'],
            'limits': {'source_eval': 0, 'evaluate': 0, 'smoke': 0, 'formal': args.updates},
            'used': {'source_eval': 0, 'evaluate': 0, 'smoke': 0, 'formal': 0},
            'attempts': attempts, 'source_eval_wall_used_s': 0,
            'sample_limit': spec['budget']['sample_limit'],
            'chain_wall_limit_s': args.wall_s,
            'hapi_session': spec['authorization']['hapi_session']}
    args.config_dir.mkdir(parents=True)
    write(args.config_dir / 'spec.json', spec)
    write(args.config_dir / 'budget.json', book)
    print(json.dumps({'spec': str((args.config_dir / 'spec.json').resolve()),
                      'updates': args.updates, 'samples': book['sample_limit'],
                      'wall_s': args.wall_s, 'reused_phases': ['source_eval', 'smoke']}))


if __name__ == '__main__':
    main()
