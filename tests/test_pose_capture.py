import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import torch
from native_stand.recovery.capture_controls import Controls,clearance

ROOT=Path(__file__).resolve().parents[1]


def test_keyboard_limits_and_independent_sides():
    controls=Controls([[-.1,.1]]*4,[0.]*4,step=.02)
    controls.key('KEY_3');controls.key('UP')
    assert controls.targets==[0.,0.,.02,0.]
    for _ in range(20):controls.key('UP')
    assert controls.targets[2]==.1
    controls.key('SPACE');assert controls.mode=='ADJUST'
    controls.key('SPACE');assert controls.mode=='PASSIVE'
    controls.key('P');controls.key('S');controls.key('R')
    assert controls.paused and controls.save_requested and controls.reset_requested


def test_nonfinite_targets_rejected():
    c=Controls([[-1,1]]*4,[0.]*4)
    with pytest.raises(ValueError):c.set(0,float('nan'))


def test_clearance_actual_body_rotation_and_shape_scale():
    matrix=torch.eye(4).tolist()
    shape={'body_index':0,'matrix':matrix,'type':'Cylinder','axis':'Y','height':.1,'radius':.06}
    pos=torch.tensor([[0.,0.,.1]])
    # Axle horizontal: lowest = .1-.06. Axle vertical: lowest = .1-.05.
    assert clearance(pos,torch.tensor([[0.,0.,0.,1.]]),[shape],0.).item()==pytest.approx(.04)
    q=torch.tensor([[2**-.5,0.,0.,2**-.5]])
    assert clearance(pos,q,[shape],0.).item()==pytest.approx(.05)
    shape['matrix'][2][2]=2.
    assert clearance(pos,torch.tensor([[0.,0.,0.,1.]]),[shape],0.).item()==pytest.approx(-.02)


def test_manual_cli_plan_does_not_create_output_or_mutate_ledger(tmp_path):
    spec=ROOT/'configs/tools/recovery_capture.json'
    import hashlib
    config=json.loads(spec.read_text())
    base=json.loads(Path(config['base_spec']).read_text())
    config['colleague_config_sha256']=hashlib.sha256(Path(base['colleague_config_path']).read_bytes()).hexdigest()
    spec=tmp_path/'capture_fixture.json';spec.write_text(json.dumps(config))
    budget=ROOT/'configs/experiments/recovery_r1_20261002/budget.json';before=budget.read_bytes()
    output=tmp_path/'UNCREATED'
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')}
    command=[sys.executable,'-m','native_stand.recovery.capture','--spec',str(spec),'--output-dir',str(output)]
    result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,check=True)
    plan=json.loads(result.stdout)
    assert plan['simulation']==plan['ppo_updates']==plan['files_written']==0
    assert not plan['policy_loaded'] and not output.exists() and budget.read_bytes()==before
    command_code="import sys; from native_stand.recovery import capture; assert not any(n.startswith(('isaaclab','omni.')) for n in sys.modules)"
    subprocess.run([sys.executable,'-c',command_code],cwd=ROOT,env=env,check=True)


def test_new_write_refuses_existing_file(tmp_path):
    from native_stand.recovery.capture import write_new
    path=tmp_path/'pose.json';write_new(path,{'mode':'PASSIVE'})
    with pytest.raises(FileExistsError):write_new(path,{})
    assert json.loads(path.read_text())=={'mode':'PASSIVE'}
