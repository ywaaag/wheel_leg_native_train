"""Declared pruning of this owner's checkpoints only; evidence references protected."""
import json
from pathlib import Path
from ..domain.checkpoint_policy import resolve,select
from .submission_receipt import digest


def references(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if isinstance(item,str) and item.endswith('.pt'):yield item
            else:yield from references(item)
    elif isinstance(value,list):
        for item in value:yield from references(item)


def plan(output,spec):
    output=Path(output).resolve();policy=resolve(spec)
    inventory_path=output/'checkpoint_inventory.json'
    inventory=json.loads(inventory_path.read_text()) if inventory_path.is_file() else []
    protected={str(Path(spec['source_checkpoint']).resolve())} if spec.get('source_checkpoint') else set()
    names={'progress.json','candidate_registry.json','candidate_selection.json','stage_passed.json','terminal_report.json'}
    names.update(p.name for p in output.glob('stage*passed*.json'))
    for name in names:
        path=output/name
        if path.is_file():protected.update(str(Path(p).resolve()) for p in references(json.loads(path.read_text())))
    for row in inventory:
        original=Path(row['path']);path=original.resolve()
        if path.parent!=output or original.is_symlink():raise ValueError('checkpoint inventory escapes owner directory')
        if row.get('removed'):continue
        if not path.is_file() and row.get('removal_pending'):
            if str(path) in protected:raise ValueError('referenced checkpoint missing after interrupted pruning')
            continue
        if not path.is_file() or digest(path)!=row['sha256']:raise ValueError('checkpoint inventory identity differs')
    pending=[r for r in inventory if r.get('removal_pending') and not Path(r['path']).exists()]
    active=[r for r in inventory if not r.get('removed') and r not in pending]
    decision=select(active,policy,protected)
    return {'version':'checkpoint_lifecycle_v1','policy':policy,'output':str(output),
            'protected_paths':sorted(protected),'pending_removed':pending,**decision,'files_written':0,
            'scope':'only this explicit owner; source/evaluated/latest/accepted references retained'}


def prune_owned(output,spec,*,attempt_id):
    """Trainer-only path. No CLI --delete, and no mutation of settled attempts."""
    output=Path(output).resolve();receipt_path=output/'submission_receipt.json'
    if resolve(spec) is None:return {'files_removed':0}
    from .submission_receipt import stable
    receipt=json.loads(receipt_path.read_text());record=receipt['record']
    if receipt['sha256']!=stable(record) or record['attempt_id']!=attempt_id or record['output_dir']!=str(output):
        raise ValueError('checkpoint cleanup owner receipt differs')
    if resolve(spec)!=resolve(record['requested']):raise ValueError('checkpoint cleanup policy differs from reserved declaration')
    import fcntl
    ledger=Path(record['spec_path']).with_name('budget.json')
    with ledger.with_suffix('.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        book=json.loads(ledger.read_text())
        row=book['attempts'].get(attempt_id,{})
        if row.get('status')!='RUNNING' or row.get('output_dir')!=str(output):raise ValueError('checkpoint cleanup requires active exact owner')
        decision=plan(output,spec)
        # Recover only persisted owner intents; a missing arbitrary file still rejects.
        from ..completion import write
        inventory_path=output/'checkpoint_inventory.json'
        inventory=json.loads(inventory_path.read_text())
        for pending in decision['pending_removed']:
            for entry in inventory:
                if entry['path']==pending['path']:entry.update(removed=True,removal_pending=False,reason='reconciled interrupted owner pruning')
        if decision['pending_removed']:write(inventory_path,inventory)
        # Persist both intent and pending inventory before deletion.
        for item in decision['remove']:
            path=Path(item['path']);write(output/'checkpoint_prune_intent.json',{'attempt_id':attempt_id,'checkpoint':item})
            if digest(path)!=item['sha256']:raise ValueError('checkpoint changed after retention plan')
            inventory=json.loads(inventory_path.read_text())
            for entry in inventory:
                if entry['path']==item['path']:entry['removal_pending']=True
            write(inventory_path,inventory)
            path.unlink()
            inventory=json.loads((output/'checkpoint_inventory.json').read_text())
            for entry in inventory:
                if entry['path']==item['path']:entry.update(removed=True,removal_pending=False,reason='declared owner retention policy')
            write(output/'checkpoint_inventory.json',inventory)
        return {'files_removed':len(decision['remove']),'reconciled_removals':len(decision['pending_removed'])}


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args()
    spec=json.loads((a.run_dir/'source_snapshot/spec.json').read_text())
    print(json.dumps(plan(a.run_dir,spec),indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
