import pytest
FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.command_v6.domain.posture_geometry import measure


def rotation():
    return torch.tensor([[[1.,0.,0.],[0.,0.,-1.],[0.,1.,0.]]])


def test_leg_lengths_not_same_as_wheel_fore_aft_offset():
    hips=torch.tensor([[[.2,0.,.4],[-.2,0.,.4]]])
    wheels=torch.tensor([[[.2,.05,.06],[-.2,-.05,.06]]])
    r=measure(hips,wheels,rotation())
    assert r['wheel_heading_offset_m'].item()==pytest.approx(.1)
    assert r['leg_length_difference_m'].item()==pytest.approx(0.)
    assert r['roll_rad'].item()==pytest.approx(0.) and r['valid'].item()


def test_length_difference_is_measured_not_joint_angle_symmetry():
    hips=torch.tensor([[[.2,0.,.4],[-.2,0.,.4]]])
    wheels=torch.tensor([[[.2,0.,.06],[-.2,0.,.08]]])
    r=measure(hips,wheels,rotation())
    assert r['leg_length_difference_m'].item()==pytest.approx(.02)
    assert r['wheel_heading_offset_m'].item()==pytest.approx(0.)
    assert r['wheel_height_difference_m'].item()==pytest.approx(-.02)


def test_ground_heading_excludes_pitch_and_invalid_geometry_does_not_pass():
    hips=torch.zeros(1,2,3);wheels=torch.zeros(1,2,3)
    r=measure(hips,wheels,torch.eye(3)[None])
    assert not r['valid'].item()
    wheels[0,0,0]=float('nan')
    assert not measure(hips,wheels,rotation())['valid'].item()


def test_diagnostic_window_light_and_full_evidence():
    from native_stand.command_v6.domain.posture_geometry import diagnostic_window
    light={'steady_window_s':[.5,2.], 'motion_window_s':None}
    for target in ([0,0],[.5,0],[-.5,0]):
        row=diagnostic_window(light,target,total_samples=400,dt=.01)
        assert row['window_s']==[.5,2.] and row['scope']=='steady_window'
        assert row['complete'] and row['required_samples']==151
        assert not row['full_motion_window_declared']
    full={'steady_window_s':[2,30], 'motion_window_s':[10,18]}
    row=diagnostic_window(full,[2,0],total_samples=3000,dt=.01)
    assert row['scope']=='motion_window' and row['required_samples']==801 and row['complete']
    assert not diagnostic_window(full,[2,0],total_samples=1799,dt=.01)['complete']
    assert diagnostic_window(full,[0,0],total_samples=3000,dt=.01)['window_s']==[2,30]


def test_runtime_uses_shared_posture_window_resolver():
    from native_stand.command_v6.tools.test_resources import source_file
    source=source_file('command_v6/tools/evaluate_checkpoint.py').read_text()
    assert 'posture_axis=diagnostic_window(protocol,target,total_samples=count,dt=env.step_dt)' in source
    assert "len(selected)==posture_axis['required_samples']" in source


def test_light_batch_protocol_matches_smoke_window_and_rejects_foreign_mode():
    import pytest
    from native_stand.command_v6.tools.evaluate_checkpoint import batch_protocol
    from native_stand.command_v6.domain.evaluation_requests import motion_request,recovery_request
    spec={'evaluation':{'light_seconds':4.,'light_window_s':[.5,2.],'scored_envs':8},'control':{'policy_dt_s':.01}}
    request={'checkpoint':'model.pt','sha256':'a'*64,'target':[.5,0],'seconds':4.,'evaluation_mode':'light'}
    validated=motion_request(request)
    protocol=batch_protocol(spec,validated,False)
    assert protocol['motion_window_s'] is None and protocol['steady_window_s']==[.5,2.]
    assert protocol['requested_seconds']==4.
    with pytest.raises(ValueError):motion_request({**request,'evaluation_mode':'unknown'})
    with pytest.raises(ValueError):recovery_request({**request,'family':'R0'})
    with pytest.raises(ValueError):batch_protocol(spec,{**request,'seconds':30.},False)
