"""Read frozen Recovery evidence on CPU; exclusive-create an offline audit bundle."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import torch


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_implementation(snapshot):
    """CLI-only frozen imports, including the domain's native contract dependency."""
    modules = {}
    for name, filename in (
        ('native_stand.command_v6.domain.contract', 'domain_contract.py'),
        ('native_stand.recovery.domain', 'recovery_domain.py'),
        ('native_stand.recovery.standing', 'recovery_standing.py')):
        path = snapshot / filename
        definition = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(definition)
        sys.modules[name] = module
        definition.loader.exec_module(module)
        modules[name] = module
    return modules['native_stand.recovery.domain'], modules['native_stand.recovery.standing']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path,
        help='legacy spelling for a new audit.json path; its parent must not exist')
    parser.add_argument('--output-dir', type=Path,
        help='new output directory for audit.json, audit.md and audit_manifest.json')
    parser.add_argument('--legacy-survival-analysis',action='store_true',
        help='also run the historical source50/new100/new200 counterfactual analysis')
    args = parser.parse_args()
    if bool(args.output) == bool(args.output_dir):
        parser.error('provide exactly one of --output or --output-dir')
    if not args.legacy_survival_analysis:
        from native_stand.command_v6.tools.correct_evidence import collect_run, write_audit
        if args.output and args.output.name != 'audit.json':
            parser.error('generic audit --output must end in audit.json; use --output-dir')
        output=args.output_dir or args.output.parent
        if output.exists():raise FileExistsError(output)
        report,inputs=collect_run(args.run)
        print(json.dumps(write_audit(report,inputs,output,corrected_aliases=False),indent=2))
        return
    if args.output_dir:
        args.output=args.output_dir/'audit.json'
    if args.output.exists():raise FileExistsError(args.output)
    torch.set_num_threads(2)
    run = args.run.resolve()
    snapshot = run/'formal/source_snapshot'
    spec = read(snapshot/'spec.json')
    manifest = read(run/'formal/manifest.json')
    source = Path(spec['source_checkpoint'])
    if sha(source) != spec['source_sha256'] or sha(snapshot/'spec.json') != manifest['spec_sha256']:
        raise ValueError('Source/spec identity mismatch')
    if sha(Path(spec['asset_path'])) != spec['asset_sha256']:
        raise ValueError('Asset identity mismatch')
    # Validate frozen implementation before importing it; shared code is not used.
    for name,expected in manifest.get('source_snapshot_sha256',{}).items():
        path=snapshot/name
        if not path.is_file() or sha(path)!=expected:
            raise ValueError('Snapshot identity mismatch: '+str(path))
    domain,standing=load_frozen_implementation(snapshot)
    report = {'simulation_steps': 0, 'ppo_updates': 0, 'asset_sha256': spec['asset_sha256'],
              'source_sha256': spec['source_sha256'], 'spec_sha256': sha(snapshot/'spec.json'),
              'inputs': {}, 'evaluations': {}, 'metric_blocks': [], 'checkpoints': {}}
    inputs = [snapshot/'spec.json', run/'formal/manifest.json',
              run/'formal/metrics.jsonl', run/'formal/terminal_report.json',
              snapshot/'recovery_recipe.py', snapshot/'recovery_standing.py',
              snapshot/'recovery_domain.py', snapshot/'recovery_runtime.py', snapshot/'domain_contract.py',
              run/'source_snapshot/native_stand/command_v6/stand_chain.py',
              run/'source_snapshot/native_stand/command_v6/tools/evaluate_checkpoint.py']
    report['identity_checks']={}
    for name,expected in manifest.get('source_snapshot_sha256',{}).items():
        path=snapshot/name
        report['identity_checks'][str(path)]='VALID' if path.is_file() and sha(path)==expected else 'INVALID'
        if report['identity_checks'][str(path)]=='INVALID':raise ValueError('Snapshot identity mismatch: '+str(path))
    for path in (run/'formal/progress.json',run/'chain_terminal_report.json',
                 Path('configs/experiments')/spec['experiment']/'budget.json'):
        if path.is_file():
            inputs.append(path)
            report.setdefault('accounting_evidence',{})[str(path)]=read(path)
        else:report.setdefault('missing_evidence',[]).append(str(path))
    for label, relative in [('source50', 'source_eval/evaluation_source.json'),
                            ('new100', 'formal/evaluation_100_0_0.json'),
                            ('new200', 'formal/evaluation_200_0_0.json'),
                            ('durability_source50', 'durability_100s.json')]:
        path = run/relative
        inputs.append(path)
        evaluation = read(path)
        episodes = evaluation['per_env']
        metric_keys = episodes[0]['standing_metrics'].keys()
        report['evaluations'][label] = {
            'passed_envs': evaluation['passed_envs'],
            'continuous_completed': sum(e['continuous_window_completed'] for e in episodes),
            'termination_reasons': [e['termination_reason'] for e in episodes],
            'failed_checks': [e['standing_failed_checks'] for e in episodes],
            'mean_metrics': {k: sum(e['standing_metrics'][k] for e in episodes)/len(episodes)
                             for k in metric_keys},
            'reported_protocol': evaluation['success_protocol']['standing_protocol']}
        if label == 'durability_source50':
            corrected, mismatches, short_window_differences = [], [], []
            for episode in episodes:
                series = torch.tensor(episode['compact_trace_100hz'])
                posture = torch.tensor(episode['posture_trace_100hz'])
                origin = series[0, 19:21].tolist()
                # Recover exact origin-independent gates. First saved xy is used
                # only for diagnostic drift; original pre-physics origin is absent.
                protocol = {**spec['recovery']['standing_task']['protocol'],
                            'seconds': 100., 'steady_window_s': [2., 100.],
                            'initial_xy': origin}
                result = standing.score_standing(series, posture, dt=.01, requested_s=100.,
                    protocol=protocol, runtime_fault=episode['runtime_fault'],
                    initial_valid=episode['initial_valid'],
                    terminated=not episode['continuous_window_completed'])
                short = standing.score_standing(series, posture, dt=.01, requested_s=100.,
                    protocol={**protocol, 'steady_window_s': [2., 10.]},
                    runtime_fault=episode['runtime_fault'], initial_valid=episode['initial_valid'],
                    terminated=not episode['continuous_window_completed'])
                for key, value in result['metrics'].items():
                    if key in ('net_drift_m', 'max_excursion_m'):
                        continue
                    if abs(value-episode['standing_metrics'][key]) > 2e-6:
                        mismatches.append({'env_id': episode['env_id'], 'field': key,
                                           'rescored': value, 'saved': episode['standing_metrics'][key]})
                short_window_differences.append({k: short['metrics'][k]-episode['standing_metrics'][k]
                    for k in ('height_steady_mean_m', 'mean_abs_pitch_rad', 'mean_abs_roll_rad')})
                corrected.append({'env_id': episode['env_id'], **result})
            from native_stand.command_v6.domain.evidence import effective_protocol,observed_protocol
            effective=effective_protocol({key:value for key,value in protocol.items() if key!='initial_xy'},
                requested_seconds=100.,steady_window_s=[2.,100.],sample_rate_hz=100.,scored_envs=len(episodes),
                termination_semantics='frozen first-episode offline rescore; drift origin reconstructed separately')
            effective=observed_protocol(effective,[len(e['compact_trace_100hz'])*.01 for e in episodes])
            report['durability_rescore'] = {'effective_protocol': effective,
                'passed_envs': sum(e['accepted'] for e in corrected), 'per_env': corrected,
                'saved_metric_mismatches_except_origin': mismatches,
                'short_window_minus_saved': short_window_differences,
                'drift_origin_limitation': 'First saved xy, not pre-physics origin; drift diagnostic only.'}
    rows = [json.loads(line) for line in (run/'formal/metrics.jsonl').read_text().splitlines()]
    for start, end in [(1, 50), (51, 100), (101, 150), (151, 200)]:
        block = [r for r in rows if start <= r['update'] <= end]
        counts = {k: sum(r['task_metrics']['counts'][k] for r in block)
                  for k in ('complete_successes', 'task_failures', 'runtime_faults')}
        samples = sum(r['rollout']['samples'] for r in block)
        completed = sum(r['rollout']['episodes']['completed'] for r in block)
        duration = sum((r['rollout']['episodes']['mean_duration_s'] or 0)*
                       r['rollout']['episodes']['completed'] for r in block)
        weighted = {k: sum(r['rollout']['weighted_mean'][k] for r in block)/len(block)
                    for k in block[0]['rollout']['weighted_mean']}
        event = (counts['complete_successes']*spec['reward']['success_once']+
                 counts['task_failures']*spec['reward']['failure_once'])/samples
        report['metric_blocks'].append({'updates': [start, end], 'counts': counts,
            'completed_episodes': completed, 'completed_mean_duration_s': duration/completed if completed else None,
            'continuous_weighted_means': weighted, 'continuous_sum': sum(weighted.values()),
            'event_reward_per_sample': event, 'estimated_total_per_sample': sum(weighted.values())+event,
            'value_loss_mean': sum(r['losses']['value'] for r in block)/len(block),
            'retention_raw_mean': sum(r['task_metrics']['standing_retention']['raw'] for r in block)/len(block),
            'contact_mean': sum(r['rollout']['dual_contact_fraction'] for r in block)/len(block),
            'saturation_mean': sum(r['rollout']['saturation_fraction'] for r in block)/len(block)})
    report['milestones'] = [{k: r[k] for k in ('update', 'losses', 'optimizer_learning_rates', 'rollout', 'task_metrics')}
                            for r in rows if r['update'] in (1, 2, 50, 100, 150, 200)]
    checkpoints = [('source50', source), ('new100', run/'formal/model_update_100.pt'),
                   ('new200', run/'formal/model_update_200.pt')]
    baseline = torch.load(source, map_location='cpu', weights_only=False)
    for label, path in checkpoints:
        inputs.append(path)
        checkpoint = torch.load(path, map_location='cpu', weights_only=False)
        data = {'sha256': sha(path), 'source_sha256': checkpoint['source_sha256'],
                'asset_sha256': checkpoint['asset_sha256'], 'spec_sha256': checkpoint['spec_sha256'],
                'std_param': checkpoint['actor']['distribution.std_param'].tolist(),
                'optimizer_lr': [g['lr'] for g in checkpoint['optimizer']['param_groups']],
                'curriculum': checkpoint['recovery_curriculum']}
        for network in ('actor', 'critic'):
            changes = {}
            for key, tensor in checkpoint[network].items():
                delta = tensor-baseline[network][key]
                changes[key] = {'delta_l2': float(delta.norm()), 'source_l2': float(baseline[network][key].norm())}
            data[network+'_parameter_changes'] = changes
        report['checkpoints'][label] = data
    # Exact reward counterfactual on the same source physical samples. Angular
    # direction is unnecessary: these costs depend on norm, yaw and x/z norm.
    old_path = source.parent/'source_snapshot/spec.json'
    inputs.append(old_path)
    old = read(old_path)
    source_eval = read(run/'source_eval/evaluation_source.json')
    counterfactual = {}
    for recipe_name, recipe in [('source_recipe', old), ('survival_recipe', spec)]:
        total_values, weighted_values = [], {}
        for e in source_eval['per_env']:
            s = torch.tensor(e['compact_trace_100hz'])
            p = torch.tensor(e['posture_trace_100hz'])
            c = torch.tensor(e['control_diagnostics_100hz'])
            g = torch.tensor(e['wheel_geometry_trace_100hz'])
            angular = torch.stack(((p[:, 9].square()-s[:, 9].square()).clamp_min(0).sqrt(),
                                   s[:, 9], torch.zeros_like(s[:, 9])), -1)
            linear = torch.stack(((p[:, 8].square()-p[:, 7].square()).clamp_min(0).sqrt(),
                                  torch.zeros_like(p[:, 7]), p[:, 7]), -1)
            offset = standing.longitudinal_geometry(g[:, :6].reshape(-1, 2, 3), g[:, 6:9]).abs()
            delta = c[1:, 18:24]-c[:-1, 18:24]
            n = len(delta)
            reward, _, weighted = domain.process_reward(s[1:, 6], torch.full((n,), .168),
                torch.full((n,), .36), torch.cos(s[1:, 15]), c[1:, 38:44], delta,
                (c[1:, (0, 1, 3, 4)]/1.6).square().mean(-1),
                torch.zeros(n, dtype=torch.bool), torch.zeros(n, dtype=torch.bool),
                weights=recipe['reward'], dt=.01, settling_config=recipe['recovery']['settling_reward'],
                linear_velocity=linear[1:], angular_velocity=angular[1:], pitch=p[1:, 0], roll=p[1:, 1],
                contact=s[1:, 10:12], wheel_velocity=c[1:, (8, 11)],
                support_balance=(s[1:, 10]-s[1:, 11]).abs()/s[1:, 10:12].sum(-1).clamp_min(1.),
                wheel_longitudinal_offset=offset[1:],
                standing_config=recipe['recovery']['standing_task']['reward'], standing_diagnostics=p[1:])
            total_values.append(reward)
            for key, values in weighted.items():
                weighted_values.setdefault(key, []).append(values)
        counterfactual[recipe_name] = {'mean_continuous_reward': float(torch.cat(total_values).mean()),
            'weighted_means': {k: float(torch.cat(v).mean()) for k, v in weighted_values.items()}}
    report['same_source_physical_inputs_reward'] = counterfactual
    report['limitations'] = [
        'No saved PPO observation/return/advantage/value batches or current-run gradient payloads; actual critic distributions and PPO-vs-BC gradients cannot be recovered.',
        'Reward counterfactual is deterministic source trajectory, not stochastic training; omits first sample and success/failure events.',
        'Retention selects first eligible 256 inputs of 8192, not uniform sampling; repeats them across 16 optimizer steps.',
        'Source control gate diagnostics are zero-filled despite diagnostic field names: recovery.gate_diagnostics=false.',
        'Milestone checkpoints precede milestone evaluation; curriculum confirmations in a checkpoint may predate progress JSON.'
    ]
    report['inputs'] = {str(p): sha(p) for p in inputs}
    report['snapshot_implementation']={str(p):sha(p) for p in snapshot.glob('*.py')}
    report['evidence_status']='VALID_WITH_LIMITATIONS'
    report['training_gradients']='UNKNOWN: not captured; no historical gradients reconstructed'
    for block in report['metric_blocks']:
        block['success_event_reward_per_sample']=block['counts']['complete_successes']*spec['reward']['success_once']/sum(
            r['rollout']['samples'] for r in rows if block['updates'][0]<=r['update']<=block['updates'][1])
        block['failure_event_reward_per_sample']=block['counts']['task_failures']*spec['reward']['failure_once']/sum(
            r['rollout']['samples'] for r in rows if block['updates'][0]<=r['update']<=block['updates'][1])
        block['timeout_event_reward_per_sample']=None
    extra_paths=[args.output.parent/'audit.md',args.output.parent/'audit_manifest.json']
    if any(p.exists() for p in extra_paths):raise FileExistsError('audit sidecar already exists')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    with extra_paths[0].open('x') as stream:
        stream.write('# Recovery corrected offline audit\n\n'
            'Frozen implementation; no simulation or PPO. Historical evidence preserved.\n\n'
            f"100s effective window: [2, 100]; passed {report['durability_rescore']['passed_envs']}/8.\n\n"
            'Legacy gate diagnostics are INVALID (runtime disabled); zero arrays are not physical measurements.\n\n'
            + '\n'.join('- '+text for text in report['limitations'])+'\n')
    with extra_paths[1].open('x') as stream:
        json.dump({'inputs':report['inputs'],'snapshot':report['snapshot_implementation'],
            'output_sha256':sha(args.output),'simulation':0,'ppo':0},stream,indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(args.output.resolve()),
        'durability_passed': report['durability_rescore']['passed_envs'],
        'durability_saved_metric_mismatches': report['durability_rescore']['saved_metric_mismatches_except_origin'],
        'blocks': [{k: v for k, v in b.items() if k != 'continuous_weighted_means'} for b in report['metric_blocks']],
        'counterfactual': counterfactual}, indent=2))


if __name__ == '__main__':
    main()
