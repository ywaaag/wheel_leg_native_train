"""Prepare bounded receiver evaluation/training through public publication."""
import argparse,copy,json,hashlib
from pathlib import Path
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.domain.recipe import resolve
from native_stand.command_v6.config import validate
from native_stand.recovery.handoff_protocol import declaration,duration
from native_stand.recovery.controlled_ppo import declaration as actor_mask

ROOT=Path(__file__).resolve().parents[1]
MOTION=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal'
RECOVERY=ROOT/'runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal'

def prepare(kind,session,write=False):
    inputs={}
    def bind(path,expected=None):
        p,h=checked_input(path,expected);inputs[p]=h;return Path(p)
    base=bind(ROOT/'configs/experiments/2026_10_10-16_44__recovery_motion_b250_handoff_ppo0/spec.json')
    s=json.loads(base.read_text());s=copy.deepcopy(s)
    cp=bind(RECOVERY/'model_update_50.pt','46add82fa9d32c04fcc0a8b79c6339a27df3b9ca6c95050b8e13f52b644b7f75')
    rp=bind(RECOVERY/'source_snapshot/spec.json')
    mp=bind(MOTION/'source_snapshot/spec.json')
    mc=bind(MOTION/'model_update_250.pt','5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e')
    pose=bind(s['recovery']['pose_library'],s['recovery']['pose_library_sha256']);lib=json.loads(pose.read_text())
    name=new_experiment_name('receiver_window_ppo0' if kind=='evaluation' else 'receiver_zero_from_b250')
    out=ROOT/'configs/experiments'/name
    s.update(experiment=name,authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'CPU preparation only'},
             resources={'mode':'exclusive','sharing_authorized':False},notifications={'enabled':False},
             execution_source_root=str(ROOT/'src'),restore_source_rng=False,restore_recovery_curriculum=False)
    s['artifacts']['run_name']=name
    r=s['recovery']
    r.pop('swing_only',None);r.pop('retention_regression_policy',None)
    if kind=='evaluation':
        cases=[]
        template=copy.deepcopy(s['motion_handoff']['cases'][0]);template['case_id']='native_baseline';cases.append(template)
        for seed in (20261010,20261011,20261012):
            for seconds in (.40,.45,.50,.55,.60):
                cases.append(dict(kind='recovery_prefix_then_motion',recovery='B50',switch_s=seconds,
                    checkpoint=str(cp),sha256=inputs[str(cp)],seconds=duration(seconds,r['initialization']['settle_max_s']),
                    family='swing_candidate_from_historical_r1',seed=seed,case_id=f'B50_{round(seconds*100):02d}_seed{seed}'))
        s['motion_handoff'].update(version='dual_frozen_handoff_v2',cases=cases,max_storage_bytes=512*2**20,
            initialization_randomization={'version':'reset_yaw_v1','root_yaw_rad':.01,'distribution':'uniform'})
        for row in cases:row.update(recovery_spec=str(rp),recovery_spec_sha256=inputs[str(rp)])
        s['budget'].update(evaluation_wall_s=1800,chain_wall_s=1800)
        limits={'source_eval':0,'evaluate':1,'smoke':0,'formal':0}
    else:
        r.pop('progress_guard',None);r.pop('support_record_reward',None);r.pop('drawback_guidance',None)
        motion=json.loads(mp.read_text());effective,report=resolve(motion)
        # Remove ineffective independent declarations, keeping actual combined reward.
        reward=copy.deepcopy(effective['reward']);reward.pop('linear_velocity_tracking',None);reward.pop('yaw_velocity_tracking',None);reward['tracking_mode']='combined'
        s.pop('motion_handoff');s.pop('evaluation_only',None);s.pop('diagnostic_identity_only',None);s.pop('action_distribution',None)
        s.update(source_checkpoint=str(mc),source_sha256=inputs[str(mc)],source_update=250,
                 source_spec_sha256=inputs[str(mp)],source_asset_sha256=motion['asset_sha256'],
                 ppo=copy.deepcopy(motion['ppo']),action=copy.deepcopy(motion['action']),
                 reward=reward,receiver_reward=copy.deepcopy(reward))
        s.pop('initialization_candidate',None);s.pop('retention',None)
        s['control']['height_command_m']=.40
        r['actor_update_scope']=actor_mask()
        r['sampling']={'version':'fixed_environment_families_v1','family_weights':{'swing_candidate_from_historical_r1':.5,'motion_native_normal':.5},
                       'environment_counts':{'swing_candidate_from_historical_r1':32,'motion_native_normal':32}}
        r['assessment']={'families':['swing_candidate_from_historical_r1','motion_native_normal'],'retained_families':['motion_native_normal']}
        # Publish train variants of the same legal holdout construction.
        for family in ('motion_native_normal','swing_candidate_from_historical_r1'):
            p=copy.deepcopy(next(p for p in lib['poses'] if p['family']==family and p['split']=='holdout'))
            p['pose_id']=family+'_receiver_train';p['split']='train';lib['poses'].append(p)
        s['receiver_training']={'version':'motion_receiver_training_v1','recovery_checkpoint':str(cp),
            'recovery_sha256':inputs[str(cp)],'recovery_spec':str(rp),'recovery_spec_sha256':inputs[str(rp)],
            'motion_checkpoint':str(mc),'motion_sha256':inputs[str(mc)],'motion_spec':str(mp),'motion_spec_sha256':inputs[str(mp)],
            'protocol':declaration(),'prefix_s':.5,'environment_counts':{'swing_candidate_from_historical_r1':32,'motion_native_normal':32},
            'critic_context':{'version':'legacy150_phase_metadata_v1','network_input':'native_motion150','phase_time':'storage_metadata_not_network_input',
                              'alias_risk':'explicit_partial_observability','GAE':'original_all_intervals'},
            'reward_source':'motion_frozen_effective_recipe','actor_mask':actor_mask(),
            'evaluation_families':['swing_candidate_from_historical_r1','motion_native_normal'],'motion_return_commands':[[.5,0],[-.5,0]]}
        s['budget'].update(source_eval_updates=0,smoke_updates=20,formal_updates=100,sample_limit=983040,
            source_eval_wall_s=900,smoke_wall_s=1500,formal_wall_s=4700,durability_wall_s=0,chain_wall_s=7200)
        s['budget'].pop('evaluation_wall_s',None)
        s['evaluation'].update(seconds=13.52,light_seconds=13.52,steady_window_s=[0.,13.52],light_window_s=[0.,13.52],
            full_every_updates=50,checkpoint_every_updates=25,unlock_full_updates=[25,50,100],full_trace_updates=[25,50,100],
            light_every_updates=0,full_at_final=True,run_final_durability=False)
        s['source_evaluation_commands']=[];s['source_required_commands']=[]
        s['wiring_smoke']={'required_event':'completed_episode','required_event_duration_s':.01,'minimum_event_count':1,'event_offset_s':1.}
        s['curriculum']['stages']=[{'id':0,'name':'receiver_zero','commands':[[0,0]],'weights':[1.]}]
        s['curriculum']['active_stage']=0;s['curriculum']['schedule_s']=[0.,0.,13.52,0.]
        s['curriculum']['episode_length_s']=13.52
        limits={'source_eval':1,'smoke':20,'formal':100}
        s['receiver_reward_provenance']={'frozen_spec':str(mp),'sha256':inputs[str(mp)],
            'effective_report':report,'zero_linear_width':.04,'formula':'combined tracking, dt.01 once + terminal',
            'removed_ineffective_fields':['linear_velocity_tracking','yaw_velocity_tracking'],
            'recovery_rewards_used':False}
    encoded=(json.dumps(lib,indent=2)+'\n').encode();r['pose_library']=str(out/'poses.json');r['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
    errors=validate(s)
    if errors:raise ValueError(errors)
    for key in ('asset','asset_module','colleague_config'):bind(s[key+'_path'],s[key+'_sha256'])
    book={'authorization':'UNAUTHORIZED','experiment':name,'limits':limits,'used':{p:0 for p in limits},'attempts':{},
          'source_eval_wall_used_s':0.,'sample_limit':s['budget']['sample_limit'],'hapi_session':None}
    report={'name':name,'kind':kind,'spec_path':str(out/'spec.json'),'budget_path':str(out/'budget.json'),
            'inputs_sha256':inputs,'runtime_status':'IMPLEMENTED_PHYSICAL_UNVERIFIED','authorization':'UNAUTHORIZED'}
    if write:publish(out,{'spec.json':s,'budget.json':book,'preparation_manifest.json':report},inputs,
                     completion_marker=True,serialized_files={'poses.json':(encoded,r['pose_library_sha256'])})
    return {**report,'spec':s}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kind',choices=('evaluation','training'),required=True)
    p.add_argument('--session',required=True);p.add_argument('--write',action='store_true');a=p.parse_args()
    print(json.dumps(prepare(a.kind,a.session,a.write),indent=2))
