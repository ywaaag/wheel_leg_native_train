"""Read-only storage inventory; no cleanup command, no process/progress polling."""
import argparse,json
from pathlib import Path
DERIVED={'analysis.json','chain_terminal_report.json','candidate_selection.json'}


def categories(root,excluded):
    root=Path(root).resolve();excluded=[Path(p).resolve() for p in excluded]
    totals={};validation={};count=0
    for path in root.rglob('*'):
        if not path.is_file() or path.is_symlink() or any(path.is_relative_to(p) for p in excluded):continue
        relative=path.relative_to(root);count+=1;size=path.stat().st_size
        is_validation=relative.parts[0]=='artifacts' and ('source_snapshot' in relative.parts or 'tests' in relative.parts)
        kind=('frozen_validation_copy' if is_validation else 'checkpoint' if path.suffix=='.pt' else
              'numeric_evidence' if path.suffix=='.npz' else 'derived_report' if path.name in DERIVED else
              'source_or_test' if path.suffix=='.py' else 'JSON_or_declaration' if path.suffix=='.json' else 'other')
        totals[kind]=totals.get(kind,0)+size
        if relative.parts[0]=='artifacts' and len(relative.parts)>1:
            key=relative.parts[1];validation[key]=validation.get(key,0)+size
    return {'bytes_by_category':totals,'artifact_directories':validation,'file_count':count,'excluded':list(map(str,excluded)),
        'retention_recommendations':['Retain historical checkpoints/raw evidence and failed/final validation receipts',
            'Reuse passed validation only against identical spec/source/test/interpreter SHA',
            'Copy only requested PORTABLE tests and conftest; reference prior result instead of another whole source copy',
            'Review derived report duplicates separately; no size-based deletion permission'],
        'files_deleted':0,'scope':'filesystem metadata only; excluded runs/activity not inspected'}


def audit(root,excluded):
    root=Path(root).resolve();excluded=[Path(p).resolve() for p in excluded]
    if not excluded:raise ValueError('Explicit active/protected directory exclusions required')
    records=[];dependencies=set()
    for spec in root.glob('**/source_snapshot/spec.json'):
        if any(spec.is_relative_to(p) for p in excluded):continue
        try:
            data=json.loads(spec.read_text())
            for key in ('source_checkpoint','source_evidence_reference'):
                if data.get(key):dependencies.add(str(Path(data[key]).resolve()))
        except (OSError,ValueError):continue
    for path in root.rglob('*'):
        if not path.is_file() or path.is_symlink() or any(path.is_relative_to(p) for p in excluded):continue
        size=path.stat().st_size
        if path.name in DERIVED or size>16*1024**2:
            records.append({'path':str(path),'bytes':size,'kind':'derived_report' if path.name in DERIVED else
                'checkpoint' if path.suffix=='.pt' else 'raw_or_unknown',
                'source_dependency':str(path) in dependencies,
                'action':'REVIEW_COMPACTION_ONLY' if path.name in DERIVED else 'RETAIN_UNTIL_DEPENDENCY_REVIEW'})
    return {'files':sorted(records,key=lambda r:-r['bytes']),'excluded':list(map(str,excluded)),
        'derived_bytes':sum(r['bytes'] for r in records if r['kind']=='derived_report'),
        'source_dependencies':sorted(dependencies),'files_deleted':0,
        'scope':'explicit exclusions; activity not inferred; size is not proof of safe deletion'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--exclude',action='append',type=Path,required=True);p.add_argument('--categories-only',action='store_true');a=p.parse_args()
    print(json.dumps(categories(a.root,a.exclude) if a.categories_only else audit(a.root,a.exclude),indent=2))

if __name__=='__main__':main()
