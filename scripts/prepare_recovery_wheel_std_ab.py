"""Prepare same-source Recovery wheel std A/B; zero-write default, no launch."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import torch
from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name,validate_new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input,differences,publish
from native_stand.recovery.exploration import VERSION
from native_stand.command_v6.domain.action_std import readback

ROOT=Path(__file__).resolve().parents[1]


def prepare(parent,checkpoint,checkpoint_sha,output,audit,*,write=False):
    parent=Path(parent).resolve();checkpoint=Path(checkpoint).resolve();audit=Path(audit).resolve();output=Path(output).resolve()
    validate_new_experiment_name(output.name)
    if output.parent!=ROOT/'configs/experiments' or output.exists():raise ValueError('Fresh project experiment root required')
    inputs=dict([checked_input(parent),checked_input(checkpoint,checkpoint_sha),checked_input(audit)])
    s=json.loads(parent.read_text());saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if (saved['spec_sha256']!=inputs[str(parent)] or saved['asset_sha256']!=s['asset_sha256'] or saved['update']!=50 or s['task']!='recovery' or s.get('wheel_envelope_conversion')):raise ValueError('P2 source identity/calibration differs')
    if s['recovery']['rising_task']['version']!='autonomous_rise_min_height_v2':raise ValueError('P2 requires actual P1 task')
    for key in ('asset','asset_module','colleague_config'):inputs.update([checked_input(s[key+'_path'],s[key+'_sha256'])])
    inputs.update([checked_input(s['recovery']['pose_library'],s['recovery']['pose_library_sha256'])])
    for key in ('actor','critic'):
        if saved[key]['mlp.0.weight'].shape!=(256,150) or any(not torch.isfinite(v).all() for v in saved[key].values()):raise ValueError('Invalid source network')
    std=saved['actor']['distribution.std_param']
    if std.shape!=(6,) or not (std>0).all() or len(saved['optimizer']['state'])!=17:raise ValueError('P2 needs complete positive scalar std/Adam warmstart')
    audit_data=json.loads(audit.read_text())
    if not any(x['checkpoint_sha256']==checkpoint_sha for x in audit_data['models']):raise ValueError('Audit does not contain selected checkpoint')
    for p,h in audit_data['inputs_sha256'].items():inputs.update([checked_input(p,h)])
    common=copy.deepcopy(s);name=output.name
    common.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=checkpoint_sha,source_update=50,
        source_spec_sha256=inputs[str(parent)],source_asset_sha256=saved['asset_sha256'],
        recipe_parent_spec=str(parent),recipe_parent_spec_sha256=inputs[str(parent)],execution_source_root=str(ROOT/'src'),
        authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'P2 A/B preparation only; runtime budget/session/GPU submission approval still required'},
        authorization_note='UNAUTHORIZED P2 wheel exploration comparison preparation',
        phase_initialization='Both arms each smoke/formal strict same50 actor/critic/all17Adam states/same declared seed; one wheel std initialization intervention after restore; source_eval remains unmodified',
        experiment_variable='Only initial wheel scalar std multiplier A1/B0.5; preserve leg std/actor mean/critic/Adam/LR/reward/pose/physics/protocol',
        preparation_note='Does not directly change deterministic source takeoff; compare subsequent learning and retain common source',
        P2_comparison={'same_source_sha256':checkpoint_sha,'training_seed':s['seed'],'initial_rng':'same declared seed and parent restore_source_rng setting; not independent training seeds',
            'protocol_compatibility':'same P1 task and gates; new shared scoring reporting clarifies completed failure windows',
            'stop_after_first_block':True,'source_wheel_normalized_std':std[[2,5]].tolist(),
            'source_wheel_physical_std_rad_s':(std[[2,5]]*100).tolist()})
    for key in ('repaired_execution_parent_spec','repaired_execution_parent_sha256','engineering_repair'):common.pop(key,None)
    common['artifacts']['run_name']=name
    # Reuse immutable identity-checked pose bytes,including authored unbounded passive limits.
    common['recovery']['authorization_note']='P2 declaration preparation only';common['recovery']['runtime_initialization_validated']=False
    common['recovery']['physical_gate_evidence']='PENDING same-source new recipe independent validation'
    common['recovery']['standing_task']['source_baseline_run']=None
    common['budget'].update(source_eval_wall_s=900,smoke_wall_s=900,formal_wall_s=7200,chain_wall_s=9060,
        smoke_updates=20,formal_updates=100,sample_limit=983040,durability_wall_s=0)
    payloads={};arm_report={}
    for arm,factor in [('A',1.),('B',.5)]:
        spec=copy.deepcopy(common)
        spec['recovery']['exploration_initialization']={'version':VERSION,'wheel_std_multiplier':factor,'channels':[2,5],
            'apply_phases':['smoke','formal'],'optimizer_moments':'preserve_all','std_parameterization':'positive_scalar'}
        errors=validate(spec)
        if errors:raise ValueError(errors)
        book={'authorization':'UNAUTHORIZED','authorization_evidence':'Prepared only, no runtime approval inferred','experiment':name,
            'limits':{'source_eval':1,'evaluate':0,'smoke':20,'formal':100},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},
            'attempts':{},'source_eval_wall_used_s':0.,'sample_limit':983040,'hapi_session':None}
        after=std.clone();after[[2,5]]*=factor
        std_args={'parameterization':'scalar','output_factor':1.,'leg_scale_rad':spec['action']['leg_scale_rad'],'wheel_scale_rad_s':spec['action']['wheel_scale_rad_s']}
        arm_report[arm]={'std_multiplier':factor,'all_normalized_std_before':std.tolist(),'all_normalized_std_after':after.tolist(),
            'source_std_readback':readback(std,**std_args),'initial_std_readback':readback(after,**std_args),
            'physical_wheel_std_before_rad_s':(std[[2,5]]*100).tolist(),'physical_wheel_std_after_rad_s':(after[[2,5]]*100).tolist(),
            'source_checkpoint_unmodified':True,'spec_differences_from_parent':differences(s,spec),'run':str(ROOT/'runs'/name/arm)}
        payloads[arm+'/spec.json']=spec;payloads[arm+'/budget.json']=book
    pair_diff=differences(payloads['A/spec.json'],payloads['B/spec.json'])
    if [x['field'] for x in pair_diff]!=['recovery.exploration_initialization.wheel_std_multiplier']:raise ValueError('Unexpected A/B difference')
    report={'name':name,'inputs_sha256':inputs,'arms':arm_report,'A_B_differences':pair_diff,'suggested_total_updates':240,
        'suggested_total_samples':1966080,'suggested_total_chain_wall_s':18120,'simulation':0,'PPO':0,'authorization':'UNAUTHORIZED',
        'selection':'same checkpoint must satisfy DrawBack/R0 height/level/contact/no lost lift; lower stochastic saturation alone insufficient',
        'physical_comparison_fields':['first2s_height_peak','entry_time','preentry_contact_intervals','landing_order','hold_contact_loss_samples','hold_prefix','full_gate','mean_peak_pitch_roll','channel_phase_limits'],
        'known_limits':'no newly collected PhysX/GUI/optimizer probe; A/B spec IDs do not grant runtime authorization'}
    payloads['preparation_manifest.json']=report
    if write:
        publish(output,payloads,inputs,completion_marker=True)
    return {**report,'output':str(output),'files_written':5 if write else 0}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--checkpoint-sha256',required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--output-dir',type=Path);p.add_argument('--write',action='store_true');a=p.parse_args()
    output=a.output_dir or ROOT/'configs/experiments'/new_experiment_name('recovery_p2_wheel_std_ab_from_new50')
    result=prepare(a.parent_spec,a.checkpoint,a.checkpoint_sha256,output,a.audit,write=a.write)
    print(json.dumps(result,indent=2))
