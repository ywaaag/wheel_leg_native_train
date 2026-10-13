"""Restricted Motion None-window engineering recovery; evidence is not runtime permission."""
import copy
import hashlib
import json
from pathlib import Path

from .experiment_preparation import checked_input,differences,digest
from .execution_identity import identity,execution_dependencies
from .update_proof import compare as actor_proof
from ..domain.experiment_identity import sections
from ..domain.evaluation_config import identities
from ..domain.evidence import validate_effective_protocol,resolve_gate
from ..domain.recovery_accounting import calculate,validate_remaining

VERSION='motion_light_none_window_recovery_v1'


def stable_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def behavior(spec):
    return sections(spec)['behavior']


def migration_recipe(spec):
    """Unknown fields fail closed; only publication/auth/budget metadata may differ."""
    result=copy.deepcopy(spec)
    for key in ('experiment','artifacts','authorization','authorization_note','notifications',
            'authorization_receipt','chain_submission','engineering_recovery','source_evidence_reference',
            'budget','execution_source_root'):
        result.pop(key,None)
    if 'motion_posture' in result:result['motion_posture'].pop('chain_wall_s',None)
    return result


def code_contract(spec):
    data=identity(spec)
    return {'project_snapshot_sha256':data['location_independent_modules_sha256'],
        'execution_dependencies':data['execution_dependencies'],'PPO_sha256':data['PPO_sha256'],
        'dependencies':data['dependencies']}


def changes(old,current):
    a=execution_dependencies(old['relative_modules_sha256'],'motion')
    b=current['execution_dependencies']
    return differences(a['modules_sha256'],b['modules_sha256'])


def audit(request,spec):
    """Every stage runs independently. A stage failure never deletes prior facts."""
    inputs={};missing=[];conflicts=[];facts={};old=None;failed_manifest=None;target=None
    try:target=code_contract(spec)
    except Exception as exc:
        missing.append('execution_identity: '+str(exc))
    def read(path):
        p,sha=checked_input(path);inputs[p]=sha;return json.loads(Path(p).read_text())
    def bind(path,expected=None):
        p,sha=checked_input(path,expected);inputs[p]=sha;return p,sha
    def stage(name,fn):
        try:facts[name]=fn()
        except Exception as exc:
            missing.append(name+': '+str(exc));facts.setdefault(name,{'status':'MISSING'})
    failed=Path(request['failed_run']).resolve();supplement=Path(request['supplement']).resolve()
    source=Path(request['source_run']).resolve();ledger=Path(request['ledger']).resolve()
    supbook=Path(request['supplement_ledger']).resolve()
    def failure():
        nonlocal old,failed_manifest
        old=read(failed/'source_snapshot/spec.json');failed_manifest=read(failed/'manifest.json')
        terminal=read(failed/'terminal_report.json');book=read(ledger)
        if old.get('task')=='recovery' or spec.get('task')=='recovery':raise ValueError('Motion only recovery')
        if terminal.get('status')!='FAILED':raise ValueError('Original FAILED terminal required')
        reason=terminal.get('failure',{})
        if reason.get('failure_stage')!='milestone_evaluation' or "NoneType" not in reason.get('exception','') or 'window' not in reason.get('traceback',''):
            raise ValueError('Unsupported failure; only known light posture None-window exception')
        if terminal.get('actual_updates')!=1 or terminal.get('samples')!=old['ppo']['envs']*old['ppo']['steps_per_env']:
            raise ValueError('Expected exactly one completed bounded smoke update')
        attempt=book['attempts'].get(failed_manifest['attempt_id'])
        if not attempt or attempt['status']!='FAILED' or attempt['updates']!=1 or Path(attempt['output_dir']).resolve()!=failed:
            raise ValueError('Failed exact ledger/terminal updates differ')
        if failed_manifest['spec_sha256']!=digest(failed/'source_snapshot/spec.json'):raise ValueError('Failed spec SHA differs')
        if migration_recipe(old)!=migration_recipe(spec):conflicts.append('behavior recipe changed or unreviewed runtime field')
        checkpoint=terminal['latest_checkpoint'];bind(checkpoint['path'],checkpoint['sha256'])
        bind(old['source_checkpoint'],old['source_sha256']);bind(old['asset_path'],old['asset_sha256'])
        for key in ('asset_module','colleague_config'):
            bind(old[key+'_path'],old[key+'_sha256'])
        import torch
        saved=torch.load(checkpoint['path'],map_location='cpu',weights_only=False)
        if saved.get('update')!=1 or saved.get('asset_sha256')!=old['asset_sha256'] or saved.get('spec_sha256')!=failed_manifest['spec_sha256']:
            raise ValueError('Smoke checkpoint internal identity differs')
        proof=json.loads(json.dumps(actor_proof(old['source_checkpoint'],checkpoint['path'])))
        if not proof['actor_parameters_changed']:raise ValueError('Saved actor update not proven')
        from .prepare_motion_experiment import full_checkpoint
        # Strict own actor/critic/Adam/RNG readback, no optimizer update.
        import contextlib,io
        with contextlib.redirect_stdout(io.StringIO()):
            state=full_checkpoint(saved,old)
            source_state=full_checkpoint(torch.load(old['source_checkpoint'],map_location='cpu',weights_only=False),old)
        return {'status':'PROVEN','attempt_id':failed_manifest['attempt_id'],'terminal_sha256':digest(failed/'terminal_report.json'),
            'original_spec_sha256':failed_manifest['spec_sha256'],'source_sha256':old['source_sha256'],
            'asset_sha256':old['asset_sha256'],'smoke_checkpoint':checkpoint,'update_proof':proof,
            'smoke_state':state,'formal_initialization_state':source_state,'original_failure':reason,'actual_updates':1,'samples':terminal['samples']}
    stage('optimizer_wiring',failure)
    def accounting():
        book=read(ledger);chain=read(Path(request['chain_terminal']));sb=read(supbook)
        for row in book.get('historical_attempts',[]):
            for key in ('ledger','terminal'):bind(row[key],row[key+'_sha256'])
        if abs(sum(r['wall_s'] for r in book.get('historical_attempts',[]))-book.get('historical_chain_wall_s',0))>1e-5:
            raise ValueError('Historical chain wall sum differs')
        settled=read(supplement/'terminal_report.json');sm=read(supplement/'manifest.json')
        attempt=sb['attempts'].get(sm['attempt_id'])
        if not attempt or attempt['status']!='COMPLETED' or settled['status']!='COMPLETED' or attempt.get('updates',0)!=0:
            raise ValueError('Supplement exact PPO0 settlement missing')
        return calculate(book,chain,sb,formal_limit=request.get('formal_updates',50))
    stage('accounting',accounting)
    def supplemental():
        if old is None:raise ValueError('Failed frozen spec unavailable')
        sm=read(supplement/'manifest.json');st=read(supplement/'terminal_report.json');frozen=read(supplement/'source_snapshot/spec.json')
        if sm['spec_sha256']!=digest(supplement/'source_snapshot/spec.json') or sm['asset_sha256']!=old['asset_sha256']:
            raise ValueError('Supplement spec/asset identity differs')
        if st.get('actual_updates')!=0 or st.get('samples',0)!=0 or st['status']!='COMPLETED':raise ValueError('Supplement not completed PPO0')
        requests=sm.get('requests')
        if not requests or len(requests)!=3:raise ValueError('Supplement requires explicit zero/positive/negative light cases')
        required=[[0,0],[.5,0],[-.5,0]];rows=[]
        from .evaluate_checkpoint import batch_protocol
        checkpoint=facts['optimizer_wiring']['smoke_checkpoint']['sha256']
        for index,target_command in enumerate(required):
            case=read(supplement/f'evaluation_{index:02d}.json');request_row=requests[index]
            if case['checkpoint_sha256']!=checkpoint or request_row['sha256']!=checkpoint:
                raise ValueError('Supplement checkpoint differs from failed smoke')
            if case.get('asset_sha256')!=old['asset_sha256'] or case.get('spec_sha256')!=sm['spec_sha256']:
                raise ValueError('Supplement raw identity differs')
            if case.get('target')!=target_command or request_row['target']!=target_command:raise ValueError('Missing light command direction')
            protocol=case['effective_protocol'];validate_effective_protocol(protocol)
            expected=batch_protocol(old,{**request_row,'evaluation_mode':'light'},True)
            if identities(protocol)['scoring_sha256']!=identities(expected)['scoring_sha256']:
                raise ValueError('Supplement light diagnostic scoring differs')
            if (protocol['requested_seconds']!=old['evaluation']['light_seconds'] or protocol['motion_window_s'] is not None or
                    not case.get('engineering_diagnostic_only') or case['capability_gate'].get('accepted') or case['capability_gate'].get('status')!='NOT_RUN'):
                raise ValueError('Light validation must never grant full capability')
            envs=case['per_env'];n=old['evaluation']['scored_envs']
            if len(envs)!=n or {e['env_id'] for e in envs}!=set(range(n)):raise ValueError('Supplement scored env coverage missing')
            expected_samples=round((protocol['steady_window_s'][1]-protocol['steady_window_s'][0])/old['control']['policy_dt_s'])+1
            for e in envs:
                if e.get('outcome')!='completed' or e.get('continuous_s',0)<protocol['requested_seconds']-1e-5:
                    raise ValueError('Supplement incomplete/runtime-fault episode')
                geometry=e.get('posture_geometry')
                if not geometry or not geometry.get('complete_window') or geometry.get('samples')!=expected_samples:
                    raise ValueError('Posture diagnostic window incomplete')
            rows.append({'path':str((supplement/f'evaluation_{index:02d}.json').resolve()),
                'sha256':digest(supplement/f'evaluation_{index:02d}.json'),'target':target_command,
                'protocol':protocol,'scored_envs':n,'valid_samples_per_env':expected_samples,'capability_accepted':False})
        return {'status':'PROVEN_ENGINEERING_ONLY','cases':rows,'full_capability_certified':False}
    stage('fault_path_repair',supplemental)
    def source_stage():
        if old is None:raise ValueError('Original spec unavailable')
        sm=read(source/'manifest.json');st=read(source/'terminal_report.json');frozen=read(source/'source_snapshot/spec.json')
        if st['status']!='COMPLETED' or st.get('actual_updates',0)!=0:raise ValueError('Source completion missing')
        if sm['spec_sha256']!=digest(source/'source_snapshot/spec.json') or migration_recipe(frozen)!=migration_recipe(old):raise ValueError('Original source recipe differs')
        if (sm['execution_identity']['relative_modules_sha256']!=failed_manifest['execution_identity']['relative_modules_sha256'] or
                sm['execution_identity']['PPO_sha256']!=failed_manifest['execution_identity']['PPO_sha256']):
            raise ValueError('Source and smoke historical execution dependencies differ')
        registry=read(source/'candidate_registry.json');entries=[e for e in registry if e.get('role')=='source']
        from .evaluation_loader import load
        from .evaluate_checkpoint import protocol_for_spec
        targets=[];evidence=[]
        for entry in entries:
            ref=source/entry['evaluation'];bind(ref,entry.get('evaluation_sha256'))
            raw,reference=load(source,entry,spec_sha256=sm['spec_sha256'],checkpoint_sha256=old['source_sha256'],asset_sha256=old['asset_sha256'])
            protocol=raw['effective_protocol'];validate_effective_protocol(protocol)
            if identities(protocol)['scoring_sha256']!=identities(protocol_for_spec(old,old['evaluation']['seconds']))['scoring_sha256']:
                raise ValueError('Source full protocol differs')
            gate=resolve_gate(raw,'capability',expected_envs=old['evaluation']['scored_envs'],expected_protocol=protocol)
            if gate.get('status')!='PASSED' or not gate.get('candidate_eligible'):raise ValueError('Original full source capability missing or failed')
            rows=raw['per_env']
            if len(rows)!=old['evaluation']['scored_envs'] or any(e['continuous_s']<old['evaluation']['seconds']-1e-5 or e['outcome']!='completed' for e in rows):
                raise ValueError('Original source full window incomplete')
            targets.append(raw['target']);evidence.append({**reference,'protocol_sha256':identities(protocol)['scoring_sha256'],
                'passed_envs':len(rows),'seconds':old['evaluation']['seconds'],'target':raw['target']})
        required=[[0,0],*old['source_evaluation_commands']]
        if len(entries)!=len(required) or {tuple(x) for x in targets}!={tuple(x) for x in required}:raise ValueError('Source nine-command coverage differs')
        return {'status':'PROVEN_ORIGINAL_SOURCE','run':str(source),'evaluations':evidence,
            'manifest_evaluator_sha256':sm.get('evaluator_sha256'),'capability_scope':'original source evidence; not smoke/new model acceptance'}
    stage('source_capability',source_stage)
    def review_stage():
        if failed_manifest is None or target is None:raise ValueError('Failed/current execution manifest unavailable')
        sm=read(supplement/'manifest.json');old_identity=failed_manifest['execution_identity'];new_identity=sm['execution_identity']
        requested_changes=changes(old_identity,target)
        supplemental_changes=differences(execution_dependencies(old_identity['relative_modules_sha256'],'motion')['modules_sha256'],
            execution_dependencies(new_identity['relative_modules_sha256'],'motion')['modules_sha256'])
        review=read(request['change_review'])
        if review.get('version')!=1 or review.get('status')!='REVIEWED' or not review.get('reviewer') or not review.get('reason'):
            raise ValueError('Explicit reviewed migration required; placeholder is not approval')
        if review.get('target_changes')!=requested_changes or review.get('supplement_changes')!=supplemental_changes:
            raise ValueError('Per-file review SHA stale or incomplete')
        rows=review.get('decisions',[])
        needed={r['field'] for r in requested_changes+supplemental_changes}
        if {r.get('module') for r in rows}!=needed or any(not r.get('reason') or r.get('disposition') not in
                ('engineering_only','unrelated_to_motion','fault_fix_verified','diagnostic_only') for r in rows):
            raise ValueError('Every changed module needs scoped reasoning; behavior changes cannot be approved here')
        critical=('env.py','learning.py','command_v6/learning.py','command_v6/learning_distribution.py',
            'command_v6/domain/reward.py','command_v6/domain/contract.py','command_v6/runtime/env.py','command_v6/runtime/configure.py')
        critical_diffs=[p for p in critical if old_identity['relative_modules_sha256'].get(p)!=target['execution_dependencies']['modules_sha256'].get(p)]
        if critical_diffs:raise ValueError('Unchanged control/reward/network contract violated: '+str(critical_diffs))
        for dep in ('PPO_sha256','dependencies'):
            if old_identity.get(dep)!=target[dep] or new_identity.get(dep)!=target[dep]:raise ValueError('PPO/package identity changed')
        if old_identity['relative_modules_sha256'].get('command_v6/domain/posture_geometry.py')==new_identity['relative_modules_sha256'].get('command_v6/domain/posture_geometry.py'):
            raise ValueError('Fault window fix not present in supplemental execution')
        # Bind actual target files too, so stale code is rejected at every consumer.
        current=identity(spec)
        for p,sha in target['execution_dependencies']['modules_sha256'].items():
            # The actual frozen load is independently verified by identity(); bind
            # stable declared inputs, not temporary run snapshot locations.
            path=Path(current.get('declared_source_root') or current['source_root'])/'native_stand'/p;bind(path,sha)
        return {'status':'REVIEWED','review_path':str(Path(request['change_review']).resolve()),
            'review_sha256':digest(request['change_review']),'target_changes':requested_changes,
            'supplement_changes':supplemental_changes,'decisions':rows,
            'failed_project_snapshot_sha256':old_identity['location_independent_modules_sha256'],
            'supplement_project_snapshot_sha256':new_identity['location_independent_modules_sha256'],
            'target_identity':target,'old_execution_dependencies':execution_dependencies(old_identity['relative_modules_sha256'],'motion')}
    stage('code_migration',review_stage)
    return {'version':VERSION,'status':'CONFLICTING' if conflicts else 'MISSING' if missing else 'READY',
        'missing':missing,'conflicts':conflicts,'request':copy.deepcopy(request),'facts':facts,'inputs_sha256':inputs,
        'behavior_sha256':stable_hash(behavior(spec)),
        'migration_recipe_sha256':stable_hash(migration_recipe(spec)),
        'storage_sha256':stable_hash(sections(spec)['storage']),'schedule_sha256':stable_hash(sections(spec)['evaluation_schedule']),
        'authorization':'UNAUTHORIZED','original_failed_terminal_changed':False,
        'new_candidate_capability_certified':False,'optimization_wiring_is_not_capability':True,
        'scope':'one failed light posture None-window + one PPO0 repair, original full source retained; no new smoke/PPO allowance'}


def validate(spec,book=None):
    reference=spec.get('engineering_recovery')
    if not reference or set(reference)!={'version','certificate','sha256','single_use_id'}:raise ValueError('Engineering recovery reference malformed')
    if reference['version']!=VERSION:raise ValueError('Unsupported recovery type')
    path,sha=checked_input(reference['certificate'],reference['sha256']);record=json.loads(Path(path).read_text())
    if record['status']!='READY' or record['version']!=VERSION:raise ValueError('Recovery certificate not READY')
    for name,expected in record['inputs_sha256'].items():checked_input(name,expected)
    if record['behavior_sha256']!=stable_hash(behavior(spec)) or record['migration_recipe_sha256']!=stable_hash(migration_recipe(spec)):raise ValueError('Recovery behavior binding differs')
    if record['storage_sha256']!=stable_hash(sections(spec)['storage']) or record['schedule_sha256']!=stable_hash(sections(spec)['evaluation_schedule']):
        raise ValueError('Recovery storage/schedule differs without review')
    if reference['single_use_id']!=stable_hash({'failed_attempt':record['facts']['optimizer_wiring']['attempt_id'],
        'terminal_sha256':record['facts']['optimizer_wiring']['terminal_sha256']}):raise ValueError('Recovery single-use identity differs')
    # Recompute all original evidence and stages, don't trust a hand-authored READY string.
    actual=audit(record['request'],spec)
    # Full snapshots are provenance, not a permit to mutate execution dependencies.
    # Unrelated excluded Recovery files may change; selected files and every bound
    # evidence SHA above remain strict. Newly added selected modules still differ.
    expected=copy.deepcopy(record)
    for data in (actual,expected):
        migration=data.get('facts',{}).get('code_migration',{})
        target=migration.get('target_identity',{})
        target.pop('project_snapshot_sha256',None)
        target.get('execution_dependencies',{}).pop('excluded_modules',None)
    if actual!=expected:raise ValueError('Recovery certificate/evidence revalidation differs')
    if book is not None:validate_remaining(spec,book,record['facts']['accounting'])
    return record


def historical_report_certificate(spec, manifest, snapshot):
    """Read ended-run provenance, never grant a new execution permission."""
    reference=spec['engineering_recovery']
    path,_=checked_input(reference['certificate'],reference['sha256'])
    record=json.loads(Path(path).read_text())
    if record['status']!='READY' or record['version']!=VERSION:
        raise ValueError('Historical recovery certificate not READY')
    snapshot=Path(snapshot)
    checked_input(snapshot/'spec.json',manifest['spec_sha256'])
    if json.loads((snapshot/'spec.json').read_text())!=spec:
        raise ValueError('Historical report spec differs')
    if stable_hash(behavior(spec))!=record['behavior_sha256']:
        raise ValueError('Historical behavior differs')
    target=record['facts']['code_migration']['target_identity']
    actual=manifest['execution_identity']
    if actual['execution_dependencies']!=target['execution_dependencies']:
        raise ValueError('Recorded run execution differs from reviewed certificate')
    for field in ('PPO_sha256','dependencies'):
        if actual[field]!=target[field]:raise ValueError('Recorded dependency differs: '+field)
    # Manifest records unarchived execution modules; archived files are byte checked.
    for name,sha in manifest.get('source_snapshot_sha256',{}).items():
        checked_input(snapshot/name,sha)
    modules=actual['modules']
    for name,sha in record['inputs_sha256'].items():
        if name in modules:
            if modules[name]!=sha:raise ValueError('Historical module receipt differs: '+name)
        else:checked_input(name,sha)
    return record


def migrated_source_entries(spec,expected_identity, *, report_manifest=None, report_snapshot=None):
    record=(historical_report_certificate(spec,report_manifest,report_snapshot)
            if report_manifest is not None else validate(spec))
    folder=Path(record['facts']['source_capability']['run'])
    entries=json.loads((folder/'candidate_registry.json').read_text())
    allowed={r['path']:r['sha256'] for r in record['facts']['source_capability']['evaluations']}
    result=[]
    for row in entries:
        if row.get('role')!='source':continue
        path=(folder/row['evaluation']).resolve();checked_input(path,allowed[str(path)])
        result.append({**row,'original_identity':row['identity'],'identity':copy.deepcopy(expected_identity),
            'engineering_migration':spec['engineering_recovery'],'evidence_run':str(folder),
            'evaluation_sha256':allowed[str(path)]})
    return result
