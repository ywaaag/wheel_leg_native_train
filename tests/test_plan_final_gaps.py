"""Actual engineering paths for previously overstated plan completion."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy,json
from pathlib import Path
import pytest
import torch
from native_stand.command_v6.tools.submission_receipt import digest,stable


def test_chain_report_keeps_receipt_references_not_payload(tmp_path):
 from native_stand.command_v6.stand_chain import chain_report
 spec=tmp_path/'spec.json';spec.write_text(json.dumps({'ppo':{'envs':2,'steps_per_env':4}}))
 book={'limits':{'formal':10},'used':{'smoke':1,'formal':2},'attempts':{'one':{'phase':'formal','status':'COMPLETED','updates':2,'submission_receipt':{'record':{'requested':{'large':'x'*200000}},'sha256':'a'*64}}}}
 spec.with_name('budget.json').write_text(json.dumps(book));before=spec.with_name('budget.json').read_bytes()
 chain=tmp_path/'chain';chain.mkdir();(chain/'manifest.json').write_text(json.dumps({'attempt_id':'chain'}))
 chain_report(chain,spec,[],'COMPLETED',None,None)
 result=json.loads((chain/'analysis.json').read_text())
 assert result['formal_updates']==2 and result['formal_samples']==16
 row=result['budget']['attempts']['one'];assert 'submission_receipt' not in row
 assert row['submission_receipt_reference']['sha256']=='a'*64
 assert (chain/'analysis.json').stat().st_size<10000
 assert spec.with_name('budget.json').read_bytes()==before


def test_optimizer_capture_is_opt_in_exact_and_rng_neutral(tmp_path):
 from native_stand.command_v6.tools.optimizer_capture import capture
 from native_stand.command_v6.domain.artifact_policy import validate
 actor=torch.nn.Linear(3,6);critic=torch.nn.Linear(3,1)
 optimizer=torch.optim.Adam([*actor.parameters(),*critic.parameters()],lr=3e-5)
 rng=torch.get_rng_state().clone();before=copy.deepcopy(actor.state_dict());state=copy.deepcopy(optimizer.state_dict())
 spec={'budget':{'formal_updates':5},'artifacts':{}}
 assert capture(tmp_path,spec,'formal',1,actor,critic,optimizer) is None
 assert not list(tmp_path.iterdir())
 spec['artifacts']['optimizer_capture']={'version':'optimizer_capture_v1','updates':{'formal':[2]},'max_bytes':1000000}
 assert capture(tmp_path,spec,'formal',1,actor,critic,optimizer) is None
 evidence=capture(tmp_path,spec,'formal',2,actor,critic,optimizer)
 saved=torch.load(evidence['path'],map_location='cpu',weights_only=False)
 assert saved['completed_updates']==1 and saved['optimizer']==state
 assert torch.equal(rng,torch.get_rng_state())
 assert all(torch.equal(value,actor.state_dict()[name]) for name,value in before.items())
 with pytest.raises(FileExistsError):capture(tmp_path,spec,'formal',2,actor,critic,optimizer)
 spec['artifacts']['optimizer_capture']['updates']['formal']=[2,3]
 spec['artifacts']['optimizer_capture']['max_bytes']=1
 with pytest.raises(OSError):capture(tmp_path,spec,'formal',3,actor,critic,optimizer)
 assert not (tmp_path/'optimizer_before_update_3.pt').exists()
 spec['artifacts']['optimizer_capture']['updates']['formal']=[6]
 with pytest.raises(ValueError):validate(spec)


def pruning_fixture(tmp_path):
 from native_stand.command_v6.tools.checkpoint_lifecycle import prune_owned
 run=tmp_path/'run';run.mkdir();spec={'artifacts':{'checkpoint_retention':{'version':'checkpoint_retention_v1','keep_last':1,'milestone_updates':[]}}}
 inventory=[]
 for update in range(3):
  path=run/f'model_update_{update}.pt';path.write_text(str(update));inventory.append({'path':str(path),'sha256':digest(path),'update':update})
 (run/'checkpoint_inventory.json').write_text(json.dumps(inventory))
 record={'requested':spec,'attempt_id':'one','output_dir':str(run),'spec_path':str(tmp_path/'spec.json')}
 (run/'submission_receipt.json').write_text(json.dumps({'record':record,'sha256':stable(record)}))
 (tmp_path/'budget.json').write_text(json.dumps({'attempts':{'one':{'status':'RUNNING','output_dir':str(run)}}}))
 return run,spec,inventory


def test_interrupted_pruning_reconciles_only_persisted_intent(tmp_path,monkeypatch):
 from native_stand.command_v6.tools import checkpoint_lifecycle as tool
 run,spec,inventory=pruning_fixture(tmp_path)
 import native_stand.command_v6.completion as completion
 actual=completion.write;calls=0
 def fail_after_delete(path,value):
  nonlocal calls
  if Path(path).name=='checkpoint_inventory.json':
   calls+=1
   if calls==2:raise OSError('crash after unlink')
  return actual(path,value)
 monkeypatch.setattr(completion,'write',fail_after_delete)
 with pytest.raises(OSError):tool.prune_owned(run,spec,attempt_id='one')
 assert not Path(inventory[1]['path']).exists()
 assert tool.plan(run,spec)['pending_removed'][0]['update']==1
 monkeypatch.setattr(completion,'write',actual)
 assert tool.prune_owned(run,spec,attempt_id='one')['reconciled_removals']==1
 assert json.loads((run/'checkpoint_inventory.json').read_text())[1]['removed']
 Path(inventory[2]['path']).unlink()
 with pytest.raises(ValueError,match='identity'):tool.plan(run,spec)


def test_student_diagnostic_preparer_requires_explicit_inputs_and_teacher_identity(tmp_path,monkeypatch):
 import importlib.util
 script=Path(__file__).resolve().parents[1]/'scripts/prepare_student_validation.py'
 module_spec=importlib.util.spec_from_file_location('prepare_validation_test',script)
 tool=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(tool)
 with pytest.raises(TypeError):tool.prepare()
 parent=tmp_path/'parent.json';parent.write_text(json.dumps({'interface_version':'wrong'}))
 with pytest.raises(ValueError,match='interface'):
  tool.prepare(parent_spec=parent,recovery_checkpoint='missing',motion_checkpoint='missing',dataset_manifest='missing',interface_version='multiskill_mcu_v2')
 import native_stand.students.model as student_model
 rec=tmp_path/'rec.pt';mot=tmp_path/'mot.pt';rec.write_text('rec');mot.write_text('mot')
 manifest=tmp_path/'manifest.json';dataset=tmp_path/'dataset.pt';dataset.write_text('dataset')
 manifest.write_text(json.dumps({'interface_version':'multiskill_mcu_v2','RecoveryStudent':{'file':'dataset.pt','sha256':digest(dataset)},'MotionZeroStudent':{'file':'dataset.pt','sha256':digest(dataset)}}))
 monkeypatch.setattr(student_model,'load',lambda path,role:(None,{'role':role,'interface_version':'multiskill_mcu_v2','manifest_sha256':digest(manifest),'dataset_sha256':digest(dataset)}))
 parent.write_text(json.dumps({'interface_version':'multiskill_mcu_v2','student_teachers':[]}))
 with pytest.raises(ValueError,match='two distinct teachers'):
  tool.prepare(parent_spec=parent,recovery_checkpoint=rec,motion_checkpoint=mot,dataset_manifest=manifest,interface_version='multiskill_mcu_v2')
 assert not list(tmp_path.glob('configs/**'))


def test_student_compact_course_path_has_no_unbound_candidate_assignment():
 # The actual evaluate_cases compact branch previously wrote a not-yet-created candidate.
 import ast
 from native_stand.students import training
 tree=ast.parse(Path(training.__file__).read_text())
 function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='evaluate_cases')
 assert not any(isinstance(node,ast.Name) and node.id=='candidate' for node in ast.walk(function))


def test_submission_plan_separates_configuration_permission_and_resources(tmp_path,monkeypatch):
 from types import SimpleNamespace
 from native_stand.command_v6.supervisor import submission_readiness
 monkeypatch.setenv('HAPI_SESSION_ID','owner')
 args=SimpleNamespace(spec=tmp_path/'spec.json',output_dir=tmp_path/'new',formal_only=False,evaluation_only=False,hapi_session='owner',physical_gpu=0,resource_policy={'mode':'exclusive'})
 result=submission_readiness(args,{'authorization':{'status':'UNAUTHORIZED'},'device':{'physical_index':0}},
  {'status':'READY_NEEDS_AUTH','config_valid':True,'authorized':False,'prerequisites_ready':True,'reason_code':'AUTHORIZATION_MISSING'})
 assert result['config_valid'] and result['prerequisites_ready']
 assert result['authorized'] is False and result['resource_ready'] is None and not result['submit_ready']


def test_analysis_selection_summary_does_not_repeat_environment_certificate(tmp_path,monkeypatch):
 from native_stand.command_v6.stand_chain import chain_report
 source=tmp_path/'spec.json';source.write_text(json.dumps({'ppo':{'envs':1,'steps_per_env':1}}))
 source.with_name('budget.json').write_text(json.dumps({'used':{'smoke':0,'formal':1},'limits':{'formal':2}}))
 chain=tmp_path/'chain';chain.mkdir();phase=chain/'formal';phase.mkdir()
 (chain/'manifest.json').write_text(json.dumps({'attempt_id':'owner'}))
 choice={'accepted_candidate':{'checkpoint':'candidate.pt','checkpoint_sha256':'a'*64,'per_env':[{'accepted':True,'values':[0]*1000}]}}
 (phase/'candidate_selection.json').write_text(json.dumps(choice))
 chain_report(chain,source,[{'phase':'formal','run':str(phase),'terminal':{},'status':'COMPLETED','exit_code':0}],'COMPLETED',None,None)
 analysis=json.loads((chain/'analysis.json').read_text())
 assert 'per_env' not in analysis['candidate_selection']['accepted_candidate']
 ref=analysis['candidate_selection_reference']
 assert digest(ref['path'])==ref['sha256']
 assert json.loads(Path(ref['path']).read_text())==choice
