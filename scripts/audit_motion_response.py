"""One-shot same-protocol B250/source vs completed short-course response audit."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(run, baseline, output):
    run, baseline, output = map(lambda p: Path(p).resolve(), (run, baseline, output))
    if output.exists():
        raise FileExistsError(output)
    inputs = {}

    def read(path):
        inputs[str(path)] = sha(path)
        return json.loads(path.read_text())

    terminal = read(run/'chain_terminal_report.json')
    if terminal['status'] not in ('COMPLETED', 'FAILED', 'STOPPED_BOUNDED'):
        raise ValueError('finished chain required; do not poll')
    spec = read(run/'formal/source_snapshot/spec.json')
    read(run/'manifest.json')
    read(run/'formal/manifest.json')
    read(run/'formal/terminal_report.json')
    read(run/'formal/candidate_selection.json')
    read(run/'smoke/wiring_certificate.json')
    read(Path(terminal['phase_results'][0]['run'])/'source_snapshot/spec.json')
    checkpoints = {'B250': Path(spec['source_checkpoint']),
                   'formal25': run/'formal/model_update_25.pt',
                   'formal50': run/'formal/model_update_50.pt'}
    identities = {name: {'path': str(path), 'sha256': sha(path)} for name, path in checkpoints.items()}
    for row in identities.values():
        inputs[row['path']] = row['sha256']
    if identities['B250']['sha256'] != spec['source_sha256']:
        raise ValueError('source SHA mismatch')
    groups = {
        'B250': sorted((run/'source_eval').glob('evaluation_source*.json')) +
                sorted(baseline.glob('evaluation_0[01].json')),
        'formal25': sorted((run/'formal').glob('evaluation_25_*.json')),
        'formal50': sorted((run/'formal').glob('evaluation_50_*.json'))}
    result = {'models': {}, 'identities': identities, 'inputs': inputs,
        'actual_usage': {key: terminal.get(key) for key in (
            'formal_updates', 'smoke_updates', 'formal_samples', 'smoke_samples', 'chain_wall_s')},
        'user_observation': {'roll_lean': True, 'scissor_wheel_longitudinal_offset_m': .05,
            'status': 'USER_REPORTED_NOT_MEASURED_BY_THIS_AUDIT',
            'checkpoint_and_command': 'not specified by user'},
        'simulation': 0, 'online_updates': 0, 'offline_optimizer_updates': 0}
    protocols = {}
    metadata_differences = []
    ignored_metadata = {'effective_protocol_sha256','scoring_protocol_sha256',
        'full_every_updates','checkpoint_every_updates','zero_every_updates','motion_commands','diagnostics',
        'observed_duration_per_env_s','actual_duration_seconds','unlock_full_updates','light_every_updates',
        'durability_only_for_selected','full_at_final','final_evaluation_seeds','run_final_durability'}
    for name, files in groups.items():
        rows = {}
        for path in files:
            d = read(path)
            if d['checkpoint_sha256'] != identities[name]['sha256']:
                raise ValueError('evaluation/checkpoint SHA conflict: '+str(path))
            target = tuple(d['target'][:2])
            if target[1] != 0 or str(target[0]) in rows:
                raise ValueError('duplicate/nonstraight command')
            protocol = d['effective_protocol']
            if target in protocols and protocols[target] != protocol:
                delta = {k: [protocols[target].get(k), protocol.get(k)] for k in set(protocols[target])|set(protocol)
                         if protocols[target].get(k) != protocol.get(k)}
                if set(delta)-ignored_metadata:
                    raise ValueError('same-command scoring/window protocol conflict: '+str(path))
                metadata_differences.append({'evaluation':str(path),'command':list(target),
                    'metadata_only_differences':delta})
            protocols.setdefault(target, protocol)
            envs = d['per_env']
            gate = d['capability_gate']
            if len(envs) != 8 or len(gate['per_env']) != 8 or protocol['scored_envs'] != 8:
                raise ValueError('incomplete scored environments')
            by_id = {row['env_id']: row for row in gate['per_env']}
            if len(by_id) != 8 or set(by_id) != {row['env_id'] for row in envs}:
                raise ValueError('environment identity conflict')
            metrics = ('mean_vx_mps', 'mean_abs_vx_mps', 'mean_abs_vx_error_mps',
                'mean_abs_vy_mps', 'mean_yaw_rad_s', 'mean_abs_yaw_error_rad_s',
                'stop_vx_abs_mps', 'net_drift_m', 'max_excursion_m', 'continuous_s',
                'dual_contact_fraction', 'peak_tilt_rad', 'height_steady_mean_m',
                'closure_max_m', 'saturation_fraction', 'hold_direction_fraction')
            per_env = [{**{k: row.get(k) for k in ('env_id', 'outcome', 'termination_reason')+metrics},
                        **by_id[row['env_id']]} for row in envs]
            required_metrics = ('mean_vx_mps','mean_abs_vx_error_mps','continuous_s')
            if any(row.get(k) is None for row in envs for k in required_metrics):
                raise ValueError('missing required physical/response metrics: '+str(path))
            values = {k: sum(row[k] for row in envs)/8 if all(row.get(k) is not None for row in envs)
                      else None for k in metrics}
            fields = d.get('fields', [])
            rows[str(target[0])] = {'command': list(target), 'evaluation': str(path),
                'effective_protocol_sha256': protocol['effective_protocol_sha256'],
                'scoring_protocol_sha256': protocol['scoring_protocol_sha256'],
                'accepted': gate['accepted'], 'passed_envs': gate['passed_envs'],
                'means': values, 'worst_env_MAE': max(row['mean_abs_vx_error_mps'] for row in envs),
                'failed_check_counts': dict(Counter(k for row in gate['per_env'] for k in row['failed_checks'])),
                'per_env': per_env, 'trace_fields': fields,
                'geometry_evidence': {'roll_rad': None, 'wheel_offset_m': None,
                    'reason': 'raw trace records aggregate tilt only; no roll/pitch or wheel centers'},
                'missing_metrics': sorted({k for row in envs for k in metrics if row.get(k) is None}),
                'physical_scope': gate.get('scope')}
        # Normalize numerical JSON command keys (+0.0 vs +0 etc).
        keyed = {float(k): v for k, v in rows.items()}
        if set(keyed) != {0, .5, -.5, 1, -1, 1.5, -1.5, 2, -2, 2.5, -2.5}:
            raise ValueError('incomplete 11-command comparison')
        v0 = keyed[0]['means']['mean_vx_mps']
        pairs = {}
        for c in (.5, 1., 1.5, 2., 2.5):
            vp, vn = keyed[c]['means']['mean_vx_mps'], keyed[-c]['means']['mean_vx_mps']
            pairs[str(c)] = {'gain': (vp-vn)/(2*c), 'asymmetry_mps': (vp+vn)/2-v0,
                'positive_vx': vp, 'negative_vx': vn,
                'complete_hold_both_directions': all(env['continuous_s']>=18. for command in (c,-c)
                    for env in keyed[command]['per_env'])}
        result['models'][name] = {'v0': v0, 'zero_mean_abs_vx': keyed[0]['means']['mean_abs_vx_mps'],
            'commands': rows, 'pairs': pairs}
    # The separate source +/-2.5 probe and regression differ in schedule metadata only;
    # compare explicitly rather than calling unequal raw protocol SHA equal.
    reference = protocols[(2., 0.)]
    for target, protocol in protocols.items():
        delta = {k: [reference.get(k), protocol.get(k)] for k in set(reference)|set(protocol)
                 if reference.get(k) != protocol.get(k)}
        if delta:
            metadata_differences.append({'command': list(target), 'differences_from_source_pos2': delta})
    result['protocol_comparison'] = {'same_command_source_vs_candidate':
        'old endpoints: exact effective match; +/-2.5 probe: same scoring/windows, different schedule/diagnostic metadata',
        'cross_command_metadata_differences': metadata_differences,
        'scope': 'no rescoring; original per-command gates preserved'}
    result['protocol_comparison']['observed_duration_note'] = (
        'requested scoring windows compared independently of observed duration; early termination never passes; '
        'any pair with incomplete hold is partial-window diagnostics, not complete response certification')
    lines = ['# Motion 同协议响应比较', '',
        '旧端点来源B250与formal25/50 effective protocol完全一致；±2.5独立probe评分/窗口一致，调度/诊断元数据不同，原SHA与gate保留。',
        '用户观察roll歪斜/轮心前后约5cm：现有trace缺roll及轮心坐标，不能量化或归因。', '',
        '|模型|zero vx|zero mean abs vx|', '|---|---:|---:|']
    for name, model in result['models'].items():
        lines.append(f"|{name}|{model['v0']:.6f}|{model['zero_mean_abs_vx']:.6f}|")
    lines += ['', '|模型|端点|增益g|不对称a m/s|双向保持完整|', '|---|---:|---:|---:|---|']
    for name, model in result['models'].items():
        for c, row in model['pairs'].items():
            lines.append(f"|{name}|{c}|{row['gain']:.6f}|{row['asymmetry_mps']:.6f}|{row['complete_hold_both_directions']}|")
    lines += ['', '|模型|命令|vx|MAE均值|最差env MAE|通过|失败原因计数|',
              '|---|---:|---:|---:|---:|---:|---|']
    for name, model in result['models'].items():
        for key, row in sorted(model['commands'].items(), key=lambda item: float(item[0])):
            lines.append(f"|{name}|{key}|{row['means']['mean_vx_mps']:.6f}|"
                f"{row['means']['mean_abs_vx_error_mps']:.6f}|{row['worst_env_MAE']:.6f}|"
                f"{row['passed_envs']}/8|{row['failed_check_counts']}|")
    lines += ['', '逐环境接触/tilt/height/closure/限矩/方向/停车/位移见comparison.json。',
        '限矩是100Hz policy采样；不是每5ms PD子步证明。tilt不是roll。',
        '若双向保持完整=False，增益仅作部分窗口诊断，不是完整验收统计；终止原因以逐环境原始记录为准。',
        '现象为高端点双向超速及响应增益扩大，不是整体增益收缩；采样因果待单变量实验。',
        '不从formal25/50续训，不解锁±3，不授权三seed或PPO。']
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (('comparison.json', result), ('audit_manifest.json', {'inputs': inputs})):
        with (output/name).open('x') as f:
            json.dump(data, f, indent=2, allow_nan=False)
    with (output/'comparison.md').open('x') as f:
        f.write('\n'.join(lines)+'\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.run, a.baseline, a.output_dir)
    print(json.dumps({'output': str(a.output_dir), 'models': result['identities'],
                      'simulation': 0, 'online_updates': 0}, indent=2))


if __name__ == '__main__':
    main()
