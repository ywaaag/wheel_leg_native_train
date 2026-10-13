"""Restricted Motion None-window recovery publication; zero-write default, no launch."""
import argparse
import copy
import fcntl
import json
from pathlib import Path
from .experiment_preparation import checked_input,publish
from .motion_recovery_certificate import audit,VERSION,stable_hash,behavior
from ..domain.experiment_naming import validate_new_experiment_name,new_experiment_name


def request(failed,supplement,ledger,review,source=None,supplement_ledger=None,formal_updates=50):
    failed=Path(failed).resolve();supplement=Path(supplement).resolve()
    manifest=json.loads((failed/'manifest.json').read_text())
    frozen=json.loads((supplement/'source_snapshot/spec.json').read_text())
    return {'failed_run':str(failed),'supplement':str(supplement),'ledger':str(Path(ledger).resolve()),
        'change_review':str(Path(review).resolve()),'source_run':str(Path(source or manifest['source_baseline_run']).resolve()),
        'supplement_ledger':str(Path(supplement_ledger or Path(__file__).resolve().parents[4]/'configs/experiments'/frozen['experiment']/'budget.json').resolve()),
        'chain_terminal':str(failed.parent/'chain_terminal_report.json'),'formal_updates':formal_updates}


def plan(failed,supplement,current_spec,ledger,review):
    """Existing Python entry now returns stage-preserving v1 engineering certificate."""
    try:
        r=request(failed,supplement,ledger,review)
        spec=json.loads(Path(current_spec).read_text())
        record=audit(r,spec);record['files_written']=0
        return record
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return {'version':VERSION,'status':'MISSING','missing':[str(exc)],'conflicts':[],
            'facts':{},'authorization':'UNAUTHORIZED','files_written':0}


def prepare(failed,supplement,parent,ledger,review,output=None,*,write=False):
    parent=Path(parent).resolve();base=json.loads(parent.read_text());r=request(failed,supplement,ledger,review)
    certificate=audit(r,base)
    if output is None:output=Path(__file__).resolve().parents[4]/'configs/experiments'/new_experiment_name('motion_posture_engineering_recovery')
    output=Path(output).resolve();validate_new_experiment_name(output.name)
    project=Path(__file__).resolve().parents[4]
    if output.parent!=project/'configs/experiments':raise ValueError('Fresh project experiment directory required')
    if output.exists():raise FileExistsError(output)
    report={'certificate':certificate,'output':str(output),'status':certificate['status'],'files_written':0,
            'runtime_authorized':False}
    if certificate['status']!='READY':return report
    accounting=certificate['facts']['accounting'];spec=copy.deepcopy(base)
    spec.update(experiment=output.name,execution_source_root=str(project/'src'),
        authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'Engineering preparation only; formal requires explicit authorization'},
        notifications={'enabled':False},source_evidence_reference=r['source_run'],
        authorization_note='CPU engineering recovery prepared only; no runtime or notification authorization')
    for key in ('chain_submission','authorization_receipt','evaluation_requests','evaluation_only','diagnostic_identity_only'):
        spec.pop(key,None)
    spec['artifacts']['run_name']=output.name
    spec['budget'].update(source_eval_updates=0,source_eval_wall_s=0.,smoke_updates=0,smoke_wall_s=0.,
        formal_updates=accounting['new_formal_limit'],formal_wall_s=min(base['budget']['formal_wall_s'],accounting['remaining_wall_s']),
        sample_limit=accounting['new_formal_limit']*base['ppo']['envs']*base['ppo']['steps_per_env'],
        formal_samples=accounting['new_formal_limit']*base['ppo']['envs']*base['ppo']['steps_per_env'])
    spec['motion_posture']['chain_wall_s']=accounting['remaining_wall_s']
    cert_bytes=(json.dumps(certificate,indent=2,allow_nan=False)+'\n').encode()
    import hashlib
    cert_sha=hashlib.sha256(cert_bytes).hexdigest()
    single=stable_hash({'failed_attempt':certificate['facts']['optimizer_wiring']['attempt_id'],
        'terminal_sha256':certificate['facts']['optimizer_wiring']['terminal_sha256']})
    spec['engineering_recovery']={'version':VERSION,'certificate':str(output/'engineering_recovery_certificate.json'),
        'sha256':cert_sha,'single_use_id':single}
    book={'authorization':'UNAUTHORIZED','experiment':output.name,'limits':{'source_eval':0,'smoke':0,'formal':accounting['new_formal_limit'],'evaluate':0,'play':0},
        'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,
        'historical_usage':accounting,'engineering_recovery_single_use_id':single,
        'budget_note':'New work only; original smoke1 and all historical walls retained in certificate, never reset'}
    from ..config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    report.update(spec=spec,budget=book,certificate_sha256=cert_sha,single_use_id=single)
    if write:
        claims=project/'configs/experiments'/'.engineering_recovery_publications';claims.mkdir(exist_ok=True)
        claim=claims/(single+'.json')
        with (claims/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if claim.exists():raise ValueError('These failed exact evidence inputs already published; no duplicate recovery')
            # Recheck before publication, zero fake historic attempts.
            if audit(r,base)!=certificate:raise ValueError('Evidence changed before publication')
            with claim.open('x') as stream:json.dump({'status':'CLAIMED','destination':str(output),'certificate_sha256':cert_sha},stream)
            try:
                publish(output,{'spec.json':spec,'budget.json':book,
                    'engineering_recovery_certificate.json':certificate,'preparation_manifest.json':{
                        'status':'READY_UNAUTHORIZED','certificate_sha256':cert_sha,'single_use_id':single,
                        'parent_spec':checked_input(parent),'behavior_sha256':stable_hash(behavior(spec)),
                        'history_not_modified':True}},certificate['inputs_sha256'],completion_marker=True)
            except BaseException:
                claim.unlink();raise
            claim.write_text(json.dumps({'status':'PUBLISHED','destination':str(output),'certificate_sha256':cert_sha}))
        report['files_written']=5
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('failed-run','supplement','spec','ledger','change-review'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--output-dir',type=Path);p.add_argument('--write',action='store_true')
    a=p.parse_args();print(json.dumps(prepare(a.failed_run,a.supplement,a.spec,a.ledger,a.change_review,a.output_dir,write=a.write),indent=2,allow_nan=False))

if __name__=='__main__':main()
