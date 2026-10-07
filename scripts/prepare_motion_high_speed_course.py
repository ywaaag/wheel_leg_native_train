"""Prepare immutable L2-L4 straight-line course from reviewed B250."""
import copy, hashlib, json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt'
SOURCE_SHA='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'
BASE=ROOT/'configs/experiments/motion_cohort_width_ab_20261006/B/spec.json'
OUT=ROOT/'configs/experiments/motion_high_speed_course_20261007'

def stage(index,target,previous):
    commands=[[0,0]]+[[v,0] for v in previous for sign in (1,-1) for v in (v*sign,)] + [[target,0],[-target,0]]
    # exact slots: zero16, retained24, new24; retained is symmetric and ordered by commands
    slots=[0]*16
    retained=list(range(1,1+2*len(previous)))
    slots += [i for i in retained for _ in range(24//len(retained))]
    new=[len(commands)-2,len(commands)-1]
    slots += [i for i in new for _ in range(12)]
    assert len(slots)==64
    weights=[slots.count(i)/64 for i in range(len(commands))]
    return {'id':index,'name':f'L{int(target)}','commands':commands,'weights':weights,
        'boundary':[[target,0],[-target,0]],'command_mode':'fixed','sampling_slots':slots,
        'schedule_s':[1.,2.,24.,2.],'episode_length_s':31.}

def main():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SOURCE_SHA: raise ValueError('B250 SHA mismatch')
    if not OUT.exists(): OUT.mkdir()
    base=json.loads(BASE.read_text())
    base['source_checkpoint']=str(SOURCE); base['source_sha256']=SOURCE_SHA; base['source_update']=250
    base['source_spec_sha256']=hashlib.sha256(BASE.read_bytes()).hexdigest()
    base['experiment']='motion_high_speed_course_20261007'; base['seed']=20261007
    base['straight_high_speed_course']=True
    base['curriculum']=copy.deepcopy(base['curriculum']); base['curriculum']['active_stage']=1
    base['curriculum']['stages']=[{'id':0,'name':'L1','commands':[[0,0],[.5,0],[-.5,0],[1,0],[-1,0]],
        'weights':[.25,.125,.125,.25,.25],'boundary':[[1,0],[-1,0]],'command_mode':'fixed',
        'sampling_slots':[0]*16+[1]*6+[2]*6+[3]*12+[4]*12+[1]*6+[2]*6,
        'schedule_s':[2.,8.,8.,8.],'episode_length_s':30.}]
    # Explicit L2/L3/L4 ids 1/2/3; stage0 remains required standing command in validator.
    base['curriculum']['stages']=[{'id':0,'name':'L0','commands':[[0,0]],'weights':[1.],
        'boundary':[[0,0]],'command_mode':'fixed','sampling_slots':[0]*64,
        'schedule_s':[2.,8.,8.,8.],'episode_length_s':30.}]+[
        stage(i,target,previous) for i,(target,previous) in enumerate(((2.,(.5,1.)),(3.,(.5,1.,2.)),(4.,(.5,1.,2.,3.))),1)]
    base['curriculum']['active_stage']=1; base['curriculum']['minimum_zero_fraction']=.25
    base['curriculum']['task_progression']={'initial_stage':1,'max_enabled_stage':3,
        'consecutive_confirmations':1,'standing_regression_confirmations':2,
        'learned_regression_confirmations':2,'confirmation_spacing_updates':250,
        'merge_nearby_updates':0,'max_updates_per_stage':1500,
        'blocked_reason':'L2-L4 straight-line capability course'}
    base['reward']['stage_linear_denominators']={'0':.04,'1':1.,'2':1.,'3':1.}
    base['reward']['stage_yaw_denominators']={'0':.09,'1':.09,'2':.09,'3':.09}
    base['evaluation'].update(protocol_identity='capability_v2',seconds=30.,
        evaluation_schedule_s=[2.,8.,8.,8.],steady_window_s=[10.,18.],motion_window_s=[10.,18.],
        full_every_updates=250,checkpoint_every_updates=100,light_every_updates=0,
        final_evaluation_seeds=[104,137,173])
    base['budget'].update(source_eval_wall_s=1800,smoke_updates=10,formal_updates=4500,
        smoke_wall_s=1200,formal_wall_s=64800,sample_limit=36864000,formal_samples=36864000)
    base['authorization_note']='2026-10-07 user authorized B250 L2-L4 straight course, GPU1; smoke<=10, formal<=4500, <=1500/stage, <=18h, no yaw'
    base['cohort_width_ab']=False
    base['reward']['linear_cohort_width']={'retained_commands':[[0,0],[.5,0],[-.5,0]],'retained_denominator':.04}
    base['source_evaluation_commands']=[[.5,0],[-.5,0],[1,0],[-1,0]]
    base['source_required_commands']=base['source_evaluation_commands']
    base['evaluation']['run_final_durability']=False
    base['external_prerequisites']=[]
    path=OUT/'spec.json'; path.write_text(json.dumps(base,indent=2)+'\n')
    ledger=OUT/'budget.json'
    if ledger.exists(): raise ValueError('course ledger already exists')
    ledger.write_text(json.dumps({'authorization':'AUTHORIZED','limits':{'source_eval':1,'smoke':10,'formal':4500,'evaluate':0,'play':0},
        'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.},indent=2)+'\n')
    config={'spec':str(path),'spec_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_checkpoint':str(SOURCE),'source_sha256':SOURCE_SHA,'gpu':1,
        'formal_updates':4500,'stage_updates':1500,'smoke_updates':10,'wall_s':64800,
        'hapi_session':os.environ.get('HAPI_SESSION_ID'),'stages':['L2','L3','L4']}
    (OUT/'course_config.json').write_text(json.dumps(config,indent=2)+'\n'); print(json.dumps(config,indent=2))
if __name__=='__main__': main()
