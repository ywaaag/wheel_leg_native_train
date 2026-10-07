"""Create an immutable corrected recipe and closure-consistent pose candidates.

Uses the existing experiment ledger; never resets consumed PPO allowance.
Offline geometry is not runtime certification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-spec',type=Path,required=True)
    parser.add_argument('--output-spec',type=Path,required=True)
    args=parser.parse_args()
    if args.output_spec.exists(): raise FileExistsError(args.output_spec)
    if args.source_spec.parent.resolve()!=args.output_spec.parent.resolve():
        raise ValueError('Corrected recipe must share the original ledger directory')
    spec=json.loads(args.source_spec.read_text())
    book=json.loads(args.source_spec.with_name('budget.json').read_text())
    if any(r['status']=='RUNNING' for r in book['attempts'].values()):
        raise RuntimeError('Existing attempt still running')
    library=json.loads(Path(spec['recovery']['pose_library']).read_text())
    source=library['poses'][0]
    asset=AssetPoses(spec['asset_path'])
    names=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')
    rotation=np.eye(4)
    rotation[:3,:3]=Rotation.from_quat(source['root_quaternion_xyzw']).as_matrix()
    poses=[];rejected=[]
    for family,factor,jitter in [('R0',0.,.005),('drawback_approx',.75,.005),('R1',1.,0.),('R2_R3',.98,.01)]:
        for split,seed in [('train',20261004),('holdout',20261005)]:
            rng=np.random.default_rng(seed)
            for index in range(4 if jitter else 1):
                active={n:source['joint_pos'][n]*factor+float(rng.uniform(-jitter,jitter)) for n in names}
                q,error=asset.solve(active,source['joint_pos'])
                supports=asset.support(q,rotation)
                height=.002-min(s['lowest_z_root'] for s in supports)
                chassis=height+min(s['lowest_z_root'] for s in supports if s['body']=='robot')
                valid=float(error.max())<=1e-4 and all(j['limits'][0]-1e-6<=q[j['name']]<=j['limits'][1]+1e-6 for j in asset.joints)
                row={'pose_id':f'{family}_{split}_{index}','family':family,'split':split,'seed':seed+index,
                    'offline_valid':bool(valid),'runtime_valid':None,'joint_pos':q,
                    'root_height_m':height,'root_quaternion_xyzw':source['root_quaternion_xyzw'],
                    'closure_max_m':float(error.max()),'support':supports,
                    'initial_root_height_m':[max(0.,height-.025),height+.025],
                    'initial_chassis_clearance_m':[max(-.005,chassis-.025),chassis+.025],
                    'initialization_control':'direct_zero_reset' if family in ('R0','drawback_approx') else 'passive_settle'}
                (poses if valid else rejected).append(row)
    library.update(poses=poses,rejected_candidates=rejected,attempted=len(poses)+len(rejected),
        offline_rejected=len(rejected),runtime_rejected=None,
        definition='Bounded closure solutions. R0 near-standing; R1 symmetric low support approximation; captured R2; perturbed R3. No reference motion.')
    pose_path=args.output_spec.with_name(args.output_spec.stem+'_poses.json')
    with pose_path.open('x') as stream: json.dump(library,stream,indent=2)
    spec['experiment']+='_corrected'
    spec['reward']['wheel_spin_scale_rad_s']=100.
    # Avoid unverified wheel sign and nominal-pose assumptions as reward inputs.
    for key in ('leg_symmetry','support_region','slip_proxy'): spec['reward'].pop(key,None)
    spec['recovery'].update(pose_library=str(pose_path.resolve()),pose_library_sha256=digest(pose_path),
        active_family='R0',runtime_initialization_validated=False,
        scope='Reverse curriculum; direct closure-valid zero-velocity reset for R0/R1; passive settle for captured R2/R3. No initialization stabilizer.')
    spec['phase_initialization']='Strict source update1500 actor/critic/Adam; actual LR3e-5; new environment reset.'
    spec['revision_of_spec_sha256']=digest(args.source_spec)
    spec['budget_remaining_at_preparation']={'smoke':book['limits']['smoke']-book['used']['smoke'],
        'formal':book['limits']['formal']-book['used']['formal']}
    spec['experiment_variable']='Wire reverse reset curriculum; normalize low-height wheel penalty by100rad/s; remove unverified geometry penalties. Physical control and limits unchanged.'
    with args.output_spec.open('x') as stream: json.dump(spec,stream,indent=2)
    print(json.dumps({'spec':str(args.output_spec),'valid_poses':len(poses),'rejected':len(rejected),
        'remaining':spec['budget_remaining_at_preparation']}))


if __name__=='__main__': main()
