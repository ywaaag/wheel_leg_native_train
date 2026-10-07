"""Shared smoke evidence validation; no fixed update number or evaluation filename."""
import hashlib
import json
from pathlib import Path
from .domain.execution_plan import smoke_plan
from .domain.episode_summary import normalize as episode_summary


def smoke_certificate(folder, spec):
    folder=Path(folder)
    errors=[]
    inputs={}
    def read(name):
        path=folder/name
        if not path.is_file():errors.append('missing '+name);return {}
        inputs[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        try:return json.loads(path.read_text())
        except (OSError,ValueError):errors.append('invalid '+name);return {}
    progress=read('progress.json')
    terminal=read('terminal_report.json')
    manifest=read('manifest.json')
    frozen_spec=read('source_snapshot/spec.json')
    if frozen_spec!=spec:errors.append('smoke frozen spec differs')
    if inputs.get('source_snapshot/spec.json')!=manifest.get('spec_sha256'):
        errors.append('smoke spec SHA differs')
    if progress.get('actual_updates')!=spec['budget']['smoke_updates']:
        errors.append('actual smoke update count differs')
    if terminal.get('actual_updates')!=progress.get('actual_updates'):
        errors.append('terminal/progress update conflict')
    if not progress.get('actor_parameters_changed'):errors.append('actor update unproven')
    if terminal.get('failure') or terminal.get('status') not in ('COMPLETED','STOPPED_BOUNDED'):
        errors.append('smoke terminal failure')
    if manifest.get('source_sha256')!=spec.get('source_sha256'):
        errors.append('source identity differs')
    try:
        requirements=smoke_plan(spec)
    except (KeyError,ValueError,TypeError) as exc:
        errors.append('wiring smoke plan invalid: '+str(exc))
        requirements={}
    if requirements.get('budget_sufficient') is False:
        errors.append('smoke sampling budget cannot cover the required event')
    if requirements.get('required_event') is not None or requirements.get('required_groups'):
        metrics_path=folder/'metrics.jsonl'
        try:
            inputs['metrics.jsonl']=hashlib.sha256(metrics_path.read_bytes()).hexdigest()
            metrics=[json.loads(line) for line in metrics_path.read_text().splitlines()]
            if requirements['required_event']=='normal_timeout':
                count=sum(row.get('task_metrics',{}).get('training_episode',{}).get('normal_timeouts',0)
                          for row in metrics)
            elif requirements['required_event'] is not None:
                count=sum(episode_summary(row.get('rollout',{}).get('episodes',{}))['completed']
                          for row in metrics)
            else:count=0
            if requirements['required_event'] is not None and count<requirements['minimum_event_count']:
                errors.append('smoke did not observe the required '+requirements['required_event'])
            if requirements['required_event'] is not None and not any((row.get('rollout',{}).get('episodes',{}).get('max_duration_s') or 0)>=requirements['required_event_duration_s']-1e-4
                       for row in metrics):
                errors.append('smoke did not record a complete required-duration training episode')
            for group in requirements.get('required_groups',[]):
                observed=[episode_summary(item) for row in metrics
                          for item in (row.get('task_metrics') or {}).get('episodes_by_pose',[])
                          if item.get('family')==group['family'] and
                          ('pose_id' not in group or item.get('pose_id')==group['pose_id'])]
                eligible=[item for item in observed if (item.get('max_duration_s') or 0)>=group.get('minimum_duration_s',0.)]
                count=sum(item['completed'] for item in eligible)
                if group.get('require_runtime_initial_valid'):
                    # Max duration and validity must refer to the same episode set.
                    count=sum(item['completed'] for item in eligible
                              if item.get('runtime_initial_valid_episodes')==item['completed'])
                if count<group.get('minimum_completed',1):
                    errors.append('smoke task group evidence missing: '+group['family']+'/'+str(group.get('pose_id','*')))
        except (OSError,ValueError,TypeError):
            errors.append('required smoke event metrics missing or invalid')
    evaluations=[case.get('path') for row in progress.get('evaluations',[]) for case in row.get('cases',[]) if case.get('path')]
    if not evaluations:errors.append('no recorded smoke evaluation')
    for name in evaluations:
        if Path(name).name!=name:errors.append('invalid evaluation path');continue
        result=read(name)
        if result.get('outcome_counts',{}).get('runtime_fault',0):errors.append('evaluation runtime fault')
        if not result.get('per_env'):errors.append('evaluation evidence absent')
        if spec.get('evaluation',{}).get('scored_envs') and len(result.get('per_env',[]))!=spec['evaluation']['scored_envs']:
            errors.append('evaluation scored environment count differs')
        if spec.get('source_sha256') and spec.get('asset_sha256'):
            for field,expected in (('source_sha256',spec['source_sha256']),('asset_sha256',spec['asset_sha256']),
                                   ('spec_sha256',manifest.get('spec_sha256'))):
                if result.get(field)!=expected:errors.append('evaluation '+field+' differs')
            checkpoint=Path(result.get('checkpoint',''))
            if not checkpoint.is_file() or checkpoint.resolve().parent!=folder.resolve():
                errors.append('evaluation checkpoint missing or outside smoke run')
            else:
                inputs[str(checkpoint.name)]=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
                if result.get('checkpoint_sha256')!=inputs[str(checkpoint.name)]:errors.append('evaluation checkpoint SHA differs')
            from .domain.evidence import validate_effective_protocol
            try:validate_effective_protocol(result.get('effective_protocol',{}))
            except (KeyError,ValueError,TypeError):errors.append('evaluation effective protocol missing or invalid')
            rows=result.get('per_env',[])
            if any(row.get('outcome') not in ('completed','success','task_failure') or
                   not isinstance(row.get('continuous_s'),(int,float)) or row['continuous_s']<=0
                   for row in rows):errors.append('evaluation incomplete or malformed episode evidence')
            if len({row.get('env_id') for row in rows})!=len(rows):errors.append('evaluation duplicate environment identity')
    return {'schema_version':1,'status':'PASSED' if not errors else 'FAILED',
            'spec_sha256':manifest.get('spec_sha256'),
            'actual_updates':progress.get('actual_updates'),'source_sha256':spec.get('source_sha256'),
            'inputs':inputs,'errors':errors,'run':str(folder.resolve()),'smoke_plan':requirements}


def validate_persisted_certificate(folder, spec, *, certificate_path=None):
    folder=Path(folder)
    try:
        record=json.loads((Path(certificate_path) if certificate_path else folder/'wiring_certificate.json').read_text())
    except (OSError,ValueError):
        return {'status':'FAILED','errors':['persisted wiring certificate missing or invalid']}
    current=smoke_certificate(folder,spec)
    # Version-one records predate smoke_plan; their other identities remain strict.
    comparable=current if 'smoke_plan' in record else {key:value for key,value in current.items() if key!='smoke_plan'}
    if record!=comparable:
        return {**current,'status':'FAILED','errors':current['errors']+['persisted wiring certificate differs from evidence']}
    return current


def completed_smoke(book,spec):
    for row in book.get('attempts',{}).values():
        if row.get('phase')!='smoke' or row.get('status') not in ('COMPLETED','STOPPED_BOUNDED'):continue
        folder=Path(row['output_dir'])
        evidence_spec=spec
        if row.get('evidence_spec_path'):
            from .tools.preflight import reusable_spec,digest
            path=Path(row['evidence_spec_path'])
            if (not path.is_file() or digest(path)!=row.get('evidence_spec_sha256') or
                    not reusable_spec(path,spec)):
                continue
            evidence_spec=json.loads(path.read_text())
        certificate=row.get('evidence_certificate_path')
        if certificate:
            p=Path(certificate)
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row.get('evidence_certificate_sha256'):
                continue
        if validate_persisted_certificate(folder,evidence_spec,certificate_path=certificate)['status']=='PASSED':return True
    return False
