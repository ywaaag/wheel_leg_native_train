import json
import pytest

from native_stand.command_v6.domain.resource_policy import resolve_resources
from native_stand.command_v6.tools.health_check import submission_health
from native_stand.command_v6.completion import choose
from test_completion import candidate,EXPECTED


@pytest.mark.parametrize('name',['/usr/NX/bin/nxnode.bin','python','unclassified_owner'])
def test_exclusive_resource_mode_never_uses_process_name_whitelist(name):
    report={'findings':[],'gpu':{'status':'OK','devices':[{'index':1,'uuid':'GPU-1'}],
        'compute_processes':[{'pid':7,'gpu_uuid':'GPU-1','process_name':name}]}}
    with pytest.raises(ValueError,match='RESOURCE_OCCUPIED'):
        submission_health(report,current_session='now',target_session='now',physical_gpu=1)
    policy=resolve_resources({'resources':{'mode':'shared','sharing_authorized':True,
        'authorization_note':'explicit user permission for concurrent use'}})
    result=submission_health(report,current_session='now',target_session='now',physical_gpu=1,resource_policy=policy)
    assert result['resource_policy']==policy and result['gpu_snapshot']==report['gpu']
    assert not result['preemption']


@pytest.mark.parametrize('declaration',[{'mode':'shared'}, {'mode':'shared','sharing_authorized':True},
    {'mode':'shared','sharing_authorized':'yes','authorization_note':'user'}, {'mode':'magic'},
    {'mode':'shared','sharing_authorized':True,'authorization_note':' '}])
def test_shared_resources_require_valid_explicit_consent(declaration):
    with pytest.raises(ValueError):resolve_resources({'resources':declaration})


def test_resource_policy_does_not_bypass_authorization_identity_or_unknown_gpu():
    policy=resolve_resources({},mode='shared',sharing_authorization='user permits sharing')
    for report in ({'findings':[],'gpu':{'status':'UNKNOWN'}},
        {'findings':[{'reason_code':'IDENTITY_ERROR'}],'gpu':{'status':'OK','devices':[{'index':1,'uuid':'GPU-1'}]}}):
        with pytest.raises(ValueError):submission_health(report,current_session='now',target_session='now',physical_gpu=1,resource_policy=policy)
    with pytest.raises(ValueError,match='HAPI'):submission_health({'findings':[]},current_session='now',target_session='old',resource_policy=policy)


def test_source_best_overall_is_not_best_new_and_latest_can_be_unreviewed():
    source=candidate('source',drift=.01,role='source')
    new=candidate('new',drift=.15)
    latest={'path':'not_evaluated','sha256':'not_evaluated'}
    result=choose([source,new],latest,EXPECTED)
    assert result['best_overall_candidate']['checkpoint']=='source'
    assert result['best_new_evaluated_candidate']['checkpoint']=='new'
    assert result['best_observed_candidate']['checkpoint']=='source'
    assert result['accepted_candidate']['checkpoint']=='source'
    assert result['model_roles']['latest']==latest


def test_source_copied_to_candidate_path_not_new_result():
    source=candidate('source',drift=.01,role='source')
    copied=candidate('copy',drift=.01)
    copied['checkpoint_sha256']=EXPECTED['source_sha256']
    result=choose([copied],None,EXPECTED)
    assert result['best_new_evaluated_candidate'] is None
    assert result['best_overall_candidate']['checkpoint']=='copy'


def test_shared_resource_mode_disclosed_by_plan_without_writes(tmp_path,capsys,monkeypatch):
    from native_stand.command_v6 import supervisor
    path=tmp_path/'spec.json';path.write_text('{}')
    monkeypatch.setattr(supervisor,'check',lambda *a:{'status':'PASS'})
    monkeypatch.setattr(supervisor,'inspect_project',lambda *a,**k:{'findings':[]})
    monkeypatch.setattr('sys.argv',['supervisor','--spec',str(path),'--output-dir',str(tmp_path/'run'),
        '--resource-mode','shared','--sharing-authorization','user permits desktop coexistence'])
    supervisor.main()
    result=json.loads(capsys.readouterr().out)
    assert result['resource_policy']['mode']=='shared' and result['files_written']==0
    assert not (tmp_path/'run').exists()
