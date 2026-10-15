"""Plan/apply one known smoke-reader correction; never launch or grant quota."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ..completion import read, sha
from ..domain.experiment_naming import validate_new_experiment_name
from ..wiring import smoke_certificate


def plan(spec_path, smoke_dir, destination):
    spec_path,smoke_dir,destination=map(lambda p:Path(p).resolve(),(spec_path,smoke_dir,destination))
    validate_new_experiment_name(destination.name)
    if destination.exists():raise FileExistsError('recovery destination already exists')
    spec=read(spec_path);book_path=spec_path.with_name('budget.json');book=read(book_path)
    if not isinstance(spec,dict) or not isinstance(book,dict):raise ValueError('original spec/ledger missing')
    attempts=book.get('attempts',{})
    if not attempts or any(row.get('status') not in ('COMPLETED','STOPPED_BOUNDED','FAILED','TERMINATED') for row in attempts.values()):
        raise ValueError('original ledger has active,unknown or missing attempts')
    if any(row.get('phase') not in ('source_eval','smoke') for row in attempts.values()):
        raise ValueError('only pre-formal source/smoke engineering failures are supported')
    if book.get('used',{}).get('formal',0)!=0:raise ValueError('formal usage exists; no restart supported')
    source_rows=[(key,row) for key,row in attempts.items() if row.get('phase')=='source_eval']
    smoke_rows=[(key,row) for key,row in attempts.items() if row.get('phase')=='smoke']
    if len(source_rows)!=1 or len(smoke_rows)!=1:raise ValueError('exactly one source and smoke attempt required')
    receipt_key=hashlib.sha256(json.dumps(sorted(attempts)).encode()).hexdigest()
    receipt=destination.parent/'.engineering_recovery_publications'/(receipt_key+'.json')
    if receipt.exists():raise ValueError('these exact attempts already have a recovery publication; no duplicate destination')
    if Path(smoke_rows[0][1]['output_dir']).resolve()!=smoke_dir:raise ValueError('smoke attempt output identity differs')
    old=read(smoke_dir/'wiring_certificate.json')
    if not old or old.get('status')!='FAILED' or old.get('errors')!=['smoke did not observe the required completed_episode']:
        raise ValueError('unsupported engineering failure; no general certificate override')
    corrected=smoke_certificate(smoke_dir,spec)
    if corrected['status']!='PASSED':raise ValueError('corrected smoke evidence does not pass: '+str(corrected['errors']))
    if (old.get('inputs')!=corrected['inputs'] or old.get('spec_sha256')!=corrected['spec_sha256'] or
            old.get('source_sha256')!=corrected['source_sha256']):
        raise ValueError('failed receipt input identities differ; evidence correction cannot rebind history')
    inputs={str(spec_path):sha(spec_path),str(book_path):sha(book_path),
            str(smoke_dir/'wiring_certificate.json'):sha(smoke_dir/'wiring_certificate.json')}
    for key,row in source_rows+smoke_rows:
        folder=Path(row['output_dir']).resolve()
        terminal=read(folder/'terminal_report.json');manifest=read(folder/'manifest.json')
        if row.get('status')!='COMPLETED' or not terminal or terminal.get('status')!='COMPLETED' or terminal.get('failure'):
            raise ValueError('phase terminal/accounting not completed cleanly')
        if not manifest or manifest.get('attempt_id')!=key or manifest.get('spec_sha256')!=sha(spec_path):
            raise ValueError('attempt/spec manifest identity differs')
        if terminal.get('actual_updates')!=row.get('updates'):
            raise ValueError('attempt/terminal actual usage differs')
        if manifest.get('source_sha256')!=spec['source_sha256']:
            raise ValueError('phase source identity differs')
        for name in ('terminal_report.json','manifest.json','source_snapshot/spec.json'):
            inputs[str(folder/name)]=sha(folder/name)
        if inputs[str(folder/'source_snapshot/spec.json')]!=sha(spec_path):raise ValueError('frozen spec differs')
    expected_used={'source_eval':1,'smoke':smoke_rows[0][1]['updates']}
    if any(book.get('used',{}).get(key)!=value for key,value in expected_used.items()):
        raise ValueError('ledger used counters differ from exact attempts')
    for key in book['used']:
        if key not in expected_used and book['used'][key]!=0:raise ValueError('unsupported existing usage')
        if book['used'][key]>book['limits'][key]:raise ValueError('original budget exceeded')
    for name,digest in corrected['inputs'].items():
        path=smoke_dir/name
        if sha(path)!=digest:raise ValueError('smoke certificate input differs')
        inputs[str(path)]=digest
    for path_key,sha_key in (('source_checkpoint','source_sha256'),('asset_path','asset_sha256')):
        if sha(spec[path_key])!=spec[sha_key]:raise ValueError(path_key+' identity differs')
        inputs[str(Path(spec[path_key]).resolve())]=spec[sha_key]
    result={'schema_version':1,'reason_code':'COMPLETED_FIELD_READER_MISMATCH',
        'source_spec':str(spec_path),'smoke_dir':str(smoke_dir),'destination':str(destination),
        'publication_receipt':str(receipt),
        'inputs':inputs,'imported_attempt_ids':list(attempts),'used':book['used'],'limits':book['limits'],
        'remaining_formal_updates':book['limits']['formal']-book['used']['formal'],
        'authorization':'UNAUTHORIZED','original_ledger_changed':False,
        'simulation':0,'ppo':0,'files_written':0,
        'action':'publish fresh corrected certificate/spec and unauthorized ledger; do not launch'}
    result['plan_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result


def apply(plan_record, expected_sha):
    current=plan(plan_record['source_spec'],plan_record['smoke_dir'],plan_record['destination'])
    if current!=plan_record or current['plan_sha256']!=expected_sha:
        raise ValueError('recovery plan or input SHA changed')
    target=Path(current['destination']);spec=copy.deepcopy(read(current['source_spec']))
    book=copy.deepcopy(read(Path(current['source_spec']).with_name('budget.json')))
    spec['experiment']=target.name
    if 'artifacts' in spec:spec['artifacts']['run_name']=target.name
    # Never inherit permission. Later launch requires a separate explicit authorization.
    book['authorization']='UNAUTHORIZED'
    book['experiment']=target.name
    book['recovery_plan_sha256']=expected_sha
    spec['authorization']={'user_scope':'engineering publication only; runtime not authorized'}
    for row in book['attempts'].values():
        row.update(evidence_spec_path=current['source_spec'],evidence_spec_sha256=sha(current['source_spec']))
        if row['phase']=='smoke':
            certificate=smoke_certificate(Path(current['smoke_dir']),read(current['source_spec']))
            row['evidence_certificate_path']=str(target/'corrected_smoke_certificate.json')
            row['evidence_certificate_sha256']=hashlib.sha256((json.dumps(certificate,indent=2)+'\n').encode()).hexdigest()
    receipt=Path(current['publication_receipt'])
    receipt.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive claim, independent of destination name. A partial publication is
    # deliberately not retried automatically and never grants runtime permission.
    with receipt.open('x') as stream:
        json.dump({'status':'PUBLICATION_CLAIMED','plan_sha256':expected_sha,
                   'destination':str(target),'attempt_ids':current['imported_attempt_ids']},stream)
    target.mkdir(parents=True,exist_ok=False)
    correct_smoke_receipt(Path(current['source_spec']),Path(current['smoke_dir']),target/'corrected_smoke_certificate.json')
    for name,value in (('spec.json',spec),('budget.json',book),('engineering_recovery_plan.json',current)):
        with (target/name).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    if any(sha(path)!=digest for path,digest in current['inputs'].items()):
        raise ValueError('original evidence changed during publication; do not use partial destination')
    return {'status':'PREPARED_UNAUTHORIZED','destination':str(target),'files_written':5,
            'publication_receipt':str(receipt),'simulation':0,'ppo':0}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--smoke-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--expected-plan-sha')
    args=parser.parse_args(argv)
    project=Path(__file__).resolve().parents[4]
    if args.output_dir.resolve().parent!=project/'configs/experiments':
        parser.error('recovery publication roots must be fresh direct children of this project configs/experiments')
    result=plan(args.spec,args.smoke_dir,args.output_dir)
    if args.execute:
        if not args.expected_plan_sha:parser.error('--execute requires the previously reviewed --expected-plan-sha')
        result=apply(result,args.expected_plan_sha)
    print(json.dumps(result,indent=2))




def correct_smoke_receipt(spec_path, evidence_folder, output):
    """Phase-owner offline correction in a fresh file; original receipt stays intact."""
    from native_stand.command_v6.wiring import smoke_certificate
    old=read(Path(evidence_folder)/'wiring_certificate.json')
    if old.get('errors')!=['smoke did not observe the required completed_episode']:
        raise ValueError('unexpected smoke failure; correction is not a general bypass')
    certificate=smoke_certificate(Path(evidence_folder),read(spec_path))
    if certificate['status']!='PASSED':raise ValueError(certificate['errors'])
    with Path(output).open('x') as stream:
        json.dump(certificate,stream,indent=2);stream.write('\n')
    return certificate


if __name__=='__main__':main()
