import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from native_stand.command_v6.config import validate
from native_stand.recovery.domain import huber_settling_costs, reward_height_gate
from native_stand.recovery.standing import standing_costs


ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'configs/experiments/recovery_standing_balance_20261006/spec.json'


@pytest.fixture
def prepare_module():
    module_spec=importlib.util.spec_from_file_location('standing_prepare',ROOT/'scripts/prepare_standing_balance.py')
    module=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_legacy_gate_and_height_independent_costs():
    spec=json.loads(PARENT.read_text())
    cfg=spec['recovery']['standing_task']['reward']
    h=torch.tensor([.2,.334,.36])
    d=torch.ones(3,10)*.2
    old=standing_costs(h,torch.full_like(h,.36),d,torch.ones(3,3),cfg)
    assert old['mirror_posture'][0]==0
    assert old['mirror_posture'][1]<old['mirror_posture'][2]
    new=standing_costs(h,torch.full_like(h,.36),d,torch.ones(3,3),
                       {**cfg,'gate_mode':'unconditional'})
    for key,value in new.items():
        if key!='standing_height':
            torch.testing.assert_close(value,value[-1].expand_as(value))
            torch.testing.assert_close(value[-1],old[key][-1])
    assert new['standing_height'][0]<new['standing_height'][2]


def test_linear_yaw_costs_do_not_disappear_when_height_drops():
    cfg=json.loads(PARENT.read_text())['recovery']['settling_reward']
    h=torch.tensor([.2,.334,.36]);v=torch.ones(3,3)*.1;w=torch.ones(3,3)*.3
    costs=huber_settling_costs(h,v,w,{**cfg,'gate_mode':'unconditional'})
    for value in costs.values():
        assert value[0]>0
        torch.testing.assert_close(value,value[-1].expand_as(value))
    assert huber_settling_costs(h,v,w,cfg)['settling_linear'][0]==0


def test_unknown_gate_mode_is_rejected():
    with pytest.raises(ValueError):
        reward_height_gate(torch.tensor([.36]),.3,.36,'conditional_typo')
    spec=json.loads(PARENT.read_text())
    for cfg,key in ((spec['reward'],'pitch_level_gate_mode'),
                    (spec['reward'],'roll_level_gate_mode'),
                    (spec['recovery']['settling_reward'],'gate_mode'),
                    (spec['recovery']['standing_task']['reward'],'gate_mode')):
        cfg[key]='conditional_typo'
        assert validate(spec)
        cfg.pop(key)


def test_corrected_recipe_is_isolated_unapproved_and_preserves_coefficients(tmp_path,prepare_module):
    before=PARENT.read_bytes();ledger_before=PARENT.with_name('budget.json').read_bytes()
    output=tmp_path/'new_recipe'
    prepare_module.prepare_height_independent(PARENT,output)
    spec=json.loads((output/'spec.json').read_text());old=json.loads(before)
    assert validate(spec)==[]
    assert spec['source_sha256']==old['source_sha256']
    for key in ('action','ground','control','ppo','termination'):
        assert spec[key]==old[key]
    assert spec['recovery']['standing_task']['protocol']==old['recovery']['standing_task']['protocol']
    assert spec['recovery']['standing_task']['reward']['weights']==old['recovery']['standing_task']['reward']['weights']
    assert spec['reward']['upright']==0
    for axis in ('pitch','roll'):
        assert spec['reward'][axis+'_level']==old['reward'][axis+'_level']
        assert spec['reward'][axis+'_level_gate_mode']=='unconditional'
    retention=spec['recovery']['standing_task']['retention']
    assert retention['height_min_m']<=.334<=retention['height_max_m']
    assert retention['coefficient']==old['recovery']['standing_task']['retention']['coefficient']
    book=json.loads((output/'budget.json').read_text())
    assert book['authorization']=='UNAUTHORIZED' and not book['attempts'] and not any(book['used'].values())
    assert PARENT.read_bytes()==before and PARENT.with_name('budget.json').read_bytes()==ledger_before
    with pytest.raises(FileExistsError):
        prepare_module.prepare_height_independent(PARENT,output)


def test_corrected_pitch_roll_costs_are_signed_symmetric_and_dt_once(tmp_path,prepare_module):
    prepare_module.prepare_height_independent(PARENT,tmp_path/'recipe')
    probe=json.loads((tmp_path/'recipe/reward_probe.json').read_text())
    rows=probe['corrected']['cases']['moving_asymmetric']
    for name in ('pitch_level','roll_level','settling_linear','settling_angular','mirror_posture'):
        values=torch.tensor([r['weighted_dt'][name] for r in rows])
        assert (values<0).all()
        torch.testing.assert_close(values,values[-1].expand_as(values))
    from native_stand.recovery.domain import process_reward
    cfg=json.loads((tmp_path/'recipe/spec.json').read_text())['reward']
    h=torch.tensor([.2,.36]);z=torch.zeros(2)
    total,raw,weighted=process_reward(h,h,torch.full_like(h,.36),torch.ones(2),
        torch.zeros(2,6),torch.zeros(2,6),z,z.bool(),z.bool(),weights=cfg,dt=.01,
        pitch=torch.tensor([.04,-.04]),roll=torch.tensor([-.04,.04]),
        contact=torch.ones(2,2)*50.,wheel_velocity=torch.zeros(2,2),support_balance=z)
    for axis in ('pitch','roll'):
        key=axis+'_level'
        torch.testing.assert_close(raw[key],torch.full_like(h,(.04/.12)**2))
        torch.testing.assert_close(weighted[key],raw[key]*cfg[key]*.01)
    assert not weighted['upright'].any()
    torch.testing.assert_close(total[0],total[1])


def test_fixed_error_height_sweep_loses_escape_in_corrected_recipe(tmp_path,prepare_module):
    prepare_module.prepare_height_independent(PARENT,tmp_path/'recipe')
    probe=json.loads((tmp_path/'recipe/reward_probe.json').read_text())
    for recipe in ('previous','corrected'):
        rows=probe[recipe]['cases']['moving_asymmetric']
        high=rows[4];low=rows[2]
        if recipe=='previous':
            assert abs(low['weighted_dt']['settling_angular'])<abs(high['weighted_dt']['settling_angular'])
        else:
            assert low['total_per_policy_step']<high['total_per_policy_step']


def test_plan_only_does_not_reserve_or_start_runtime(tmp_path,prepare_module):
    import sys
    from native_stand.command_v6.tools.preflight import check
    prepare_module.prepare_height_independent(PARENT,tmp_path/'recipe')
    path=tmp_path/'recipe/spec.json';book=path.with_name('budget.json');before=book.read_bytes()
    run=tmp_path/'NOT_CREATED'
    result=check(path,run,'source_eval')
    assert result['cpu_valid'] and result['status']=='READY_NEEDS_AUTH'
    assert book.read_bytes()==before and not run.exists()
    assert not any(name=='isaaclab' or name.startswith('isaaclab.') for name in sys.modules)


@pytest.mark.parametrize('stop_phase,exit_code',[
    ('source_eval',0),('smoke',0),('formal',0),('formal',1)])
def test_user_stop_never_starts_later_phase_or_durability(tmp_path,monkeypatch,stop_phase,exit_code,complete_smoke_fixture):
    from native_stand.command_v6 import stand_chain
    from native_stand.command_v6.completion import write
    path=tmp_path/'spec.json';write(path,json.loads(PARENT.read_text()))
    chain=tmp_path/'chain';chain.mkdir()
    write(chain/'manifest.json',{'attempt_id':'fixture','hapi_session':None})
    write(tmp_path/'budget.json',{'limits':{'formal':500},'used':{'formal':0,'smoke':0}})
    phases=[];notifications=[]
    def fake_phase(spec,phase,output,handshake_fd=None):
        phases.append(phase);output.mkdir()
        if phase=='smoke' and phase!=stop_phase:
            write(output/'progress.json',{'actual_updates':3,'actor_parameters_changed':True,
                'evaluations':[{'cases':[{'path':'evaluation_fixture.json'}]}]})
            write(output/'terminal_report.json',{'status':'COMPLETED','actual_updates':3})
            write(output/'manifest.json',{'source_sha256':json.loads(path.read_text())['source_sha256']})
            (output/'source_snapshot').mkdir()
            (output/'source_snapshot/spec.json').write_bytes(path.read_bytes())
            import hashlib
            write(output/'manifest.json',{'source_sha256':json.loads(path.read_text())['source_sha256'],
                'spec_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            write(output/'evaluation_fixture.json',{'per_env':[{}]*8,'outcome_counts':{}})
            complete_smoke_fixture(output,path,3)
        return {'phase':phase,'run':str(output),'exit_code':exit_code if phase==stop_phase else 0,
                'status':'STOPPED_BOUNDED' if phase==stop_phase else 'COMPLETED',
                'terminal':{'actual_updates':3,'stop_kind':'user_signal' if phase==stop_phase else None},
                'progress':{'actor_parameters_changed':True}}
    monkeypatch.setattr(stand_chain,'run_phase',fake_phase)
    monkeypatch.setattr(stand_chain,'notify',lambda p:notifications.append(p))
    reader,writer=os.pipe()
    try:
        assert stand_chain.worker(SimpleNamespace(output_dir=chain,spec=path,handshake_fd=writer))==exit_code
    finally:
        os.close(reader)
    assert phases==['source_eval','smoke','formal'][:['source_eval','smoke','formal'].index(stop_phase)+1]
    terminal=json.loads((chain/'chain_terminal_report.json').read_text())
    if exit_code:
        assert terminal['status']=='FAILED' and 'terminal/exit conflict' in terminal['failure']
    else:
        assert terminal['status']=='STOPPED_BOUNDED' and terminal['durability']['reason']=='user stopped chain'
    assert notifications==[chain]
