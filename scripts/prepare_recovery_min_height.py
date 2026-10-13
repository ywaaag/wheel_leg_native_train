"""Prepare P1 minimum-height finite rise/hold declaration; never authorize or launch."""
import hashlib
import json
from pathlib import Path
import torch
from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.recovery.min_height import VERSION,protocol

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare():
    parent=ROOT/'runs/2026_10_7-18_06__recovery_level2_settle_cost_probe/formal/source_snapshot/spec.json'
    checkpoint=parent.parent.parent/'model_update_50.pt'
    s=json.loads(parent.read_text());saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if sha(checkpoint)!='de06b39d2a88c44250309b4ae0509188b532cc5c51a681d456a545c307243694':raise ValueError('S50 SHA differs')
    if saved['spec_sha256']!=sha(parent) or saved['asset_sha256']!=s['asset_sha256'] or saved['update']!=50:raise ValueError('Source internals differ')
    for key in ('asset','asset_module','colleague_config'):
        if sha(s[key+'_path'])!=s[key+'_sha256']:raise ValueError(key+' identity differs')
    pose_path=Path(s['recovery']['pose_library']);pose_bytes=pose_path.read_bytes()
    if sha(pose_path)!=s['recovery']['pose_library_sha256']:raise ValueError('Pose library identity differs')
    name=new_experiment_name('recovery_min_height_p1_from_s50');folder=ROOT/'configs/experiments'/name
    if folder.exists():raise FileExistsError(folder)
    note='UNAUTHORIZED preparation only; proposed source900s/PPO0, smoke20/900s, formal100/7200s, total120updates/983040samples. Requires new explicit runtime authorization, physical GPU identity and current session; no inherited historical permission.'
    s.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=sha(checkpoint),
        source_update=50,source_spec_sha256=sha(parent),source_asset_sha256=saved['asset_sha256'],
        recipe_parent_spec=str(parent),recipe_parent_spec_sha256=sha(parent),
        authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':note},authorization_note=note,
        phase_initialization='Strict S50 actor/critic/Adam/RNG; smoke/formal each start from S50; new value target not certified',
        experiment_variable='Task objective migration: minimum height platform,20-sample first entry,1000-sample finite hold; no geometry intervention',
        preparation_note='Observation height command .36 remains compatibility input, not reward/gate height target')
    s['execution_source_root']=str(ROOT/'src');s['artifacts']['run_name']=name
    c=s['recovery'];c['pose_library']=str(folder/'poses.json');c['runtime_initialization_validated']=False
    c['authorization_note']=note;c['physical_gate_evidence']='PENDING new source evaluation; old flags not reused'
    c['standing_task']['source_baseline_run']=None;c['autonomous_stability']=protocol();c['standing_task']['protocol']=protocol()
    c['rising_task']={'version':VERSION,'recovery_deadline_s':11.5,'post_rise_hold_s':10.,'entry_dwell_s':.20,'minimum_height_m':.30,'retained_families':['R0'],'retained_fraction':.4}
    c['standing_task']['training_episode']=None
    c['r0_task_declaration']='Same first-confirmed-entry finite rise/hold flow,maximum23s; not fixed10s; independent family results'
    s['reward']['height_objective_version']=VERSION;s['reward']['height_overshoot']=0.;s['reward']['lift']=2.
    s['reward']['success_once']=10.;s['reward']['failure_once']=-1.
    s['curriculum']['episode_length_s']=23.
    s['evaluation']['seconds']=23.;s['evaluation']['steady_window_s']=[0.,23.]
    s['evaluation']['full_trace_updates']=[25,50,100]
    s['evaluation']['full_every_updates']=100;s['evaluation']['light_every_updates']=0
    s['evaluation']['checkpoint_every_updates']=25;s['evaluation']['unlock_full_updates']=[25,50,100]
    s['evaluation']['run_final_durability']=False;s['evaluation']['protocol_identity']=VERSION
    s['budget'].update(source_eval_wall_s=900,smoke_wall_s=900,formal_wall_s=7200,
        smoke_updates=20,formal_updates=100,sample_limit=983040,durability_wall_s=0,chain_wall_s=9060)
    s['wiring_smoke'].update(required_event_duration_s=11.5,minimum_event_count=1,event_offset_s=1.)
    s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':'Existing user explicitly allows shared GPU0 and forbids stopping other processes; not PPO authorization.'}
    c['progress_guard']={'entry_count_drop':2,'confirmations':2,'delta_min_rad_s':10.,'alternation_fraction_min':.8,'limit_fraction_min':.5}
    c['gate_diagnostics']=False
    s['diagnostics']['enabled']=False;s['diagnostics']['record_updates']=[]
    errors=validate(s)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','authorization_evidence':note,'experiment':name,
        'limits':{'source_eval':1,'evaluate':0,'smoke':20,'formal':100},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':983040,'hapi_session':None}
    manifest={'parent_spec':str(parent),'parent_spec_sha256':sha(parent),'source_sha256':sha(checkpoint),
        'asset_sha256':s['asset_sha256'],'protocol':protocol(),'simulation':0,'PPO':0,
        'runtime_readiness':'Pending CPU/evidence/guards, frozen-worker plan and runtime authorization'}
    folder.mkdir();(folder/'poses.json').write_bytes(pose_bytes)
    for filename,value in [('spec.json',s),('budget.json',book),('preparation_manifest.json',manifest)]:
        with (folder/filename).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(str(folder/'spec.json'))

if __name__=='__main__':prepare()
