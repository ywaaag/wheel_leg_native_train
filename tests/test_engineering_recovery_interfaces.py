FROZEN_TEST_SCOPE='PORTABLE'
import pytest
import torch
from native_stand.command_v6.domain.experiment_identity import sections
from native_stand.command_v6.tools.execution_identity import execution_dependencies
from native_stand.command_v6.tools.update_proof import compare


def test_motion_scope_excludes_recovery_but_preserves_behavior_dependencies():
    before={'env.py':'a','recovery/runtime.py':'r','command_v6/domain/protocol.py':'p'}
    after={**before,'recovery/runtime.py':'changed'}
    assert execution_dependencies(before,'motion')['modules_sha256']==execution_dependencies(after,'motion')['modules_sha256']
    assert execution_dependencies(before,'motion')['excluded_modules']!=execution_dependencies(after,'motion')['excluded_modules']
    assert execution_dependencies(before,'recovery')!=execution_dependencies(after,'recovery')
    after['env.py']='changed'
    assert execution_dependencies(before,'motion')!=execution_dependencies(after,'motion')


def test_budget_metadata_is_not_behavior_recipe():
    a={'reward':{'w':1},'motion_posture':{'chain_wall_s':100,'acceptance':{'tilt':.2}},'budget':{'formal_updates':10}}
    b={'reward':{'w':1},'motion_posture':{'chain_wall_s':200,'acceptance':{'tilt':.2}},'budget':{'formal_updates':20}}
    assert sections(a)['behavior']==sections(b)['behavior']
    b['reward']['w']=2
    assert sections(a)['behavior']!=sections(b)['behavior']


def test_saved_update_proof_survives_absent_progress(tmp_path):
    old=tmp_path/'source.pt';new=tmp_path/'candidate.pt'
    torch.save({'actor':{'w':torch.zeros(2)}},old)
    torch.save({'actor':{'w':torch.ones(2)},'update':1,'asset_sha256':'a','spec_sha256':'s'},new)
    proof=compare(old,new)
    assert proof['actor_parameters_changed'] and proof['update']==1
    assert not (tmp_path/'progress.json').exists()


def test_group_policy_explicit_not_fixed_order():
    from native_stand.command_v6.domain.evaluation_requests import motion_request
    r={'checkpoint':'model.pt','sha256':'a'*64,'target':[.5,0],'evaluation_group':'source_regression','on_group_failure':'stop'}
    assert motion_request(r)['on_group_failure']=='stop'
    with pytest.raises(ValueError):motion_request({**r,'on_group_failure':'guess'})


def test_light_window_uses_shared_parser_not_full_motion_none():
    from native_stand.command_v6.domain.posture_geometry import diagnostic_window
    p=diagnostic_window({'motion_window_s':None,'steady_window_s':[2,4]},[.5,0],total_samples=400,dt=.01)
    assert p['index_half_open']==[199,400] and not p['full_motion_window_declared']


def test_recovery_missing_evidence_never_ready(tmp_path):
    from native_stand.command_v6.tools.prepare_engineering_recovery import plan
    result=plan(tmp_path/'failed',tmp_path/'supplement',tmp_path/'spec.json',tmp_path/'ledger.json',tmp_path/'review.json')
    assert result['status']=='MISSING' and result['authorization']=='UNAUTHORIZED'
    assert not list(tmp_path.iterdir())
