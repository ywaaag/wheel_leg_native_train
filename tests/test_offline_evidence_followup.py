import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import torch

from native_stand.command_v6.domain.evidence import effective_protocol
from native_stand.command_v6.tools.correct_evidence import audit_run, collect_run
from native_stand.command_v6.tools.health_check import digest


def save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


@pytest.fixture
def frozen_run(tmp_path):
    run = tmp_path / 'historical'
    phase = run / 'formal'
    snapshot = phase / 'source_snapshot'
    snapshot.mkdir(parents=True)
    source = tmp_path / 'source.pt'
    actor = {'mlp.0.weight': torch.ones(4, 150), 'distribution.std_param': torch.ones(6)}
    model = {'update': 12, 'asset_sha256': 'asset', 'spec_sha256': 'source_spec',
        'actor': actor, 'critic': {'mlp.0.weight': torch.ones(4, 150)},
        'optimizer': {'param_groups': [{'lr': 3e-5}], 'state': {0: {'step': torch.tensor(3)}}}}
    torch.save(model, source)
    asset = tmp_path / 'fixture.usd'
    asset.write_text('fixture physics identity only')
    model['asset_sha256'] = digest(asset)
    torch.save(model, source)
    spec = {'experiment': 'nonexistent_fixture', 'source_checkpoint': str(source), 'source_sha256': digest(source),
        'source_update': 12, 'source_spec_sha256': 'source_spec', 'asset_path': str(asset),
        'asset_sha256': digest(asset), 'evaluation': {'scored_envs': 2},
        'reward': {'success_once': 10, 'failure_once': -1}}
    save(snapshot / 'spec.json', spec)
    for name in ('domain_protocol.py', 'evaluate_checkpoint.py'):
        (snapshot / name).write_text('# complete fixture frozen identity\n')
    frozen = {path.name: digest(path) for path in snapshot.iterdir()}
    evaluator = hashlib.sha256((frozen['domain_protocol.py'] + frozen['evaluate_checkpoint.py']).encode()).hexdigest()
    manifest = {'spec_sha256': digest(snapshot / 'spec.json'), 'source_snapshot_sha256': frozen,
        'source_sha256': digest(source), 'asset_sha256': digest(asset), 'evaluator_sha256': evaluator}
    save(phase / 'manifest.json', manifest)
    save(phase / 'progress.json', {'actual_updates': 7})
    save(phase / 'terminal_report.json', {'actual_updates': 7, 'status': 'COMPLETED', 'exit_code': 0})
    model.update(update=7, spec_sha256=manifest['spec_sha256'], source_sha256=digest(source))
    candidate = phase / 'model_update_7.pt'
    torch.save(model, candidate)
    protocol = effective_protocol({}, requested_seconds=10, steady_window_s=[2, 10],
        sample_rate_hz=100, scored_envs=2, termination_semantics='first episode')
    result = {'task': 'recovery', 'checkpoint': str(candidate), 'checkpoint_sha256': digest(candidate),
        'spec_sha256': manifest['spec_sha256'], 'evaluator_sha256': evaluator, 'effective_protocol': protocol,
        'recovery_gate': {'accepted': True, 'passed_envs': 2, 'per_env': [{'env_id': 0, 'accepted': True},
                                                                            {'env_id': 1, 'accepted': True}]},
        'per_env': [{'env_id': i, 'termination_reason': 'evaluation_window', 'continuous_s': 10,
                     'standing_metrics': {'mean_abs_roll_rad': .03},
                     'control_diagnostics_100hz': [[0.] * 54] * 2} for i in range(2)]}
    save(phase / 'evaluation_7_arbitrary_name.json', result)
    (phase / 'metrics.jsonl').write_text(json.dumps({'update': 7, 'rollout': {'samples': 100,
        'weighted_mean': {'upright': .03}}, 'task_metrics': {'counts': {'complete_successes': 2, 'task_failures': 3}}}) + '\n')
    return run, phase, spec, manifest, result


def test_generic_discovery_frozen_identity_and_reward_separation(frozen_run, tmp_path):
    run, phase, spec, manifest, result = frozen_run
    report, inputs = collect_run(run)
    assert len(report['evaluations']) == 1
    assert report['evaluations'][0]['gate_evidence']['status'] == 'PASSED'
    assert report['evaluations'][0]['protocol_status'] == 'VALID'
    assert report['evaluator_identity'][str(phase)]['actual_sha256'] == manifest['evaluator_sha256']
    assert all('/src/native_stand/' not in path for path in inputs)
    candidate = report['checkpoints'][str(phase / 'model_update_7.pt')]
    assert candidate['evaluated'] and candidate['status'] == 'VALID'
    assert candidate['actor_sha256'] and candidate['critic_sha256'] and candidate['optimizer_sha256'] and candidate['std_sha256']
    reward = report['reward_blocks'][0]
    assert reward['continuous_reward'] == {'upright': .03}
    assert reward['success_event_reward'] == .2
    assert reward['failure_event_reward'] == -.03
    assert reward['timeout_event_reward'] is None
    diagnostic = report['evaluations'][0]['diagnostics_validity']['control_diagnostics_100hz']
    assert diagnostic['valid'] is False and diagnostic['value'] is None and diagnostic['sample_count'] == 0
    output = tmp_path / 'audit'
    audit_run(run, output)
    assert {'audit.json', 'audit.md', 'audit_manifest.json', 'corrected_report.md', 'corrected_analysis.json'} <= {path.name for path in output.iterdir()}
    assert all(digest(path) == expected for path, expected in inputs.items())


@pytest.mark.parametrize('conflict', ['spec', 'asset', 'snapshot', 'evaluator', 'checkpoint', 'protocol'])
def test_identity_conflicts_are_structured_invalid(frozen_run, conflict):
    run, phase, spec, manifest, result = frozen_run
    if conflict == 'spec':
        manifest['spec_sha256'] = 'incorrect'
    elif conflict == 'asset':
        Path(spec['asset_path']).write_text('changed fixture')
    elif conflict == 'snapshot':
        (phase / 'source_snapshot/domain_protocol.py').write_text('modified')
    elif conflict == 'evaluator':
        manifest['evaluator_sha256'] = 'incorrect'
    elif conflict == 'checkpoint':
        result['checkpoint_sha256'] = 'incorrect'
    elif conflict == 'protocol':
        result['effective_protocol']['steady_window_s'] = [3, 10]
    save(phase / 'manifest.json', manifest)
    save(phase / 'evaluation_7_arbitrary_name.json', result)
    report, _ = collect_run(run)
    assert report['evidence_status'] == 'INVALID'
    assert any(row['status'] == 'INVALID' for row in report['issues'])


def test_missing_snapshot_protocol_and_source_are_unknown(frozen_run):
    run, phase, spec, manifest, result = frozen_run
    (phase / 'source_snapshot/domain_protocol.py').unlink()
    Path(spec['source_checkpoint']).unlink()
    del result['effective_protocol']
    save(phase / 'evaluation_7_arbitrary_name.json', result)
    report, _ = collect_run(run)
    assert report['evidence_status'] == 'UNKNOWN'
    assert any('source.pt' in row['path'] for row in report['issues'])
    assert report['evaluations'][0]['protocol_status'] == 'UNKNOWN'


def test_unevaluated_checkpoint_is_not_accepted(frozen_run):
    run, phase, *_ = frozen_run
    latest = phase / 'model_update_99.pt'
    latest.write_bytes((phase / 'model_update_7.pt').read_bytes())
    save(phase / 'candidate_selection.json', {'latest_checkpoint': {'path': str(latest), 'sha256': digest(latest)}})
    report, _ = collect_run(run)
    row = report['checkpoints'][str(latest)]
    assert row['evaluated'] is False
    assert row['evaluation_status'].startswith('UNKNOWN')
    assert report['candidate_roles']['formal/candidate_selection.json']['accepted_candidate'] is None


def test_bad_checkpoint_and_json_are_reported(frozen_run):
    run, phase, *_ = frozen_run
    (phase / 'model_bad.pt').write_bytes(b'not a checkpoint')
    (phase / 'evaluation_bad.json').write_text('{broken')
    report, _ = collect_run(run)
    assert report['evidence_status'] == 'INVALID'
    assert report['checkpoints'][str(phase / 'model_bad.pt')]['status'] == 'INVALID'


def test_exclusive_outputs_and_history_untouched(frozen_run, tmp_path):
    run, *_ = frozen_run
    before = {str(path): digest(path) for path in run.rglob('*') if path.is_file()}
    output = tmp_path / 'corrected'
    audit_run(run, output)
    preserved = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError):
        audit_run(run, output)
    with pytest.raises(ValueError):
        audit_run(run, run / 'new_output')
    assert preserved == {path.name: path.read_bytes() for path in output.iterdir()}
    assert before == {str(path): digest(path) for path in run.rglob('*') if path.is_file()}


def test_generic_script_handles_missing_inputs_without_legacy_milestones(tmp_path):
    run = tmp_path / 'empty'
    run.mkdir()
    output = tmp_path / 'audit'
    project = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(project / 'scripts/audit_recovery_survival.py'),
        '--run', str(run), '--output-dir', str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads((output / 'audit.json').read_text())
    assert report['evidence_status'] == 'UNKNOWN'
    assert set(path.name for path in output.iterdir()) == {'audit.json', 'audit.md', 'audit_manifest.json'}
    assert 'model_update_100.pt' not in json.dumps(report)


def test_legacy_loader_uses_frozen_contract_domain_and_standing(tmp_path):
    snapshot = tmp_path / 'snapshot'
    snapshot.mkdir()
    (snapshot / 'domain_contract.py').write_text('FROZEN_SENTINEL = 17\n')
    (snapshot / 'recovery_domain.py').write_text(
        'from native_stand.command_v6.domain.contract import FROZEN_SENTINEL\n'
        'def reward_height_gate(): return FROZEN_SENTINEL\n')
    (snapshot / 'recovery_standing.py').write_text(
        'from native_stand.recovery.domain import reward_height_gate\n'
        'def value(): return reward_height_gate()\n')
    script = Path(__file__).resolve().parents[1] / 'scripts/audit_recovery_survival.py'
    code = ('import importlib.util; from pathlib import Path; '
        f'spec=importlib.util.spec_from_file_location("offline_audit",{str(script)!r}); '
        'module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); '
        f'domain,standing=module.load_frozen_implementation(Path({str(snapshot)!r})); '
        'assert standing.value()==17')
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_chain_manifest_resolves_nonstandard_arm_ledger(frozen_run, tmp_path):
    run, phase, spec, manifest, _ = frozen_run
    alternate = tmp_path / 'configs/pair/positive_arm/spec.json'
    alternate.parent.mkdir(parents=True)
    alternate.write_bytes((phase / 'source_snapshot/spec.json').read_bytes())
    ledger = alternate.with_name('budget.json')
    save(ledger, {'attempts': {}, 'used': {'formal': 7}})
    save(run / 'manifest.json', {'kind': 'cohort_width_ab', 'config': {'arms': {'A': {
        'spec': str(alternate), 'sha256': digest(alternate)}}}})
    report, inputs = collect_run(run)
    association = report['ledger_associations'][str(phase)]
    assert association['paths'] == [str(ledger)]
    assert association['source'] == 'manifest spec path'
    assert str(ledger) in inputs
    assert not any('ledger evidence absent' == row['reason'] for row in report['issues'])
