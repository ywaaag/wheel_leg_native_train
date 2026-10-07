import json
from pathlib import Path
from collections import Counter

import torch

from native_stand.command_v6.config import validate
from native_stand.command_v6.completion import choose, sha
from native_stand.command_v6.domain.tracking_width import linear_width
from native_stand.command_v6.domain.task_curriculum import TaskProgression
from test_motion_cohort_width_ab import fixture_entry

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/motion_high_speed_course_20261007/spec.json'


def test_frozen_course_and_source():
    spec=json.loads(SPEC.read_text())
    assert validate(spec)==[]
    assert sha(spec['source_checkpoint'])==spec['source_sha256']=='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'
    source=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
    assert source['update']==250
    assert source['actor']['mlp.0.weight'].shape==(256,150)
    assert source['critic']['mlp.0.weight'].shape==(256,150)
    assert len(source['optimizer']['state'])==17
    assert source['optimizer']['param_groups'][0]['lr']==spec['ppo']['learning_rate']==3e-5
    assert spec['restore_source_rng'] and 'cpu_rng' in source and 'cuda_rng' in source
    assert not spec['retention']['enabled']
    assert not spec['ppo'].get('clear_adam_first_moment',False)
    assert not spec['ppo'].get('critic_warmup_updates',0)
    assert spec['budget']['smoke_updates']==10 and spec['budget']['formal_updates']==4500
    assert spec['curriculum']['task_progression']['max_updates_per_stage']==1500
    assert spec['evaluation']['final_evaluation_seeds']==[104,137,173]
    assert spec['curriculum']['schedule_s']==[1.,2.,24.,2.]
    assert 24/spec['curriculum']['episode_length_s']>=.7


def test_slots_and_episode_target_width():
    spec=json.loads(SPEC.read_text())
    for stage in spec['curriculum']['stages'][1:]:
        slots=Counter(stage['sampling_slots'])
        n=len(stage['commands'])
        assert sum(slots.values())==64 and slots[0]==16
        assert slots[n-2]==slots[n-1]==12
        assert sum(slots[i] for i in range(1,n-2))==24
        assert all(c[1]==0 for c in stage['commands'])
        target=torch.tensor(stage['commands'],dtype=torch.float32)
        width=linear_width(target,{**spec['reward'],'linear_error_denominator':1.})
        torch.testing.assert_close(width,torch.tensor([.04,.04,.04]+[1.]*(n-3)))
        for error in (0.,.2,.5,1.,2.,3.,4.):
            raw=torch.exp(-torch.full_like(width,error).square()/width)
            assert torch.isfinite(raw).all() and ((raw>=0)&(raw<=1)).all()


def test_source_latest_and_stage_selection_are_separate():
    entries=[]
    for stage in (1,2):
        for role in ('source','candidate'):
            for command in ([0,0],[1,0],[-1,0]):
                row=fixture_entry(command)
                row.update(role=role,checkpoint=f'{role}{stage}',checkpoint_sha256=f'{role}{stage}')
                row['identity'].update(straight_high_speed_course=True,course_stage=stage)
                entries.append(row)
    latest={'path':'unevaluated','sha256':'unevaluated'}
    selected=choose(entries,latest,entries[-1]['identity'])
    assert selected['source_baseline']['role']=='source'
    assert selected['best_new_evaluated_candidate']['checkpoint']=='candidate2'
    assert selected['accepted_by_stage']['1']['checkpoint']=='candidate1'
    assert selected['accepted_by_stage']['2']['checkpoint']=='candidate2'
    assert selected['unreviewed_checkpoints']==[latest]


def test_regression_blocks_progression_and_two_checks_stop():
    spec=json.loads(SPEC.read_text())
    manager=TaskProgression(spec['curriculum']['task_progression'])
    commands=spec['curriculum']['stages'][1]['commands']
    cases=[{'command':command,'gate':{'accepted':command!=[-.5,0]}} for command in commands]
    first=manager.confirm(250,cases,new_commands=[[2,0],[-2,0]],episode_length_s=31)
    assert not first['passed'] and not first['stop'] and first['next_stage']==1
    second=manager.confirm(500,cases,new_commands=[[2,0],[-2,0]],episode_length_s=31)
    assert second['stop'] and second['learned_failures']==2


def test_bounded_smoke_prerequisite_requires_completed_updates_and_evaluation(tmp_path,complete_smoke_fixture):
    import copy
    from native_stand.command_v6.completion import write
    from native_stand.command_v6.ledger import Ledger
    from native_stand.command_v6.tools.preflight import check
    spec=json.loads(SPEC.read_text())
    path=tmp_path/'spec.json'; write(path,spec)
    smoke=tmp_path/'smoke'; smoke.mkdir()
    write(smoke/'progress.json',{'actual_updates':10,'actor_parameters_changed':True,
        'evaluations':[{'cases':[{'path':'evaluation_10_0_0.json'}]}]})
    write(smoke/'terminal_report.json',{'status':'STOPPED_BOUNDED','failure':None,'actual_updates':10})
    write(smoke/'manifest.json',{'source_sha256':spec['source_sha256']})
    (smoke/'source_snapshot').mkdir()
    (smoke/'source_snapshot/spec.json').write_bytes(path.read_bytes())
    import hashlib
    write(smoke/'manifest.json',{'source_sha256':spec['source_sha256'],
        'spec_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    book={'authorization':'AUTHORIZED','limits':{'source_eval':1,'smoke':10,'formal':4500},
        'used':{'source_eval':1,'smoke':10,'formal':0},'attempts':{
        's':{'phase':'smoke','status':'STOPPED_BOUNDED','output_dir':str(smoke),'updates':10}}}
    write(tmp_path/'budget.json',book)
    assert 'preceding phase has not completed' in check(path,tmp_path/'formal','formal')['errors']
    write(smoke/'evaluation_10_0_0.json',{'outcome_counts':{'runtime_fault':0},'per_env':[{}]*8})
    complete_smoke_fixture(smoke,path,10)
    assert check(path,tmp_path/'formal','formal')['status']=='PASS'
    Ledger(tmp_path/'budget.json').reserve('formal','formal',tmp_path/'formal')
