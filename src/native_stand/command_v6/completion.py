"""Local evidence analysis and at-most-once HAPI delivery.

Notification locking follows Fudan adapters/notifications/hapi.py; no Gym imports.
"""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def read(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).is_file() else default


def read_metrics(path):
    rows, issues = [], []
    if not Path(path).is_file():
        return rows, ['metrics.jsonl missing']
    lines = Path(path).read_text().splitlines()
    for index, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except ValueError:
            issues.append({'line': index + 1, 'kind': 'truncated_tail' if index == len(lines)-1 else 'invalid_line'})
    return rows, issues


def compact_report_value(value, key=''):
    """Presentation-only reduction; raw evidence/analysis remain untouched."""
    if isinstance(value,(dict,list)) and any(word in key.lower() for word in
            ('trace','diagnostics_100hz','geometry_100hz','control_rows')):
        return {'omitted_from_markdown':True,'raw_evidence_key':key,
                'item_count':len(value),'reason':'link raw evaluation instead of embedding arrays'}
    if isinstance(value,dict):
        return {name:compact_report_value(item,name) for name,item in value.items()}
    if isinstance(value,list):
        if len(value)>64:
            return {'omitted_from_markdown':True,'raw_evidence_key':key,'item_count':len(value)}
        return [compact_report_value(item,key) for item in value]
    return value


def plan(spec, phase):
    from .config import schedule
    from .domain.execution_limits import ExecutionLimits
    updates = 0 if phase == 'source_eval' else spec['budget'][phase + '_updates']
    schedules = [schedule(update, phase, spec['evaluation']) for update in range(1, updates+1)]
    if schedules and phase=='smoke':schedules[-1]['light']=True
    if schedules and phase=='formal' and spec.get('task')=='recovery' and spec['evaluation'].get('full_at_final'):
        schedules[-1]['full']=True
    cases = len(spec['curriculum']['stages'][spec['curriculum']['active_stage']]['commands'])
    full = sum(row['full'] for row in schedules)
    light = sum(row['light'] and not row['full'] for row in schedules)
    return {'updates': updates, 'samples': updates*spec['ppo']['envs']*spec['ppo']['steps_per_env'],
        'checkpoints': sum(row['checkpoint'] or row['light'] or row['full'] or index == updates
                           for index, row in enumerate(schedules, 1)),
        'light_evaluations': light*cases, 'full_evaluations': (full*cases if updates else 1),
        'training_wall_estimate_s': None, 'evaluation_wall_estimate_s': None,
        'estimate_reason': 'no measured plane-project runtime; historical mesh timing is not an equivalent benchmark',
        'wall_limit_s': ExecutionLimits.resolve(spec,phase).wall_s, 'terminal_reserve_s': 60 if updates else 30,
        'evaluation_fraction_target': [0.10, 0.15], 'frozen_schedule_not_skipped': True}


def evaluation_identity(spec, evaluator_sha):
    physical = {key: spec[key] for key in ('asset_sha256', 'ground', 'control', 'action', 'termination')}
    if spec.get('task')=='recovery':
        physical['recovery']=spec['recovery']
    result={'source_sha256': spec['source_sha256'], 'physical_sha256': identity(physical),
        'protocol_sha256': identity(spec['evaluation']), 'evaluator_sha256': evaluator_sha,
        'seed': spec['evaluation']['seed'], 'layout_envs': spec['evaluation']['envs'],
        'scored_envs': spec['evaluation']['scored_envs']}
    from .tools.evaluate_checkpoint import protocol_for_spec
    base=protocol_for_spec(spec,spec['evaluation']['seconds'])
    result['effective_protocols']={'zero':base}
    if spec.get('task')!='recovery':
        from .domain.evidence import effective_protocol
        result['effective_protocols']['motion']=effective_protocol(base,
            requested_seconds=base['requested_seconds'],
            steady_window_s=spec['evaluation'].get('motion_window_s',base['steady_window_s']),
            motion_window_s=base.get('motion_window_s'),parking_window_s=base.get('parking_window_s'),
            sample_rate_hz=base['sample_rate_hz'],scored_envs=base['scored_envs'],
            termination_semantics=base['termination_semantics'])
    if spec['evaluation'].get('protocol_identity') in ('capability_v2','motion_absolute_v3'):
        result['capability_commands']=spec.get('motion_posture',{}).get('assessment_commands',
            spec['curriculum']['stages'][spec['curriculum']['active_stage']]['commands'])
        if spec.get('motion_posture'):
            result['posture_acceptance']=spec['motion_posture']['acceptance']
        result['source_baseline_commands']=[[0,0],*spec.get('source_required_commands',
            [command for command in result['capability_commands'] if command!=[0,0]])]
        if spec.get('straight_high_speed_course'):
            result['straight_high_speed_course']=True
            result['course_stage']=spec['curriculum']['active_stage']
    return result


def classify(entry, expected):
    result = entry.get('result', {})
    if result.get('task')=='recovery':
        from native_stand.recovery.selection import classify_recovery
        return classify_recovery(entry,expected)
    rows = result.get('per_env', [])
    problems = []
    if entry.get('identity') != expected:
        problems.append('identity_mismatch')
    if entry.get('kind') != 'full':
        problems.append('light_only')
    if len(rows) != expected['scored_envs']:
        problems.append('missing_environments')
    fields = ('continuous_s', 'net_drift_m', 'max_excursion_m', 'dual_contact_fraction',
              'mean_abs_vx_error_mps', 'mean_abs_yaw_error_rad_s', 'height_steady_mean_m',
              'peak_tilt_rad', 'closure_max_m', 'saturation_fraction')
    if any(row.get(field) is None or not math.isfinite(float(row[field])) for row in rows for field in fields):
        problems.append('missing_metrics')
    if any(row.get('outcome') not in ('completed', 'task_failure') for row in rows):
        problems.append('runtime_fault_or_unknown')
    gate = result.get('capability_gate') if expected.get('capability_commands') else result.get('standing_gate')
    from native_stand.command_v6.domain.evidence import resolve_gate
    normalized=resolve_gate(result,'capability' if expected.get('capability_commands') else 'standing',
        expected_envs=expected['scored_envs'],expected_protocol=expected.get('effective_protocols',{}).get(
            'zero' if not any(result.get('target',[0,0])[:2]) else 'motion'))
    if not normalized['candidate_eligible']:
        problems.append('missing_gate')
    if expected.get('posture_acceptance') and any(
            not row.get('posture_geometry',{}).get('complete_window') or
            row.get('posture_cost_mean') is None or not math.isfinite(row['posture_cost_mean']) for row in rows):
        problems.append('missing_posture_window')
    eligible = not problems
    means = {field: sum(row[field] for row in rows)/len(rows) if rows and
        all(row.get(field) is not None and math.isfinite(float(row[field])) for row in rows) else None for field in fields}
    clean_rows=[{key:(None if isinstance(value,float) and not math.isfinite(value) else value)
                 for key,value in row.items() if key!='trace'} for row in rows]
    return {**{key: value for key, value in entry.items() if key != 'result'},
        'eligible': eligible, 'exclusion_reasons': problems,
        'accepted': eligible and bool(gate['accepted']), 'passed_envs': gate['passed_envs'] if gate else 0,
        'per_env': clean_rows, 'gate': gate, 'gate_evidence':normalized,'means': means,'command':result.get('target')}


def choose(entries, latest, expected, checkpoints=None):
    if expected.get('straight_high_speed_course'):
        stages={}
        for entry in entries:
            ident=entry.get('identity',{})
            if {k:v for k,v in ident.items() if k not in ('course_stage','capability_commands')} != {k:v for k,v in expected.items() if k not in ('course_stage','capability_commands')}:
                continue
            stages.setdefault(ident['course_stage'],[]).append(entry)
        selections={stage:choose_capability([classify(row,rows[0]['identity']) for row in rows],latest,rows[0]['identity'],checkpoints)
                    for stage,rows in stages.items()}
        evaluated=[stage for stage,selection in selections.items() if selection['best_new_evaluated_candidate']]
        current=selections[max(evaluated)] if evaluated else choose_capability([],latest,expected,checkpoints)
        accepted={str(stage):selection['accepted_candidate'] for stage,selection in selections.items() if selection['accepted_candidate']}
        source=next((selection['source_baseline'] for selection in selections.values() if selection['source_baseline']),None)
        baseline_entries=[row for rows in stages.values() for row in rows if row.get('role')=='source']
        if baseline_entries:
            baseline_expected={**expected,'capability_commands':expected.get('source_baseline_commands',
                baseline_entries[0]['identity'].get('capability_commands',[]))}
            baseline=choose_capability([classify(row,row['identity']) for row in baseline_entries],
                None,baseline_expected)
            source=baseline['source_baseline']
        candidates=[candidate for selection in selections.values() for candidate in selection['candidates']]
        reviewed={candidate['checkpoint_sha256'] for candidate in candidates if candidate['eligible']}
        result={**current,'accepted_by_stage':accepted,'source_baseline':source,
            'fallback_checkpoint':accepted[str(max(map(int,accepted)))] if accepted else source,
            'candidates':candidates,'full_eligible_count':sum(candidate['eligible'] for candidate in candidates),
            'unreviewed_checkpoints':[checkpoint for checkpoint in (checkpoints or ([latest] if latest else []))
                                     if checkpoint['sha256'] not in reviewed],
            'stage_selections':selections}
        from .domain.candidate_roles import register_roles
        return register_roles(result,source=source,latest=latest,
            best_new=result['best_new_evaluated_candidate'],best_overall=result.get('best_overall_candidate'),
            accepted=result['accepted_candidate'])
    classified = [classify(entry, expected) for entry in entries]
    if expected.get('capability_commands'):
        return choose_capability(classified,latest,expected,checkpoints)
    eligible = [entry for entry in classified if entry['eligible']]
    def rank(entry):
        means = entry['means']
        if entry.get('result_protocol')=='autonomous_rise':
            from native_stand.recovery.selection import rise_rank
            return rise_rank(entry)
        if entry.get('task')=='recovery' and entry.get('result_protocol')=='continuous_standing':
            if entry.get('objective')=='survival_level':
                return (-int(entry['accepted']),-entry['passed_envs'],-means['continuous_s'],
                    -entry['evaluation_curriculum_stage'] if entry['accepted'] else 0,
                    means['mean_abs_pitch_rad']+means['mean_abs_roll_rad'],
                    -means['dual_contact_fraction'],means['closure_max_m'],entry['checkpoint_sha256'])
            return (-int(entry['accepted']),-means['continuous_s'],-entry['passed_envs'],
                means.get('net_drift_m',float('inf')),means.get('mean_abs_pitch_rad',float('inf')),
                means.get('mean_abs_roll_rad',float('inf')),means.get('mean_mirror_error_rad',float('inf')),
                -means['dual_contact_fraction'],entry['checkpoint_sha256'])
        if entry.get('task')=='recovery':
            return (-int(entry['accepted']),-entry['passed_envs'],
                (means['recovery_s'] if means['recovery_s'] is not None else float('inf'))
                    if entry['accepted'] else -means['continuous_s'],
                means['closure_max_m'],entry['checkpoint_sha256'])
        return (-int(entry['accepted']), -means['continuous_s'], -entry['passed_envs'],
                means['net_drift_m'], -means['dual_contact_fraction'], entry['checkpoint_sha256'])
    eligible.sort(key=rank)
    accepted = next((entry for entry in eligible if entry['accepted']), None)
    reviewed = {entry['checkpoint_sha256'] for entry in eligible}
    best_overall=eligible[0] if eligible else None
    from .domain.candidate_roles import is_source
    best_new=next((entry for entry in eligible if not is_source(entry,expected.get('source_sha256'))),None)
    result={'latest_checkpoint': latest, 'best_observed_candidate': best_overall,
        'best_new_evaluated_candidate':best_new,'accepted_candidate': accepted,
        'source_baseline': next((entry for entry in classified if entry.get('role') == 'source'), None),
        'unreviewed_checkpoints': [checkpoint for checkpoint in (checkpoints or ([latest] if latest else []))
                                  if checkpoint['sha256'] not in reviewed],
        'candidates': classified, 'full_eligible_count': len(eligible),
        'ranking': ('Autonomous rise: full acceptance, passed envs, retained passed envs, complete valid hold windows, fewer terminations, standing entries, SHA; failed pre-entry duration/height/reward unused'
            if any(row.get('result_protocol')=='autonomous_rise' for row in classified) else
            'Survival/level: accepted, passed envs, continuous duration, accepted curriculum stage, pitch+roll, contact, closure, SHA; motion/symmetry/reward unused'
            if any(row.get('objective')=='survival_level' for row in classified) else
            'Recovery: accepted, successful envs, recovery time for accepted / survival for failed, closure, SHA; reward unused'
            if any(row.get('task')=='recovery' for row in classified) else
            'accepted, mean continuous survival, passed envs, mean drift, contact, SHA tie-break; reward unused')}
    recovery_candidates=[entry for entry in eligible if entry.get('task')=='recovery']
    if recovery_candidates:
        def diagnostic(entry):
            rows=entry['per_env']
            contact=[r.get('standing_metrics',{}).get('dual_contact_fraction',r.get('dual_contact_fraction')) for r in rows]
            tilt=[r.get('standing_metrics',{}).get('peak_tilt_rad',r.get('tilt_peak_rad')) for r in rows]
            prefix=[r.get('diagnostic_hold_prefix_s') for r in rows]
            return {'checkpoint':entry['checkpoint'],'sha256':entry['checkpoint_sha256'],
                'accepted':entry['accepted'],'min_contact':min(contact) if all(v is not None for v in contact) else None,
                'max_tilt':max(tilt) if all(v is not None for v in tilt) else None,
                'min_hold_prefix_s':min(prefix) if all(v is not None for v in prefix) else None}
        rows=[diagnostic(entry) for entry in recovery_candidates]
        result['diagnostic_comparison']={'candidates':rows,'certification_ranking_unchanged':True,
            'best_contact':max((r for r in rows if r['min_contact'] is not None),key=lambda r:r['min_contact'],default=None),
            'best_posture':min((r for r in rows if r['max_tilt'] is not None),key=lambda r:r['max_tilt'],default=None),
            'best_prefix':max((r for r in rows if r['min_hold_prefix_s'] is not None),key=lambda r:r['min_hold_prefix_s'],default=None),
            'scope':'diagnostic alternatives; no new acceptance or stitched model capability'}
    from .domain.candidate_roles import register_roles
    return register_roles(result,source=result['source_baseline'],latest=latest,best_new=best_new,
                          best_overall=best_overall,accepted=accepted)


def choose_capability(classified,latest,expected,checkpoints=None):
    """Require every command on the same checkpoint; never accept a zero-only result."""
    required={tuple(command) for command in expected['capability_commands']}
    groups={}
    for entry in classified:
        groups.setdefault((entry['checkpoint_sha256'],entry['role']),[]).append(entry)
    candidates=[]
    for entries in groups.values():
        commands={tuple(row['command']) for row in entries if row['command'] is not None and row['eligible']}
        eligible=commands==required and len(entries)==len(required) and all(row['eligible'] for row in entries)
        base=next((row for row in entries if row['command']==[0,0]),entries[0])
        candidate={**base,'eligible':eligible,'accepted':eligible and all(row['accepted'] for row in entries),
            'exclusion_reasons':[] if eligible else ['incomplete_command_set'],
            'passed_envs':sum(row['passed_envs'] for row in entries),'command_results':entries,
            'per_env':[],'gate':{'per_env':[]},'command':None}
        for entry in entries:
            for row in entry['per_env']:
                env_id=f"{entry['command']}:{row['env_id']}"
                candidate['per_env'].append({**row,'env_id':env_id,'command':entry['command']})
                check=next((item for item in (entry['gate'] or {}).get('per_env',[]) if item['env_id']==row['env_id']),None)
                if check:
                    candidate['gate']['per_env'].append({**check,'env_id':env_id})
        candidate['gate'].update(accepted=candidate['accepted'],passed_envs=candidate['passed_envs'],
            scored_envs=len(required)*expected['scored_envs'])
        candidates.append(candidate)
    eligible=[row for row in candidates if row['eligible']]
    posture_rule=expected.get('posture_acceptance')
    if posture_rule:
        source=next((r for r in eligible if r['role']=='source'),None)
        def score_posture(candidate):
            values=[r.get('posture_cost_mean') for r in candidate['per_env']]
            return sum(values)/len(values) if values and all(v is not None and math.isfinite(v) for v in values) else None
        baseline=score_posture(source) if source else None
        def component_means(candidate):
            metrics=[r.get('posture_geometry',{}).get('posture_component_means') for r in candidate['per_env']]
            if not metrics or any(not isinstance(m,dict) for m in metrics):return None
            keys=set(metrics[0])
            if any(set(m)!=keys or any(not math.isfinite(v) for v in m.values()) for m in metrics):return None
            return {k:sum(m[k] for m in metrics)/len(metrics) for k in keys}
        baseline_components=component_means(source) if source else None
        for candidate in eligible:
            value=score_posture(candidate)
            motion_pass=candidate['accepted']
            improved=(value is not None and baseline is not None and
                value<=baseline*(1-posture_rule['minimum_relative_improvement']))
            components=component_means(candidate)
            component_guard=bool(components and baseline_components and all(
                components[k]<=baseline_components[k]*(1+posture_rule['maximum_component_regression_fraction'])+.005
                for k in components))
            candidate['posture_goal']={'motion_retained':motion_pass,'mean_cost':value,
                'baseline_cost':baseline,'improvement_passed':improved,'component_guard':component_guard,
                'component_means':components,'baseline_component_means':baseline_components,
                'scope':'all assessment command environments'}
            candidate['accepted']=motion_pass and improved and component_guard and candidate['role']!='source'
            candidate['gate']['accepted']=candidate['accepted']
        passing=[r for r in eligible if r['accepted']]
        updates=sorted({r['update'] for r in passing})
        repeated=len(updates)>=posture_rule['required_confirmations'] and updates[-1]-updates[0]>=posture_rule['minimum_confirmation_spacing_updates']
        if not repeated:
            for candidate in passing:
                candidate['accepted']=False
                candidate['gate']['accepted']=False
                candidate['posture_goal']['awaiting_repeated_confirmation']=True
    def rank(row):
        motion=[env for env in row['per_env'] if env['command']!=[0,0]]
        endpoint=max((abs(command[0]) for command in required),default=0.)
        retained=all(case['accepted'] for case in row['command_results']
                     if abs(case['command'][0])<endpoint or case['command']==[0,0])
        current=all(case['accepted'] for case in row['command_results'] if abs(case['command'][0])==endpoint)
        worst=max((env.get('mean_abs_vx_error_mps',float('inf')) for env in motion),default=float('inf'))
        posture_score=row.get('posture_goal',{}).get('mean_cost')
        return (-int(row['accepted']),-int(retained),-int(current),-row['passed_envs'],
                (posture_score if posture_score is not None else float('inf')) if posture_rule else 0.,worst,
                max((env['peak_tilt_rad'] for env in row['per_env']),default=float('inf')),
                -min((env['dual_contact_fraction'] for env in row['per_env']),default=0.))
    eligible.sort(key=rank)
    accepted=next((row for row in eligible if row['accepted'] and row.get('role')!='source'),None)
    from .domain.candidate_roles import is_source
    best_new=next((row for row in eligible if not is_source(row,expected.get('source_sha256'))),None)
    reviewed={row['checkpoint_sha256'] for row in eligible}
    result={'latest_checkpoint':latest,'best_observed_candidate':best_new,
        'best_new_evaluated_candidate':best_new,'accepted_candidate':accepted,
        'source_baseline':next((row for row in candidates if row['role']=='source'),None),
        'candidates':candidates,'full_eligible_count':len(eligible),
        'unreviewed_checkpoints':[row for row in (checkpoints or ([latest] if latest else [])) if row['sha256'] not in reviewed],
        'ranking':'complete same-checkpoint stage set; zero/old retention, current bilateral pass, passed environments, worst velocity error, tilt/contact; motion displacement and reward unused'}
    from .domain.candidate_roles import register_roles
    return register_roles(result,source=result['source_baseline'],latest=latest,best_new=best_new,
        best_overall=eligible[0] if eligible else None,accepted=accepted)


def _finalize_report(run, exit_code=None, *, corrected_output=None):
    run = Path(run).resolve()
    destination=run
    if corrected_output is not None:
        destination=Path(corrected_output).resolve()
        if destination==run or destination.is_relative_to(run):
            raise ValueError('Corrected report must be outside immutable run')
        destination.mkdir(parents=True,exist_ok=False)
    with (destination/'completion.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if corrected_output is None and (run/'report_ready.json').is_file():
            return read(run/'analysis.json')
        manifest = read(run/'manifest.json', {})
        spec = read(run/'source_snapshot/spec.json')
        if spec is None:
            raise ValueError('immutable run spec snapshot missing')
        if manifest.get('spec_sha256') and sha(run/'source_snapshot/spec.json')!=manifest['spec_sha256']:
            raise ValueError('Recorded configuration SHA differs')
        terminal = read(run/'terminal_report.json', {})
        progress = read(run/'progress.json', {})
        metrics, issues = read_metrics(run/'metrics.jsonl')
        if spec.get('student_training'):
            from native_stand.students.training_evidence import finalize
            return finalize(run,spec,manifest,terminal,progress,metrics,exit_code,destination)
        expected = manifest.get('evaluation_identity') or evaluation_identity(spec, manifest.get('evaluator_sha256'))
        entries = read(run/'candidate_registry.json', [])
        baseline_run = manifest.get('source_baseline_run')
        if baseline_run and Path(baseline_run).resolve() != run:
            if spec.get('engineering_recovery'):
                from .tools.motion_recovery_certificate import migrated_source_entries
                try:
                    entries+=migrated_source_entries(spec,expected,recorded_receipt=read(run/'submission_receipt.json')) if (run/'submission_receipt.json').is_file() else migrated_source_entries(spec,expected,report_manifest=manifest,report_snapshot=run/'source_snapshot')
                except (OSError,ValueError,KeyError,TypeError) as error:
                    issues.append({'source_evidence':'MISSING_OR_INVALID','error':str(error)})
            else:entries += [entry for entry in read(Path(baseline_run)/'candidate_registry.json', []) if entry.get('role') == 'source']
        for entry in entries:
            reference=entry.get('evaluation')
            if reference:
                folder=Path(entry.get('evidence_run') or run)
                raw=(folder/reference).resolve()
                expected_sha=entry.get('evaluation_sha256')
                if (not raw.is_relative_to(folder.resolve()) or not raw.is_file() or
                    expected_sha is None or sha(raw)!=expected_sha):
                    entry['identity']={**entry.get('identity',{}),'raw_integrity':'missing_or_changed'}
                    issues.append({'evaluation':reference,'status':'MISSING_OR_INVALID'})
            checkpoint=Path(entry['checkpoint'])
            if not checkpoint.is_file() or sha(checkpoint)!=entry['checkpoint_sha256']:
                entry['identity']={**entry.get('identity',{}),'checkpoint_integrity':'missing_or_changed'}
        selection = choose(entries, terminal.get('latest_checkpoint') or progress.get('latest_checkpoint'), expected,
                           read(run/'checkpoint_inventory.json'))
        totals = {field: sum(float(row.get(field, 0)) for row in metrics) for field in
                  ('rollout_s', 'ppo_s', 'evaluation_s', 'serialization_s')}
        if terminal.get('source_evaluation_s') is not None:
            totals['evaluation_s']+=terminal['source_evaluation_s']
        latest=selection['latest_checkpoint']
        evaluated_checkpoint_shas={entry['checkpoint_sha256'] for entry in selection['candidates'] if entry['eligible']}
        selection['latest_evaluation_status']=('REVIEWED' if latest and latest['sha256'] in evaluated_checkpoint_shas
                                              else 'UNREVIEWED' if latest else None)
        samples = terminal.get('samples', progress.get('samples', 0))
        wall = terminal.get('wall_s')
        best, source = selection['best_observed_candidate'], selection['source_baseline']
        comparison = {field: best['means'][field]-source['means'][field] for field in best['means']
            if best['means'][field] is not None and source['means'][field] is not None} if best and source and source['eligible'] else None
        conflict = exit_code is not None and exit_code != 0 and terminal.get('status') == 'COMPLETED'
        monitor=read(run/'monitor_exit.json',{})
        event_id = identity({'attempt': manifest.get('attempt_id'), 'run': str(run), 'session': manifest.get('hapi_session')})[:24]
        analysis = {'event_id': event_id, 'run': str(run), 'status': terminal.get('status', 'UNKNOWN'),
            'exit_code': exit_code, 'terminal_exit_conflict': conflict,
            'accounting_conflict': monitor.get('ledger_updates',terminal.get('actual_updates')) != terminal.get('actual_updates'),
            'wall_including_cleanup_s':monitor.get('attempt_wall_including_cleanup_s'),
            'actual_updates': terminal.get('actual_updates', progress.get('actual_updates', 0)), 'samples': samples,
            'accounted_updates_without_metrics':max(0,terminal.get('actual_updates',progress.get('actual_updates',0))-len(metrics)),
            'reason': terminal.get('reason') or terminal.get('failure') or 'phase budget/normal completion; consult terminal',
            'wall_s': wall, 'timing_s': totals, 'metrics_issues': issues,
            'initialization_s':terminal.get('initialization_s'),
            'unattributed_wall_s':max(0.,wall-sum(totals.values())-(terminal.get('initialization_s') or 0.)) if wall else None,
            'rollout_samples_per_s': samples/totals['rollout_s'] if totals['rollout_s'] else None,
            'end_to_end_samples_per_s': samples/wall if wall else None,
            'evaluation_fraction': totals['evaluation_s']/wall if wall else None,
            'evaluation_planning_target_exceeded':bool(wall and totals['evaluation_s']/wall>.15),
            'comparison_best_minus_source': comparison, 'candidate_selection': selection,
            'accepted_by_stage':progress.get('accepted_by_stage',{}),
            'final_capability_certificate':progress.get('final_capability_certificate'),
            'confirmed': ['only identity-matched complete evaluations are ranked'],
            'unknown': ['reward/actuator/dynamics causal explanations require separate evidence'],
            'timing_caveat': 'host elapsed timing; GPU asynchronous work not independently synchronized'}
        from .domain.evidence_summary import compact
        analysis=compact(analysis);selection=compact(selection)
        from .tools.storage_budget import actual_bytes
        analysis['artifact_storage_actual']=actual_bytes(run)
        from .domain.evidence_summary import selection_summary
        write(destination/'candidate_selection.json', selection)
        analysis['candidate_selection']=selection_summary(selection)
        analysis['candidate_selection_reference']={'path':str((destination/'candidate_selection.json').resolve()),'sha256':sha(destination/'candidate_selection.json')}
        write(destination/'analysis.json', analysis)
        report = ['# Native '+('straight-line capability' if spec.get('straight_high_speed_course') else 'recovery' if spec.get('task')=='recovery' else 'standing')+' completion', f'Event: {event_id}', f'Run: {run}',
            f"Terminal: {analysis['status']}; exit={exit_code}; conflict={conflict}",
            f"Updates/samples: {analysis['actual_updates']} / {samples}; wall={wall}",
            f"Timing seconds: {totals}; rollout/end-to-end samples/s: {analysis['rollout_samples_per_s']} / {analysis['end_to_end_samples_per_s']}",
            f"Reason: {analysis['reason']}", f"Eligible full evaluations: {selection['full_eligible_count']}",
            f"Best: {best['checkpoint'] if best else 'none'}; accepted={bool(selection['accepted_candidate'])}",
            f"Latest: {selection['latest_checkpoint']}; unreviewed={selection['unreviewed_checkpoints']}",
            f"Stage models: {progress.get('accepted_by_stage',{})}; final multi-seed certificate: {progress.get('final_capability_certificate')}",
            f"Best-minus-source metrics: {comparison}", '## Per-environment evidence']
        for entry in selection['candidates']:
            report.append(f"Candidate {entry['checkpoint']}: accepted={entry['accepted']}; exclusions={entry['exclusion_reasons']}")
            for row in entry['per_env']:
                failures=next((check['failed_checks'] for check in (entry.get('gate') or {}).get('per_env',[])
                               if check['env_id']==row['env_id']),[])
                report.append(json.dumps(compact_report_value({**row,'failed_checks':failures})))
        report += ['Missing values are unknown, never zero. Drift alone does not prove a reward defect.',
                   'Read analysis.json and candidate_selection.json for gates and identities. This report does not authorize more training.']
        (destination/'completion_report.md').write_text('\n\n'.join(report)+'\n')
        write(destination/'report_ready.json', {'event_id': event_id, 'status': 'report_ready',
            'report_sha256': sha(destination/'completion_report.md'), 'time': time.time(),
            'original_run':str(run),'corrected_output':corrected_output is not None})
        return analysis


def finalize_report(run,exit_code=None,*,corrected_output=None):
    """Always deliver a conservative ended-run summary even if rich scoring fails."""
    if corrected_output is not None:
        destination=Path(corrected_output).resolve();original=Path(run).resolve()
        if destination==original or destination.is_relative_to(original):raise ValueError('Corrected report must be outside immutable run')
        if destination.exists():raise FileExistsError(destination)
    try:return _finalize_report(run,exit_code,corrected_output=corrected_output)
    except Exception as error:
        run=Path(run).resolve();destination=Path(corrected_output).resolve() if corrected_output else run
        if corrected_output and (destination==run or destination.is_relative_to(run)):raise
        destination.mkdir(parents=True,exist_ok=True)
        with (destination/'completion.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if (destination/'report_ready.json').exists():return read(destination/'analysis.json',{})
            def safe(name):
                try:return read(run/name,{}) or {}
                except (OSError,ValueError,TypeError):return {}
            terminal=safe('terminal_report.json');manifest=safe('manifest.json');monitor=safe('monitor_exit.json')
            event=identity({'attempt':manifest.get('attempt_id'),'run':str(run),'session':manifest.get('hapi_session')})[:24]
            analysis={'event_id':event,'run':str(run),'status':terminal.get('status','UNKNOWN'),
                'actual_updates':terminal.get('actual_updates'),'samples':terminal.get('samples'),
                'wall_including_cleanup_s':monitor.get('attempt_wall_including_cleanup_s'),
                'reason':terminal.get('reason') or terminal.get('failure'),'report_status':'MISSING_OR_INVALID_EVIDENCE',
                'report_error':repr(error),'accepted':False,'candidate_selection':{'accepted_candidate':None},
                'training_accounting_unchanged':True,'capability_status':'UNKNOWN'}
            selection={'accepted_candidate':None,'best_observed_candidate':None,'evidence_status':'MISSING_OR_INVALID'}
            write(destination/'analysis.json',analysis);write(destination/'candidate_selection.json',selection)
            (destination/'completion_report.md').write_text('# Native terminal summary\n\n'+json.dumps(analysis,indent=2,ensure_ascii=False)+'\n')
            write(destination/'report_ready.json',{'event_id':event,'status':'summary_ready','report_sha256':sha(destination/'completion_report.md'),
                'time':time.time(),'original_run':str(run),'corrected_output':corrected_output is not None})
            return analysis


def transport(session, message):
    result = subprocess.run(['hapi', 'ping-peer', session, '--message-file', '-'], input=message,
        text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    return {'status': 'sent' if result.returncode == 0 else 'failed', 'returncode': result.returncode}


def notify(run, send=transport):
    run = Path(run)
    with (run/'hapi_notification.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ready = read(run/'report_ready.json')
        if not ready or not (run/'completion_report.md').is_file() or ready['report_sha256'] != sha(run/'completion_report.md'):
            raise ValueError('report not ready')
        reviewed = read(run/'completion_review.json', {})
        if reviewed.get('event_id') == ready['event_id']:
            return {'status': 'reviewed', 'event_id': ready['event_id']}
        prior = read(run/'hapi_notification.json')
        if prior:
            if prior['status']=='sending':
                prior['status']='unknown_delivery'
                write(run/'hapi_notification.json',prior)
            return prior
        manifest = read(run/'manifest.json', {})
        session = manifest.get('hapi_session')
        # Match frozen submission/authorization records; never silently reroute a report.
        route_errors=[]
        frozen=read(run/'source_snapshot/spec.json',{})
        if frozen.get('notifications',{}).get('enabled') is False:
            event={'event_id':ready['event_id'],'status':'notification_disabled',
                   'reason':'Frozen experiment explicitly disables external delivery'}
            write(run/'hapi_notification.json',event)
            return event
        declared=frozen.get('authorization',{})
        configured=declared.get('hapi_session') if isinstance(declared,dict) else None
        if configured and configured!=session:route_errors.append('frozen authorization target differs from manifest')
        route=manifest.get('notification_route')
        if route is not None:
            if (not isinstance(route,dict) or route.get('target_session')!=session
                    or route.get('owner_session')!=session):
                route_errors.append('explicit notification owner/target differs')
        spec_path=manifest.get('spec_path')
        if spec_path:
            receipt=read(Path(spec_path).with_name('chain_submission.json'),{})
            if receipt and (receipt.get('chain')!=str(run.resolve()) or receipt.get('hapi_session')!=session):
                route_errors.append('chain submission notification target differs')
        event = {'event_id': ready['event_id'], 'session_id': session, 'status': 'sending', 'time': time.time()}
        if route_errors:
            event.update(status='notification_route_conflict',errors=route_errors)
            write(run/'hapi_notification.json',event)
            return event
        if not session:
            event['status'] = 'notification_not_configured'
        write(run/'hapi_notification.json', event)
        if not session:
            return event
        selection = read(run/'candidate_selection.json', {})
        best = selection.get('best_observed_candidate')
        message = (f"事件ID：{ready['event_id']}\nrun：{run}\n终态：{read(run/'analysis.json')['status']}\n"
            f"最佳候选：{best['checkpoint'] if best else '暂无'}；通过：{bool(selection.get('accepted_candidate'))}\n"
            f"报告：{run/'completion_report.md'}\n请读取报告复盘，并按当前有效用户授权处理后续工作。")
        if 'stage_selections' in selection:
            certificate=read(run/'analysis.json').get('final_capability_certificate') or {}
            message += (f"\n已通过阶段：{list(selection.get('accepted_by_stage',{}))}；"
                f"完整±4三seed认证：{bool(certificate.get('accepted'))}。阶段通过不等于最终高速通过。")
        try:
            event.update(send(session, message))
        except FileNotFoundError:
            event['status']='failed'
            event['reason']='hapi executable not found; no delivery attempted'
        except (subprocess.TimeoutExpired, OSError):
            event['status'] = 'unknown_delivery'
        write(run/'hapi_notification.json', event)
        return event


def acknowledge(run):
    run = Path(run)
    with (run/'hapi_notification.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ready = read(run/'report_ready.json')
        if not ready:
            raise ValueError('report not ready')
        previous=read(run/'completion_review.json')
        if previous and previous['event_id']!=ready['event_id']:
            raise ValueError('review belongs to another event')
        write(run/'completion_review.json', {'event_id': ready['event_id'], 'status': 'reviewed', 'time': time.time()})
