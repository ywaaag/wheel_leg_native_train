"""Exclusive offline same-input actor comparison and Recovery run summaries."""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from tensordict import TensorDict

from native_stand.command_v6.learning import model


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-run',type=Path,required=True)
    parser.add_argument('--coverage-run',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():raise FileExistsError(args.output_dir)
    torch.set_num_threads(2)
    old=args.previous_run/'formal'
    spec_path=old/'source_snapshot/spec.json';spec=json.loads(spec_path.read_text())
    inputs={str(spec_path.resolve()):sha(spec_path)}
    paths=[('source50',Path(spec['source_checkpoint']))]+[(f'hold10_{u}',old/f'model_update_{u}.pt') for u in (25,50,100)]
    report={'simulation':0,'online_PPO':0,'offline_optimizer_updates':0,'same_input':[],
            'evaluations':[],'limitations':['Saved previous-run BC inputs only; no claim of representative full-episode distribution or causal gradients.',
                                           'Missing current arm evaluations remain unmeasured; this tool never simulates.']}
    for update in (1,8,25,50,100):
        p=old/f'bc_gradient_update_{update}.pt'
        payload=torch.load(p,map_location='cpu',weights_only=False)
        if payload['spec_sha256']!=sha(spec_path) or payload['source_sha256']!=spec['source_sha256']:
            raise ValueError('Saved input identity differs')
        inputs[str(p.resolve())]=sha(p)
        obs=TensorDict(payload['observations'],batch_size=[len(payload['observations']['policy'])])
        predictions={}
        for label,path in paths:
            checkpoint=torch.load(path,map_location='cpu',weights_only=False)
            if checkpoint['asset_sha256']!=spec['asset_sha256']:raise ValueError('Asset differs')
            actor=model(obs,actor=True,spec=spec)
            actor.load_state_dict(checkpoint['actor'],strict=True);actor.eval()
            with torch.no_grad():predictions[label]=actor(obs,stochastic_output=False)
            inputs[str(path.resolve())]=sha(path)
        report['same_input'].append({'input_rollout_update':update,'sample_count':len(obs),
            'input_actor_update':update-1,'comparisons':{
                label:{'normalized_channel_mse':(values-predictions['source50']).square().mean(0).tolist(),
                       'normalized_rms':float((values-predictions['source50']).square().mean().sqrt())}
                for label,values in predictions.items() if label!='source50'}})
    for p in sorted(args.coverage_run.glob('**/evaluation*.json')):
        if p.name.endswith('.terminal.json'):continue
        d=json.loads(p.read_text())
        if d.get('task')!='recovery':continue
        es=d['per_env'];inputs[str(p.resolve())]=sha(p)
        report['evaluations'].append({'path':str(p.resolve()),'family':d['evaluation_family'],
            'seed':d['seed'],'passed_envs':d['passed_envs'],
            'pose_counts':{pose:sum(e['pose_id']==pose for e in es) for pose in sorted({e['pose_id'] for e in es})},
            'per_env':[{'env_id':e['env_id'],'pose_id':e['pose_id'],'continuous_s':e['continuous_s'],
                        'runtime_fault':e['runtime_fault'],'failed_checks':e['standing_failed_checks']}
                       for e in es],
            'means':{k:sum(e['standing_metrics'][k] for e in es)/len(es)
                for k in ('height_steady_mean_m','mean_abs_pitch_rad','mean_abs_roll_rad','dual_contact_fraction')}})
    report['inputs']=inputs
    args.output_dir.mkdir(parents=True)
    with (args.output_dir/'review.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    lines=['# Recovery coverage offline review','No simulation/PPO/offline optimizer updates.',
           '|family/seed|passed|mean pitch|mean roll|','|---|---:|---:|---:|']
    for row in report['evaluations']:
        lines.append(f"|{row['family']}/{row['seed']}|{row['passed_envs']}/8|{row['means']['mean_abs_pitch_rad']:.6f}|{row['means']['mean_abs_roll_rad']:.6f}|")
    lines.extend(['','Same-input previous checkpoints and input SHA: review.json.','No automatic follow-up authorized by this review.'])
    with (args.output_dir/'review.md').open('x') as stream:stream.write('\n'.join(lines)+'\n')
    assert all(sha(Path(path))==digest for path,digest in inputs.items())
    print(json.dumps({'output':str(args.output_dir.resolve()),'same_input_batches':len(report['same_input']),
                      'evaluations':len(report['evaluations']),'files_written':2,'simulation':0,'PPO':0}))


if __name__=='__main__':main()
