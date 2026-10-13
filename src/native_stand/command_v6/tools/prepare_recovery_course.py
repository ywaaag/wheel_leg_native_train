"""Prepare a single Recovery curriculum block; no simulation or authorization."""
import argparse
import copy
import json
from pathlib import Path
import torch
from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish,differences
from native_stand.recovery.sampling import sample_poses,scoring_config,allocation_plan

ROOT=Path(__file__).resolve().parents[4]


def prepare(parent,checkpoint,library,request,*,checkpoint_sha256,write=False,output=None,return_package=False,reward_recipe=None):
    from native_stand.command_v6.domain.recovery_course import parse_request
    from native_stand.command_v6.tools.prepare_motion_experiment import full_checkpoint
    from native_stand.command_v6.domain.experiment_naming import validate_new_experiment_name
    data=parse_request(request)
    current=data["current_family"];retained=data["retained_families"];masses=data["family_weights"]
    parent=Path(parent).resolve();checkpoint=Path(checkpoint).resolve();library=Path(library).resolve()
    inputs=dict(checked_input(p) for p in (parent,library))
    inputs.update([checked_input(checkpoint,checkpoint_sha256)])
    s=json.loads(parent.read_text());saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if (s.get('task')!='recovery' or saved['spec_sha256']!=inputs[str(parent)] or
            saved['asset_sha256']!=s['asset_sha256']):
        raise ValueError('Expected identity-matched Recovery checkpoint and parent spec')
    for key in ('asset','asset_module','colleague_config'):
        inputs.update([checked_input(s[key+'_path'],s[key+'_sha256'])])
    inputs.update([checked_input(s['recovery']['pose_library'],s['recovery']['pose_library_sha256'])])
    poses=copy.deepcopy(json.loads(library.read_text()))
    original=json.loads(Path(s['recovery']['pose_library']).read_text())
    poses['poses']=[p for p in poses['poses'] if p['family'] in masses]
    for split in ('train','holdout'):
        for family,mass in masses.items():
            group=[p for p in poses['poses'] if p['family']==family and p['split']==split and p['offline_valid']]
            if not group:raise ValueError('Missing valid family split')
            if family in retained:
                expected_ids={p['pose_id'] for p in original['poses'] if p['family']==family and p['split']==split and p['offline_valid']}
                if {p['pose_id'] for p in group}!=expected_ids:raise ValueError('Retained pose coverage changed')
            for p in group:
                old=next((x for x in original['poses'] if x['pose_id']==p['pose_id']),None)
                if family in retained and (old is None or {k:v for k,v in p.items() if k!='sample_weight'}!={k:v for k,v in old.items() if k!='sample_weight'}):
                    raise ValueError('Old initial state changed')
                p['sample_weight']=mass/len(group)
    name=(Path(output).name if output else new_experiment_name(data['purpose']))
    output=Path(output).resolve() if output else ROOT/'configs/experiments'/name
    validate_new_experiment_name(name)
    if output.exists():raise FileExistsError(output)
    if output.parent!=ROOT/'configs/experiments':raise ValueError('Project experiment directory required')
    s=copy.deepcopy(s)
    if reward_recipe is not None:
        recipe=Path(reward_recipe).resolve();inputs.update([checked_input(recipe)]);effective=json.loads(recipe.read_text())
        if effective.get('task')!='recovery' or effective['asset_sha256']!=s['asset_sha256']:raise ValueError('Reward recipe identity differs')
        s['reward']=copy.deepcopy(effective['reward'])
        for key in ('settling_reward','standing_task','support_record_reward','drawback_guidance'):
            if key in effective['recovery']:s['recovery'][key]=copy.deepcopy(effective['recovery'][key])
        s['reward_recipe_source']={'path':str(recipe),'sha256':inputs[str(recipe)],'checkpoint_lineage_unchanged':True}
    if saved.get('initialization_candidate'):
        from native_stand.recovery.initialization_candidate import verify
        s['initialization_candidate']=verify(saved,checkpoint)
    s['seed']=data.get('seed',s['seed']);s['restore_source_rng']=data.get('restore_source_rng',s.get('restore_source_rng',False))
    s.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=inputs[str(checkpoint)],
        source_update=saved['update'],source_spec_sha256=inputs[str(parent)],source_asset_sha256=saved['asset_sha256'],
        recipe_parent_spec=str(parent),recipe_parent_spec_sha256=inputs[str(parent)],
        execution_source_root=str(ROOT/'src'),
        authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'Prepared course; register current approval before submission'},
        authorization_note='Fresh curriculum declaration; no historical budget reused',
        phase_initialization='smoke/formal each strict source actor/critic/Adam warmstart; actual std inherited without multiplier',
        experiment_variable='Only reset family sampling; identical reward/control/scoring protocol')
    s.pop('P2_comparison',None)
    for key in ('chain_submission','authorization_receipt','smoke_certificate'):
        s.pop(key,None)
    s['notifications']=copy.deepcopy(data.get('notifications',{'enabled':False}))
    s.pop('input_capture',None);s.pop('evaluation_requests',None)
    s['artifacts']['run_name']=name
    r=s['recovery'];r.pop('exploration_initialization',None)
    r.update(active_family=current,preview_family=current,pose_library=str(output/'poses.json'),
        scope='Explicit single-block course; preserve retained physical initial states',
        authorization_note='Prepared only; runtime approval required',runtime_initialization_validated=False,
        runtime_initialization_evidence=None,physical_gate_evidence='New source/smoke readback required')
    r['rising_task']=scoring_config(r['rising_task'])
    r['sampling']={'version':'family_weights_v1','family_weights':dict(masses)}
    if 'environment_counts' in data:
        if sum(data['environment_counts'].values())!=s['ppo']['envs']:
            raise ValueError('Fixed environment allocation differs from PPO env count')
        r['sampling'].update(version='fixed_environment_families_v1',environment_counts=data['environment_counts'])
    r['assessment']={'families':list(masses),'retained_families':list(retained)}
    if 'wheel_mean_auxiliary' in data:
        r['wheel_mean_auxiliary']=copy.deepcopy(data['wheel_mean_auxiliary'])
        s['experiment_variable']='Swing pre-entry wheel rawmean auxiliary only; fixed-family26/25/13 course,reward,std,Adam,physical/gates preserved relative to prior fixed course'
    if 'support_record_reward' in data:
        r.pop('wheel_mean_auxiliary',None)
        r['support_record_reward']=copy.deepcopy(data['support_record_reward'])
        s['experiment_variable']='Only Swing pre-entry smooth support record reward beta=.3; fixed26/25/13, source std/Adam/control/original reward and scoring preserved'
    if 'action_distribution' in data:
        s['action_distribution']=copy.deepcopy(data['action_distribution'])
        s['experiment_variable']='Only wheelmean bounded Gaussian; beta=.3 record/oldreward,std,legs,fixed26/25/13,control,gates preserved against supportrecord baseline'
    r.pop('leg_center_auxiliary',None)
    if 'leg_center_auxiliary' in data:
        r['leg_center_auxiliary']=copy.deepcopy(data['leg_center_auxiliary'])
        s['experiment_variable']='Only training earlySwing leg center auxiliary lambda=.1; same boundedwheel/reward/std/control/initial states'
    r.pop('drawback_guidance',None)
    if 'drawback_guidance' in data:
        r['drawback_guidance']=copy.deepcopy(data['drawback_guidance'])
        s['experiment_variable']='Only Swing DrawBack root-wheel position times native mirror dense guidance; source reward/std/control unchanged; leg center auxiliary OFF'
    r.pop('retention_regression_policy',None)
    if 'retention_regression_policy' in data:
        r['retention_regression_policy']=copy.deepcopy(data['retention_regression_policy'])
        s['experiment_variable']='Only retained contact-only regression changes stop to diagnostic; source model/reward/control/std unchanged'
    for key in ('actor_update_scope','swing_only'):
        r.pop(key,None)
        if key in data:r[key]=copy.deepcopy(data[key])
    if r.get('swing_only'):
        s['restore_recovery_curriculum']=False
        r['scope']='Swing-only task:64 Swing, no retained training/evaluation/stop scope; original hold gate remains'
    r['curriculum']['levels']=[{'id':data['level_id'],'pose_family':current,'description':'Explicit curriculum request'}]
    r['standing_task']['source_baseline_run']=None
    r['progress_guard_scope']='Current-family entry/oscillation; existing StandingRegression protects all retained families after two full failures'
    samples=(data['smoke_updates']+data['formal_updates'])*s['ppo']['envs']*s['ppo']['steps_per_env']
    s['budget'].update(source_eval_wall_s=data['wall_s']['source_eval'],smoke_wall_s=data['wall_s']['smoke'],formal_wall_s=data['wall_s']['formal'],
        chain_wall_s=sum(data['wall_s'].values())+data.get('cleanup_wall_s',60),smoke_updates=data['smoke_updates'],formal_updates=data['formal_updates'],sample_limit=samples,durability_wall_s=0)
    if s.get('selected_diagnostics',{}).get('enabled'):
        s['selected_diagnostics']['updates']=data['evaluation_updates']
    s['evaluation'].update(full_trace_updates=data['evaluation_updates'],unlock_full_updates=data['evaluation_updates'],
        checkpoint_every_updates=data['evaluation_updates'][0],full_every_updates=data['evaluation_updates'][0])
    if 'wheel_mean_auxiliary' in data or 'support_record_reward' in data:
        s['evaluation']['full_every_updates']=data['formal_updates']
        s['evaluation']['checkpoint_every_updates']=25
    s['evaluation'].update(data.get('evaluation_schedule',{}))
    s['wiring_smoke']['required_groups']=[{'family':f,'minimum_completed':1,
        'require_runtime_initial_valid':True} for f in masses]
    if r.get('swing_only'):
        from native_stand.command_v6.domain.recovery_course import swing_smoke_contract
        s['wiring_smoke']=swing_smoke_contract(s['control']['policy_dt_s'],r['initialization']['settle_max_s'],current)
    # Preparation does not grant a shared-device authorization.
    s['resources']={'mode':'exclusive','sharing_authorized':False}
    # Historical library uses +/-Infinity for unbounded passive joints; preserve
    # those authored semantics rather than invent finite limits for publication.
    encoded=json.dumps(poses,indent=2)+'\n'
    import hashlib
    r['pose_library_sha256']=hashlib.sha256(encoded.encode()).hexdigest()
    actual={}
    for split in ('train','holdout'):
        ids,weights=sample_poses(poses['poses'],r,current,split,training=True)
        actual[split]={f:sum(w for i,w in zip(ids,weights) if poses['poses'][i]['family']==f) for f in masses}
        if any(abs(actual[split][f]-v)>1e-12 for f,v in masses.items()):
            raise ValueError('Effective pose sampling mass differs')
    errors=validate(s)
    if errors:raise ValueError(errors)
    from native_stand.command_v6.tools.checkpoint_initialization import audit
    import contextlib,io
    rng=torch.get_rng_state().clone()
    try:
        with contextlib.redirect_stdout(io.StringIO()):checkpoint_fields=full_checkpoint(saved,s)
    finally:torch.set_rng_state(rng)
    with contextlib.redirect_stdout(io.StringIO()):initialized=audit(s,saved)
    if any(p['max_abs_difference'] for p in initialized['parameter_differences']):
        raise ValueError('Source initialization changed')
    book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':1,'evaluate':0,'smoke':data['smoke_updates'],'formal':data['formal_updates']},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':samples,'hapi_session':None}
    def json_sha(value):return hashlib.sha256((json.dumps(value,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
    approval={'approval_id':'REQUIRES_USER_APPROVAL','user_scope':'REQUIRES_EXPLICIT_SCOPE',
        'session':'REQUIRES_CURRENT_SESSION','physical_gpu':s['device']['physical_index'],
        'gpu_uuid':s['device']['uuid'],'max_online_updates':data['smoke_updates']+data['formal_updates'],
        'max_phase_wall_s':sum(data['wall_s'].values()),
        'arms':[{'spec':str(output/'spec.json'),'spec_sha256':json_sha(s),'budget_sha256':json_sha(book)}]}
    report={'name':name,'inputs_sha256':inputs,'sampling_mass':actual,'checkpoint_initialization':initialized,
        'request':data,'request_sha256':json_sha(data),'checkpoint_fields':checkpoint_fields,
        'authorization_request_template':approval,'approval_template_is_authorization':False,
        'sampling_adapter':r['sampling']['version']+'; no sampling fields in scoring protocol',
        'allocation_plan':allocation_plan(r,s['ppo']['envs']),
        'pose_derivation':{'source_sha256':inputs[str(library)],'output_sha256':r['pose_library_sha256'],
            'changes':'selected family subset and sample_weight only; all retained pose fields unchanged'},
        'inheritance':inheritance(json.loads(parent.read_text()),s),
        'differences':differences(json.loads(parent.read_text()),s),'simulation':0,'optimizer_updates':0,
        'output':str(output),'files_written':5 if write else 0}
    package={'payloads':{'spec.json':s,'budget.json':book,'preparation_manifest.json':report},
        'serialized_files':{'poses.json':(encoded.encode(),r['pose_library_sha256'])},'inputs':inputs}
    if write:publish(output,**package,completion_marker=True)
    result={**report,'spec':s,'budget':book}
    if return_package:result['publication_package']=package
    return result




def inheritance(parent,child):
    changes=differences(parent,child)
    def exists(data,path):
        for key in path.split('.'):
            if not isinstance(data,dict) or key not in data:return False
            data=data[key]
        return True
    return {'inherited_sections':[k for k in parent if k in child and parent[k]==child[k]],
        'deleted':[d for d in changes if not exists(child,d['field'])],
        'overridden':[d for d in changes if exists(parent,d['field']) and exists(child,d['field'])],
        'added':[d for d in changes if not exists(parent,d['field'])]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent-spec',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--checkpoint-sha256',required=True);p.add_argument('--pose-library',type=Path,required=True)
    p.add_argument('--request',type=Path,required=True);p.add_argument('--output-dir',type=Path);p.add_argument('--write',action='store_true')
    a=p.parse_args();request=json.loads(a.request.read_text())
    result=prepare(a.parent_spec,a.checkpoint,a.pose_library,request,checkpoint_sha256=a.checkpoint_sha256,write=a.write,output=a.output_dir)
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
