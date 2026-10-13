FROZEN_TEST_SCOPE='PROJECT_DATA'
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from native_stand.recovery.handoff_evaluator import atomic_result
from native_stand.command_v6.tools.evaluate_checkpoint import batch_plan
from native_stand.recovery.handoff_requests import validate
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/2026_10_10-16_28__recovery_motion_b250_handoff_ppo0/spec.json'

def test_actual_public_planner_and_baseline_condition_order(tmp_path):
    s=json.loads(SPEC.read_text());p=batch_plan(SimpleNamespace(spec=SPEC,output=tmp_path/'run',attempt_id=None),s)
    assert p['preflight']['status'] in ('PASS','READY_NEEDS_AUTH')
    assert len(p['requests'])==22 and p['online_PPO']==0
    assert p['requests'][0]['family']=='motion_native_normal'
    assert [r['switch_s'] for r in p['requests'][2:6]]==[.1]*4
    bad=json.loads(SPEC.read_text());bad['motion_handoff']['cases'][0]['foreign']=True
    with pytest.raises(ValueError):validate(bad)

def test_atomic_trace_budget_no_overwrite(tmp_path):
    a={'state':np.zeros((2,8,39))};p=atomic_result(tmp_path,0,{'per_env':[]},a,1048576)
    assert p.exists() and (tmp_path/'trace_00.npz').exists()
    with pytest.raises(FileExistsError):atomic_result(tmp_path,0,{},a,1048576)
    with pytest.raises(RuntimeError):atomic_result(tmp_path,1,{},a,1)
    assert not (tmp_path/'evaluation_01.json').exists()

def test_runtime_switch_no_physical_writes_or_actor_calls_and_snapshot_before_reset():
    import ast
    p=ROOT/'src/native_stand/recovery/handoff_runtime.py';tree=ast.parse(p.read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='HandoffEnv')
    pre=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_pre_physics_step')
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and ('write_' in n.func.attr or n.func.attr in ('reset','set_root_velocity')) for n in ast.walk(pre))
    assert 'physical_targets(' not in ast.get_source_segment(p.read_text(),pre) # one direct physical decode using per-env native scales
    # Explicit adapter may override prefix scale; legacy default must remain1.6.
    scale=next(n for n in ast.walk(pre) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
               and n.func.id=='getattr' and len(n.args)==3 and isinstance(n.args[1],ast.Constant)
               and n.args[1].value=='prefix_leg_scale')
    assert isinstance(scale.args[2],ast.Constant) and scale.args[2].value==1.6
    getobs=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_get_observations')
    assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='motion_frame' for n in ast.walk(getobs))==1

def test_actual_switch_numpy_scalars_roundtrip_and_nonfinite_reject(tmp_path):
    payload={'switch_state':{'policy_index':np.int64(0),'raw':np.float32(.2),'valid':np.bool_(True)},'accepted':False}
    p=atomic_result(tmp_path,0,payload,{'state':np.zeros((1,8,39))},1048576)
    assert json.loads(p.read_text())['switch_state']['policy_index']==0
    with pytest.raises(ValueError):atomic_result(tmp_path,1,{'bad':float('nan')},{},1048576)


def test_frozen_normal_reset_quaternion_preserves_actual_runtime_slots():
    import importlib.util, math, ast
    p=ROOT/'scripts/prepare_recovery_motion_handoff_scan.py'
    spec=importlib.util.spec_from_file_location('handoff_prepare_test',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    text=(ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/native_env.py').read_text()
    q=module.native_normal_root_quaternion(text)
    assert q==[math.sqrt(.5),0.,0.,math.sqrt(.5)]
    # Both normal source and Recovery runtime pass the four slots verbatim.
    runtime=(ROOT/'src/native_stand/recovery/runtime.py').read_text()
    assert "*p['root_quaternion_xyzw']" in runtime
    assert 'root_quaternion_xyzw=native_normal_root_quaternion(text)' in p.read_text()
    with pytest.raises(ValueError):module.native_normal_root_quaternion('unknown reset')
