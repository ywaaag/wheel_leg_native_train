"""Registry-selected ended-chain Recovery event audit; no polling or launch."""
import argparse
import json
from pathlib import Path
from ..domain.recovery_events import analyze,coverage_from_metrics
from ..domain.trace_schema import VERSION
from .evaluation_loader import load
from .experiment_preparation import checked_input,publish


def review(chain,output=None,updates=None):
    chain=Path(chain).resolve();inputs={}
    def read(path):
        p,sha=checked_input(path);inputs[p]=sha;return json.loads(Path(p).read_text())
    terminal=read(chain/'chain_terminal_report.json')
    if terminal['status'] not in ('COMPLETED','FAILED','STOPPED_BOUNDED'):raise ValueError('Ended chain required; do not poll')
    formal=chain/'formal';spec=read(formal/'source_snapshot/spec.json')
    from native_stand.recovery.sampling import allocation_plan
    plan=allocation_plan(spec['recovery'],spec['ppo']['envs']);cases=[];found=set()
    for phase in ('source_eval','formal'):
        folder=chain/phase
        if not (folder/'candidate_registry.json').exists():continue
        registry=read(folder/'candidate_registry.json');frozen=read(folder/'source_snapshot/spec.json')
        spec_sha=checked_input(folder/'source_snapshot/spec.json')[1]
        for entry in registry:
            if updates is not None and phase=='formal' and entry['update'] not in updates:continue
            data,evidence=load(folder,entry,spec_sha256=spec_sha,checkpoint_sha256=entry['checkpoint_sha256'],
                asset_sha256=frozen['asset_sha256'])
            if data.get('trace_schema_version',VERSION)!=VERSION:raise ValueError('Unsupported trace schema')
            inputs[evidence['path']]=evidence['sha256'];groups=[]
            if data.get('numeric_trace_storage'):
                artifact=data['numeric_trace_storage'];inputs.update([checked_input(folder/Path(entry['evaluation']).parent/artifact['path'],artifact['sha256'])])
            for group in [data]+data.get('retained_evaluations',[]):
                groups.append({'family':group['evaluation_family'],'passed':sum(bool(r.get('success')) for r in group['per_env']),
                    'rows':[analyze(r,dt=frozen['control']['policy_dt_s'],
                        hold_s=frozen['recovery']['rising_task']['post_rise_hold_s'],
                        wheel_scale=frozen['action']['wheel_scale_rad_s']) for r in group['per_env']]})
            cases.append({'phase':phase,'update':entry['update'],'checkpoint_sha256':entry['checkpoint_sha256'],
                'evidence':evidence,'groups':groups})
            if phase=='formal':found.add(entry['update'])
    if updates is not None and set(updates)-found:raise ValueError('Requested update missing from registry')
    if not cases:raise ValueError('No registry evidence available')
    metric_path=formal/'metrics.jsonl';inputs.update([checked_input(metric_path)])
    metrics=[json.loads(line) for line in metric_path.read_text().splitlines() if line]
    report={'inputs_sha256':inputs,'cases':cases,'coverage':coverage_from_metrics(metrics,plan),'sampling_plan':plan,
        'trace_schema':VERSION,'scope':'first-episode events and actual training transitions; no optimizer/causal claim',
        'simulation':0,'optimizer_updates':0}
    if output is not None:publish(output,{'review.json':report},inputs,completion_marker=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output-dir',type=Path);p.add_argument('--update',type=int,action='append');a=p.parse_args()
    print(json.dumps(review(a.run,a.output_dir,a.update),indent=2,allow_nan=False))

if __name__=='__main__':main()
