"""Offline candidate review and isolated knee-stop experiment preparation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

def review():
    old = ROOT/'runs/recovery_level_from1000_20261003/formal'
    sweep = ROOT/'runs/recovery_checkpoint_sweep_20261004/results'
    candidates = []
    for update in range(100, 2001, 100):
        path = sweep/f'update_{update}/result.json'
        if not path.exists():
            path = old/f'evaluation_{update}_0_0.json'
        if not path.exists():
            continue
        evidence = json.loads(path.read_text())
        rows = []
        for env in evidence['per_env']:
            trace = np.asarray(env['compact_trace_100hz'])
            trace = trace[(trace[:,0] > 0) & (trace[:,0] <= 9.60) & (trace[:,32] != 7)]
            if not len(trace):
                raise ValueError('No common Recovery window')
            late = trace[trace[:,0] >= 7.60]
            gravity = Rotation.from_quat(late[:,22:26]).inv().apply(np.tile([0,0,-1.], (len(late),1)))
            # Canonical forward=-asset Z; canonical up=asset Y.
            pitch = np.arctan2(gravity[:,2], -gravity[:,1])
            rows.append({'env_id':env['env_id'], 'continuous_s':float(trace[-1,0]),
                'runtime_fault':env['runtime_fault'], 'late_samples':len(late),
                'height_mean_m':float(late[:,6].mean()) if len(late) else None,
                'pitch_abs_mean_rad':float(np.abs(pitch).mean()) if len(late) else None,
                'tilt_mean_rad':float(late[:,15].mean()) if len(late) else None,
                'vx_abs_mean_mps':float(np.abs(late[:,7]).mean()) if len(late) else None,
                'yaw_abs_mean_rad_s':float(np.abs(late[:,9]).mean()) if len(late) else None,
                'contact_fraction':float((late[:,10:12]>2).all(-1).mean()) if len(late) else None,
                'closure_max_m':float(trace[:,12].max())})
        model = old/f'model_update_{update}.pt'
        candidate = {'update':update,'checkpoint':str(model),'sha256':sha(model),
            'evaluation':str(path),'per_env':rows,'accepted':False,
            'mean':{k:(float(np.mean([r[k] for r in rows])) if all(r[k] is not None for r in rows) else None) for k in rows[0] if k not in ('env_id','runtime_fault')},
            'faults':sum(r['runtime_fault'] for r in rows)}
        candidates.append(candidate)
    # Prefer sustained elevated, supported states before comparing pitch.
    def rank(c):
        elevated = sum(r['height_mean_m'] is not None and r['height_mean_m']>=.37 and r['contact_fraction']>=.95 and r['late_samples']>=190 for r in c['per_env'])
        return (c['faults'], -elevated, -c['mean']['continuous_s'], c['mean']['pitch_abs_mean_rad'] if c['mean']['pitch_abs_mean_rad'] is not None else float('inf'),
                c['mean']['vx_abs_mean_mps'] if c['mean']['vx_abs_mean_mps'] is not None else float('inf'), c['update'])
    candidates.sort(key=rank)
    return {'scope':'Historical original USD/manual0001 only. Common Recovery 0-9.60s; late7.60-9.60s. Not new USD acceptance.',
        'ranking':'runtime faults; elevated supported env count; continuity; late abs pitch; vx; yaw; update',
        'accepted_candidate':None,'recommended':candidates[0],'candidates':candidates}

def main():
    from pxr import Usd, UsdPhysics
    result=review()
    directory=ROOT/'configs/experiments/recovery_knee_stop_pitch_20261004'
    write(directory/'candidate_review.json',result)
    base=json.loads((ROOT/'configs/experiments/recovery_level_from1000_20261003/spec.json').read_text())
    source=Path(base['asset_path'])
    target=ROOT/'assets/diagnostic/rmuc_robot_closed_loop_knee_stop_0233_v2.usd'
    if target.exists():raise FileExistsError(target)
    stage=Usd.Stage.Open(str(source))
    changes=[]
    for prim in stage.Traverse():
        if prim.GetName() not in ('left_knee_pitch','right_knee_pitch'):continue
        j=UsdPhysics.RevoluteJoint(prim)
        before=[j.GetLowerLimitAttr().Get(),j.GetUpperLimitAttr().Get()]
        if prim.GetName().startswith('left'):
            j.GetLowerLimitAttr().Set(float(np.rad2deg(-.233)))
        else:j.GetUpperLimitAttr().Set(float(np.rad2deg(.233)))
        changes.append({'joint':prim.GetName(),'before_deg':before,
            'after_deg':[j.GetLowerLimitAttr().Get(),j.GetUpperLimitAttr().Get()]})
    if len(changes)!=2:raise ValueError('Knee identity differs')
    stage.Flatten().Export(str(target))
    write(directory/'asset_changes.json',{'source':str(source),'source_sha256':sha(source),
        'copy':str(target),'copy_sha256':sha(target),'changes':changes,
        'semantics':'One-sided knee extension joint stops; finite solver compliance, no gas spring force.'})
    captured=json.loads((ROOT/'runs/recovery_capture_20261003_224308/pose_0000_d9204dc9.json').read_text())
    asset=AssetPoses(target)
    q0=dict(captured['joint_pos'])
    active={n:v for n,v in q0.items() if n in ('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')}
    q,error=asset.solve(active,q0)
    if error.max()>1e-4:raise ValueError(f'Closure not feasible: {error}')
    rotation=np.eye(4);rotation[:3,:3]=Rotation.from_quat(captured['root_quaternion_xyzw']).as_matrix()
    support=asset.support(q,rotation)
    root_height=-min(r['lowest_z_root'] for r in support)+.002
    poses=[]
    for split in ('train','holdout'):
        poses.append({'pose_id':f'{split}_captured_knee_stop','split':split,'seed':20261004,'family':'R1',
            'offline_valid':True,'runtime_valid':None,'joint_pos':q,'root_height_m':root_height,
            'root_quaternion_xyzw':captured['root_quaternion_xyzw'],
            'closure_max_m':float(error.max()),'support':support,'source_pose':str(ROOT/'runs/recovery_capture_20261003_224308/pose_0000_d9204dc9.json')})
    write(directory/'poses.json',{'asset_sha256':sha(target),'attempted':2,'offline_rejected':0,'runtime_rejected':None,
        'poses':poses,'definition':'Captured geometry, closure-resolved with knee stop. Initial velocities set zero by shared reset; runtime validation pending.'})
    chosen=result['recommended']
    base.update(experiment=directory.name,source_checkpoint=chosen['checkpoint'],source_sha256=chosen['sha256'],
        source_update=chosen['update'],source_asset_sha256=base['asset_sha256'],asset_path=str(target),asset_sha256=sha(target))
    base['source_spec_sha256']=sha(ROOT/'runs/recovery_level_from1000_20261003/formal/source_snapshot/spec.json')
    base['budget'].update(source_eval_wall_s=300,smoke_wall_s=300,formal_wall_s=None,smoke_updates=3,formal_updates=9997,sample_limit=81920000)
    base['recovery'].update(pose_library=str(directory/'poses.json'),pose_library_sha256=sha(directory/'poses.json'),
        runtime_initialization_validated=False,initial_pose_record=poses[0]['source_pose'],
        initial_pose_record_sha256=sha(poses[0]['source_pose']))
    base['recovery']['initialization'].update(settle_min_s=.2,settle_dwell_s=.2,settle_max_s=1.,chassis_clearance_m=[0.,.15])
    base['reward'].update(pitch_level=-1.,pitch_level_scale_rad=.2,pitch_level_start_m=.32,pitch_level_full_m=.38)
    base['experiment_variable']='New knee-stop USD and captured low pose; explicit high-position pitch cost. Existing PD, limits, action, PPO unchanged.'
    base['authorization']={'hapi_session':'6cc03979-87e5-4f7b-a7e7-e48ebf85d4c1','user_scope':'10000 total PPO updates including smoke; no formal wall limit; new knee USD, captured pose, improve pitch.'}
    base['authorization_note']=base['authorization']['user_scope']
    write(directory/'spec.json',base)
    write(directory/'budget.json',{'authorization':'AUTHORIZED','authorization_evidence':base['authorization_note'],
        'limits':{'source_eval':0,'smoke':3,'formal':9997,'evaluate':0,'play':0},
        'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0,'source_eval_wall_limit_s':300})
    print(json.dumps({'recommended_update':chosen['update'],'mean':chosen['mean'],'asset':str(target),'root_height_m':root_height,'spec':str(directory/'spec.json')},indent=2))

def complete_library():
    directory=ROOT/'configs/experiments/recovery_knee_stop_pitch_20261004'
    spec=json.loads((directory/'spec.json').read_text())
    asset=AssetPoses(spec['asset_path'])
    library=json.loads((directory/'poses.json').read_text())
    library['collision_geometry']=[{key:(value.tolist() if isinstance(value,np.ndarray) else value) for key,value in row.items()} for row in asset.colliders]
    library['joint_limits_rad']={row['name']:row['limits'] for row in asset.joints}
    (directory/'poses.json').write_text(json.dumps(library,indent=2)+'\n')
    spec['recovery']['pose_library_sha256']=sha(directory/'poses.json')
    (directory/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')

if __name__=='__main__':
    import sys
    if '--complete-library' in sys.argv:complete_library()
    elif '--review-only' in sys.argv:
        write(ROOT/'configs/experiments/recovery_knee_stop_pitch_20261004/candidate_review_corrected.json',review())
    else:main()
