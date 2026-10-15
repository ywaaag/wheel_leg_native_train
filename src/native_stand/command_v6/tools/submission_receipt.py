"""One ledger-owned submission binding; code is provenance, inputs remain strict."""
import copy
import hashlib
import json
from pathlib import Path

VERSION='submission_receipt_v1'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stable(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class Approval(dict):
    """Process-local output of real preflight, never deserialized as permission."""
    pass


def bindings(spec_path,spec):
    paths={str(Path(spec_path).resolve()):digest(spec_path)}
    keys=(('source_checkpoint','source_sha256'),('asset_path','asset_sha256'),
          ('asset_module_path','asset_module_sha256'),('colleague_config_path','colleague_config_sha256'))
    for key,sha in keys:
        if spec.get(key):paths[str(Path(spec[key]).resolve())]=spec[sha]
    for section in (spec.get('student_dependencies',{}),):paths.update(section)
    for row in [*spec.get('student_evaluation',{}).get('cases',[]),*spec.get('evaluation_requests',[]),*spec.get('motion_handoff',{}).get('cases',[])]:
        if row.get('checkpoint') and row.get('sha256'):paths[str(Path(row['checkpoint']).resolve())]=row['sha256']
    for row in spec.get('student_teachers',[]):
        for key,sha in (('checkpoint','sha256'),('spec','spec_sha256')):
            if row.get(key) and row.get(sha):paths[str(Path(row[key]).resolve())]=row[sha]
    ref=spec.get('engineering_recovery')
    if ref:paths[str(Path(ref['certificate']).resolve())]=ref['sha256']
    recovery=spec.get('recovery',{})
    for key,sha in (('pose_library','pose_library_sha256'),('stand_checkpoint','stand_sha256'),('stand_spec','stand_spec_sha256')):
        if recovery.get(key):paths[str(Path(recovery[key]).resolve())]=recovery[sha]
    # Bind persisted prerequisite receipts/raw references too. Source code is
    # deliberately not a critical file binding; related changes are recorded.
    book_path=Path(spec_path).with_name('budget.json')
    if book_path.is_file():
        book=json.loads(book_path.read_text())
        folders=[Path(r['output_dir']) for r in book.get('attempts',{}).values()
                 if r.get('status') in ('COMPLETED','STOPPED_BOUNDED')]
        if spec.get('source_evidence_reference'):folders.append(Path(spec['source_evidence_reference']))
        for folder in folders:
            for name in ('manifest.json','terminal_report.json','candidate_registry.json','wiring_certificate.json','source_snapshot/spec.json'):
                file=folder/name
                if file.is_file():paths[str(file.resolve())]=digest(file)
            registry=folder/'candidate_registry.json'
            if registry.is_file():
                entries=json.loads(registry.read_text())
                for row in entries:
                    if row.get('evaluation'):
                        raw=(folder/row['evaluation']).resolve()
                        if not raw.is_relative_to(folder.resolve()):raise ValueError('Prerequisite evidence escapes run')
                        if raw.is_file():
                            paths[str(raw)]=digest(raw)
                            storage=json.loads(raw.read_text()).get('numeric_trace_storage')
                            if storage:
                                archive=(raw.parent/storage['path']).resolve()
                                if not archive.is_relative_to(folder.resolve()):raise ValueError('Prerequisite archive escapes run')
                                if digest(archive)!=storage['sha256']:raise ValueError('Prerequisite archive SHA differs')
                                paths[str(archive)]=storage['sha256']
    return paths


def approve(result,spec_path,output,phase,ledger_path=None):
    if result.get('status')!='PASS':return result
    spec_path=Path(spec_path).resolve();book=Path(ledger_path or spec_path.with_name('budget.json'))
    spec=json.loads(spec_path.read_text())
    if result.get('spec_sha256')!=digest(spec_path):raise ValueError('Spec changed during preflight')
    return Approval({**result,'approval_binding':{'spec_path':str(spec_path),'output':str(Path(output).resolve()),
        'phase':phase,'ledger_path':str(book.resolve()),'ledger_sha256':digest(book),'limits':json.loads(book.read_text())['limits'],'inputs':bindings(spec_path,spec)}})


def from_approval(approval,spec_path,book_path,output,phase,attempt):
    if not isinstance(approval,Approval) or approval.get('status')!='PASS':raise ValueError('Real process-local preflight approval required')
    bind=approval['approval_binding']
    if (bind['spec_path']!=str(Path(spec_path).resolve()) or bind['ledger_path']!=str(Path(book_path).resolve()) or
        bind['output']!=str(Path(output).resolve()) or bind['phase']!=phase):raise ValueError('Preflight target differs')
    if digest(book_path)!=bind['ledger_sha256']:raise ValueError('Budget changed since preflight; recheck required')
    for path,sha in bind['inputs'].items():
        if digest(path)!=sha:raise ValueError('Critical input changed since preflight: '+path)
    spec=json.loads(Path(spec_path).read_text())
    effective=approval.get('effective_recipe')
    if effective is None:effective={'interface':spec.get('student_interface'),'recipe':spec.get('student_training'),'scope':'validated versioned task declaration'}
    if hasattr(approval,'resource_review'):resource_review=approval.resource_review
    else:resource_review=None
    receipt={'version':VERSION,'attempt_id':attempt,'phase':phase,'output_dir':bind['output'],
        'spec_path':bind['spec_path'],'spec_sha256':digest(spec_path),'requested':spec,
        'effective':effective,'inputs_sha256':copy.deepcopy(bind['inputs']),
        'authorization':spec.get('authorization'),'device':spec.get('device'),'resources':spec.get('resources'),
        'budget':spec['budget'],'ledger_limits':bind['limits'],'resource_review':resource_review,'prerequisites':{'status':'VERIFIED_BEFORE_RESERVE',
        'source':approval.get('source_evidence_certificate'),'recovery':approval.get('engineering_recovery_certificate')},
        'execution_identity_at_check':{k:v for k,v in (approval.get('execution_identity') or {}).items() if k in ('actual_execution_root','source_root','location_independent_modules_sha256','PPO_path','PPO_sha256','dependencies','python')},
        'plan':{k:v for k,v in approval.items() if k not in ('approval_binding','execution_identity')},
        'code_policy':'shared src, record changes; no byte replay guarantee'}
    return {'record':receipt,'sha256':stable(receipt)}


def reserved_plan(spec_path,output,phase,attempt_id,ledger_path=None):
    book_path=Path(ledger_path or Path(spec_path).with_name('budget.json'))
    book=json.loads(book_path.read_text());row=book.get('attempts',{}).get(attempt_id,{})
    envelope=row.get('submission_receipt')
    if envelope is None:raise ValueError('Reserved attempt has no current submission receipt')
    receipt=envelope['record']
    if envelope['sha256']!=stable(receipt) or receipt['version']!=VERSION:raise ValueError('Submission receipt corrupt')
    if row.get('status')!='RUNNING' or row.get('phase')!=phase or row.get('output_dir')!=str(Path(output).resolve()):raise ValueError('Exact reservation differs')
    if receipt['attempt_id']!=attempt_id or receipt['phase']!=phase or receipt['output_dir']!=row['output_dir']:raise ValueError('Receipt attempt differs')
    if book.get('authorization')!='AUTHORIZED':raise ValueError('Reservation authorization revoked')
    for path,sha in receipt['inputs_sha256'].items():
        if digest(path)!=sha:raise ValueError('Reserved critical input changed: '+path)
    if book['limits']!=receipt['ledger_limits']:raise ValueError('Reserved budget limits changed')
    if book['used'][phase]>book['limits'][phase]:raise ValueError('Reserved budget exceeded')
    from .execution_identity import identity
    current=identity(receipt['requested'])
    return {**receipt['plan'],'status':'PASS','errors':[],'execution_identity':current,
            'submission_receipt_sha256':envelope['sha256'],'receipt_prerequisites_reused':True,
            'simulation':0,'ppo':0,'files_written':0}
