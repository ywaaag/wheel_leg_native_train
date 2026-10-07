"""CPU-only preparation: USD-authored closure, candidate rejection evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses


def generate(spec):
    asset = AssetPoses(spec['asset_path'])
    rotation = np.eye(4)
    rotation[:3,:3] = Rotation.from_quat(spec['recovery']['initialization']['root_quaternion_xyzw']).as_matrix()
    config = spec['recovery']['initialization']
    records = []
    for split,seed in config['seeds'].items():
        rng = np.random.default_rng(seed)
        for family,settings in config['families'].items():
            for index in range(settings['count_per_split']):
                base = np.array(settings['active_q'])
                values = base+rng.uniform(-settings['jitter_rad'],settings['jitter_rad'],4)
                names = ['left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch']
                q,residual = asset.solve(dict(zip(names,values)))
                support = asset.support(q,rotation)
                lowest = min(row['lowest_z_root'] for row in support)
                root_height = -lowest+config['ideal_gap_m']
                chassis = min(row['lowest_z_root']+root_height for row in support if row['body']=='robot')
                limits_ok = all(j['limits'][0]-1e-6<=q[j['name']]<=j['limits'][1]+1e-6 for j in asset.joints)
                accepted = bool(max(residual)<config['offline_closure_max_m'] and limits_ok)
                records.append({'pose_id':f'{split}_{family}_{index}', 'split':split,'seed':seed,'family':family,
                    'offline_valid':accepted,'runtime_valid':None,'joint_pos':q,
                    'root_height_m':root_height,'root_quaternion_xyzw':config['root_quaternion_xyzw'],
                    'chassis_bottom_clearance_m':chassis,'closure_each_m':residual.tolist(),
                    'ideal_collider_gaps_m':{row['path']:row['lowest_z_root']+root_height for row in support},
                    'rejection_reason':None if accepted else 'offline_closure_or_joint_limit'})
    return {'asset_sha256':hashlib.sha256(Path(spec['asset_path']).read_bytes()).hexdigest(),
        'definition':'Authored primitive geometry and joint frames; not runtime contacts/penetration.',
        'attempted':len(records),'offline_rejected':sum(not row['offline_valid'] for row in records),
        'runtime_rejected':None,'runtime_rejection_rate':None,'poses':records,
        'collision_inventory':[{'path':x['path'],'body':x['body'],'type':x['type']} for x in asset.colliders],
        'collision_geometry':[{**{k:v for k,v in x.items() if k!='matrix'},'matrix':x['matrix'].tolist()} for x in asset.colliders],
        'joint_limits_rad':{j['name']:j['limits'] for j in asset.joints if np.isfinite(j['limits']).all()},
        'geometry_limitation':'Chassis robot bottom stays ~0.10m above floor at guide-wheel-supported low pose; body-bottom-on-floor is not valid with current USD.'}


def main():
    parser = argparse.ArgumentParser(description='CPU pose preparation; no Isaac/PPO. New output only.')
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    result = generate(spec)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({'attempted':result['attempted'],'offline_rejected':result['offline_rejected'],
        'runtime_valid':None,'geometry_limitation':result['geometry_limitation']}))


if __name__=='__main__':
    main()
