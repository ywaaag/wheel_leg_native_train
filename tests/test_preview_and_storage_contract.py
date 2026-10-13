FROZEN_TEST_SCOPE='PORTABLE'
import copy
import json
from pathlib import Path
import pytest
import torch
from tensordict import TensorDict
from native_stand.command_v6.domain.environment_mode import resolve
from native_stand.command_v6.runtime.execution_mode import apply
from native_stand.command_v6.tools.runtime_cleanup import run
from native_stand.command_v6.tools.evaluation_storage import read,write


def test_explicit_modes_partial_reset_and_preview_quota():
    class Env:
        num_envs=1;recovery_config={'active_family':'R0'};family='R0';curriculum_training=True
        def select_initial_family(self,family,split):self.family=family;self.split=split
        def reset(self,ids=None):
            assert not self.curriculum_training
            assert self.split=='holdout' and self.execution_mode=='preview'
    env=Env();plan=apply(env,'preview',family='Swing')
    env.reset();env.reset([0]);assert plan['family']=='Swing'
    apply(env,'training');assert env.curriculum_training
    for mode in ('evaluation','preview'):
        assert not resolve(mode,envs=1)['curriculum_training']
    with pytest.raises(ValueError):resolve('preview',envs=64)
    with pytest.raises(ValueError):resolve('guess',envs=1)


def test_cleanup_preserves_original_and_attempts_app_close():
    error=ValueError('original reset error');called=[]
    def bad():raise RuntimeError('cleanup error')
    results=run([('env',bad),('app',lambda:called.append('app'))],primary_error=error)
    assert called==['app'] and results[0]['step']=='env'
    assert 'cleanup error' in error.__notes__[0]
    with pytest.raises(RuntimeError,match='Runtime cleanup failed'):run([('env',bad)])


def test_task_distribution_isolated_and_preview_identity_preserves_rng(tmp_path):
    from native_stand.command_v6.tools.model_factory import model
    from native_stand.command_v6.tools.preview_plan import model_identity
    from native_stand.command_v6.domain.action_distribution import declaration
    spec={'task':'recovery','source_input_dim':150,'action':{'wheel_scale_rad_s':100},'recovery':{},'ppo':{'hidden_dims':[4,4]},'action_distribution':declaration()}
    obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
    actor=model(obs,actor=True,spec=spec)
    checkpoint=tmp_path/'model.pt';torch.save({'actor':actor.state_dict()},checkpoint)
    rng=torch.get_rng_state().clone();identity=model_identity(spec,checkpoint,family='Swing')
    assert torch.equal(rng,torch.get_rng_state())
    assert identity['class'].startswith('native_stand.recovery.learning_distribution:')
    assert identity['version']==declaration()['version'] and identity['pose_family']=='Swing'
    base=copy.deepcopy(spec);base.pop('action_distribution');base['task']='motion'
    plain=model(obs,actor=True,spec=base);plain.load_state_dict(actor.state_dict(),strict=True)
    assert type(plain.distribution).__module__=='rsl_rl.modules.distribution'
    assert list(plain.state_dict())==list(actor.state_dict())


def test_trace_roundtrip_summary_size_sha_and_no_pickle(tmp_path):
    path=tmp_path/'evaluation.json';rows=[[float(i),None,0.] for i in range(5000)]
    original={'asset_sha256':'asset','per_env':[{'env_id':0,'success':False,
        'compact_trace_100hz':rows,'failed_checks':['tilt']}], 'effective_protocol':{'scored_envs':1}}
    sizes=write(path,original);stored=json.loads(path.read_text())
    assert sizes['arrays']==1 and sizes['json_bytes']<5000
    assert stored['per_env'][0]['success'] is False
    hydrated=read(path);hydrated.pop('numeric_trace_storage')
    assert hydrated==original
    assert original['per_env'][0]['compact_trace_100hz']==rows
    with pytest.raises(FileExistsError):write(path,original)
    artifact=path.with_suffix('.traces.npz');artifact.write_bytes(artifact.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='SHA differs'):read(path)


def test_legacy_evidence_and_path_escape(tmp_path):
    p=tmp_path/'old.json';old={'per_env':[{'trace':[[1,2]]}]};p.write_text(json.dumps(old));assert read(p)==old
    p.write_text(json.dumps({'numeric_trace_storage':{'version':'evaluation_numeric_npz_v1','path':'../outside.npz'}}))
    with pytest.raises(ValueError,match='escapes'):read(p)


def test_loader_hydrates_raw_identity_bound_traces(tmp_path):
    from native_stand.command_v6.tools.evaluation_loader import load
    from native_stand.command_v6.tools.experiment_preparation import digest
    result={'spec_sha256':'s','checkpoint_sha256':'c','asset_sha256':'a',
        'per_env':[{'env_id':0,'compact_trace_100hz':[[1.,2.],[3.,4.]]}]}
    write(tmp_path/'eval.json',result)
    (tmp_path/'manifest.json').write_text(json.dumps({'spec_sha256':'s','asset_sha256':'a'}))
    raw,ref=load(tmp_path,{'checkpoint_sha256':'c','evaluation':'eval.json','evaluation_sha256':digest(tmp_path/'eval.json')},
        spec_sha256='s',checkpoint_sha256='c',asset_sha256='a')
    assert raw['per_env'][0]['compact_trace_100hz']==result['per_env'][0]['compact_trace_100hz']
    assert ref['sha256']==digest(tmp_path/'eval.json')


def test_all_new_public_tools_are_documented():
    # Portable fixture checks tool names; repo integration checks doc paths separately.
    from native_stand.command_v6.tools.entrypoints import ENTRIES
    wanted={'scripts/audit_recovery_leg_execution.py','scripts/prepare_recovery_bounded_mean_train.py',
        'native_stand.command_v6.tools.play'}
    assert wanted<={e['entry'] for e in ENTRIES if e['status']=='CURRENT'}


def test_mode_restored_on_recovery_reset_exception():
    from types import SimpleNamespace
    from native_stand.command_v6.tools.evaluation_state import isolated_evaluation
    class Env:
        num_envs=1;recovery_config={};family='R0';split='train';curriculum_training=True
        continuous_evaluation=False;capture_terminal=False;execution_mode='training'
        fsm=SimpleNamespace(config={'timeout_s':3.})
        def select_initial_family(self,family,split):self.family=family;self.split=split
        def reset(self):pass
    actor=torch.nn.Linear(1,1);env=Env()
    @isolated_evaluation
    def bad(actor,wrapped,env):
        apply(env,'evaluation');raise ValueError('reset failure')
    with pytest.raises(ValueError,match='reset failure'):bad(actor,None,env)
    assert env.execution_mode=='training' and not env.capture_terminal and env.curriculum_training
    assert env.split=='train' and actor.training


def test_recovery_distribution_changes_do_not_change_motion_scope():
    from native_stand.command_v6.tools.execution_identity import execution_dependencies
    before={'command_v6/learning.py':'same','command_v6/learning_distribution.py':'same',
        'command_v6/tools/model_factory.py':'factory','recovery/learning_distribution.py':'a'}
    after={**before,'recovery/learning_distribution.py':'b'}
    assert execution_dependencies(before,'motion')['modules_sha256']==execution_dependencies(after,'motion')['modules_sha256']
    assert execution_dependencies(before,'recovery')['modules_sha256']!=execution_dependencies(after,'recovery')['modules_sha256']
    after['command_v6/tools/model_factory.py']='changed'
    assert execution_dependencies(before,'motion')['modules_sha256']!=execution_dependencies(after,'motion')['modules_sha256']


def test_registry_write_compacts_all_numeric_traces_without_mutating_raw(tmp_path):
    from native_stand.command_v6.train import _write
    rows=[{'result':{'per_env':[{'wheel_geometry_trace_100hz':[[1,2,3]]}],
        'control_diagnostics':{'rows':[[[1,2,3]]]}}}]
    path=tmp_path/'candidate_registry.json';_write(path,rows)
    summary=json.loads(path.read_text())
    assert summary[0]['result']['per_env'][0]['wheel_geometry_trace_100hz']['raw_array_omitted']
    assert summary[0]['result']['control_diagnostics']['raw_array_omitted']
    assert isinstance(rows[0]['result']['per_env'][0]['wheel_geometry_trace_100hz'],list)
