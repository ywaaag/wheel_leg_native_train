"""Prepare the authorized update50 Level2 single-variable alignment short probe."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare(session):
    parent=ROOT/'runs/2026_10_7-18_06__recovery_level2_settle_cost_probe/formal/source_snapshot/spec.json'
    checkpoint=parent.parent.parent/'model_update_50.pt'
    audit=ROOT/'isolated/recovery_update50_geometry_event_review_20261007/review.json'
    review=json.loads(audit.read_text())
    if not all(e['scorer_replay_matches'] for e in review['per_env']):raise ValueError('Window audit failed')
    for p,h in review['inputs_sha256'].items():
        if sha(p)!=h:raise ValueError('Audit input changed')
    s=json.loads(parent.read_text());saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if saved['spec_sha256']!=sha(parent) or saved['asset_sha256']!=s['asset_sha256'] or saved['update']!=50:raise ValueError('Source identity differs')
    for key in ('asset','asset_module','colleague_config'):
        if sha(s[key+'_path'])!=s[key+'_sha256']:raise ValueError(key+' identity differs')
    name=new_experiment_name('recovery_level2_alignment_from50')
    folder=ROOT/'configs/experiments'/name
    if folder.exists():raise FileExistsError(folder)
    pose_path=Path(s['recovery']['pose_library']);pose_bytes=pose_path.read_bytes()
    if sha(pose_path)!=s['recovery']['pose_library_sha256']:raise ValueError('Pose identity differs')
    scope=('User explicitly approved offline event/window audit and single-variable weak height-gated wheel longitudinal alignment from18_06 update50; source_eval<=600s/PPO0, smoke10<=600s, formal<=100<=3600s, total110updates/901120samples; shared GPU0, no stopping other processes, no automatic extension/retry.')
    s.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=sha(checkpoint),
        source_update=50,source_spec_sha256=sha(parent),source_asset_sha256=saved['asset_sha256'],
        recipe_parent_spec=str(parent),recipe_parent_spec_sha256=sha(parent),
        authorization={'hapi_session':session,'user_scope':scope},authorization_note=scope,
        phase_initialization='Strict update50 actor/critic/Adam warmstart; fixed original LR; smoke/formal each start from source50',
        experiment_variable='Only add weak height-gated wheel longitudinal offset cost; acceptance/physics/PPO/poses unchanged',
        preparation_note='Offline formula magnitude and temporal ordering do not establish causal gradients')
    s['execution_source_root']=str(ROOT/'src');s['artifacts']['run_name']=name
    c=s['recovery'];c['pose_library']=str(folder/'poses.json');c['runtime_initialization_validated']=False
    c['authorization_note']=scope;c['physical_gate_evidence']='PENDING new source phase; historical flags not reused'
    c['standing_task']['source_baseline_run']=None
    s['reward'].update(wheel_longitudinal_offset=-.1,wheel_longitudinal_deadband_m=.04,
        wheel_longitudinal_scale_m=.2,wheel_longitudinal_start_m=.32,wheel_longitudinal_full_m=.36)
    s['evaluation']['full_trace_updates']=[25,50,100]
    s['resources']={'mode':'shared','sharing_authorized':True,'authorization_note':'User approved shared GPU0; no stopping other processes.'}
    s['budget'].update(source_eval_wall_s=600,smoke_wall_s=600,formal_wall_s=3600,
        smoke_updates=10,formal_updates=100,sample_limit=901120,durability_wall_s=0,chain_wall_s=4860)
    errors=validate(s)
    if errors:raise ValueError(errors)
    book={'authorization':'AUTHORIZED','authorization_evidence':scope,'experiment':name,
        'limits':{'source_eval':1,'evaluate':0,'smoke':10,'formal':100},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':901120,'hapi_session':session}
    manifest={'parent_spec':str(parent),'parent_spec_sha256':sha(parent),'source_sha256':sha(checkpoint),
        'asset_sha256':s['asset_sha256'],'audit':str(audit),'audit_sha256':sha(audit),
        'reward_only_changes':{k:v for k,v in s['reward'].items() if k not in json.loads(parent.read_text())['reward']},
        'simulation':0,'PPO':0}
    folder.mkdir();(folder/'poses.json').write_bytes(pose_bytes)
    for filename,value in [('spec.json',s),('budget.json',book),('preparation_manifest.json',manifest)]:
        with (folder/filename).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'config':str(folder),'run':str(ROOT/'runs'/name),'manifest':manifest},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hapi-session',required=True)
    prepare(p.parse_args().hapi_session)
