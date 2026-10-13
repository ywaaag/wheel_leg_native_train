"""CPU preparation of closure-solved Swing-branch support poses and B25 PPO0."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.recovery.asset_poses import AssetPoses

ROOT=Path(__file__).resolve().parents[1]

def prepare(*,write=False):
    parent=ROOT/'configs/experiments/2026_10_8-13_28__recovery_b25_swing_bridge_ppo0/spec.json'
    spec=json.loads(parent.read_text());library=Path(spec['recovery']['pose_library'])
    poses=json.loads(library.read_text());inputs=dict(checked_input(p) for p in (parent,library,Path(spec['source_checkpoint'])))
    for key in ('asset','asset_module','colleague_config'):
        inputs.update([checked_input(spec[key+'_path'],spec[key+'_sha256'])])
    checked_input(library,spec['recovery']['pose_library_sha256'])
    swing=next(p for p in poses['poses'] if p['pose_id']=='swing_candidate_from_historical_r1_train')
    asset=AssetPoses(spec['asset_path']);rotation=np.eye(4)
    rotation[:3,:3]=Rotation.from_quat(swing['root_quaternion_xyzw']).as_matrix()
    names=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')
    candidates=[]
    for hip,active in [(1.1,-1.3),(1.,-1.2),(.9,-1.1),(.8,-1.)]:
        family=f'swing_support_hip{round(hip*100):03d}_active{round(-active*100):03d}'
        q,error=asset.solve(dict(zip(names,(hip,active,-hip,active))),swing['joint_pos'])
        support=asset.support(q,rotation);height=-min(x['lowest_z_root'] for x in support)+.002
        violations=[j['name'] for j in asset.joints if not j['limits'][0]-1e-8<=q[j['name']]<=j['limits'][1]+1e-8]
        if max(error)>1e-4 or violations:raise ValueError('Illegal closed-chain candidate')
        clearance=height+min(x['lowest_z_root'] for x in support if x['body']=='robot')
        for split in ('train','holdout'):
            p=copy.deepcopy(swing);p.update(pose_id=family+'_'+split,family=family,split=split,
                joint_pos=q.copy(),root_height_m=height,chassis_bottom_clearance_m=clearance,
                closure_each_m=error.tolist(),closure_max_m=float(max(error)),runtime_valid=None,
                initial_root_height_m=[height-.04,height+.04],
                initial_chassis_clearance_m=[max(0.,clearance-.04),clearance+.04],
                ideal_collider_gaps_m={x['path']:height+x['lowest_z_root'] for x in support},
                scope='Static closure-solved Swing branch support; zero velocities; not reconstructed PhysX state',
                derivation_active_q_rad=[hip,active,-hip,active])
            p.pop('source_bridge_alpha',None);poses['poses'].append(p)
        candidates.append({'family':family,'active_q_rad':[hip,active,-hip,active],
            'height_m':height,'clearance_m':clearance,'closure_max_m':float(max(error))})
    name=new_experiment_name('recovery_b25_swing_support_probe_ppo0');output=ROOT/'configs/experiments'/name
    encoded=json.dumps(poses,indent=2)+'\n'
    spec['recovery']['pose_library']=str(output/'poses.json')
    spec['recovery']['pose_library_sha256']=hashlib.sha256(encoded.encode()).hexdigest()
    spec.update(experiment=name,execution_source_root=str(ROOT/'src'),notifications={'enabled':False},
        authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'New bounded static Swing-support PPO0 preparation'},
        evaluation_only=True,diagnostic_identity_only=True)
    spec['artifacts']['run_name']=name;spec['resources']={'mode':'exclusive','sharing_authorized':False}
    families=['drawback_manual0001','R0']+[x['family'] for x in candidates]
    spec['evaluation_requests']=[{'checkpoint':spec['source_checkpoint'],'sha256':spec['source_sha256'],
        'target':[0,0],'family':f,'seconds':23.,'seed':104,'diagnostic_profile':'full_transition'} for f in families]
    spec['budget'].update(evaluation_wall_s=1800,smoke_updates=0,formal_updates=0,sample_limit=0)
    spec['evaluation']['full_trace_updates']=[]
    errors=validate(spec)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0,'play':0},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'sample_limit':0}
    report={'inputs_sha256':inputs,'candidates':candidates,'families':families,'output':str(output),
        'simulation':0,'PPO':0,'wall_limit_s':1800,'candidate_scope':'Static branch support; settling fidelity and policy skill require runtime readback'}
    if write:publish(output,{'spec.json':spec,'budget.json':book,'preparation_manifest.json':report},inputs,
        serialized_files={'poses.json':(encoded.encode(),spec['recovery']['pose_library_sha256'])},completion_marker=True)
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(write=a.write),indent=2))
