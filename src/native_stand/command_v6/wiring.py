"""Shared smoke evidence validation; no fixed update number or evaluation filename."""
import hashlib
import json
from pathlib import Path


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
            'inputs':inputs,'errors':errors,'run':str(folder.resolve())}


def completed_smoke(book,spec):
    for row in book.get('attempts',{}).values():
        if row.get('phase')!='smoke' or row.get('status') not in ('COMPLETED','STOPPED_BOUNDED'):continue
        folder=Path(row['output_dir'])
        path=folder/'wiring_certificate.json'
        try:record=json.loads(path.read_text())
        except (OSError,ValueError):continue
        current=smoke_certificate(folder,spec)
        if current['status']=='PASSED' and record==current:return True
    return False
