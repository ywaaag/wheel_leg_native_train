"""Prepare an identity-checked PPO0 low-pose capability locator; no simulator."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.config import validate

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(session):
    import numpy as np
    from scipy.spatial.transform import Rotation
    from native_stand.recovery.asset_poses import AssetPoses
    parent = ROOT/'configs/experiments/recovery_coverage_ab_20261007/B_uniform/spec.json'
    spec = json.loads(parent.read_text())
    for path, identity in [('source_checkpoint','source_sha256'), ('asset_path','asset_sha256'),
                           ('asset_module_path','asset_module_sha256'),
                           ('colleague_config_path','colleague_config_sha256')]:
        if sha(spec[path]) != spec[identity]:
            raise ValueError(path+' identity differs')
    library = json.loads(Path(spec['recovery']['pose_library']).read_text())
    low = next(p for p in library['poses'] if p['family']=='R1' and p['split']=='train')
    asset = AssetPoses(spec['asset_path'])
    rotation = np.eye(4)
    rotation[:3,:3] = Rotation.from_quat(low['root_quaternion_xyzw']).as_matrix()
    names = ('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')
    generated = []
    for family, factor in [('rise_mid',.5), ('rise_lower',.75)]:
        q, error = asset.solve({n:low['joint_pos'][n]*factor for n in names},low['joint_pos'])
        support = asset.support(q,rotation)
        height = .002-min(p['lowest_z_root'] for p in support)
        gap = height+min(p['lowest_z_root'] for p in support if p['body']=='robot')
        if max(error)>1e-4 or any(not j['limits'][0]-1e-6<=q[j['name']]<=j['limits'][1]+1e-6
                                for j in asset.joints):
            raise ValueError('invalid offline closure pose')
        for split in ('train','holdout'):
            row = copy.deepcopy(low)
            row.update(pose_id=family+'_'+split, family=family, split=split,
                joint_pos=q, root_height_m=height, closure_max_m=float(max(error)),
                support=support, initial_root_height_m=[height-.05,height+.05],
                initial_chassis_clearance_m=[max(-.005,gap-.05),gap+.05],
                initialization_control='passive_settle', runtime_valid=None,
                definition='Offline physical-joint closure candidate, no reference controller')
            generated.append(row)
    library['poses'].extend(generated)
    name = new_experiment_name('recovery_rise_source_locator')
    folder = ROOT/'configs/experiments'/name
    if folder.exists():
        raise FileExistsError(folder)
    config = spec['recovery']
    config['pose_library'] = str(folder/'poses.json')
    pose_bytes = (json.dumps(library,indent=2)+'\n').encode()
    config['pose_library_sha256'] = hashlib.sha256(pose_bytes).hexdigest()
    config['holdout_sampling'] = 'balanced_pose_cycle'
    spec.update(experiment=name, evaluation_only=True, effective_recipe_version=1, execution_source_root=str(ROOT/'src'),
                device={'physical_index':0,'uuid':'GPU-e704e7d4-2965-4712-9759-ba6b9910bd72'})
    spec['artifacts']['run_name'] = name
    scope = ('User approved recovery rising plan execution: PPO0 source locator, '
             '3 low-pose families x 8env x10s, <=1200s; no PPO in this ledger. '
             'Subsequent separate training maximum smoke10+formal100, no automatic extension.')
    spec['authorization'] = {'hapi_session':session,'user_scope':scope}
    spec['resources'] = {'mode':'shared','sharing_authorized':True,
        'authorization_note':'User explicitly allows GPU0 sharing; never stop another process.'}
    config['authorization_note'] = scope
    spec['evaluation_requests'] = [{'checkpoint':spec['source_checkpoint'],
        'sha256':spec['source_sha256'],'target':[0,0],'family':family,'seconds':10.,'seed':104}
        for family in ('rise_mid','rise_lower','R1')]
    spec['budget'].update(evaluation_wall_s=1200,smoke_updates=0,formal_updates=0,sample_limit=0)
    spec['experiment_variable'] = 'PPO0 capability locator; 10s standing gate is diagnostic, not low-pose recovery certification'
    errors = validate(spec)
    if errors:
        raise ValueError(errors)
    book = {'authorization':'AUTHORIZED','authorization_evidence':scope,'experiment':name,
        'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},
        'attempts':{},'source_eval_wall_used_s':0.,'sample_limit':0,'hapi_session':session}
    folder.mkdir()
    (folder/'poses.json').write_bytes(pose_bytes)
    for filename, value in [('spec.json',spec),('budget.json',book)]:
        with (folder/filename).open('x') as stream:
            json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'config':str(folder),'run':str(ROOT/'runs'/name),
        'poses':[(p['family'],p['root_height_m']) for p in generated if p['split']=='train'],
        'simulation':0,'PPO':0},indent=2))


def prepare_training(locator, session):
    locator = Path(locator).resolve()
    terminal = json.loads((locator/'terminal_report.json').read_text())
    low = json.loads((locator/'evaluation_02.json').read_text())
    if (terminal['status']!='COMPLETED' or terminal['missing_requests'] or
            low['evaluation_family']!='R1' or len(low['per_env'])!=8 or
            any(not p['initial_valid'] or p['runtime_fault'] for p in low['per_env'])):
        raise ValueError('low-pose initialization evidence missing or invalid')
    parent = ROOT/'configs/experiments/recovery_coverage_ab_20261007/B_uniform/spec.json'
    s = json.loads(parent.read_text())
    library = Path(s['recovery']['pose_library'])
    name = new_experiment_name('recovery_rise_low_from50')
    folder = ROOT/'configs/experiments'/name
    if folder.exists():raise FileExistsError(folder)
    scope = ('User approved autonomous rising plan execution: validated R1 low pose60%, '
        'R0 rehearsal40%; source PPO0<=600s, smoke10<=600s, formal<=100<=3600s; '
        '110updates/901120samples maximum; no extension or harder pose promotion.')
    s.update(experiment=name, effective_recipe_version=1,execution_source_root=str(ROOT/'src'))
    s['authorization']={'hapi_session':session,'user_scope':scope}
    s['resources']={'mode':'shared','sharing_authorized':True,
        'authorization_note':'User explicitly allows GPU0 sharing; never stop another process.'}
    s['artifacts']['run_name']=name
    c=s['recovery'];c.update(task_kind='rising',active_family='R1',holdout_sampling='balanced_pose_cycle',
        authorization_note=scope,pose_library=str(folder/'poses.json'),
        rising_task={'version':'autonomous_rise_v1','recovery_deadline_s':11.5,
                     'post_rise_hold_s':10.,'retained_families':['R0'],'retained_fraction':.4})
    c['scope']='One validated low pose, autonomous recovery; no STAND control or automatic upgrade'
    c['physical_gate_evidence']=str(locator/'evaluation_02.json')
    c['fsm']['timeout_s']=11.5
    c['curriculum']['automatic_upgrade']=False
    c['standing_task'].pop('training_episode',None)
    c['standing_task']['retention']['sample_selection']='uniform_rollout'
    c['standing_task']['reward']['gate_mode']='height'
    s['reward'].update(lift=2.,upright=.5,success_once=10.,
        pitch_level_gate_mode='height',roll_level_gate_mode='height')
    s['curriculum']['episode_length_s']=11.5
    s['evaluation'].update(seconds=23.,steady_window_s=[0.,23.],light_seconds=23.,
        light_window_s=[0.,23.],protocol_identity='autonomous_rise_v1',run_final_durability=False)
    s['budget'].update(source_eval_wall_s=600,smoke_wall_s=600,formal_wall_s=3600,
        smoke_updates=10,formal_updates=100,sample_limit=901120,chain_wall_s=4860)
    s['wiring_smoke']={'required_event':'completed_episode','required_event_duration_s':2.,
        'event_offset_s':1.,'minimum_event_count':1,
        'required_groups':[
            {'family':'R1','minimum_completed':1,'minimum_duration_s':.01,'require_runtime_initial_valid':True},
            {'family':'R0','minimum_completed':1,'minimum_duration_s':2.,'require_runtime_initial_valid':True}]}
    s['experiment_variable']='First low-pose rising task: lift/upright signal, height-gated level costs, autonomous2s success, event-aligned10s acceptance'
    errors=validate(s)
    if errors:raise ValueError(errors)
    folder.mkdir()
    with (folder/'poses.json').open('xb') as stream:stream.write(library.read_bytes())
    book={'authorization':'AUTHORIZED','authorization_evidence':scope,'experiment':name,
        'limits':{'source_eval':1,'evaluate':0,'smoke':10,'formal':100},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':901120,'hapi_session':session}
    for filename,value in [('spec.json',s),('budget.json',book)]:
        with (folder/filename).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'config':str(folder),'run':str(ROOT/'runs'/name),
        'simulation':0,'PPO':0,'maximum_PPO_updates':110},indent=2))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hapi-session',required=True)
    parser.add_argument('--locator-run',type=Path)
    args = parser.parse_args()
    if args.locator_run:prepare_training(args.locator_run,args.hapi_session)
    else:prepare(args.hapi_session)
