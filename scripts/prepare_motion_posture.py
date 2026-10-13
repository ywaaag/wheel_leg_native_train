"""Prepare one B250 posture-only reward experiment; never launch or authorize."""
import argparse
import copy
import json
from pathlib import Path

from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.recipe import resolve
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish,differences
from native_stand.command_v6.tools.prepare_motion_experiment import full_checkpoint

ROOT=Path(__file__).resolve().parents[1]
ASSESS=[[0,0],[.5,0],[-.5,0],[1,0],[-1,0],[1.5,0],[-1.5,0],[2,0],[-2,0]]


def prepare(session,write=False,output=None):
    if not session or not session.strip():raise ValueError('current HAPI session required')
    parent=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/spec.json'
    template=ROOT/'runs/2026_10_8-14_56__motion_old_endpoint_rehearsal/formal/source_snapshot/spec.json'
    checkpoint=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt'
    inputs=dict([checked_input(parent),checked_input(template),checked_input(checkpoint,
        '5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'),checked_input(ROOT/'参考文献.md')])
    original=json.loads(parent.read_text());_,effective=resolve(original)
    spec=copy.deepcopy(original)
    spec['reward']=copy.deepcopy(effective['reward'])
    for key in ('linear_velocity_tracking','yaw_velocity_tracking'):
        spec['reward'].pop(key,None)
    spec['reward']['posture_balance']={'version':'bounded_geometry_v1','weight':-.5,
        'deadbands':{'wheel_heading_offset_m':.02,'leg_length_difference_m':.005,'roll_rad':.02},
        'denominators':{'wheel_heading_offset_m':.01,'leg_length_difference_m':.01,'roll_rad':.04}}
    for field,sha_field in (('asset_path','asset_sha256'),('asset_module_path','asset_module_sha256'),
                            ('colleague_config_path','colleague_config_sha256')):
        inputs.update([checked_input(spec[field],spec[sha_field])])
    import torch
    saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    checkpoint_review=full_checkpoint(saved,spec)
    output=Path(output).resolve() if output else ROOT/'configs/experiments'/new_experiment_name('motion_b250_posture_balance_v2')
    from native_stand.command_v6.domain.experiment_naming import validate_new_experiment_name
    validate_new_experiment_name(output.name)
    if output.exists():raise FileExistsError(output)
    spec.update(experiment=output.name,source_checkpoint=str(checkpoint),source_sha256=inputs[str(checkpoint)],
        source_update=250,source_input_dim=150,source_spec_sha256=saved['spec_sha256'],
        execution_source_root=str(ROOT/'src'),effective_recipe_version=1,objective='global_adv_norm',
        restore_source_rng=True,cohort_width_ab=True,straight_high_speed_course=False,
        source_evaluation_commands=ASSESS[1:],source_required_commands=ASSESS[1:],
        authorization={'status':'UNAUTHORIZED','hapi_session':session,'user_scope':'Prepared posture experiment; explicit registration required'})
    spec['phase_initialization']='source actor/critic/own Adam/std/CPU+CUDA RNG strictly restored from B250; formal restarts B250, not smoke; new physical reset'
    spec['device']={'physical_index':1,'uuid':'GPU-dfc076b6-b082-3065-512a-e21064067db1','logical':'cuda:0','headless':True}
    spec['resources']={'mode':'exclusive','sharing_authorized':False}
    spec['artifacts']['run_name']=output.name
    for stage in spec['curriculum']['stages']:
        stage['command_mode']='ramp';stage['enforce_whitelist']=True
    task=spec['curriculum']['task_progression']
    task.update(initial_stage=1,max_enabled_stage=1,consecutive_confirmations=99,
        standing_regression_confirmations=2,learned_regression_confirmations=2,
        confirmation_spacing_updates=25,max_updates_per_stage=50,required_commands=ASSESS,
        blocked_reason='Posture-only50 updates; no velocity/yaw unlock; all assessed motion endpoints are retained abilities')
    spec['evaluation']=copy.deepcopy(json.loads(template.read_text())['evaluation'])
    spec['evaluation'].update(motion_commands=ASSESS,full_every_updates=25,checkpoint_every_updates=25,
        light_every_updates=0,zero_every_updates=25,run_final_durability=False,full_trace_updates=[25,50])
    spec['diagnostics']={'enabled':False}
    spec['motion_posture']={'version':'native_posture_v1','assessment_commands':ASSESS,'chain_wall_s':10800,
        'acceptance':{'minimum_relative_improvement':.2,'required_confirmations':2,
            'maximum_component_regression_fraction':.1,'minimum_confirmation_spacing_updates':25}}
    spec['budget'].update(source_eval_wall_s=2500,smoke_updates=1,smoke_wall_s=300,
        formal_updates=50,formal_wall_s=6000,formal_samples=409600,sample_limit=417792)
    spec.pop('retention',None)
    errors=validate(spec)
    if errors:raise ValueError(errors)
    if spec['curriculum']['stages'][1]['commands']!=original['curriculum']['stages'][1]['commands'] or spec['curriculum']['stages'][1]['weights']!=original['curriculum']['stages'][1]['weights']:
        raise ValueError('source sampling changed')
    for key in ('ppo','action','control','ground','termination','observation','history'):
        if spec[key]!=original[key]:raise ValueError('source contract changed: '+key)
    for key,value in effective['reward'].items():
        if key not in ('linear_velocity_tracking','yaw_velocity_tracking') and spec['reward'][key]!=value:
            raise ValueError('original effective reward changed: '+key)
    book={'authorization':'UNAUTHORIZED','experiment':output.name,
        'limits':{'source_eval':1,'smoke':1,'formal':50,'evaluate':0,'play':0},
        'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},
        'total_online_PPO_limit':51,'source_eval_wall_used_s':0.,'inherited_usage':0}
    manifest={'inputs':inputs,'checkpoint_review':checkpoint_review,
        'source_effective_recipe':effective,'changes':differences(original,spec),
        'primary_intervention':'one composite measured-posture reward; original B250 training distribution preserved',
        'runtime_authorized':False,'simulation':0,'PPO_updates':0}
    from native_stand.command_v6.tools.execution_identity import identity
    manifest['execution_identity']=identity(spec)
    if write:
        if output.parent!=ROOT/'configs/experiments':raise ValueError('write under project experiments only')
        publish(output,{'spec.json':spec,'budget.json':book,'preparation_manifest.json':manifest},inputs)
    return {'output':str(output),'spec':spec,'budget':book,'manifest':manifest,'files_written':3 if write else 0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hapi-session',required=True)
    p.add_argument('--output-dir',type=Path);p.add_argument('--write',action='store_true');a=p.parse_args()
    result=prepare(a.hapi_session,a.write,a.output_dir)
    print(json.dumps(result,indent=2))
