FROZEN_TEST_SCOPE='PORTABLE'
import copy
import numpy as np
import pytest
import torch
from native_stand.command_v6.domain.sim2sim_contract import resolve,compare,JOINTS
from native_stand.command_v6.tools.trace_loader import control_tensor,paired_tensor,group,GROUPS,VERSION,AXES
from native_stand.command_v6.domain.contract import frame,history
from native_stand.command_v6.domain.diagnostic_profiles import storage_plan
from native_stand.command_v6.domain.evaluation_requests import motion_request
from native_stand.command_v6.domain.paired_state import concatenate,CHANNELS


def spec():
    return {'task':'motion','observation':{'frame_dim':25},'history':{'frames':5,'order':'oldest_to_newest'},
        'action':{'dim':6,'order':list(JOINTS),'leg_scale_rad':.5,'leg_pair_radius_rad':0.,'wheel_scale_rad_s':100},
        'control':{'physics_dt_s':.001,'pd_dt_s':.005,'policy_dt_s':.01,
        'effort_limits_nm':[40,40,5.5,40,40,5.5],'leg_kp':60,'leg_kd':2,'wheel_kv':1},'evaluation':{}}


def control():
    return {'effective_protocol':{'scored_envs':2},'control_diagnostics':{'axes':list(AXES),'schema_version':VERSION,
        'groups':copy.deepcopy(GROUPS),'valid':[[True,True]]*3,'rows':np.zeros((3,2,54)).tolist()}}


def test_frame_semantics_not_just_dimensions():
    c=resolve(spec());assert c['measurement_point']=='body_COM'
    other={**c,'actor_frame':'canonical','actor_initial_gravity':[0,0,-1]}
    assert compare(c,other)['status']=='NOT_PASS'
    angular=torch.tensor([[.1,.2,.3]]);gravity=torch.tensor([[0.,-1.,0.]])
    cmd=torch.tensor([[.5,-.2,.4]]);zero=torch.zeros(1,6)
    obs=frame(angular,gravity,cmd,zero,zero,zero,zero)
    assert obs[0,:9].tolist()==pytest.approx([.025,.05,.075,0,-1,0,1,-.05,2])
    wrong=frame(angular,torch.tensor([[0.,0.,-1.]]),cmd,zero,zero,zero,zero)
    assert obs.shape==wrong.shape and not torch.equal(obs,wrong)
    h=history(torch.zeros(1,125),obs,torch.tensor([True]));assert torch.equal(h,obs.repeat(1,5))
    bad=spec();bad['action']['order'].reverse()
    with pytest.raises(ValueError):resolve(bad)


def test_control_axes_transpose_and_validity_fail_closed():
    r=control();t=control_tensor(r);assert t['axes']==AXES and t['shape']==[3,2,54]
    assert group(t,'raw_action').shape==(3,2,6)
    r['control_diagnostics']['axes']=['scored_env','policy_time','channel']
    with pytest.raises(ValueError,match='axis'):control_tensor(r)
    r=control();r['control_diagnostics']['rows']=np.zeros((2,3,54)).tolist()
    with pytest.raises(ValueError):control_tensor(r)
    r=control();r['control_diagnostics']['rows'][0][0]=None
    with pytest.raises(ValueError):control_tensor(r)
    r['control_diagnostics']['valid'][0][0]=False
    assert not control_tensor(r)['valid'][0,0]
    r=control();r['control_diagnostics'].pop('axes');r['control_diagnostics'].pop('schema_version')
    with pytest.raises(ValueError):control_tensor(r)
    assert 'explicit_legacy' in control_tensor(r,allow_legacy_axes=True)['axis_identity_origin']


def test_profile_routes_to_actual_recorder_and_does_not_touch_inputs():
    from native_stand.command_v6.domain.paired_state import GROUPS as paired_groups,VERSION as paired_version
    s=spec();s['evaluation']={'diagnostic_profile':'paired_state'}
    plan=storage_plan(s,full=True)
    assert plan['runtime_kwargs']=={'full_trace':True,'diagnostics':True,'paired_state':True}
    q=torch.ones(2,25);h=torch.ones(2,125);a=torch.zeros(2,6);cmd=torch.zeros(2,3)
    obs={'policy':q,'history':h};before=(q.clone(),h.clone());pre=torch.ones(2,19);post=torch.ones(2,19)*2
    rows=concatenate(obs,a,cmd,pre,post)
    assert rows.shape==(2,CHANNELS) and torch.equal(q,before[0]) and torch.equal(h,before[1])
    record={'effective_protocol':{'scored_envs':2},'paired_state':{'axes':list(AXES),'schema_version':paired_version,
        'groups':paired_groups,'rows':[rows.tolist()],'valid':[[True,True]]}}
    assert group(paired_tensor(record),'actor_policy_25D').shape==(1,2,25)
    request={'checkpoint':'model.pt','sha256':'a'*64,'target':[0,0],'diagnostic_profile':'paired_state'}
    assert motion_request(request)['diagnostic_profile']=='paired_state'
    s['task']='recovery'
    with pytest.raises(ValueError):storage_plan(s,full=True)


def test_actual_recorder_keeps_pre_action_and_pre_reset_validity():
    from native_stand.command_v6.tools.test_resources import source_file
    import ast
    tree=ast.parse(source_file('command_v6/tools/evaluate_checkpoint.py').read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_actor')
    text=ast.unparse(fn)
    assert text.index("actor_inputs =")<text.index('wrapped.step')
    assert 'buffer.active & ~dones' in text
    assert 'paired_state' in text and 'root_geometry' in text
    assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='actor' for n in ast.walk(fn))==1


def test_legacy_flag_does_not_allow_contradictory_declared_axis():
    r=control();r['control_diagnostics'].pop('schema_version')
    r['control_diagnostics']['axes']=['scored_env','policy_time','channel']
    with pytest.raises(ValueError):control_tensor(r,allow_legacy_axes=True)
