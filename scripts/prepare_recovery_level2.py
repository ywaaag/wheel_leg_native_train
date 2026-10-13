"""Migrate the user-confirmed DrawBack pose/model into a fresh limited-USD recipe."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(session):
    import numpy as np
    import torch
    from native_stand.recovery.asset_poses import AssetPoses
    parent = ROOT/'configs/experiments/2026_10_7-16_18__recovery_rise_formal_from50/spec.json'
    s = json.loads(parent.read_text())
    for path, identity in [('asset_path','asset_sha256'),('asset_module_path','asset_module_sha256'),
                           ('colleague_config_path','colleague_config_sha256')]:
        if sha(s[path]) != s[identity]:raise ValueError(path+' identity differs')
    checkpoint = ROOT/'runs/recovery_self_stand_from1500_20261003_chain/formal/model_update_1000.pt'
    old_spec = ROOT/'runs/recovery_self_stand_from1500_20261003_chain/formal/source_snapshot/spec.json'
    old = json.loads(old_spec.read_text())
    saved = torch.load(checkpoint,map_location='cpu',weights_only=False)
    if saved['spec_sha256']!=sha(old_spec) or saved['asset_sha256']!=old['asset_sha256'] or saved['update']!=1000:
        raise ValueError('historical checkpoint identity differs')
    for key in ('action','observation','history'):
        if s[key]!=old[key]:raise ValueError('migration interface differs: '+key)
    for key in ('physics_dt_s','pd_dt_s','policy_dt_s','leg_kp','leg_kd','wheel_kv','effort_limits_nm'):
        if s['control'][key]!=old['control'][key]:raise ValueError('migration control differs: '+key)
    if saved['actor']['mlp.0.weight'].shape[-1]!=150 or saved['critic']['mlp.0.weight'].shape[-1]!=150:
        raise ValueError('migration requires strict150D actor/critic')
    record_path = ROOT/'runs/recovery_pose_capture_20261002_145814/pose_0001_73d09dbe.json'
    record = json.loads(record_path.read_text())
    asset = AssetPoses(s['asset_path'])
    q = record['joint_pos']
    error = float(np.linalg.norm(asset.residual(q).reshape(-1,3),axis=-1).max())
    violations = [j['name'] for j in asset.joints if not j['limits'][0]-1e-6<=q[j['name']]<=j['limits'][1]+1e-6]
    if error>1e-4 or violations:raise ValueError('captured pose incompatible with current stops')
    library = json.loads(Path(s['recovery']['pose_library']).read_text())
    old_library = json.loads(Path(old['recovery']['pose_library']).read_text())
    poses = [copy.deepcopy(p) for p in library['poses'] if p['family']=='R0']
    for split in ('train','holdout'):
        p = copy.deepcopy(next(p for p in old_library['poses'] if p['family']=='R1' and p['split']==split))
        p.update(pose_id='drawback_manual0001_'+split,family='drawback_manual0001',
            initialization_control='passive_settle',runtime_valid=None,closure_max_m=error,
            initial_root_height_m=[.12,.22],initial_chassis_clearance_m=[.04,.15],
            source_record=str(record_path),source_record_sha256=sha(record_path))
        if p['joint_pos']!=q:raise ValueError('historical library does not use measured capture joints')
        poses.append(p)
    library['poses']=poses
    library['definition']='Confirmed DrawBack actual captured joint_pos plus R0 rehearsal; current USD geometry/limits'
    name = new_experiment_name('recovery_level2_drawback_from1000')
    folder = ROOT/'configs/experiments'/name
    if folder.exists():raise FileExistsError(folder)
    c = s['recovery']
    c.update(active_family='drawback_manual0001',pose_library=str(folder/'poses.json'),
        initial_pose_record=str(record_path),initial_pose_record_sha256=sha(record_path),
        runtime_initialization_validated=False,
        scope='Level2 user-confirmed captured DrawBack on current knee-stop USD; no Swing/random falls')
    c['standing_task']['retention']['enabled']=False
    c['standing_task']['note']='Old lifting actor is source; no BC target is certified for current near-standing states'
    c['curriculum']['levels']=[{'id':'Level2','pose_family':'drawback_manual0001',
        'description':'Captured measured contracted-leg support pose, current USD initialization pending'}]
    pose_bytes=(json.dumps(library,indent=2)+'\n').encode()
    c['pose_library_sha256']=hashlib.sha256(pose_bytes).hexdigest()
    s.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=sha(checkpoint),
        source_update=1000,source_spec_sha256=sha(old_spec),source_asset_sha256=saved['asset_sha256'])
    s.pop('pre_app_failure_predecessor',None)
    s['artifacts']['run_name']=name
    scope=('User explicitly requested migration of GUI-confirmed old update1000 and DrawBack manual0001 '
        'to current knee-stop USD and start Level2: source_eval<=600s/PPO0, smoke10<=600s, '
        'formal<=100<=3600s, total110updates/901120samples. No automatic restart or Level3/4.')
    s['authorization']={'hapi_session':session,'user_scope':scope}
    c['authorization_note']=scope
    c['physical_gate_evidence']='PENDING: source_eval on current USD, no historical runtime flags reused'
    s['phase_initialization']='Strict old150D actor/critic/Adam; same physical action scaling; new simulator reset; current LR3e-5'
    s['migration']={'old_spec':str(old_spec),'old_spec_sha256':sha(old_spec),
        'old_asset_sha256':saved['asset_sha256'],'new_asset_sha256':s['asset_sha256'],
        'pose_sha256':sha(record_path),'offline_closure_max_m':error,'joint_limit_violations':violations,
        'height_command_before_m':.4,'height_command_after_m':.36,
        'retention_disabled_reason':'Old actor not certified for current R0; preserve via rehearsal and independent gate instead of unverified BC'}
    s['experiment_variable']='Level2 old lifting policy/actual captured DrawBack migration to limited USD; height goal .36, no inherited source50 BC'
    s['wiring_smoke']={'required_event':'completed_episode','required_event_duration_s':2.,
        'event_offset_s':1.,'minimum_event_count':1,'required_groups':[
            {'family':'drawback_manual0001','minimum_completed':1,'require_runtime_initial_valid':True},
            {'family':'R0','minimum_completed':1,'require_runtime_initial_valid':True}]}
    errors=validate(s)
    if errors:raise ValueError(errors)
    book={'authorization':'AUTHORIZED','authorization_evidence':scope,'experiment':name,
        'limits':{'source_eval':1,'evaluate':0,'smoke':10,'formal':100},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':901120,'hapi_session':session}
    folder.mkdir()
    (folder/'poses.json').write_bytes(pose_bytes)
    for filename,value in [('spec.json',s),('budget.json',book)]:
        with (folder/filename).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'config':str(folder),'run':str(ROOT/'runs'/name),'migration':s['migration'],
        'simulation':0,'PPO':0},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hapi-session',required=True)
    args=parser.parse_args()
    prepare(args.hapi_session)
