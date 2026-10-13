"""Publish diagnostic through existing spec/ledger/supervisor, never launch here."""
import argparse,json,copy,math,hashlib,os
from pathlib import Path
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish,digest
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.config import validate
from native_stand.recovery.motion_handoff import scan_conditions
from native_stand.recovery.handoff_protocol import declaration,duration

def native_normal_root_quaternion(reset_text):
    """Preserve the actual four array slots passed by the frozen reset.

    Installed IsaacLab3 and the pose library use xyzw; runtime forwards the
    four values verbatim. Do not reinterpret the frozen reset as wxyz.
    """
    if 'pose[:,3]=math.sqrt(.5);pose[:,6]=math.sqrt(.5)' not in reset_text:
        raise ValueError('Frozen normal reset quaternion implementation not recognized')
    return [math.sqrt(.5),0.,0.,math.sqrt(.5)]


def prepare(session,write=False):
    root=Path.cwd();inputs={}
    def bind(p,sha=None):
        path,h=checked_input(root/p if not Path(p).is_absolute() else p,sha);inputs[path]=h;return Path(path)
    parent=bind('runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/source_snapshot/spec.json');s=copy.deepcopy(json.loads(parent.read_text()))
    cp=bind('isolated/recovery_swing_leg_initialization_qualified_20261010/initialization_candidate.pt','d074488410257e02b44704f8b2119612617cf44267c50d6e4561f72d39a9ab51')
    mp=bind('runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/spec.json');motion=bind('runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt','5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e')
    # Frozen Motion normal initialization implemented by frozen env.py parent class.
    reset_source=bind('runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/native_env.py')
    text=reset_source.read_text()
    if not all(v in text for v in ('pose[:,2]+=.4','pose[:,3]=math.sqrt(.5);pose[:,6]=math.sqrt(.5)','q=torch.zeros')):raise ValueError('Frozen normal reset implementation not recognized')
    posepath=bind(s['recovery']['pose_library'],s['recovery']['pose_library_sha256']);lib=json.loads(posepath.read_text());normal=copy.deepcopy(lib['poses'][0]);normal.update(pose_id='motion_native_zero_normal',family='motion_native_normal',split='holdout',joint_pos={k:0. for k in normal['joint_pos']},root_height_m=.4,root_quaternion_xyzw=native_normal_root_quaternion(text),initialization_control='direct_zero_reset',sample_weight=.5,runtime_valid=False,initial_root_height_m=[.399,.401],initial_chassis_clearance_m=[0.,1.],offline_valid=True,closure_max_m=0.,support={'definition':'Motion frozen original zero-joint root.4 initialization, runtime geometry must verify'})
    normal['normal_initialization_provenance']={'path':str(reset_source),'sha256':inputs[str(reset_source)],'method':'original direct zero root/joint velocities and q; no settling or adjusted pose'}
    lib['poses'].append(normal)
    for p in lib['poses']:p['sample_weight']=.5 if p['split']=='holdout' else 1.
    name=new_experiment_name('recovery_motion_b250_handoff_ppo0');out=root/'configs/experiments'/name
    candidates={'B_init':cp,**{f'B{u}':bind(f'runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_{u}.pt') for u in (25,50,100)}}
    for u in (25,50,100):
        ep=bind(f'runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/evaluation_{u}_0_0.json');e=json.loads(ep.read_text());assert e['checkpoint_sha256']==inputs[str(candidates[f'B{u}'])] and e['spec_sha256']==inputs[str(parent)]
    cases=scan_conditions(list(candidates))
    for row in cases:
        source=candidates.get(row['recovery'],cp);row.update(checkpoint=str(source),sha256=inputs[str(source)],family='motion_native_normal' if row['kind']=='normal_motion_baseline' else 'swing_candidate_from_historical_r1',seed=20261010,seconds=duration(row['switch_s'],s['recovery']['initialization']['settle_max_s']))
    s.update(experiment=name,effective_recipe_version=1,evaluation_only=True,diagnostic_identity_only=True,source_checkpoint=str(cp),source_sha256=inputs[str(cp)],source_input_dim=150,source_update=25,seed=20261010,execution_source_root=str(root/'src'),authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'handoff preparation only'})
    s['artifacts']['run_name']=name;s['budget'].update(source_eval_updates=0,smoke_updates=0,formal_updates=0,sample_limit=0,evaluation_wall_s=3600,chain_wall_s=3600,durability_wall_s=0)
    s['evaluation'].update(envs=64,scored_envs=8,full_trace_updates=[],run_final_durability=False);s['evaluation_requests']=[];s['resources']={'mode':'exclusive','sharing_authorized':False};s['notifications']={'enabled':False};s['wiring_smoke']={}
    r=s['recovery'];r.pop('swing_only',None);r.pop('actor_update_scope',None);r.pop('retention_regression_policy',None)
    r['sampling']={'version':'family_weights_v1','family_weights':{'swing_candidate_from_historical_r1':.5,'motion_native_normal':.5}};r['assessment']={'families':['swing_candidate_from_historical_r1','motion_native_normal'],'retained_families':['motion_native_normal']}
    encoded=(json.dumps(lib,indent=2)+'\n').encode();r['pose_library']=str(out/'poses.json');r['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
    s['motion_handoff']={'version':'dual_frozen_handoff_v1','protocol':declaration(),'motion_checkpoint':str(motion),'motion_sha256':inputs[str(motion)],'motion_spec':str(mp),'motion_spec_sha256':inputs[str(mp)],'cases':cases,'max_storage_bytes':1073741824,'normal_initialization_source':normal['normal_initialization_provenance']}
    for key in ('asset','asset_module','colleague_config'):bind(s[key+'_path'],s[key+'_sha256'])
    errors=validate(s)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'source_eval_wall_used_s':0.,'sample_limit':0,'hapi_session':None}
    report={'name':name,'spec_path':str(out/'spec.json'),'budget_path':str(out/'budget.json'),'inputs_sha256':inputs,'PPO':0,'optimizer':0,'simulated_envs':64,'scored_envs':8,'episodes_max':176,'wall_s':3600,'storage_max_bytes':1073741824,'normal_initialization':normal['normal_initialization_provenance'],'motion_old_vx_threshold':.02,'user_main_vx_threshold':.5,'strict_vx_is_diagnostic':True,'runnable':True,'authorization':'UNAUTHORIZED'}
    if write:publish(out,{'spec.json':s,'budget.json':book,'preparation_manifest.json':report},inputs,completion_marker=True,serialized_files={'poses.json':(encoded,r['pose_library_sha256'])})
    return {**report,'spec':s,'budget':book}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.session,a.write),indent=2))
