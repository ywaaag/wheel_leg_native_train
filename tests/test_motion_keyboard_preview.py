import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from native_stand.command_v6.domain.keyboard_command import KeyboardCommand, synchronize_observation


@pytest.mark.parametrize('gpu',[0,1])
def test_keyboard_render_and_cuda_mappings_are_explicit(gpu):
    from native_stand.command_v6.tools.play import keyboard_app_options
    options=keyboard_app_options(gpu)
    assert options['device']=='cuda:0' and options['multi_gpu'] is False
    assert f'--/renderer/activeGpu={gpu}' in options['kit_args']
    assert '--/renderer/multiGpu/enabled=false' in options['kit_args']


def test_linear_keyboard_ramp_release_reverse_and_disabled_yaw():
    c=KeyboardCommand(1.,0.,max_speed=2.,max_yaw_speed=0.)
    c.event('W',True)
    assert c.advance(.01)==pytest.approx([.005,0.])
    c.event('SPACE',True)
    assert c.advance(.01)==pytest.approx([0.,0.])
    c.event('S',True)
    assert c.advance(.01)==pytest.approx([-.005,0.])
    c.event('A',True)
    assert c.target()==[-1.,0.]
    for _ in range(150):c.event('UP',True)
    assert c.speed==2.
    c.event('R',True);assert c.reset_requested
    c.reset();assert c.current==[0.,0.] and not c.pressed
    c.event('ESCAPE',True);assert c.stop


def test_newest_command_matches_history_without_touching_other_channels():
    obs={'policy':torch.randn(1,25),'history':torch.randn(1,125)}
    history=obs['history'].clone()
    before={k:v.clone() for k,v in obs.items()}
    synchronize_observation(obs,history,[1.,-.4])
    assert torch.allclose(obs['policy'][0,6:8],torch.tensor([2.,-.1]))
    assert torch.equal(obs['history'][:,-19:-17],obs['policy'][:,6:8])
    assert torch.equal(history,obs['history'])
    mask=torch.ones(125,dtype=torch.bool);mask[-19:-17]=False
    assert torch.equal(obs['history'][:,mask],before['history'][:,mask])
    mask=torch.ones(25,dtype=torch.bool);mask[6:8]=False
    assert torch.equal(obs['policy'][:,mask],before['policy'][:,mask])


def test_reused_script_b250_cpu_plan_shared_source_no_ledger_changes():
    root=Path(__file__).resolve().parents[1]
    formal=root/'runs/motion_cohort_width_ab_20261006/B/formal'
    if not (formal/'model_update_250.pt').exists():pytest.skip('local historical checkpoint unavailable')
    ledger=root/'configs/experiments/motion_cohort_width_ab_20261006/B/budget.json'
    before=ledger.read_bytes()
    p=subprocess.run([sys.executable,str(root/'scripts/play_motion_keyboard.py'),
        '--spec',str(formal/'source_snapshot/spec.json'),
        '--checkpoint',str(formal/'model_update_250.pt')],cwd=root,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    plan=json.loads(p.stdout)
    assert plan['simulation']==plan['files_written']==plan['PPO_updates']==0
    assert plan['keyboard']['max_speed_mps']==2.
    assert plan['keyboard']['max_yaw_rad_s']==0.
    assert plan['identity_warnings']==[]
    assert ledger.read_bytes()==before
