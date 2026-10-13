"""Read-only failed-run retry plan; --write publishes UNAUTHORIZED, never launches."""
import argparse
import copy
import json
from pathlib import Path
from .experiment_preparation import checked_input,publish,differences
from ..domain.experiment_naming import validate_new_experiment_name
from ..config import validate


def prepare(run,ledger,output,*,session,write=False):
    run,ledger,output=map(lambda p:Path(p).resolve(),(run,ledger,output))
    validate_new_experiment_name(output.name)
    if output.exists():raise FileExistsError(output)
    if not session:raise ValueError('current session required')
    paths=[run/'manifest.json',run/'terminal_report.json',run/'source_snapshot/spec.json',ledger]
    inputs=dict(checked_input(p) for p in paths)
    manifest=json.loads(paths[0].read_text());terminal=json.loads(paths[1].read_text())
    original=json.loads(paths[2].read_text());book=json.loads(ledger.read_text())
    if original.get('task')!='recovery':raise ValueError('Recovery failed run required')
    attempt=manifest.get('attempt_id');row=book.get('attempts',{}).get(attempt)
    if (not row or row.get('output_dir')!=str(run) or row.get('status')=='RUNNING'
            or terminal.get('status') not in ('FAILED','TERMINATED') or row['status']!=terminal['status']):
        raise ValueError('settled failed exact attempt required; no automatic successful-chain continuation')
    if row.get('updates')!=terminal.get('actual_updates'):raise ValueError('actual update accounting differs')
    if manifest.get('spec_sha256')!=inputs[str(paths[2])]:raise ValueError('frozen spec SHA differs')
    spec=copy.deepcopy(original)
    for key,digest in (('source_checkpoint','source_sha256'),('asset_path','asset_sha256'),
                       ('asset_module_path','asset_module_sha256'),('colleague_config_path','colleague_config_sha256')):
        inputs.update([checked_input(spec[key],spec[digest])])
    library=spec['recovery']['pose_library'];inputs.update([checked_input(library,spec['recovery']['pose_library_sha256'])])
    spec.update(experiment=output.name,authorization={'status':'UNAUTHORIZED','hapi_session':session,
        'user_scope':'Engineering retry proposal only; no budget transfer or launch'})
    spec['artifacts']['run_name']=output.name
    proposal={'authorization':'UNAUTHORIZED','limits':{key:0 for key in book['limits']},
        'used':{key:0 for key in book['limits']},'attempts':{},'source_eval_wall_used_s':0.,
        'historical_usage_reference':str(ledger),'historical_attempt':attempt,
        'historical_actual_updates':row['updates'],'historical_wall_s':row.get('wall_s'),
        'budget_note':'No old balance imported; new explicit authorization must allocate phase limits'}
    errors=validate(spec)
    if errors:raise ValueError(errors)
    report={'inputs':inputs,'failed_run':str(run),'exact_attempt':attempt,
        'stop_reason':terminal.get('reason'),'actual_updates':row['updates'],'wall_s':row.get('wall_s'),
        'differences':differences(original,spec),'runtime_authorized':False,
        'files_written':3 if write else 0,'simulation':0,'ppo':0}
    if write:publish(output,{'spec.json':spec,'budget.json':proposal,'preparation_manifest.json':report},inputs)
    return {'spec':spec,'budget':proposal,'preparation_manifest':report}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','ledger','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--hapi-session',required=True);p.add_argument('--write',action='store_true')
    args=p.parse_args();print(json.dumps(prepare(args.run,args.ledger,args.output_dir,
        session=args.hapi_session,write=args.write),indent=2))


if __name__=='__main__':main()
