"""CPU-only USD reconstruction of saved native BC observations; no physics/PPO."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from native_stand.recovery.asset_poses import AssetPoses

LEGS=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')


def wheel_geometry(wheels,anchors,gravity):
    """Native root axes: forward=-Z, up=+Y; project forward onto gravity plane."""
    wheels=np.asarray(wheels,dtype=float);anchors=np.asarray(anchors,dtype=float)
    gravity=np.asarray(gravity,dtype=float)
    if wheels.shape!=(2,3) or anchors.shape!=(2,3) or gravity.shape!=(3,):
        raise ValueError('Expected two wheel/hip centers and one body gravity vector')
    if not all(np.isfinite(v).all() for v in (wheels,anchors,gravity)) or np.linalg.norm(gravity)<1e-8:
        raise ValueError('Nonfinite geometry or missing gravity')
    up=-gravity/np.linalg.norm(gravity)
    forward=np.array([0.,0.,-1.]);forward-=np.dot(forward,up)*up
    if np.linalg.norm(forward)<1e-6:raise ValueError('Forward projection undefined near vertical pitch')
    forward/=np.linalg.norm(forward)
    longitudinal=wheels@forward;vectors=wheels-anchors
    pitch=np.arctan2(vectors@forward,-vectors@up)
    return {'wheel_longitudinal_m':longitudinal.tolist(),
            'wheel_longitudinal_offset_m':float(abs(longitudinal[0]-longitudinal[1])),
            'leg_pitch_rad':pitch.tolist(),'leg_pitch_difference_rad':float(abs(pitch[0]-pitch[1])),
            'leg_length_m':np.linalg.norm(vectors,axis=1).tolist()}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples-per-payload',type=int,default=16)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    if args.samples_per_payload<1:raise ValueError('Positive sample count required')
    report={'ppo_updates':0,'new_physics_wall_s':0,'cases':[],
        'scope':'Saved pre-action training observations, not checkpoint holdout trajectory. Joint offsets /2, reference=0 in snapshotted native env. Passive branch solved from saved reset pose. Authored USD reconstruction, not runtime wheel-center measurement.',
        'missing':['Actual wheel center and passive joint time series in prior holdout JSON',
                   'Substep contact patch geometry and direct evidence of passive static stability']}
    for arm in ('A_fixed','B_annealed'):
        folder=args.pair/arm/'formal'
        spec_path=folder/'source_snapshot/spec.json';spec=json.loads(spec_path.read_text())
        if digest(spec['asset_path'])!=spec['asset_sha256']:raise ValueError('USD identity differs')
        asset=AssetPoses(spec['asset_path']);library_path=Path(spec['recovery']['pose_library'])
        if digest(library_path)!=spec['recovery']['pose_library_sha256']:raise ValueError('Pose identity differs')
        library=json.loads(library_path.read_text())
        start=next(p for p in library['poses'] if p['family']=='R0' and p['split']=='train')
        anchors=spec['recovery']['standing_task']['hip_anchors_root_m']
        for update in (1,50,100):
            path=folder/f'bc_gradient_update_{update}.pt'
            data=torch.load(path,map_location='cpu',weights_only=False)
            if data['spec_sha256']!=digest(spec_path):raise ValueError('Payload/spec identity differs')
            obs=data['observations']['policy']
            rows=[]
            indices=np.linspace(0,len(obs)-1,min(len(obs),args.samples_per_payload),dtype=int)
            for i in indices:
                active=dict(zip(LEGS,(obs[i,9:13]/2.).tolist()))
                q,residual=asset.solve(active,start['joint_pos']);bodies=asset.forward(q)
                wheels=np.array([bodies[f'{side}_wheel'][:3,3] for side in ('left','right')])
                rows.append({'observation_index':int(i),'active_q_rad':active,
                    'closure_max_m':float(residual.max()),'wheel_centers_root_m':wheels.tolist(),
                    'body_gravity':obs[i,3:6].tolist(),**wheel_geometry(wheels,anchors,obs[i,3:6])})
            valid=[r for r in rows if r['closure_max_m']<=1e-4]
            report['cases'].append({'arm':arm,'rollout_update':update,'actor_used_update':update-1,
                'input_path':str(path.resolve()),'input_sha256':digest(path),'asset_sha256':spec['asset_sha256'],
                'source_sha256':data['source_sha256'],'samples':len(rows),'closure_valid':len(valid),
                'mean_offset_m':float(np.mean([r['wheel_longitudinal_offset_m'] for r in valid])) if valid else None,
                'mean_pitch_difference_rad':float(np.mean([r['leg_pitch_difference_rad'] for r in valid])) if valid else None,
                'rows':rows})
        metrics=[json.loads(line) for line in (folder/'metrics.jsonl').read_text().splitlines()]
        report.setdefault('reward_evidence',{})[arm]={'actual_update':metrics[-1]['actual_update'],
            'weighted_mean_per_policy_step':metrics[-1]['rollout']['weighted_mean'],
            'note':'GPU aggregated rollout means, not a claim about same-state counterfactual total reward.'}
        reset=asset.forward(start['joint_pos'])
        wheels=np.array([reset[f'{side}_wheel'][:3,3] for side in ('left','right')])
        report.setdefault('reset_geometry',{})[arm]=wheel_geometry(wheels,anchors,[0.,-1.,0.])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps([{k:v for k,v in row.items() if k not in ('rows','input_sha256','source_sha256','asset_sha256')} for row in report['cases']],indent=2))


if __name__=='__main__':main()
