"""Unsubmitted half-step course declaration; no quota transfer or runtime."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def prepare(source_spec,destination,checkpoint=None,initial_stage=3):
    destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    spec=json.loads(Path(source_spec).read_text())
    spec=copy.deepcopy(spec)
    if checkpoint is not None:
        import torch
        checkpoint=Path(checkpoint).resolve()
        saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
        spec.update(source_checkpoint=str(checkpoint),
            source_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            source_update=saved['update'],source_spec_sha256=saved['spec_sha256'])
    spec.update(experiment='motion_absolute_halfstep_PREPARED_20261007',evaluation_only=False,
        authorization='UNAUTHORIZED',authorization_note='Preparation only. This turn authorizes PPO0, not training.',
        experiment_variable='explicit half-step course and absolute-error acceptance; reward/PPO/physics preserved')
    spec.pop('evaluation_requests',None)
    commands=[[0.,0.]];stages=[{'id':0,'name':'L0','commands':[[0.,0.]],'weights':[1.],
        'boundary':[[0.,0.]],'command_mode':'ramp','enforce_whitelist':True}]
    for axis in (0,1):
        for level in range(1,9):
            boundary=[]
            for sign in (1,-1):
                command=[0.,0.];command[axis]=sign*level*.5
                commands.append(command);boundary.append(command)
            old=len(commands)-3
            weights=[.25]+([.375/old]*old if old else [])+[.1875,.1875]
            if not old:weights=[.25,.375,.375]
            stages.append({'id':len(stages),'name':('L' if axis==0 else 'Y')+str(level),
                'commands':copy.deepcopy(commands),'weights':weights,'boundary':boundary,
                'command_mode':'ramp','enforce_whitelist':True})
            # Preserve fixed env slots and every retained endpoint; paired signs get equal counts.
            old_slots=max(24,old) if old else 0
            new_slots=(48-old_slots)//2
            counts=[16]
            if old:
                base,extra=divmod(old_slots,old)
                counts += [base+(1 if i<extra else 0) for i in range(old)]
            counts += [new_slots,new_slots]
            slots=[i for i,count in enumerate(counts) for _ in range(count)]
            assert len(slots)==64 and all(count>0 for count in counts)
            stages[-1].update(weights=[count/64 for count in counts],sampling_slots=slots)
    if not 1<=initial_stage<=16:raise ValueError('initial_stage outside frozen halfstep course')
    spec['curriculum'].update(stages=stages,active_stage=initial_stage,minimum_zero_fraction=.25)
    spec['curriculum']['task_progression'].update(initial_stage=initial_stage,max_enabled_stage=16,
        consecutive_confirmations=3,standing_regression_confirmations=2,
        learned_regression_confirmations=2,max_updates_per_stage=200,
        blocked_reason='advance one half-step only after full same-checkpoint positive/negative/retention gates')
    spec['reward']['stage_linear_denominators']={str(i):1. for i in range(17)}
    spec['reward']['stage_yaw_denominators']={str(i):.09 for i in range(17)}
    spec['evaluation'].update(full_every_updates=50,checkpoint_every_updates=50,zero_every_updates=25)
    spec['source_evaluation_commands']=[c for c in stages[initial_stage-1]['commands'] if c!=[0.,0.]]
    spec['source_required_commands']=copy.deepcopy(spec['source_evaluation_commands'])
    spec['budget'].update(smoke_updates=3,formal_updates=200,formal_wall_s=7200,
        smoke_wall_s=600,source_eval_wall_s=1200)
    from native_stand.command_v6.domain.execution_plan import samples_for_updates
    spec['budget'].update(sample_limit=samples_for_updates(spec,200),formal_samples=samples_for_updates(spec,200))
    spec['physical_precondition']='All source_required_commands need identity-matched full bilateral evidence. New stage is not source retention. Missing evidence blocks launch.'
    spec['phase_initialization']='Strict selected150D actor/critic/Adam, restore source RNG explicitly; new experiment course from evidence, counters start at zero against fresh authorized quota; never restore PhysX state.'
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    book={'authorization':'UNAUTHORIZED','limits':{'source_eval':1,'smoke':3,'formal':200,'evaluate':0,'play':0},
        'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},
        'source_eval_wall_used_s':0.,'quota_origin':'proposal only; no historical quota transferred'}
    destination.mkdir(parents=True,exist_ok=False)
    for name,payload in (('spec.json',spec),('budget.json',book)):
        with (destination/name).open('x') as stream:json.dump(payload,stream,indent=2)
    print(json.dumps({'spec':str(destination/'spec.json'),
        'sha256':hashlib.sha256((destination/'spec.json').read_bytes()).hexdigest(),
        'training_started':False,'authorization':'UNAUTHORIZED'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--initial-stage',type=int,default=3)
    args=parser.parse_args()
    prepare(args.source_spec,args.output_dir,args.checkpoint,args.initial_stage)
