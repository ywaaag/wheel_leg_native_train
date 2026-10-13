"""Independent CPU fixtures for actual preparer and shared submission contract."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import torch
from tensordict import TensorDict

from native_stand.command_v6.learning import model
from native_stand.command_v6.tools import prepare_motion_experiment as tool
from native_stand.command_v6.tools.experiment_preparation import digest,publish


@pytest.fixture
def inputs(tmp_path):
    asset=tmp_path/'asset';asset.write_text('fixture only')
    spec={'experiment':'fixture','version':6,'effective_recipe_version':1,'objective':'global_adv_norm',
        'interpreter':'/home/kellen/anaconda3/envs/issaclab/bin/python','seed':104,
        'observation':{'frame_dim':25,'scales':[.25,1.,2.,.25,5.,2.,.05,1.]},
        'history':{'frames':5,'dim':125},
        'action':{'dim':6,'order':['l0','l1','lw','r0','r1','rw'],'leg_scale_rad':.5,'leg_pair_radius_rad':0.,'wheel_scale_rad_s':100.},
        'wheel_envelope_conversion':{'source_scale_rad_s':100.,'destination_scale_rad_s':100.},
        'control':{'physics_dt_s':.001,'pd_dt_s':.005,'policy_dt_s':.01,'leg_kp':60.,'leg_kd':2.,'wheel_kv':1.,'closure_fault_m':.005,'height_command_m':.4,'effort_limits_nm':[40,40,5.5,40,40,5.5]},
        'ground':{'collider':'plane','height_m':0.,'normal_axis':'Z','width_m':128.,'length_m':128.,'material_path':'/World/native_ground_material','static_friction':.5,'dynamic_friction':.5,'restitution':0.},
        'termination':{'fall_root_height_m':.2,'minimum_up_cos':.5,'body_contact_max_n':200.,'active_leg_angle_max_rad':.5},
        'reward':{'upright':2.,'height':2.,'velocity_tracking':8.,'two_wheel_contact':.5,'effort':-.02,'action_delta':-.01,'joint_margin':-.05,'height_width_m':.06,'linear_error_denominator':1.,'yaw_error_denominator':.09,'terminal_penalty':-1.,'tracking_mode':'combined','stage_linear_denominators':{'0':1.,'1':1.},'stage_yaw_denominators':{'0':.09,'1':.09},'linear_cohort_width':{'retained_commands':[[0,0],[.5,0],[-.5,0]],'retained_denominator':.04,'selector':'episode_target_not_instantaneous_command'}},
        'curriculum':{'active_stage':1,'minimum_zero_fraction':.25,'episode_length_s':31.,'schedule_s':[1.,2.,24.,2.],
            'stages':[{'id':0,'commands':[[0,0]],'weights':[1.]},{'id':1,'commands':[[0,0],[.5,0],[-.5,0]],'weights':[.25,.375,.375]}],
            'task_progression':{'initial_stage':1,'max_enabled_stage':1,'consecutive_confirmations':2,'standing_regression_confirmations':2,'learned_regression_confirmations':2,'blocked_reason':'fixture'}},
        'evaluation':{'protocol_identity':'motion_absolute_v3','command_mode':'ramp','tracking_mode':'combined','motion_protocol':'ramp','seed':104,'seconds':30.,'envs':64,'scored_envs':8,'full_every_updates':50,'checkpoint_every_updates':50,'light_every_updates':0},
        'ppo':{'envs':64,'steps_per_env':128,'learning_rate':3e-5,'hidden_dims':[4,4,4],'epochs':4,'minibatches':4,'gamma':.99,'lam':.95,'entropy_coef':.001},
        'budget':{'source_eval_wall_s':600,'smoke_updates':1,'smoke_wall_s':300,'formal_updates':2,'formal_wall_s':900},
        'artifacts':{'checkpoint_name':'model_update_{update}.pt'},'cohort_width_ab':True,
        'asset_path':str(asset),'asset_sha256':digest(asset),'asset_module_root':str(tmp_path),
        'asset_module_path':str(asset),'asset_module_sha256':digest(asset),'colleague_config_path':str(asset),'colleague_config_sha256':digest(asset)}
    obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
    actor=model(obs,actor=True,spec=spec);critic=model(obs,actor=False,spec=spec)
    params=list(actor.parameters())+list(critic.parameters());optimizer=torch.optim.Adam(params,lr=3e-5)
    for parameter in params:optimizer.state[parameter]={'step':torch.tensor(7.),'exp_avg':torch.zeros_like(parameter),'exp_avg_sq':torch.ones_like(parameter)}
    checkpoint=tmp_path/'model.pt'
    saved={'actor':actor.state_dict(),'critic':critic.state_dict(),'optimizer':optimizer.state_dict(),
        'cpu_rng':torch.get_rng_state(),'cuda_rng':[],'update':50,'spec_sha256':'a'*64,'asset_sha256':digest(asset),
        'parameter_names':{role:list(dict(network.named_parameters())) for role,network in [('actor',actor),('critic',critic)]}}
    torch.save(saved,checkpoint)
    spec.update(source_checkpoint=str(checkpoint),source_sha256=digest(checkpoint),source_input_dim=150,source_update=50,source_spec_sha256='a'*64)
    parent=tmp_path/'parent.json';parent.write_text(json.dumps(spec))
    request=tmp_path/'request.json';request.write_text(json.dumps({'mode':'evaluation','commands':[[1,0],[-1,0]],'wall_s':600}))
    return parent,checkpoint,request,tmp_path/'2026_10_7-21_00__motion_fixture'


def call(inputs,**kwargs):
    parent,checkpoint,request,output=inputs
    return tool.prepare(parent,checkpoint,request,output,checkpoint_sha256=digest(checkpoint),
        session='current',physical_gpu=1,gpu_uuid='GPU-fixture',**kwargs)


def test_default_zero_write_and_exclusive_unauthorized_publish(inputs):
    parent,checkpoint,request,output=inputs
    before={p:p.read_bytes() for p in (parent,checkpoint,request)}
    plan=call(inputs);assert plan['files_written']==0 and not output.exists()
    result=call(inputs,write=True)
    assert result['preparation_manifest']['files_written']==3
    assert result['budget']['authorization']=='UNAUTHORIZED' and result['budget']['attempts']=={}
    assert all(v==0 for v in result['budget']['used'].values())
    assert result['spec']['authorization']['status']=='UNAUTHORIZED'
    assert all(p.read_bytes()==value for p,value in before.items())
    with pytest.raises(FileExistsError):call(inputs,write=True)


def test_course_preserves_recipe_and_total_counts(inputs):
    parent,checkpoint,request,output=inputs
    request.write_text(json.dumps({'mode':'course','retained_commands':[[0,0],[.5,0],[-.5,0]],
        'current_commands':[[1,0],[-1,0]],'weights':[.25,.125,.125,.25,.25],
        'online_updates':100,'smoke_updates':1,'full_every_updates':25,
        'wall_s':{'source_eval':600,'smoke':300,'formal':1200}}))
    result=call(inputs)
    assert result['budget']['total_online_PPO_limit']==100
    assert result['spec']['budget']['formal_updates']==99
    assert result['spec']['curriculum']['task_progression']['max_enabled_stage']==1
    old=json.loads(parent.read_text())
    for field in ('action','control','ppo','ground','reward'):
        assert result['spec'][field]==old[field]


@pytest.mark.parametrize('mutation',[
    lambda d:d.update(reward={'weight':99}),lambda d:d.update(mode='magic'),
    lambda d:d.update(commands=[[1,1]]),lambda d:d.update(commands=[[1,0],[1,0]]),
    lambda d:d.update(wall_s=float('nan'))])
def test_invalid_request_never_publishes(inputs,mutation):
    parent,checkpoint,request,output=inputs;data=json.loads(request.read_text());mutation(data);request.write_text(json.dumps(data))
    with pytest.raises(ValueError):call(inputs,write=True)
    assert not output.exists()


def test_course_rejects_skipping_an_endpoint_level(inputs):
    parent,checkpoint,request,output=inputs
    request.write_text(json.dumps({'mode':'course','retained_commands':[[0,0],[.5,0],[-.5,0]],
        'current_commands':[[2,0],[-2,0]],'weights':[.25,.125,.125,.25,.25],
        'online_updates':100,'smoke_updates':1,'full_every_updates':25,
        'wall_s':{'source_eval':600,'smoke':300,'formal':1200}}))
    with pytest.raises(ValueError,match='next 0.5 step'):call(inputs)
    assert not output.exists()


def test_bad_sha_and_moment_mapping_fail_before_writes(inputs):
    parent,checkpoint,request,output=inputs
    with pytest.raises(ValueError,match='SHA'):
        tool.prepare(parent,checkpoint,request,output,checkpoint_sha256='0'*64,session='current',physical_gpu=1,gpu_uuid='GPU-fixture',write=True)
    saved=torch.load(checkpoint,weights_only=False);saved['parameter_names']['actor'].reverse();torch.save(saved,checkpoint)
    with pytest.raises(ValueError,match='parameter-name'):call(inputs,write=True)
    assert not output.exists()


def test_publish_failure_removes_only_created_files(tmp_path,monkeypatch):
    output=tmp_path/'new';original=Path.open
    def broken(path,*args,**kwargs):
        if path.name=='budget.json':raise OSError('fixture disk write failed')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',broken)
    with pytest.raises(OSError):publish(output,{'spec.json':{},'budget.json':{}},{})
    assert not output.exists()


def test_reference_identity_drift_and_recovery_parent_rejected(inputs):
    parent,checkpoint,request,output=inputs
    data=json.loads(parent.read_text());Path(data['asset_path']).write_text('drift')
    with pytest.raises(ValueError,match='SHA'):call(inputs)
    data['task']='recovery';parent.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Recovery'):call(inputs)
    assert not output.exists()


def test_actual_cli_plan_imports_no_isaac_and_writes_nothing(inputs):
    parent,checkpoint,request,output=inputs
    code="import runpy,sys; runpy.run_module('native_stand.command_v6.tools.prepare_motion_experiment',run_name='__main__'); assert 'isaaclab.app' not in sys.modules; assert 'isaacsim' not in sys.modules"
    command=[sys.executable,'-c',code,'--parent-spec',str(parent),'--checkpoint',str(checkpoint),
        '--checkpoint-sha256',digest(checkpoint),'--request',str(request),'--output-dir',str(output),
        '--hapi-session','current','--physical-gpu','1','--gpu-uuid','GPU-fixture']
    completed=subprocess.run(command,capture_output=True,text=True,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')})
    assert completed.returncode==0,completed.stderr
    result=json.loads(completed.stdout)
    assert result['files_written']==result['simulation']==result['ppo']==0
    assert not output.exists()


def test_explicit_audit_identity_has_no_implicit_authorization(inputs):
    audit=inputs[0].parent/'audit.json';audit.write_text('{"accepted": true}')
    with pytest.raises(ValueError,match='expected SHA'):call(inputs,audit=audit)
    result=call(inputs,audit=audit,audit_sha256=digest(audit))
    assert not result['runtime_authorized'] and result['budget']['authorization']=='UNAUTHORIZED'
    assert str(audit) in result['preparation_manifest']['inputs']


def test_course_rejects_bad_weights_and_one_sided_rehearsal(inputs):
    parent,checkpoint,request,output=inputs
    data={'mode':'course','retained_commands':[[0,0],[.5,0]],'current_commands':[[1,0],[-1,0]],
        'weights':[.25,.25,.25,.25],'online_updates':10,'smoke_updates':1,'full_every_updates':25,
        'wall_s':{'source_eval':600,'smoke':300,'formal':900}}
    request.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='both directions'):call(inputs)
    data['retained_commands']=[[0,0],[.5,0],[-.5,0]];request.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='weights'):call(inputs)
    assert not output.exists()


def test_random_parent_cannot_silently_ignore_selected_checkpoint(inputs):
    parent,checkpoint,request,output=inputs;spec=json.loads(parent.read_text());spec['initialization']='random';parent.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='warmstart'):call(inputs)
    assert not output.exists()


def test_missing_request_fields_fail_clearly_before_publication(inputs):
    parent,checkpoint,request,output=inputs;request.write_text('{"mode":"evaluation"}')
    with pytest.raises(ValueError,match='missing request fields'):call(inputs,write=True)
    assert not output.exists()
