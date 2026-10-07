"""Fresh authorized PPO0 recipe migration; never consumes historical allowance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(destination,physical_gpu=0):
    destination=Path(destination).resolve()
    if destination.exists():raise FileExistsError(destination)
    old=ROOT/'runs/motion_high_speed_course_20261007/formal/source_snapshot/spec.json'
    spec=json.loads(old.read_text())
    checkpoint=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt'
    expected='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'
    if sha(checkpoint)!=expected:raise ValueError('B250 SHA differs')
    spec.update(experiment='motion_recheck_20261007',effective_recipe_version=1,evaluation_only=True,
        execution_source_root=str(ROOT/'src'),execution_version='shared_native_20261007',
        objective='global_adv_norm',authorization='AUTHORIZED',diagnostic_identity_only=True,
        authorization_note=f'User authorized GPU{physical_gpu} PPO0 engineering/capability recheck <=3600s, at most two startup retries; no optimizer or training',
        source_evidence={'historical_spec':str(old),'sha256':sha(old)},
        phase_initialization='Frozen B250 actor only for evaluation; no optimizer constructed, no PhysX resume')
    for key in ('reward_revision','offline_candidate','source_trajectory_baseline','experiment_variable'):
        spec.pop(key,None)
    spec['reward']['tracking_mode']='combined'
    spec['reward'].pop('linear_velocity_tracking',None)
    spec['reward'].pop('yaw_velocity_tracking',None)
    for stage in spec['curriculum']['stages']:stage['command_mode']='ramp'
    e=spec['evaluation']
    e.update(protocol_identity='motion_absolute_v3',gate_identity='absolute_error_0p3_glide_0p5_v1',
        command_mode='ramp',motion_protocol='ramp',tracking_mode='combined',
        parking_window_s=[26.,30.],motion_window_s=[10.,18.],steady_window_s=[10.,18.],
        zero_mode='low_speed',zero_mean_abs_vx_max_mps=.5,
        motion_vx_error_max_mps=.3,motion_yaw_error_max_rad_s=.3,
        direction_fraction_min=.95,straight_yaw_max_rad_s=.3,yaw_translation_max_mps=.3,
        field_boundary_max_m=60.,yaw_drift_max_m=.3,yaw_excursion_max_m=.5,
        vy_abs_max_mps=.02,yaw_error_max_rad_s=.3,seconds=30.)
    # The old capability gate used .3 zero yaw and .5 tilt; preserve these physical bounds.
    for key in ('motion_vx_min_speed_enabled','motion_vx_min_speed_fraction',
            'relative_motion_error_fraction','motion_yaw_min_speed_enabled',
            'motion_yaw_min_speed_fraction','stop_window_s','standing_drift_max_m',
            'standing_excursion_max_m','height_steady_fraction_min','vx_error_max_mps'):
        e.pop(key,None)
    requests=[]
    for vx in (0.,1.,-1.,1.5,-1.5,2.,-2.):
        requests.append({'checkpoint':str(checkpoint),'sha256':expected,'role':'source','target':[vx,0.]})
    new=ROOT/'runs/motion_high_speed_course_20261007/formal/model_update_250.pt'
    for vx in (1.5,-1.5):
        requests.append({'checkpoint':str(new),'sha256':sha(new),'role':'candidate','target':[vx,0.]})
    spec['evaluation_requests']=requests
    spec['budget']['evaluation_wall_s']=3600.
    spec['budget'].update(formal_updates=0,smoke_updates=0,sample_limit=0,formal_samples=0)
    spec['device']={'physical_index':physical_gpu,'uuid':('GPU-e704e7d4-2965-4712-9759-ba6b9910bd72' if physical_gpu==0 else 'GPU-dfc076b6-b082-3065-512a-e21064067db1'),
                    'logical':'cuda:0','headless':True}
    spec['curriculum']['task_progression']['max_enabled_stage']=1
    # This declaration is evaluation-only. No historical update allowance is transferred.
    book={'authorization':'AUTHORIZED','limits':{'source_eval':0,'smoke':0,'formal':0,'evaluate':3,'play':0},
          'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},
          'source_eval_wall_used_s':0.,'online_PPO_limit':0,'offline_optimizer_limit':0,
          'evaluation_wall_limit_s':3600.,'authorization_note':spec['authorization_note']}
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    destination.mkdir(parents=True,exist_ok=False)
    for name,value in (('spec.json',spec),('budget.json',book)):
        with (destination/name).open('x') as stream:json.dump(value,stream,indent=2)
    print(json.dumps({'spec':str(destination/'spec.json'),'SHA':sha(destination/'spec.json')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--physical-gpu',type=int,choices=(0,1),default=0)
    args=parser.parse_args()
    prepare(args.output_dir,args.physical_gpu)
