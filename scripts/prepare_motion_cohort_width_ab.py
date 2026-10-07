"""Prepare a single-variable, same-source native tracking-width comparison."""
import copy
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'configs/experiments/motion_cohort_width_ab_20261006'


def arm_specs(base):
    common=copy.deepcopy(base)
    common['cohort_width_ab']=True
    common['source_evaluation_commands']=[[0,0],[.5,0],[-.5,0],[1.,0],[-1.,0]]
    common['source_required_commands']=[[0,0],[.5,0],[-.5,0]]
    common['curriculum']['stages']=common['curriculum']['stages'][:2]
    common['curriculum']['task_progression'].update(max_enabled_stage=1,
        consecutive_confirmations=99,confirmation_spacing_updates=125,
        max_updates_per_stage=250,learned_regression_confirmations=2)
    common['reward']['linear_error_denominator']=1.
    common['reward']['stage_linear_denominators']={'0':.04,'1':1.}
    common['reward']['stage_yaw_denominators']={'0':.09,'1':.09}
    common['reward']['width_diagnostics']=True
    common['reward'].pop('linear_cohort_width',None)
    common['evaluation'].update(checkpoint_every_updates=125,full_every_updates=125)
    common['budget'].update(source_eval_wall_s=1500,smoke_wall_s=180,formal_wall_s=6000,
        source_eval_updates=0,smoke_updates=1,formal_updates=250,
        formal_samples=2048000,sample_limit=2056192)
    common['authorization_note']='2026-10-06 user authorized same-source cohort-width A/B; each arm 1 smoke + <=250 formal; chain <=14400s; no retries or promotion'
    common['external_prerequisites']=[]
    a=copy.deepcopy(common)
    a['experiment']='motion_cohort_width_ab_20261006_A_wide'
    b=copy.deepcopy(common)
    b['experiment']='motion_cohort_width_ab_20261006_B_preserve_old'
    b['reward']['linear_cohort_width']={'retained_commands':[[0,0],[.5,0],[-.5,0]],
        'retained_denominator':.04,'selector':'episode_target_not_instantaneous_command'}
    return a,b


def main():
    base=json.loads((ROOT/'runs/motion_capability_course_20261006/formal/source_snapshot/spec.json').read_text())
    session=os.environ.get('HAPI_SESSION_ID')
    if not session:
        raise ValueError('current worker HAPI_SESSION_ID is required, never reuse a historical target')
    source=Path(base['source_checkpoint'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=base['source_sha256']:
        raise ValueError('frozen B checkpoint SHA differs')
    OUT.mkdir(parents=True,exist_ok=False)
    arms={}
    for label,spec in zip(('A','B'),arm_specs(base)):
        folder=OUT/label
        folder.mkdir()
        path=folder/'spec.json'
        path.write_text(json.dumps(spec,indent=2)+'\n')
        phases=('source_eval','smoke','formal','evaluate','play')
        ledger=dict(authorization='AUTHORIZED',limits=dict(zip(phases,(1,1,250,0,0))),
            used={phase:0 for phase in phases},attempts={},source_eval_wall_used_s=0.)
        (folder/'budget.json').write_text(json.dumps(ledger,indent=2)+'\n')
        arms[label]={'spec':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    config=dict(experiment='motion_cohort_width_ab_20261006',arms=arms,
        source_checkpoint=str(source),source_sha256=base['source_sha256'],
        physical_gpu=1,gpu_uuid='GPU-dfc076b6-b082-3065-512a-e21064067db1',
        wall_limit_s=14400,formal_updates_per_arm=250,smoke_updates_per_arm=1,
        online_updates_total=502,automatic_retries=0,hapi_session=session,
        source_required_commands=base['curriculum']['stages'][1]['commands'][:3],
        recipe_variable='linear denominator: all 1.0 vs retained target cohorts .04 / new +/-1 1.0')
    (OUT/'ab_spec.json').write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps(config,indent=2))


if __name__=='__main__':
    main()
