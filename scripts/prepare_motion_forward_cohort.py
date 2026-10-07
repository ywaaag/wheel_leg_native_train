"""Freeze the single-variable positive-cohort experiment and its ledger."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'runs/motion_retention_ab_20261006/off_formal/source_snapshot/spec.json'
CHECKPOINT=ROOT/'runs/motion_retention_ab_20261006/off_formal/model_update_49.pt'
OUT=ROOT/'configs/experiments/motion_forward_cohort_20261006'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    spec=json.loads(BASE.read_text())
    spec['experiment']='motion_forward_cohort_20261006'
    spec['source_checkpoint']=str(CHECKPOINT)
    spec['source_sha256']=digest(CHECKPOINT)
    spec['source_update']=49
    spec['source_spec_sha256']=digest(BASE)
    spec['colleague_config_sha256']=digest(spec['colleague_config_path'])
    spec['retention']={'enabled':False}
    spec['curriculum']['minimum_zero_fraction']=.25
    spec['curriculum']['stages'][1]['weights']=[.25,.50,.25]
    spec['evaluation']['full_every_updates']=25
    spec['evaluation']['checkpoint_every_updates']=25
    spec['safety_stop_commands']=[[0,0],[-.5,0]]
    spec['budget'].update(source_eval_wall_s=240,smoke_wall_s=300,
        formal_wall_s=1100,smoke_updates=1,formal_updates=49,
        sample_limit=409600,formal_samples=401408)
    OUT.mkdir(parents=True)
    (OUT/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    ledger={'authorization':'AUTHORIZED',
        'limits':{'source_eval':1,'smoke':1,'formal':49,'evaluate':0,'play':0},
        'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},
        'attempts':{},'source_eval_wall_used_s':0.}
    (OUT/'budget.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({'spec':str(OUT/'spec.json'),'spec_sha256':digest(OUT/'spec.json'),
        'source_sha256':spec['source_sha256'],'cohort_weights':spec['curriculum']['stages'][1]['weights']}))


if __name__=='__main__':
    main()
