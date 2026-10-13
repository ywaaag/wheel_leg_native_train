"""Static reference/guard audit; zero-write by default, never delete historical tools."""
import argparse
import json
from pathlib import Path
from .entrypoints import ENTRIES
from .experiment_preparation import checked_input,publish


def documentation_coverage(root,entries=ENTRIES):
    text=(Path(root)/'TOOL_INDEX.md').read_text()
    missing=[]
    for row in entries:
        if row['status']!='CURRENT':continue
        name=row['entry']
        token=name.split('/')[-1] if name.startswith('scripts/') else name.removeprefix('native_stand.command_v6.')
        if name not in text and token not in text:missing.append(name)
    return {'status':'PASS' if not missing else 'MISSING_DOCUMENTATION','missing':missing,
        'scope':'current public catalog versus the sole TOOL_INDEX body'}


def audit(root):
    root=Path(root).resolve();inputs={};texts={}
    for folder in ('src','scripts','tests','docs'):
        for path in (root/folder).rglob('*'):
            if path.is_file() and path.suffix in ('.py','.md'):
                inputs.update([checked_input(path)]);texts[str(path.relative_to(root))]=path.read_text()
    records=[]
    for item in ENTRIES:
        entry=item['entry'];path=(root/entry) if entry.startswith('scripts/') else root/'src'/Path(entry.replace('.','/')).with_suffix('.py')
        name=path.name
        references=[file for file,text in texts.items() if file!=str(path.relative_to(root)) and (entry in text or name in text)]
        source=path.read_text() if path.is_file() else ''
        guarded=('historical_cli_guard' in source or 'require_historical_option' in source or 'DEPRECATED' in source or 'RETIRED_ENTRY' in source)
        old=item['status'] in ('HISTORICAL','DEPRECATED','RETIRED')
        records.append({**item,'path':str(path),'exists':path.is_file(),'references':references,
            'historical_guard_detected':guarded if old else None,
            'deletion_decision':'KEEP_REFERENCED' if old and references else 'REVIEW_REPLACEMENT_COVERAGE' if old else 'KEEP_CURRENT_OR_INTERNAL'})
    return {'documentation_coverage':documentation_coverage(root),'entries':records,'inputs':inputs,'scope':'static src/scripts/tests/docs references only; dynamic imports and historical frozen run commands not treated as deletion clearance',
        'files_deleted':0,'simulation':0,'ppo':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path)
    a=p.parse_args();result=audit(Path(__file__).resolve().parents[4])
    if a.output_dir:publish(a.output_dir,{'audit.json':result},result['inputs'])
    print(json.dumps({k:v for k,v in result.items() if k!='inputs'},indent=2))


if __name__=='__main__':main()
