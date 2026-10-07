"""Offline frozen evidence discovery; no simulation, selection changes or overwrites."""
import argparse
import hashlib
import json
import pickle
from pathlib import Path

from .health_check import digest
from ..domain.evidence import resolve_gate, validate_effective_protocol


def _state_identity(value):
    import numpy as np
    import torch
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        return {'dtype': str(tensor.dtype), 'shape': list(tensor.shape),
                'sha256': hashlib.sha256(tensor.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()}
    if isinstance(value, np.ndarray):
        return {'dtype': str(value.dtype), 'shape': list(value.shape),
                'sha256': hashlib.sha256(value.tobytes()).hexdigest()}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _state_identity(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_state_identity(item) for item in value]
    return value


def _state_sha(value):
    return hashlib.sha256(json.dumps(_state_identity(value), sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _summary_row(row):
    # Keep scalar/vector metrics without copying policy-step trace matrices.
    return {key: value for key, value in row.items()
            if not isinstance(value, list) or not value or not isinstance(value[0], list)}


def _diagnostics(result):
    if result.get('diagnostics_validity') is not None:
        return result['diagnostics_validity']
    fields = set(result.get('gate_diagnostic_fields') or [])
    for row in result.get('per_env', []):
        if isinstance(row, dict):
            fields.update(key for key in row if key.endswith('_100hz') and 'diagnostic' in key)
    return {field: {'value': None, 'requested': None, 'enabled': None, 'valid': False,
                   'sample_count': 0, 'missing_reason': 'historical_collection_validity_not_recorded',
                   'scope': 'UNKNOWN'} for field in sorted(fields)} or None


def collect_run(run):
    run = Path(run).resolve()
    inputs, records, issues, specs, manifests, checkpoints = {}, {}, [], {}, {}, {}
    configured_specs = {}

    def issue(status, path, reason, code='MISSING_EVIDENCE'):
        row = {'status': status, 'path': str(path), 'reason_code': code, 'reason': reason}
        if row not in issues:
            issues.append(row)

    def track(path, expected=None, label='SHA'):
        path = Path(path)
        if not path.is_file():
            issue('UNKNOWN', path, 'missing evidence')
            return None
        try:
            actual = inputs.setdefault(str(path), digest(path))
        except OSError as exc:
            issue('UNKNOWN', path, str(exc))
            return None
        if expected is not None and actual != expected:
            issue('INVALID', path, label + ' differs', 'IDENTITY_ERROR')
        return actual

    def read(path, required=False):
        path = Path(path)
        if not path.is_file() and not required:
            return None
        if track(path) is None:
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            issue('INVALID', path, str(exc), 'CONFIG_ERROR')
            return None

    def inside(path):
        return not any(part in ('source_snapshot', 'execution_snapshot') for part in path.relative_to(run).parts)

    evidence_paths = sorted(path for path in run.rglob('*.json') if inside(path) and
        (path.name in ('manifest.json', 'progress.json', 'chain_progress.json', 'terminal_report.json',
                       'chain_terminal_report.json', 'submission_terminal.json', 'analysis.json',
                       'candidate_selection.json', 'candidate_registry.json', 'budget.json') or
         path.name.endswith('.terminal.json')))
    for path in evidence_paths:
        value = read(path)
        if value is not None:
            records[str(path.relative_to(run))] = value
            if path.name == 'manifest.json' and isinstance(value, dict):
                manifests[path.parent] = value
    if not manifests:
        issue('UNKNOWN', run, 'run manifest absent')
    if not any('terminal' in Path(name).name for name in records):
        issue('UNKNOWN', run, 'terminal evidence absent')

    def checkpoint(path, *, expected=None, context=None, role='candidate'):
        path = Path(path).resolve()
        actual = track(path, expected, 'checkpoint SHA')
        if actual is None:
            return
        if str(path) not in checkpoints:
            import torch
            row = {'sha256': actual, 'status': 'VALID', 'roles': [], 'evaluations': []}
            try:
                saved = torch.load(path, map_location='cpu', weights_only=False)
                if not isinstance(saved, dict):
                    raise ValueError('checkpoint is not an object')
                row['internal_identity'] = {key: saved.get(key) for key in
                    ('update', 'source_sha256', 'asset_sha256', 'spec_sha256', 'seed')}
                for field in ('actor', 'critic', 'optimizer'):
                    row[field + '_sha256'] = _state_sha(saved[field]) if field in saved else None
                    if field not in saved:
                        issue('UNKNOWN', path, field + ' state absent')
                        row['status'] = 'UNKNOWN'
                std = saved.get('actor', {}).get('distribution.std_param')
                row['std_sha256'] = _state_sha(std) if std is not None else None
                row['std'] = std.detach().cpu().tolist() if isinstance(std, torch.Tensor) else std
                if std is None:
                    issue('UNKNOWN', path, 'action std state absent')
                    row['status'] = 'UNKNOWN'
                row['optimizer_lr'] = [group.get('lr') for group in saved.get('optimizer', {}).get('param_groups', [])]
                row['rng_identity'] = {key: _state_sha(value) for key, value in saved.items() if 'rng' in key.lower()}
                row['curriculum'] = saved.get('recovery_curriculum', saved.get('task_curriculum'))
            except (OSError, RuntimeError, ValueError, KeyError, TypeError, AttributeError, EOFError, pickle.UnpicklingError) as exc:
                row['status'] = 'INVALID'
                row['error'] = str(exc)
                issue('INVALID', path, 'checkpoint unreadable: ' + str(exc), 'IDENTITY_ERROR')
            checkpoints[str(path)] = row
        row = checkpoints[str(path)]
        if role not in row['roles']:
            row['roles'].append(role)
        if expected is not None and expected != actual:
            row['status'] = 'INVALID'
        for key, wanted in (context or {}).items():
            got = row.get('internal_identity', {}).get(key)
            if got is None:
                issue('UNKNOWN', path, 'checkpoint internal ' + key + ' absent')
            elif got != wanted:
                row['status'] = 'INVALID'
                issue('INVALID', path, 'checkpoint internal ' + key + ' differs', 'IDENTITY_ERROR')

    snapshot_identity, evaluator_identity = {}, {}
    for folder, manifest in manifests.items():
        if manifest.get('spec_path'):
            actual = track(manifest['spec_path'], manifest.get('spec_sha256'), 'manifest spec SHA')
            if actual:
                configured_specs.setdefault(actual, []).append(Path(manifest['spec_path']))
        if manifest.get('kind') and not manifest.get('phase'):
            configuration = manifest.get('config', {})
            if isinstance(configuration, dict):
                for arm in configuration.get('arms', {}).values():
                    if isinstance(arm, dict) and arm.get('spec'):
                        actual = track(arm['spec'], arm.get('sha256'), 'chain arm spec SHA')
                        if actual:
                            configured_specs.setdefault(actual, []).append(Path(arm['spec']))
                if configuration.get('source_checkpoint'):
                    checkpoint(configuration['source_checkpoint'], expected=configuration.get('source_sha256'), role='source_baseline')
            continue
        snapshot = folder / 'source_snapshot'
        spec_path = snapshot / 'spec.json'
        spec = read(spec_path, required=True)
        if not isinstance(spec, dict):
            continue
        specs[folder] = spec
        track(spec_path, manifest.get('spec_sha256'), 'manifest/spec SHA')
        frozen = manifest.get('source_snapshot_sha256')
        if not isinstance(frozen, dict):
            issue('UNKNOWN', snapshot, 'snapshot SHA inventory absent')
            frozen = {}
        snapshot_identity[str(folder)] = {name: {'expected_sha256': expected,
            'actual_sha256': track(snapshot / name, expected, 'snapshot SHA')}
            for name, expected in frozen.items()}
        for field, sha_key in (('source_checkpoint', 'source_sha256'), ('asset_path', 'asset_sha256'),
            ('asset_module_path', 'asset_module_sha256'), ('colleague_config_path', 'colleague_config_sha256')):
            if field not in spec:
                if field in ('source_checkpoint', 'asset_path'):
                    issue('UNKNOWN', spec_path, field + ' absent')
                continue
            path = Path(spec[field])
            track(path, spec.get(sha_key), sha_key)
            if sha_key not in spec:
                issue('UNKNOWN', spec_path, sha_key + ' absent')
            if sha_key in manifest and spec.get(sha_key) != manifest[sha_key]:
                issue('INVALID', spec_path, 'manifest/' + sha_key + ' differs', 'IDENTITY_ERROR')
            if field == 'source_checkpoint':
                context = {key: value for key, value in (
                    ('update', spec.get('source_update')), ('spec_sha256', spec.get('source_spec_sha256')),
                    ('asset_sha256', spec.get('source_asset_sha256', spec.get('asset_sha256')))) if value is not None}
                checkpoint(path, expected=spec.get(sha_key), context=context, role='source_baseline')
        # Historical evaluator versions declare different components. Verify only
        # frozen components; current shared implementation drift is irrelevant.
        names = ['domain_protocol.py', 'evaluate_checkpoint.py']
        if 'domain_evidence.py' in frozen:
            names.insert(1, 'domain_evidence.py')
        if 'evaluation_state.py' in frozen:
            names.insert(-1, 'evaluation_state.py')
        if spec.get('recovery', {}).get('standing_task'):
            names += ['recovery_' + name for name in ('recipe.py', 'domain.py', 'standing.py', 'selection.py')]
        components = [track(snapshot / name) for name in names]
        expected = manifest.get('evaluator_sha256')
        computed = hashlib.sha256(''.join(components).encode()).hexdigest() if all(components) else None
        evaluator_identity[str(folder)] = {'expected_sha256': expected, 'actual_sha256': computed,
                                          'components': names}
        if expected is None or computed is None:
            issue('UNKNOWN', folder / 'manifest.json', 'evaluator identity incomplete')
        elif expected != computed:
            issue('INVALID', folder / 'manifest.json', 'evaluator SHA differs', 'IDENTITY_ERROR')
        progress = records.get(str((folder / 'progress.json').relative_to(run)), {})
        terminal = records.get(str((folder / 'terminal_report.json').relative_to(run)), {})
        if progress and terminal and progress.get('actual_updates') != terminal.get('actual_updates'):
            issue('INVALID', folder, 'progress/terminal updates differ', 'IDENTITY_ERROR')
        if terminal.get('status') == 'COMPLETED' and terminal.get('exit_code', 0) != 0:
            issue('INVALID', folder, 'terminal exit/status conflict', 'IDENTITY_ERROR')

    def nearest(path, mapping):
        return next((mapping[parent] for parent in (path.parent, *path.parents) if parent in mapping), {})

    registry_links = {}
    for name, value in records.items():
        if Path(name).name != 'candidate_registry.json' or not isinstance(value, list):
            continue
        folder = (run / name).parent
        for row in value:
            if not isinstance(row, dict) or not row.get('checkpoint'):
                continue
            checkpoint(row['checkpoint'], expected=row.get('checkpoint_sha256'), role=row.get('role', 'candidate'))
            if row.get('evaluation'):
                registry_links[str((folder / row['evaluation']).resolve())] = row

    for path in sorted(run.rglob('model*.pt')):
        if inside(path):
            manifest = nearest(path, manifests)
            context = {key: manifest[key] for key in ('source_sha256', 'asset_sha256', 'spec_sha256') if key in manifest}
            checkpoint(path, context=context)

    evaluations = []
    for path in sorted(path for path in run.rglob('*.json') if inside(path) and
                       (path.name.startswith('evaluation') or path.name.startswith('durability')) and
                       not path.name.endswith('.terminal.json')):
        result = read(path)
        if not isinstance(result, dict):
            continue
        spec = nearest(path, specs)
        task = ('recovery' if result.get('task') == 'recovery' else 'capability' if 'capability_gate' in result
                else 'motion' if 'motion_gate' in result else 'standing')
        scored = spec.get('evaluation', {}).get('scored_envs')
        gate = resolve_gate(result, task, expected_envs=scored)
        if gate['status'] == 'CONFLICTING_EVIDENCE':
            issue('INVALID', path, gate['conflicts'], 'IDENTITY_ERROR')
        elif gate['status'] == 'MISSING_EVIDENCE':
            issue('UNKNOWN', path, gate['missing_fields'])
        protocol = result.get('effective_protocol')
        protocol_status = 'UNKNOWN'
        if protocol is None:
            issue('UNKNOWN', path, 'effective protocol absent; historical serialized windows are not actual-window proof')
        else:
            try:
                validate_effective_protocol(protocol)
                protocol_status = 'VALID'
            except (KeyError, TypeError, ValueError) as exc:
                protocol_status = 'INVALID'
                issue('INVALID', path, 'effective protocol invalid: ' + str(exc), 'IDENTITY_ERROR')
        link = registry_links.get(str(path), {})
        checkpoint_path = result.get('checkpoint', link.get('checkpoint'))
        expected_sha = result.get('checkpoint_sha256', link.get('checkpoint_sha256'))
        if checkpoint_path:
            checkpoint(checkpoint_path, expected=expected_sha, role=link.get('role', 'evaluated_candidate'))
            saved = checkpoints.get(str(Path(checkpoint_path).resolve()))
            if saved and str(path) not in saved['evaluations']:
                saved['evaluations'].append(str(path))
        else:
            issue('UNKNOWN', path, 'evaluation checkpoint association absent')
        if expected_sha is None:
            issue('UNKNOWN', path, 'evaluation checkpoint SHA absent')
        manifest = nearest(path, manifests)
        for field in ('spec_sha256', 'evaluator_sha256', 'asset_sha256'):
            if field in result and field in manifest and result[field] != manifest[field]:
                issue('INVALID', path, 'evaluation/manifest ' + field + ' differs', 'IDENTITY_ERROR')
        evaluations.append({'path': str(path), 'checkpoint': checkpoint_path, 'checkpoint_sha256': expected_sha,
            'checkpoint_association': 'raw' if result.get('checkpoint') else 'registry' if link else 'UNKNOWN',
            'task': task, 'gate_evidence': gate, 'effective_protocol': protocol,
            'reported_protocol': result.get('success_protocol', result.get('protocol')),
            'protocol_status': protocol_status,
            'diagnostics_validity': _diagnostics(result),
            'per_env': [_summary_row(row) for row in result.get('per_env', []) if isinstance(row, dict)]})

    candidate_roles = {}
    for name, selection in records.items():
        if Path(name).name != 'candidate_selection.json' or not isinstance(selection, dict):
            continue
        roles = {role: selection.get(role) for role in ('source_baseline', 'latest_checkpoint',
            'best_new_evaluated_candidate', 'accepted_by_stage', 'fallback_checkpoint',
            'accepted_candidate', 'best_observed_candidate')}
        candidate_roles[name] = roles
        for role, entry in roles.items():
            values = entry.values() if role == 'accepted_by_stage' and isinstance(entry, dict) else [entry]
            for candidate in values:
                if not isinstance(candidate, dict):
                    continue
                path = candidate.get('checkpoint', candidate.get('path'))
                if path:
                    checkpoint(path, expected=candidate.get('checkpoint_sha256', candidate.get('sha256')), role=role)
                    if role == 'best_new_evaluated_candidate' and candidate.get('role') == 'source':
                        issue('INVALID', path, 'source registered as new candidate', 'IDENTITY_ERROR')
                elif candidate:
                    issue('UNKNOWN', run / name, role + ' checkpoint path absent')
    for path, row in checkpoints.items():
        row['evaluated'] = bool(row['evaluations'])
        if not row['evaluated']:
            row['evaluation_status'] = 'UNKNOWN: no associated raw evaluation; not eligible for acceptance'
    reward_blocks = []
    for path in sorted(path for path in run.rglob('metrics.jsonl') if inside(path)):
        track(path)
        spec = nearest(path, specs)
        try:
            lines = path.read_text().splitlines()
        except OSError as exc:
            issue('UNKNOWN', path, str(exc))
            continue
        for line_number, line in enumerate(lines, 1):
            try:
                metric = json.loads(line)
            except ValueError:
                issue('INVALID', path, 'invalid metrics line ' + str(line_number), 'CONFIG_ERROR')
                continue
            rollout, task = metric.get('rollout', {}), metric.get('task_metrics', {})
            counts = task.get('counts', {}) if isinstance(task, dict) else {}
            samples = rollout.get('samples', 0)
            def event(count, weight):
                return counts[count] * spec['reward'][weight] / samples if samples and count in counts and weight in spec.get('reward', {}) else None
            reward_blocks.append({'path': str(path), 'update': metric.get('update'), 'samples': samples,
                'continuous_reward': rollout.get('weighted_mean'), 'success_event_reward': event('complete_successes', 'success_once'),
                'failure_event_reward': event('task_failures', 'failure_once'),
                'timeout_event_reward': event('timeouts', 'timeout_once'),
                'timeout_reason': 'UNKNOWN unless timeout count and reward weight are explicitly saved',
                'reward_scope': 'update-level captured training aggregate; not per-env trajectory reward',
                'episode_durations': rollout.get('episodes'), 'counts': counts,
                'retention': task.get('standing_retention') if isinstance(task, dict) else None})

    reference = None
    reference_path = run / 'reference.pt'
    if reference_path.is_file():
        track(reference_path)
        import torch
        try:
            bundle = torch.load(reference_path, map_location='cpu', weights_only=False)
            commands, counts = torch.unique(bundle['commands'], dim=0, return_counts=True)
            reference = {'sha256': inputs[str(reference_path)], 'observation_shape': list(bundle['observations'].shape),
                'observation_sha256': _state_sha(bundle['observations']),
                'command_sha256': _state_sha(bundle['commands']),
                'episode_age_sha256': _state_sha(bundle['episode_age_s']),
                'commands': commands.tolist(), 'counts': counts.tolist(), 'balanced': len(set(counts.tolist())) == 1,
                'episode_age_min_s': float(bundle['episode_age_s'].min()), 'episode_age_max_s': float(bundle['episode_age_s'].max()),
                'metadata': bundle.get('metadata')}
        except (OSError, RuntimeError, ValueError, KeyError, TypeError, EOFError, pickle.UnpicklingError) as exc:
            issue('INVALID', reference_path, 'reference bundle unreadable: ' + str(exc), 'IDENTITY_ERROR')
    project = Path(__file__).resolve().parents[4]
    ledger_associations = {}
    for folder, spec in specs.items():
        spec_sha = inputs[str(folder / 'source_snapshot/spec.json')]
        locations = configured_specs.get(spec_sha, [])
        ledgers = list(dict.fromkeys(path.with_name('budget.json') for path in locations))
        if not ledgers:
            ledgers = [project / 'configs/experiments' / spec.get('experiment', '') / 'budget.json']
        ledger_associations[str(folder)] = {'spec_sha256': spec_sha, 'paths': [str(path) for path in ledgers],
            'source': 'manifest spec path' if locations else 'experiment name fallback'}
        for ledger in ledgers:
            if ledger.is_file():
                records[str(ledger)] = read(ledger)
            else:
                issue('UNKNOWN', ledger, 'ledger evidence absent')
    status = 'INVALID' if any(row['status'] == 'INVALID' for row in issues) else 'UNKNOWN' if issues else 'VALID'
    report = {'run': str(run), 'evidence_status': status, 'historical_records_unchanged': True,
        'simulation': 0, 'ppo': 0, 'evaluations': evaluations, 'candidate_roles': candidate_roles,
        'issues': issues, 'reference_bundle': reference, 'checkpoints': checkpoints,
        'snapshot_identity': snapshot_identity, 'evaluator_identity': evaluator_identity,
        'ledger_associations': ledger_associations,
        'reward_blocks': reward_blocks, 'accounting': records,
        'limitations': ['No new behavior acceptance. Missing windows or physical data remain UNKNOWN.',
            'Historical gate thresholds and results are preserved, not relaxed.',
            'Offline state hashes identify captured parameters; they do not prove actual optimizer execution.',
            'Per-env reward/event/retention metrics are UNKNOWN unless explicitly captured.']}
    return report, inputs


def write_audit(report, inputs, output, *, corrected_aliases=True):
    output = Path(output).resolve()
    run = Path(report['run']).resolve()
    if output == run or run in output.parents:
        raise ValueError('corrected output must be outside historical run')
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=False)
    content = '# Corrected offline evidence audit\n\nStatus: ' + report['evidence_status'] + '\n\n'
    content += 'No simulation or PPO; historical evidence unchanged.\n\n'
    for row in report['evaluations']:
        content += f"- {row['path']}: {row['task']} {row['gate_evidence']['status']}; protocol {row['protocol_status']}\n"
    content += '\nMissing evidence is UNKNOWN; identity conflicts are INVALID. No additional capability is certified.\n'
    for row in report['issues']:
        content += '\n- ' + json.dumps(row, ensure_ascii=True) + '\n'
    filenames = [('audit.json', report)]
    if corrected_aliases:
        filenames.append(('corrected_analysis.json', report))
    for name, payload in filenames:
        with (output / name).open('x') as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.write('\n')
    for name in ('audit.md', 'corrected_report.md') if corrected_aliases else ('audit.md',):
        with (output / name).open('x') as stream:
            stream.write(content)
    manifest = {'inputs': inputs, 'outputs': {name: digest(output / name) for name in
        ('audit.json', 'audit.md')}, 'simulation': 0, 'ppo': 0}
    with (output / 'audit_manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    for path, expected in inputs.items():
        if digest(path) != expected:
            raise RuntimeError('historical input changed during audit: ' + path)
    return {'output': str(output), 'evidence_status': report['evidence_status'],
            'evaluations': len(report['evaluations']), 'issues': report['issues'], 'history_sha_verified': True}


def audit_run(run, output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    report, inputs = collect_run(run)
    return write_audit(report, inputs, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--protocol-spec',type=Path,help='fresh protocol: rescore saved traces, no new ability claim')
    args = parser.parse_args()
    if args.protocol_spec:
        print(json.dumps(rescore_run(args.run,args.protocol_spec,args.output_dir),indent=2));return
    print(json.dumps(audit_run(args.run, args.output_dir), indent=2))


def rescore_run(run,spec_path,output):
    """Reuse online score/gate and selector on immutable recorded policy-step traces."""
    import torch
    from .evaluate_checkpoint import protocol_for_spec
    from ..domain.protocol import score,capability_gate,CAUSES
    from ..completion import classify,choose_capability,evaluation_identity
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    spec=json.loads(Path(spec_path).read_text())
    protocol=protocol_for_spec(spec,30.,True)
    expected=evaluation_identity(spec,'offline_same_score_gate')
    entries=[];summaries=[];inputs={str(Path(spec_path).resolve()):digest(spec_path)}
    for path in sorted(Path(run).rglob('evaluation*.json')):
        if 'source_snapshot' in path.parts or path.name.endswith('.terminal.json'):continue
        raw=json.loads(path.read_text())
        if not raw.get('per_env'):continue
        inputs[str(path.resolve())]=digest(path)
        trace_rows=raw['per_env']
        if len(trace_rows)!=8 or any(not row.get('trace') for row in trace_rows):
            summaries.append({'path':str(path),'status':'MISSING_EVIDENCE:full_trace'});continue
        lengths=[len(row['trace']) for row in trace_rows]
        rows=torch.zeros(max(lengths),8,18,dtype=torch.float64)
        valid=torch.zeros(rows.shape[:2],dtype=torch.bool)
        done=torch.zeros_like(valid);causes=torch.zeros(8,len(CAUSES),dtype=torch.bool)
        timeout=torch.zeros(8,dtype=torch.bool)
        for i,row in enumerate(trace_rows):
            rows[:lengths[i],i]=torch.tensor(row['trace'],dtype=rows.dtype)
            valid[:lengths[i],i]=True
            if row['outcome']!='completed':
                done[lengths[i]-1,i]=True
                if row['outcome']=='runtime_fault':causes[i,0]=True
                else:causes[i,2]=True
        result=score(rows,valid,done,causes,timeout,dt=raw['dt'],target_window=(10.,18.),
            requested_steps=3000,full_trace=True,effective_protocol=protocol)
        result.update(seconds=30.,target=raw['target'],effective_protocol=protocol)
        result['capability_gate']=capability_gate(result,raw['target'],protocol)
        model_path=raw.get('checkpoint',raw.get('checkpoint_path'))
        model_sha=raw.get('checkpoint_sha256')
        if not model_sha:
            # Frozen manifests/registry may supply identity; no inference from filename number.
            registry=path.parent/'candidate_registry.json'
            if registry.exists():
                item=next((r for r in json.loads(registry.read_text()) if r.get('evaluation')==path.name),None)
                if item:model_sha=item.get('checkpoint_sha256');model_path=item.get('checkpoint')
        role='source' if model_sha==spec['source_sha256'] else 'candidate'
        entry={'role':role,'kind':'full','identity':expected,'checkpoint_sha256':model_sha,
               'checkpoint':model_path,'command':raw['target'][:2],'result':result,'update':raw.get('update',0),
               'evaluation':str(path)}
        classified=classify(entry,expected)
        if not model_sha:classified['eligible']=False
        entries.append(classified)
        summaries.append({'path':str(path),'checkpoint':model_path,'checkpoint_sha256':model_sha,
            'target':raw['target'],'old_gate':raw.get('capability_gate',raw.get('standing_gate')),
            'new_gate':result['capability_gate'],'per_env':[_summary_row(r) for r in result['per_env']],
            'interpretation':'same historical trajectory rescored; no learned capability improvement',
            'code_compatibility':'historical source SHA differs; new physical results cannot silently certify a combined same-code set'})
    output.mkdir(parents=True,exist_ok=False)
    report={'evaluations':summaries,'effective_protocol':protocol,'inputs':inputs,
            'candidates':choose_capability(entries,None,expected),
            'online_PPO':0,'offline_optimizer_updates':0,'simulation':0}
    with (output/'rescore.json').open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    for path,sha in inputs.items():
        if digest(path)!=sha:raise ValueError('historical input changed')
    return {'output':str(output),'evaluations':len(summaries),'historical_inputs_unchanged':True}


if __name__ == '__main__':
    main()
