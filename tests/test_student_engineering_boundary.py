FROZEN_TEST_SCOPE='PORTABLE'
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from native_stand.students import training
from native_stand.students.artifacts import atomic,npz,checkpoint,storage


def test_atomic_tensor_and_npz_writes_keep_previous_on_failure(tmp_path):
 p=tmp_path/'model.pt';checkpoint(p,{'actor':torch.ones(2)});old=p.read_bytes()
 def bad(stream):stream.write(b'partial');raise OSError('ENOSPC fixture')
 with pytest.raises(OSError):atomic(p,bad)
 assert p.read_bytes()==old and not list(tmp_path.glob('.*.tmp'))
 n=tmp_path/'rollout.npz';npz(n,{'a':np.ones((2,3))})
 with np.load(n,allow_pickle=False) as d:assert d['a'].shape==(2,3)
 assert torch.equal(torch.load(p,weights_only=False)['actor'],torch.ones(2))


def test_evaluation_original_error_survives_save_and_close_errors_rng_restored(monkeypatch,tmp_path):
 import sys
 actor=torch.nn.Linear(1,1);rng=torch.get_rng_state().clone()
 class Env:
  ids=[];num_envs=8;reference=torch.zeros(8,6);robot=SimpleNamespace(joint_names=[])
  def close(self):torch.rand(3);raise RuntimeError('cleanup secondary')
 monkeypatch.setattr(training,'environment',lambda *a,**kw:Env())
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.configure',SimpleNamespace(verify_asset_import=lambda s:{}))
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.control_readback',SimpleNamespace(verify=lambda e:{},verify_ground=lambda e,s:{}))
 error=ValueError('original rollout');error.student_partial_arrays={'x':np.zeros((2,8,1))}
 def explode(*a,**kw):torch.rand(7);raise error
 monkeypatch.setattr(training,'rollout',explode)
 monkeypatch.setattr(training,'atomic_npz',lambda *a:(_ for _ in ()).throw(OSError('save secondary')))
 with pytest.raises(ValueError,match='original rollout') as caught:
  training.evaluate_cases({'asset_sha256':'a'},tmp_path,actor,[{'case_id':'test','kind':'student','role':'RecoveryStudent','family':'swing'}])
 assert caught.value is error
 assert any('save secondary' in n for n in error.__notes__) and any('cleanup secondary' in n for n in error.__notes__)
 assert torch.equal(rng,torch.get_rng_state())
 matrix=json.loads((tmp_path/'evaluation_matrix_00.json').read_text())
 assert matrix[0]['fault_trace'] is None and matrix[0]['status']=='INCOMPLETE'


def test_storage_limits_from_declaration():
 spec={'student_training':{'storage_max_bytes':800},'student_evaluation':{'max_output_bytes':300},'artifacts':{'terminal_reserve_bytes':100}}
 assert storage(spec)=={'chain_max_bytes':800,'evaluation_max_bytes':300,'terminal_reserve_bytes':100}
 spec['artifacts']['terminal_reserve_bytes']=900
 with pytest.raises(ValueError):storage(spec)


def test_retired_watcher_rejects_import_call_and_historical_selector_schema(tmp_path):
 # Imported tools follow real module path; no run, notifier or process access.
 from native_stand.command_v6.tools.entrypoints import historical_cli_guard
 with pytest.raises(SystemExit):historical_cli_guard('scripts/watch_recovery_submission.py',[])
 with pytest.raises(SystemExit):historical_cli_guard('scripts/select_recovery_checkpoint.py',[])


def test_storage_classification_is_read_only_and_excludes_runs(tmp_path):
 from native_stand.command_v6.tools.audit_storage import categories
 runs=tmp_path/'runs';runs.mkdir();(runs/'checkpoint.pt').write_bytes(b'protected')
 source=tmp_path/'artifacts'/'cpu'/'source_snapshot';source.mkdir(parents=True);(source/'s.py').write_text('x=1')
 before={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
 result=categories(tmp_path,[runs])
 assert result['file_count']==1 and result['bytes_by_category']['frozen_validation_copy']==3
 assert result['files_deleted']==0
 assert before=={str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_execute_failure_restores_rng_before_app_close_and_records_secondary(monkeypatch,tmp_path):
 import sys,time
 from native_stand.command_v6 import train
 output=tmp_path/'source_eval';specpath=tmp_path/'spec.json'
 spec={'asset_module_root':str(tmp_path),'seed':7,'source_checkpoint':'not-loaded',
       'budget':{'source_eval_wall_s':120},'source_sha256':'source','asset_sha256':'asset',
       'interface_version':'multiskill_mcu_v2','student_training':{'version':'student_recovery_ppo_bc_v1'}}
 specpath.write_text(json.dumps(spec));(tmp_path/'budget.json').write_text(json.dumps({'attempts':{'one':{'status':'RUNNING','output_dir':str(output),'started_unix_s':time.time()}}}))
 rng=torch.get_rng_state().clone();closed=[]
 class App:
  def close(self,**kwargs):
   closed.append(torch.equal(rng,torch.get_rng_state()));torch.rand(2);raise RuntimeError('close secondary')
 monkeypatch.setitem(sys.modules,'isaaclab.app',SimpleNamespace(AppLauncher=lambda *a:SimpleNamespace(app=App())))
 monkeypatch.setattr(train,'record_run_configuration',lambda *a:'cpu-fixture')
 monkeypatch.setattr(train,'install_stop_handlers',lambda:None)
 def fail(*a):torch.rand(4);raise ValueError('original model load')
 monkeypatch.setattr(training,'load',fail)
 args=SimpleNamespace(output_dir=output,phase='source_eval',attempt_id='one',spec=specpath,hapi_session=None,handshake_fd=None)
 assert training.execute(args,spec,{'execution_identity':{}})==1
 report=json.loads((output/'terminal_report.json').read_text())
 assert report['failure']['exception']=="ValueError('original model load')"
 assert json.loads((output/'cleanup.json').read_text())['errors']==["RuntimeError('close secondary')"]
 assert closed==[True] and torch.equal(rng,torch.get_rng_state())


def test_exact_validation_reuse_rejects_stale_inputs_and_copies_only_receipt(monkeypatch,tmp_path):
 from native_stand.command_v6.tools import validate_cpu as validator
 project=tmp_path/'project';source=project/'src/native_stand';source.mkdir(parents=True)
 (source/'x.py').write_text('x=1')
 testdir=project/'tests';testdir.mkdir();(testdir/'conftest.py').write_text('')
 (testdir/'test_one.py').write_text("FROZEN_TEST_SCOPE='PORTABLE'\n")
 spec=project/'spec.json';spec.write_text('{}')
 monkeypatch.setattr(validator,'__file__',str(source/'command_v6/tools/validate_cpu.py'))
 plan=validator.validate(spec,project/'never',['tests/test_one.py'])
 prior=project/'prior';prior.mkdir();(prior/'validation_result.json').write_text(json.dumps({**plan,'passed':True}))
 output=project/'reused';result=validator.validate(spec,output,['tests/test_one.py'],reuse=prior,write=True)
 assert result['passed'] and not (output/'source_snapshot').exists()
 assert (output/'publication_complete.json').exists()
 (source/'x.py').write_text('x=2')
 with pytest.raises(ValueError,match='input identities differ'):
  validator.validate(spec,project/'stale',['tests/test_one.py'],reuse=prior,write=True)
 assert not (project/'stale').exists()
