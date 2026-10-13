"""One-shot finished-arm comparison plus common source; no waiting or new evaluation."""
import argparse
import json
from pathlib import Path
import torch
from .experiment_preparation import checked_input,publish
from ..domain.action_std import readback


def compare(runs):
    inputs={};arms=[];source=None;protocol=None
    for run in map(lambda p:Path(p).resolve(),runs):
        files={name:run/name for name in ('manifest.json','terminal_report.json','candidate_selection.json')}
        for path in files.values():inputs.update([checked_input(path)])
        d={name:json.loads(path.read_text()) for name,path in files.items()}
        terminal=d['terminal_report.json'];manifest=d['manifest.json']
        if terminal.get('status') not in ('COMPLETED','STOPPED_BOUNDED','FAILED','TERMINATED'):
            raise ValueError('finished phase run required; no polling')
        path=run/'source_snapshot/spec.json';inputs.update([checked_input(path)]);spec=json.loads(path.read_text())
        if source is None:source=spec['source_sha256'];protocol=spec['evaluation']
        if spec['source_sha256']!=source or spec['evaluation']!=protocol:raise ValueError('arms source/evaluation protocol differ')
        checkpoint=Path(spec['source_checkpoint']);inputs.update([checked_input(checkpoint,source)])
        wheel_factor=spec.get('wheel_envelope_conversion',{}).get('source_scale_rad_s',spec['action']['wheel_scale_rad_s'])/spec['action']['wheel_scale_rad_s']
        config={'parameterization':'scalar','output_factor':[1,1,wheel_factor,1,1,wheel_factor],'leg_scale_rad':spec['action']['leg_scale_rad'],'wheel_scale_rad_s':spec['action']['wheel_scale_rad_s']}
        source_model=torch.load(checkpoint,map_location='cpu',weights_only=False)
        candidates=[]
        for candidate in d['candidate_selection.json'].get('candidates',[]):
            model=Path(candidate['checkpoint']);inputs.update([checked_input(model,candidate['checkpoint_sha256'])])
            saved=torch.load(model,map_location='cpu',weights_only=False)
            candidates.append({'checkpoint':str(model),'sha256':candidate['checkpoint_sha256'],'update':candidate.get('update'),
                'accepted':candidate.get('accepted'),'passed_envs':candidate.get('passed_envs'),
                'means':candidate.get('means'),'per_env':candidate.get('per_env'),
                'checkpoint_std':readback(saved['actor']['distribution.std_param'],**config)})
        progress={}
        if (run/'progress.json').exists():
            inputs.update([checked_input(run/'progress.json')]);progress=json.loads((run/'progress.json').read_text())
        arms.append({'run':str(run),'status':terminal['status'],'actual_updates':terminal.get('actual_updates'),
            'declared_initialization':spec.get('recovery',{}).get('exploration_initialization'),
            'initialization_readback':progress.get('exploration_initialization'),
            'source_std':readback(source_model['actor']['distribution.std_param'],**config),'candidates':candidates})
    return {'arms':arms,'common_source_sha256':source,'inputs':inputs,'simulation':0,'optimizer_updates':0,
        'scope':'same-source finished runs, declared/initial/checkpoint std distinct; no winner or capability inferred from std'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,action='append',required=True)
    p.add_argument('--output-dir',type=Path);a=p.parse_args()
    if len(a.run)<2:p.error('at least two finished phase runs required')
    result=compare(a.run)
    if a.output_dir:publish(a.output_dir,{'comparison.json':result},result['inputs'])
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
