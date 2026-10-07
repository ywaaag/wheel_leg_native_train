"""Generate a fresh CPU-only standing recipe, pose library and unapproved ledger."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reward_probe(spec):
    """Synthetic fixed-state height sweeps, not a physical performance result."""
    import torch
    from native_stand.recovery.domain import process_reward
    h=torch.tensor([.30,.32,.334,.34,.36,.38,.40])
    result={}
    for name,pitch,roll,vx,yaw,mirror in (
            ('level_stationary',0.,0.,0.,0.,0.),
            ('moving_asymmetric',.04,.04,.23,.8,.59)):
        n=len(h);z=torch.zeros(n);d=torch.zeros(n,10)
        d[:,0]=pitch;d[:,1]=roll;d[:,2:4]=.30;d[:,4:6]=mirror
        v=torch.zeros(n,3);v[:,0]=vx
        w=torch.zeros(n,3);w[:,1]=yaw
        total,raw,weighted=process_reward(h,torch.full_like(h,.168),torch.full_like(h,.36),
            torch.full_like(h,float(np.cos(pitch)*np.cos(roll))),torch.zeros(n,6),torch.zeros(n,6),
            z,z.bool(),z.bool(),weights=spec['reward'],dt=.01,pitch=torch.full_like(h,pitch),
            roll=torch.full_like(h,roll),contact=torch.ones(n,2)*50.,wheel_velocity=torch.zeros(n,2),
            support_balance=z,linear_velocity=v,angular_velocity=w,
            settling_config=spec['recovery']['settling_reward'],
            standing_config=spec['recovery']['standing_task']['reward'],standing_diagnostics=d)
        result[name]=[{'height_m':float(h[i]),'total_per_policy_step':float(total[i]),
            'raw':{k:float(value[i]) for k,value in raw.items()},
            'weighted_dt':{k:float(value[i]) for k,value in weighted.items()}} for i in range(n)]
    return {'scope':'Synthetic same-state height sweep; no empirical optimum or policy gradient claim',
            'policy_dt_s':.01,'cases':result}


def prepare_height_independent(source_spec, output):
    """New R0 recipe only; previous run/spec and authorization stay untouched."""
    output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    spec=json.loads(Path(source_spec).read_text())
    if not spec.get('recovery',{}).get('standing_task'):
        raise ValueError('A standing recipe is required')
    if sha(spec['source_checkpoint'])!=spec['source_sha256']:
        raise ValueError('Source identity differs')
    spec.update(experiment=output.name,recipe_parent_spec_sha256=sha(source_spec))
    spec['authorization']['user_scope']='CPU height-gate repair only; new simulation/PPO authorization pending'
    spec['authorization_note']='No restart or transfer of the stopped chain allowance is authorized'
    spec['recovery']['authorization_note']='CPU-only R0 standing repair; no new Recovery or standing run submitted'
    # Existing coefficients stay fixed to expose the effect of removing height escape.
    spec['reward']['upright']=0.
    for axis in ('pitch','roll'):
        spec['reward'][axis+'_level_gate_mode']='unconditional'
    standing=spec['recovery']['standing_task']
    standing.update(version=2,source_baseline_run=None)
    standing['reward']['gate_mode']='unconditional'
    standing['retention'].update(height_min_m=.30,height_max_m=.40)
    standing['retention']['scope_note']=('Actual valid R0 zero-command inputs at0.30-0.40m; '
        'source behavior outside its observed near-standing range is not certified. '
        'This is actor preservation, not teacher control or a success guarantee.')
    spec['recovery']['settling_reward']['gate_mode']='unconditional'
    spec['recovery'].update(runtime_initialization_validated=False,runtime_initialization_evidence=None)
    spec['budget'].update(source_eval_wall_s=300,smoke_updates=3,smoke_wall_s=300,
                         formal_updates=500,formal_wall_s=7200,sample_limit=503*8192,
                         chain_wall_s=8460)
    spec['artifacts']['run_name']=output.name
    spec['experiment_variable']=('R0 height-independent stability constraints: pitch/roll level costs '
        'replace upright contribution, all standing/settling costs are unconditional; '
        'retention scope widens to0.30-0.40m. Other coefficients and physics unchanged. '
        'This is a combined mechanism repair, not a single-variable efficacy claim.')
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    budget={'authorization':'UNAUTHORIZED','authorization_evidence':'Stopped by user; CPU repair only, no new run authorized',
        'experiment':spec['experiment'],'limits':{'source_eval':1,'evaluate':2,'smoke':3,'formal':500},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':503*8192}
    output.mkdir(parents=True)
    (output/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    (output/'budget.json').write_text(json.dumps(budget,indent=2)+'\n')
    (output/'reward_probe.json').write_text(json.dumps(
        {'previous':reward_probe(json.loads(Path(source_spec).read_text())),
         'corrected':reward_probe(spec)},indent=2)+'\n')
    return {'spec':str(output/'spec.json'),'simulation':0,'ppo':0,'authorization':'UNAUTHORIZED'}


def prepare(source_spec, output):
    output=Path(output).resolve()
    if output.exists() and any(output.iterdir()):raise FileExistsError(output)
    spec=json.loads(Path(source_spec).read_text())
    checkpoint=Path(spec['source_checkpoint'])
    if sha(checkpoint)!='c82125438bc17cdb5f559dcad3ca40cc7dff654f2dcc9d5fae97ec700a69fc82':
        raise ValueError('Expected selected R0 update1500 source')
    asset=AssetPoses(spec['asset_path'])
    library=json.loads(Path(spec['recovery']['pose_library']).read_text())
    base=next(p for p in library['poses'] if p['family']=='R0')
    poses=[];rejected=[]
    active_names=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')
    for family,jitter,tilt in [('R0',.005,0.),('R0_perturbed',.025,.03)]:
        for split,seed in [('train',20261006),('holdout',20261016)]:
            rng=np.random.default_rng(seed)
            for index in range(4):
                active={n:0. if index==0 else float(rng.uniform(-jitter,jitter)) for n in active_names}
                q,residual=asset.solve(active,base['joint_pos'])
                rot=Rotation.from_quat(base['root_quaternion_xyzw'])
                if index and tilt:
                    rot=Rotation.from_rotvec([float(rng.uniform(-tilt,tilt)),0.,
                                             float(rng.uniform(-tilt,tilt))])*rot
                matrix=np.eye(4);matrix[:3,:3]=rot.as_matrix()
                support=asset.support(q,matrix)
                height=.002-min(s['lowest_z_root'] for s in support)
                chassis=height+min(s['lowest_z_root'] for s in support if s['body']=='robot')
                valid=(residual.max()<=1e-4 and all(j['limits'][0]-1e-6<=q[j['name']]<=j['limits'][1]+1e-6
                                                  for j in asset.joints))
                row={**base,'pose_id':f'{family}_{split}_{index}','family':family,'split':split,
                    'seed':seed+index,'joint_pos':q,'root_quaternion_xyzw':rot.as_quat().tolist(),
                    'root_height_m':height,'closure_max_m':float(residual.max()),'support':support,
                    'initial_root_height_m':[height-.025,height+.025],
                    'initial_chassis_clearance_m':[chassis-.025,chassis+.025],
                    'sample_weight':.7 if index==0 else .1,'offline_valid':bool(valid),
                    'runtime_valid':None,'initialization_control':'direct_zero_reset'}
                (poses if valid else rejected).append(row)
    # Keep captured/asymmetric candidates for explicitly enabled future stages.
    for index,p in enumerate(p for p in library['poses'] if p['family'] in ('R1','R2_R3')):
        row=copy.deepcopy(p)
        row['seed']=(20262000 if row['split']=='train' else 20263000)+index
        row['runtime_valid']=None
        poses.append(row)
    library.update(poses=poses,rejected_candidates=rejected,attempted=len(poses)+len(rejected),
        offline_rejected=len(rejected),runtime_rejected=None,
        definition='R0 nominal70%/small closure-consistent perturbations30%; R1 enlarged near-standing; '
                   'R2 captured low pose; R3 existing asymmetric poses. Offline only; no reference motion.')
    protocol={'version':'standing_balance_v1','seconds':10.,'steady_window_s':[2.,10.],
        'height_m':[.34,.38],'height_fraction_min':.9,'vx_abs_max_mps':.03,'vy_abs_max_mps':.03,
        'yaw_abs_max_rad_s':.03,'excursion_max_m':.2,'dual_contact_min':.95,
        'level_mean_max_rad':.05,'level_peak_max_rad':.1,'peak_tilt_max_rad':.12,
        'mirror_error_max_rad':.10,'leg_length_difference_max_m':.01,
        'support_difference_max':.30,'saturation_max':.05,'closure_max_m':.005}
    import torch
    source=torch.load(checkpoint,map_location='cpu',weights_only=False)
    spec.update(experiment=output.name,source_spec_sha256=source['spec_sha256'],
                recipe_parent_spec_sha256=sha(source_spec),initialization='warmstart',
                restore_source_rng=False,restore_recovery_curriculum=False)
    # Freeze the current colleague dependency identity for this new recipe only.
    dependency_changes={}
    for key in ('asset_path','asset_module_path','colleague_config_path'):
        sha_key={'asset_path':'asset_sha256','asset_module_path':'asset_module_sha256',
                 'colleague_config_path':'colleague_config_sha256'}[key]
        actual=sha(spec[key])
        if actual!=spec[sha_key]:dependency_changes[key]={'previous':spec[sha_key],'current':actual}
        spec[sha_key]=actual
    if 'asset_path' in dependency_changes:raise ValueError('USD changed; preparation refuses altered physics')
    spec['dependency_identity_changes']=dependency_changes
    spec['reward'].pop('leg_symmetry',None)
    spec['reward']['lift']=0.  # Gaussian target reward replaces saturated progress for R0.
    for axis in ('pitch','roll'):
        spec['reward'][axis+'_level_full_m']=.36
    spec['recovery']['settling_reward'].update(height_full_m=.36,
        settling_linear_weight=-.6,settling_angular_weight=-.4)
    reward={'gate_start_m':.30,'gate_full_m':.36,'height_width_m':.04,
        'vertical_scale_mps':.1,'level_angular_scale_rad_s':.3,'mirror_deadband_rad':.03,
        'mirror_scale_rad':.2,'leg_length_scale_m':.02,'wheel_difference_scale_rad_s':10.,
        'weights':{'standing_height':3.,'vertical_motion':-.1,'level_angular_motion':-.1,
                  'mirror_posture':-.02,'leg_length_balance':-.02,'wheel_difference':-.01}}
    hips={j['name']:j['ta'][:3,3].tolist() for j in asset.joints if j['name'] in
          ('left_hip_pitch','right_hip_pitch')}
    spec['recovery']['standing_task']={'version':1,'protocol':protocol,'reward':reward,
        'hip_anchors_root_m':[hips['left_hip_pitch'],hips['right_hip_pitch']],
        'retention':{'enabled':True,'coefficient':.02,'max_samples_per_rollout':256,
                     'height_min_m':.34,'height_max_m':.38},
        'source_baseline_run':None,'note':'Teacher is frozen update1500 with leg1.6/wheel100 semantics; '
            'old STAND update500 is not used as a teacher for this auxiliary loss.'}
    spec['recovery']['autonomous_stability'].update(tilt_max_rad=.1,linear_speed_max_mps=.05,
                                                   angular_speed_max_rad_s=.1)
    spec['recovery']['curriculum'].update(automatic_upgrade=True,max_enabled_stage=0,
        full_confirmations_required=2,episodes_per_window=128,windows_required=2,
        levels=[{'id':'R0','pose_family':'R0','description':'nominal70% and small perturbations30%'},
                {'id':'R1','pose_family':'R0_perturbed','description':'enlarged near-standing perturbations'},
                {'id':'R2','pose_family':'R1','description':'captured bottom-down low pose'},
                {'id':'R3','pose_family':'R2_R3','description':'expanded asymmetric low poses'}])
    spec['recovery']['runtime_initialization_validated']=False
    spec['recovery']['runtime_initialization_evidence']=None
    spec['recovery']['handover_domain_validated']=False
    spec['recovery']['handover_domain_scope']='Autonomous standing; no frozen STAND takeover certification'
    spec['curriculum']['stages']=spec['curriculum']['stages'][:1]
    spec['evaluation'].update(full_every_updates=250,light_every_updates=100,light_seconds=2,
        full_at_final=True,standing_height_m=[.34,.38],peak_tilt_max_rad=.12,
        vx_error_max_mps=.03,vy_abs_max_mps=.03)
    spec['budget'].update(source_eval_wall_s=300,smoke_updates=3,smoke_wall_s=300,
                         formal_updates=500,formal_wall_s=7200,sample_limit=503*8192)
    spec['proposed_durability_budget']={'wall_s':600,'ppo_updates':0,'seconds':100}
    spec['experiment_variable']=('R0 standing balance recipe: Gaussian height, velocity settling, '
        'weak deadband mirror/leg-length costs and explicit source retention; not a single-variable ablation.')
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    output.mkdir(parents=True,exist_ok=True)
    pose_path=output/'poses.json'
    pose_path.write_text(json.dumps(library,indent=2)+'\n')
    spec['recovery'].update(pose_library=str(pose_path),pose_library_sha256=sha(pose_path))
    (output/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    budget={'authorization':'UNAUTHORIZED','authorization_evidence':'Implementation only; proposed execution budget pending',
        'experiment':spec['experiment'],'limits':{'source_eval':1,'evaluate':2,'smoke':3,'formal':500},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':503*8192}
    (output/'budget.json').write_text(json.dumps(budget,indent=2)+'\n')
    return {'spec':str(output/'spec.json'),'valid_candidates':len(poses),'rejected':len(rejected),
            'simulation':0,'ppo':0,'authorization':'UNAUTHORIZED'}


def prepare_survival_level(source_spec, checkpoint, output, *, authorize=False):
    """Fresh user-goal recipe; no mutation of previous experiments or allowances."""
    import torch
    output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    checkpoint=Path(checkpoint).resolve()
    expected='1fa4255a90be6a9d43294a532a9f8cbf8c620d228ac6e7e5b2f6cc7301376d71'
    if sha(checkpoint)!=expected:raise ValueError('Expected GUI-approved scissor update50')
    spec=json.loads(Path(source_spec).read_text())
    source=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if sha(source_spec)!=source['spec_sha256'] or sha(spec['asset_path'])!=source['asset_sha256']:
        raise ValueError('Source snapshot or physical asset identity differs')
    spec.update(experiment=output.name,source_checkpoint=str(checkpoint),source_sha256=expected,
        source_update=50,source_input_dim=150,source_spec_sha256=source['spec_sha256'],
        recipe_parent_spec_sha256=sha(source_spec),restore_recovery_curriculum=False,restore_source_rng=False)
    for key,sha_key in (('asset_module_path','asset_module_sha256'),('colleague_config_path','colleague_config_sha256')):
        if sha(spec[key])!=spec[sha_key]:raise ValueError(f'{key} changed; review before preparing')
    for key in ('comparison_evidence','budget_remaining_at_preparation','diagnostic_source_spec',
                'diagnostic_checkpoint_sha256','revision_of_spec_sha256','proposed_durability_budget'):
        spec.pop(key,None)
    for key in ('wheel_longitudinal_offset','wheel_longitudinal_deadband_m','wheel_longitudinal_scale_m'):
        spec['reward'].pop(key,None)
    spec['reward']['support_balance']=0.
    config=spec['recovery']
    config['settling_reward'].update(settling_linear_weight=0.,settling_angular_weight=0.,settling_yaw_weight=0.)
    config['autonomous_stability']={'objective':'survival_level','height_m':[.34,.38],
        'tilt_max_rad':.18,'dual_contact_min_n':2.,'chassis_clearance_min_m':.25}
    standing=config['standing_task']
    protocol=standing['protocol']
    for key in ('vx_abs_max_mps','vy_abs_max_mps','yaw_abs_max_rad_s','excursion_max_m',
                'mirror_error_max_rad','leg_length_difference_max_m','support_difference_max'):
        protocol.pop(key,None)
    protocol.update(version='survival_level_v1',objective='survival_level',
        level_mean_max_rad=.10,level_peak_max_rad=.15,peak_tilt_max_rad=.18)
    standing['reward']['weights'].update(mirror_posture=0.,leg_length_balance=0.,wheel_difference=0.)
    standing['retention'].update(gradient_diagnostics=False,save_gradient_updates=[])
    standing['note']='Frozen retention teacher is approved scissor update50; STAND takeover disabled.'
    config['autonomous_stability_note']='Height/support/level continuous2s qualifies training success; full10s evaluation plus R0 retention confirms curriculum.'
    config['curriculum'].update(max_enabled_stage=1)
    config['curriculum']['levels'][1].update(retained_families=['R0'],retained_fraction=.4,
        description='60% enlarged near-standing poses,40% R0 rehearsal; never a bottom-down pose')
    library=json.loads(Path(config['pose_library']).read_text())
    for split in ('train','holdout'):
        rows=[row for row in library['poses'] if row['family']=='R0_perturbed' and row['split']==split]
        if len(rows)!=4 or any(not row['offline_valid'] for row in rows):
            raise ValueError('Expected four closure-valid near-standing poses per split')
        for index,row in enumerate(rows):row['sample_weight']=.1 if index==0 else .3
    config['pose_library']=str(output/'poses.json')
    config['scope']='R0 survival/level confirmation -> R1 near-standing perturbations with40% R0; R2/R3 disabled.'
    config['physical_gate_evidence']={'approved_source_evaluation':str(checkpoint.with_name('evaluation_50_0_0.json'))}
    spec['evaluation'].update(light_every_updates=0,full_every_updates=500,
        checkpoint_every_updates=100,unlock_full_updates=[100,200],run_final_durability=True,
        peak_tilt_max_rad=.18,protocol_identity='survival_level_v1')
    for key in ('standing_drift_max_m','standing_excursion_max_m','vx_error_max_mps','yaw_error_max_rad_s',
                'vy_abs_max_mps','motion_vx_error_max_mps','motion_yaw_error_max_rad_s','relative_motion_error_fraction'):
        spec['evaluation'].pop(key,None)
    spec['budget'].update(source_eval_wall_s=300,smoke_updates=3,smoke_wall_s=300,
        formal_updates=9997,formal_wall_s=34140,sample_limit=10000*8192,
        durability_wall_s=1200,chain_wall_s=36000)
    spec['diagnostics'].pop('wheel_geometry_readback_gate',None)
    spec['artifacts']['run_name']=output.name
    note='2026-10-06 user authorized headless detached10000total PPO updates;3smoke+9997formal, conservative10h physical chain cap, same physics; R1 maximum.'
    spec['authorization_note']=note
    spec['authorization']['user_scope']=note
    config['authorization_note']=note
    spec['phase_initialization']='Strict scissor update50 actor/critic/Adam; LR3e-5 read back; new physical reset and new curriculum counters.'
    spec['experiment_variable']='Changed objective: survival+pitch/roll level; removed speed/yaw/symmetry/offset costs and gates, enabled R1 after frozen new confirmations. Not a single-variable ablation.'
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    book={'authorization':'AUTHORIZED' if authorize else 'UNAUTHORIZED',
        'authorization_evidence':note if authorize else 'Prepared only; no budget enabled',
        'experiment':output.name,'limits':{'source_eval':1,'evaluate':1,'smoke':3,'formal':9997},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':10000*8192,'chain_wall_limit_s':36000,
        'quota_origin':{'kind':'new_explicit_user_authorization','total_updates':10000,
                        'old_allowances_not_transferred':True},'hapi_session':spec['authorization']['hapi_session']}
    output.mkdir(parents=True)
    (output/'poses.json').write_text(json.dumps(library,indent=2)+'\n')
    config['pose_library_sha256']=sha(output/'poses.json')
    (output/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    (output/'budget.json').write_text(json.dumps(book,indent=2)+'\n')
    (output/'reward_probe.json').write_text(json.dumps(reward_probe(spec),indent=2)+'\n')
    return {'spec':str(output/'spec.json'),'simulation':0,'ppo':0,'authorization':book['authorization']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-spec',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--recipe',choices=('initial','height-independent','survival-level'),default='initial')
    p.add_argument('--source-checkpoint',type=Path)
    p.add_argument('--authorize',action='store_true',help='enable the explicitly approved survival/level budget')
    a=p.parse_args()
    if a.recipe=='survival-level':
        if a.source_checkpoint is None:p.error('--source-checkpoint required for survival-level')
        result=prepare_survival_level(a.source_spec,a.source_checkpoint,a.output_dir,authorize=a.authorize)
    else:
        entry=prepare if a.recipe=='initial' else prepare_height_independent
        result=entry(a.source_spec,a.output_dir)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
