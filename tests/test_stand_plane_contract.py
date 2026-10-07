"""CPU gates for the new project's explicit standing and physics identity."""
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import torch

from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.contract import frame, history, targets, effort
from native_stand.command_v6.domain.reward import compute
from native_stand.command_v6.tools.preflight import check
from native_stand.command_v6.tools.checkpoint_input import inspect
from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import


ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"configs/experiments/stand_plane.json"


def test_spec_is_stand_only_with_plane_and_frozen_control():
    spec=json.loads(SPEC.read_text())
    assert validate(spec)==[]
    assert spec["curriculum"]["stages"]==[{"id":0,"commands":[[0,0]],"weights":[1.]}]
    assert spec["ground"]["collider"]=="plane"
    assert spec["control"]["effort_limits_nm"]==[40,40,5.5,40,40,5.5]


def test_single_spec_configures_all_runtime_periods_targets_and_ground():
    spec=json.loads(SPEC.read_text())
    cfg=SimpleNamespace(scene=SimpleNamespace(),sim=SimpleNamespace())
    configure_env(cfg,spec,envs=64)
    assert cfg.scene.num_envs==64
    assert cfg.sim.dt==.001 and cfg.decimation==10 and cfg.pd_interval_steps==5
    assert (cfg.ground_static_friction,cfg.ground_dynamic_friction,cfg.ground_restitution)==(.5,.5,0.)
    assert cfg.ground_height_m==0. and cfg.ground_normal_axis=="Z"
    assert (cfg.ground_width_m,cfg.ground_length_m)==(128.,128.)
    assert (cfg.leg_position_scale_rad,cfg.leg_pair_radius_rad,cfg.wheel_speed_scale_rad_s)==(.1,.12,6.)
    assert (cfg.leg_kp,cfg.leg_kd,cfg.wheel_kv)==(60.,2.,1.)
    assert cfg.closure_fault_m==.005 and cfg.fall_root_height_m==.2


def test_actual_asset_module_path_and_yaml_are_checked(monkeypatch):
    spec=json.loads(SPEC.read_text())
    import hashlib
    spec['colleague_config_sha256']=hashlib.sha256(Path(spec['colleague_config_path']).read_bytes()).hexdigest()
    key="agent_world.assets.rmuc_wheel_leg"
    monkeypatch.setitem(sys.modules,key,SimpleNamespace(__file__=spec["asset_module_path"]))
    assert verify_asset_import(spec)["module_sha256"]==spec["asset_module_sha256"]
    monkeypatch.setitem(sys.modules,key,SimpleNamespace(__file__="/tmp/wrong_asset_module.py"))
    with pytest.raises(RuntimeError,match="path differs"):
        verify_asset_import(spec)


def test_unapproved_budget_blocks_isaac_without_creating_output(tmp_path):
    output=tmp_path/"not-created"
    import hashlib
    spec=json.loads(SPEC.read_text())
    spec['colleague_config_sha256']=hashlib.sha256(Path(spec['colleague_config_path']).read_bytes()).hexdigest()
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    path.with_name('budget.json').write_bytes(SPEC.with_name('budget.json').read_bytes())
    plan=check(path,output,"source_eval")
    assert plan["status"]=="READY_NEEDS_AUTH" and plan["cpu_valid"]
    assert "not been authorized" in " ".join(plan["errors"])
    assert plan["simulation"]==plan["ppo"]==plan["files_written"]==0
    assert not output.exists()


def test_public_plan_entries_do_not_create_runs(tmp_path):
    import hashlib
    fixture=json.loads(SPEC.read_text())
    fixture['colleague_config_sha256']=hashlib.sha256(Path(fixture['colleague_config_path']).read_bytes()).hexdigest()
    fixture_spec=tmp_path/'spec.json';fixture_spec.write_text(json.dumps(fixture))
    fixture_spec.with_name('budget.json').write_bytes(SPEC.with_name('budget.json').read_bytes())
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    checkpoint=Path(json.loads(SPEC.read_text())["source_checkpoint"])
    commands=(
        ["launcher.py","--phase","source_eval","--output-dir",str(tmp_path/"source")],
        ["tools/evaluate_checkpoint.py","--checkpoint",str(checkpoint),
         "--output",str(tmp_path/"evaluation.json")],
        ["tools/play.py","--checkpoint",str(checkpoint),
         "--output",str(tmp_path/"play.json")],
    )
    base=ROOT/"src/native_stand/command_v6"
    for command in commands:
        run=subprocess.run([sys.executable,str(base/command[0]),"--spec",str(fixture_spec),*command[1:]],
                           cwd=ROOT,capture_output=True,text=True,check=True)
        assert run.stdout.strip().startswith("{")
    assert before=={p.name:p.read_bytes() for p in tmp_path.iterdir()}


def test_checkpoint_identity_is_checked_before_app_launcher(tmp_path):
    spec=json.loads(SPEC.read_text())
    source=Path(spec["source_checkpoint"])
    assert inspect(source,spec,SPEC)["kind"]=="B200_SOURCE_EXPAND"
    wrong=tmp_path/"wrong_candidate.pt"
    torch.save({"actor":{"mlp.0.weight":torch.zeros(256,150)},
                "spec_sha256":"wrong","asset_sha256":spec["asset_sha256"]},wrong)
    with pytest.raises(ValueError,match="spec or asset identity"):
        inspect(wrong,spec,SPEC)


def test_zero_command_observation_history_action_and_reward():
    spec=json.loads(SPEC.read_text())
    q=torch.zeros(2,6)
    command=torch.tensor([[0.,0.,.363],[0.,0.,.363]])
    gravity=torch.tensor([[0.,-1.,0.]]).repeat(2,1)
    current=frame(torch.zeros(2,3),gravity,command,q,q,q,q)
    assert current.shape==(2,25)
    torch.testing.assert_close(current[:,6:9],torch.tensor([[0.,0.,1.815]]).repeat(2,1))
    first=history(torch.zeros(2,125),current,torch.ones(2,dtype=torch.bool))
    torch.testing.assert_close(first.reshape(2,5,25),current[:,None,:].expand(-1,5,-1))
    action=torch.tensor([[2.,0.,-1.,0.,0.,1.],[-2.,0.,1.,0.,0.,-1.]])
    clipped,legs,wheels=targets(action,q)
    assert clipped.abs().max()==1.
    assert wheels.tolist()==[[-6.,6.],[6.,-6.]]
    requested,applied=effort(q,q,legs,wheels)
    assert torch.all(applied.abs()<=torch.tensor([40.,40.,5.5,40.,40.,5.5]))
    reward,raw,weighted=compute(torch.full((2,),.363),torch.ones(2),
        torch.zeros(2),torch.zeros(2),torch.zeros(2),command,
        torch.ones(2,2,dtype=torch.bool),q,q,q,torch.zeros(2,4),
        torch.zeros(2,dtype=torch.bool),weights=spec["reward"],
        height_width=spec["reward"]["height_width_m"],
        linear_denominator=spec["reward"]["linear_error_denominator"],
        yaw_denominator=spec["reward"]["yaw_error_denominator"],
        terminal_penalty=spec["reward"]["terminal_penalty"])
    torch.testing.assert_close(raw["height"],torch.ones(2))
    torch.testing.assert_close(raw["velocity_tracking"],torch.ones(2))
    torch.testing.assert_close(reward,sum(weighted.values())*.01)
    fallen,_,_=compute(torch.full((2,),.363),torch.ones(2),
        torch.zeros(2),torch.zeros(2),torch.zeros(2),command,
        torch.ones(2,2,dtype=torch.bool),q,q,q,torch.zeros(2,4),
        torch.tensor([True,False]),weights=spec["reward"],
        height_width=spec["reward"]["height_width_m"],
        linear_denominator=spec["reward"]["linear_error_denominator"],
        yaw_denominator=spec["reward"]["yaw_error_denominator"],
        terminal_penalty=spec["reward"]["terminal_penalty"])
    torch.testing.assert_close(fallen,reward+torch.tensor([-1.,0.]))
