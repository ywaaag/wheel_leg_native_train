import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]


def tool():
    spec=importlib.util.spec_from_file_location('native_mujoco',ROOT/'scripts/validate_native_mujoco.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_cad_native_rotation_matches_reset_yaw90():
    module=tool()
    roll90=np.array([[1,0,0],[0,0,-1],[0,1,0]])
    expected=np.array([[0,-1,0],[1,0,0],[0,0,1]])
    assert np.allclose(roll90@module.CAD_TO_UPRIGHT_REPORTING_ONLY.T,expected)
    assert np.allclose(module.CAD_TO_UPRIGHT_REPORTING_ONLY@module.CAD_TO_UPRIGHT_REPORTING_ONLY.T,np.eye(3))


def test_reference_binding_and_gear_output_torque_preserves_limits():
    m=pytest.importorskip('mujoco')
    path=Path('/home/kellen/wheel_leg_sim2sim/assets/wheeled_infantry.xml')
    if not path.exists():pytest.skip('reference repository unavailable')
    module=tool();model=m.MjModel.from_xml_path(str(path));refs=module.binding(model)
    limits=np.array([40,40,5.5,40,40,5.5])
    controls=limits/refs['gears']
    assert np.allclose(controls*refs['gears'],limits)
    data=m.MjData(model);m.mj_forward(model,data)
    _,gravity,state=module.state(model,data,refs)
    assert np.allclose(gravity,[0,-1,0],atol=1e-8)
    assert state['closure_m']<1e-12
    assert model.nu==6 and model.neq==4


def test_native_actor_uses_CAD_axes_not_Fudan_canonical_axes():
    m=pytest.importorskip('mujoco')
    path=Path('/home/kellen/wheel_leg_sim2sim/assets/wheeled_infantry.xml')
    if not path.exists():pytest.skip('reference repository unavailable')
    module=tool();model=m.MjModel.from_xml_path(str(path));refs=module.binding(model)
    data=m.MjData(model)
    data.qvel[:3]=[1.,2.,3.]
    data.qvel[3:6]=[.1,.2,.3]
    m.mj_forward(model,data)
    angular,gravity,state=module.state(model,data,refs)
    assert np.allclose(gravity,[0.,-1.,0.],atol=1e-8)
    assert np.allclose(angular,[.1,.2,.3],atol=1e-8)
    # native root_lin_vel_w is COM velocity, not freejoint/link-origin velocity.
    rotation=data.xmat[refs['root']].reshape(3,3)
    omega_world=rotation@np.array([.1,.2,.3])
    com_velocity=np.array([1.,2.,3.])+np.cross(omega_world,
        data.xipos[refs['root']]-data.xpos[refs['root']])
    cad_linear=rotation.T@com_velocity
    assert state['vx']==pytest.approx(-cad_linear[2])
    assert state['vy']==pytest.approx(-cad_linear[0])
    assert state['yaw_rate']==pytest.approx(.2)
    assert state['up']==pytest.approx(1.)


def test_recorded_native_first_action_proves_corrected_frame():
    import json
    paths=list((ROOT/'sim2sim').glob('*__motion_b250_frame_parity/parity.json'))
    if not paths:pytest.skip('local offline parity evidence unavailable')
    corrected=paths[-1].parent/'corrected/parity.json'
    result=json.loads((corrected if corrected.exists() else paths[-1]).read_text())
    assert result['initial_gravity']==pytest.approx([0.,-1.,0.])
    assert result['corrected_action_max_difference']<1e-6
    assert result['wrong_action_max_difference']>1.
    assert result['native_actuator_vs_physical_clipped_max_difference_Nm']==0.
    assert result['native_control_records']==24000
    assert all(row['max_difference']<1e-8 for row in result['joint_axis_parity'])


def test_viewer_refactor_preserves_headless_zero_budget_stop():
    import json,time
    m=pytest.importorskip('mujoco')
    path=Path('/home/kellen/wheel_leg_sim2sim/assets/wheeled_infantry.xml')
    if not path.exists():pytest.skip('reference repository unavailable')
    module=tool();model=m.MjModel.from_xml_path(str(path));refs=module.binding(model)
    spec=json.loads((ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/spec.json').read_text())
    summary,rows=module.run_case(spec,model,refs,None,2.,time.monotonic()-1,viewer=False)
    assert summary['termination']=='WALL_BUDGET' and summary['completed_physics_steps']==0
    assert not rows


def test_atomic_diagnostic_budget_settles_exception_without_physics(tmp_path,monkeypatch):
    import json,sys
    import torch
    from native_stand.command_v6 import learning
    module=tool();output=tmp_path/'2026_10_8-19_00__mujoco_fixture'
    checkpoint=tmp_path/'model.pt';checkpoint.write_bytes(b'fixture')
    manifest={'protocol':{'commands':[0.]},'checkpoint':{'checkpoint_sha256':'a'*64},'scope':'CPU fake only'}
    monkeypatch.setattr(module,'plan',lambda args:({},None,None,manifest))
    monkeypatch.setattr(torch,'load',lambda *a,**kw:{'actor':{}})
    monkeypatch.setattr(torch,'set_num_threads',lambda *a:None)
    class Actor:
        def load_state_dict(self,*a,**kw):pass
        def eval(self):return self
    monkeypatch.setattr(learning,'model',lambda *a,**kw:Actor())
    def broken(*a,**kw):raise RuntimeError('CPU fixture interruption')
    monkeypatch.setattr(module,'run_case',broken)
    monkeypatch.setattr(sys,'argv',['validate','--spec',str(tmp_path/'spec.json'),'--checkpoint',str(checkpoint),
        '--output-dir',str(output),'--run'])
    with pytest.raises(RuntimeError,match='fixture'):module.main()
    budget=json.loads((output/'budget.json').read_text());terminal=json.loads((output/'terminal_report.json').read_text())
    assert budget['schema_version']=='mujoco_diagnostic_budget_v1'
    case=budget['attempts']['command_00']
    assert case['settled'] and case['status']=='FAILED' and case['actual_physics_steps'] is None
    assert terminal['status']=='FAILED' and not terminal['capability_certified']
    assert not terminal['all_windows_completed']
