"""Portable producer/consumer contracts for remaining plan engineering work."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy,json
from pathlib import Path
import pytest
import torch
from native_stand.command_v6.domain.execution_limits import ExecutionLimits,validate_budget
from native_stand.command_v6.tools.model_adapter import ModelAdapter
from native_stand.command_v6.tools import artifact_io


def limits_spec():
 return {'ppo':{'envs':4,'steps_per_env':8},'budget':{'smoke_updates':2,'formal_updates':8,'sample_limit':320,'source_eval_wall_s':90,'smoke_wall_s':None,'formal_wall_s':None,'chain_wall_s':None}}


def test_update_only_limits_not_bound_to_reward_version():
 s=limits_spec();assert validate_budget(s)['updates']==10
 for phase in ('smoke','formal'):
  limits=ExecutionLimits.resolve(s,phase)
  assert limits.wall_s is None and limits.deadline(100)==float('inf')
  assert limits.monitor_bound(60)==60
 assert ExecutionLimits.resolve(s,'source_eval').wall_s==90
 assert s==limits_spec()


@pytest.mark.parametrize('value',[True,0,-1,float('inf'),float('nan'),'100'])
def test_invalid_wall_values_rejected(value):
 s=limits_spec();s['budget']['formal_wall_s']=value
 with pytest.raises(ValueError):ExecutionLimits.resolve(s,'formal')


def test_zero_updates_no_unbounded_evaluation_and_sample_inconsistency():
 s=limits_spec();s['budget']['formal_updates']=0
 with pytest.raises(ValueError):ExecutionLimits.resolve(s,'formal')
 s['budget']['sample_limit']=1
 with pytest.raises(ValueError):validate_budget(s)
 s=limits_spec();s['budget']['source_eval_wall_s']=None
 with pytest.raises(ValueError):ExecutionLimits.resolve(s,'source_eval')
 s=limits_spec();s['budget']['formal_wall_s']=100
 with pytest.raises(ValueError):ExecutionLimits.resolve(s,'formal').monitor_bound(101)


def test_real_actor_bc_metadata_health_and_strict_load_agree(tmp_path):
 from native_stand.command_v6.tools.health_check import checkpoint_metadata
 from native_stand.students.model import Student
 from native_stand.command_v6.tools.model_factory import model
 actor=Student(True,version='multiskill_mcu_v2')
 data={'interface_version':'multiskill_mcu_v2','role':'RecoveryStudent','actor':actor.state_dict(),'dataset_sha256':'d','manifest_sha256':'m','offline_bc_steps':10}
 path=tmp_path/'bc.pt';torch.save(data,path)
 before=torch.get_rng_state().clone();metadata=checkpoint_metadata(path)
 assert torch.equal(before,torch.get_rng_state())
 assert metadata['actor_input_shape']==[128,31] and metadata['critic_input_shape'] is None
 assert metadata['missing_optional']==['critic','optimizer']
 target=model(None,actor=True,spec={'interface_version':'multiskill_mcu_v2'})
 ModelAdapter(data).load(target,'actor')
 x=torch.randn(5,31);torch.testing.assert_close(actor(x),target(x))
 renamed={**data,'actor':{k.replace('mlp.','net.'):v for k,v in data['actor'].items()}}
 assert ModelAdapter(renamed).describe()['actor_input_shape']==[128,31]
 with pytest.raises(ValueError,match='names'):ModelAdapter(renamed).load(target,'actor')
 bad=copy.deepcopy(data);bad['actor']['mlp.0.weight'][0,0]=float('nan')
 with pytest.raises(ValueError,match='nonfinite'):ModelAdapter(bad).describe()


def test_checkpoint_atomic_failure_preserves_previous_and_removes_temp(tmp_path):
 path=tmp_path/'model.pt';artifact_io.checkpoint(path,{'old':torch.ones(2)})
 before=path.read_bytes()
 def fail(stream):stream.write(b'partial');raise OSError('disk failure')
 with pytest.raises(OSError):artifact_io.atomic(path,fail)
 assert path.read_bytes()==before and not list(tmp_path.glob('*.tmp'))


def test_policy_protects_sources_evidence_latest_and_milestones(tmp_path):
 from native_stand.command_v6.tools.checkpoint_lifecycle import plan,prune_owned
 from native_stand.command_v6.tools.submission_receipt import digest,stable
 run=tmp_path/'run';run.mkdir();spec={'source_checkpoint':str(tmp_path/'source.pt'),'artifacts':{'checkpoint_retention':{'version':'checkpoint_retention_v1','keep_last':1,'milestone_updates':[2]}}}
 rows=[]
 for update in range(5):
  path=run/f'model_update_{update}.pt';path.write_bytes(str(update).encode());rows.append({'path':str(path),'sha256':digest(path),'update':update})
 (run/'checkpoint_inventory.json').write_text(json.dumps(rows))
 (run/'candidate_registry.json').write_text(json.dumps([{'checkpoint':rows[1]['path']}]))
 (run/'progress.json').write_text(json.dumps({'latest_checkpoint':rows[4]}))
 assert [r['update'] for r in plan(run,spec)['remove']]==[3]
 # An owned running exact attempt plus bound requested policy are required.
 record={'attempt_id':'one','output_dir':str(run),'spec_path':str(tmp_path/'spec.json'),'requested':spec}
 (run/'submission_receipt.json').write_text(json.dumps({'record':record,'sha256':stable(record)}))
 (tmp_path/'budget.json').write_text(json.dumps({'attempts':{'one':{'status':'COMPLETED','output_dir':str(run)}}}))
 with pytest.raises(ValueError,match='active exact'):prune_owned(run,spec,attempt_id='one')
 assert Path(rows[3]['path']).is_file()
 (tmp_path/'budget.json').write_text(json.dumps({'attempts':{'one':{'status':'RUNNING','output_dir':str(run)}}}))
 assert prune_owned(run,spec,attempt_id='one')['files_removed']==1
 assert [r['update'] for r in plan(run,spec)['retain']]==[0,1,2,4]
 assert not Path(rows[3]['path']).exists()
 assert plan(run,{})['remove']==[]


def test_recipe_source_cadence_and_limits_are_instance_fields():
 from native_stand.students.training_recipe import declaration,validate_instance,STANDING_RECIPE
 recipe=declaration(STANDING_RECIPE)
 recipe.update(source_actor_sha256='a'*64,milestones=[25,75],selected_rollouts_smoke=[],selected_rollouts_formal=[25],storage_max_bytes=512*2**20)
 assert validate_instance(recipe,'a'*64)==recipe
 bad=copy.deepcopy(recipe);bad['reward']['version']='unknown'
 with pytest.raises(ValueError):validate_instance(bad,'a'*64)
 bad=copy.deepcopy(recipe);bad['BC_coefficient']=1.
 with pytest.raises(ValueError):validate_instance(bad,'a'*64)
 for milestones in ([2,1],[1,1],[0],[True]):
  bad=copy.deepcopy(recipe);bad['milestones']=milestones
  with pytest.raises(ValueError):validate_instance(bad,'a'*64)
 assert validate_budget(limits_spec())['updates']==10


def test_declared_log_and_storage_ceiling_keep_terminal_reserve(tmp_path):
 from native_stand.command_v6.domain.artifact_policy import validate
 s={'artifacts':{'runtime_log':{'max_bytes':8,'backups':2},'storage_max_bytes':100,'terminal_reserve_bytes':10}}
 assert validate(s)['runtime_log']['backups']==2
 path=tmp_path/'owner.log'
 artifact_io.rotate_bytes(path,b'0123456789'*4,maximum=8,backups=2)
 assert path.stat().st_size<=8
 assert len(list(tmp_path.glob('owner.log*')))==3
 assert sum(p.stat().st_size for p in tmp_path.iterdir())<=24
 assert artifact_io.runtime_storage(tmp_path,s)['actual_bytes']<=24
 s['artifacts']['storage_max_bytes']=30
 with pytest.raises(OSError):artifact_io.runtime_storage(tmp_path,s)
 s['artifacts']['runtime_log']['max_bytes']=True
 with pytest.raises(ValueError):validate(s)


def test_storage_estimate_consumes_log_and_reserve_declaration(tmp_path):
 from native_stand.command_v6.tools.storage_budget import estimate,check
 spec={'budget':{},'artifacts':{'runtime_log':{'max_bytes':16,'backups':2},'terminal_reserve_bytes':123},'evaluation':{}}
 summary=estimate(spec,'source_eval')
 assert summary['runtime_log_bytes']==48 and summary['terminal_reserve_bytes']==123
 spec['artifacts']['storage_max_bytes']=1000
 assert check(spec,tmp_path,'source_eval')['status']=='DECLARED_STORAGE_TOO_SMALL'


def test_CPU_reuse_checks_dependencies_not_only_interpreter(tmp_path,monkeypatch):
 from native_stand.command_v6.tools import validate_cpu,source_identity
 path=tmp_path/'spec.json';path.write_text('{}')
 monkeypatch.setattr(source_identity,'dependencies',lambda:{'torch':'old'})
 report=validate_cpu.validate(path,tmp_path/'no-write')
 prior=tmp_path/'prior';prior.mkdir();(prior/'validation_result.json').write_text(json.dumps({**report,'passed':True}))
 monkeypatch.setattr(source_identity,'dependencies',lambda:{'torch':'changed'})
 with pytest.raises(ValueError,match='identities differ'):
  validate_cpu.validate(path,tmp_path/'reuse',reuse=prior)
 assert not (tmp_path/'reuse').exists()


def test_checkpoint_cleanup_rejects_policy_tampering_and_foreign_inventory(tmp_path):
 from native_stand.command_v6.tools.checkpoint_lifecycle import plan,prune_owned
 from native_stand.command_v6.tools.submission_receipt import stable,digest
 run=tmp_path/'run';run.mkdir();cp=tmp_path/'foreign.pt';cp.write_bytes(b'keep')
 policy={'version':'checkpoint_retention_v1','keep_last':1,'milestone_updates':[]}
 spec={'artifacts':{'checkpoint_retention':policy}}
 (run/'checkpoint_inventory.json').write_text(json.dumps([{'path':str(cp),'sha256':digest(cp),'update':1}]))
 with pytest.raises(ValueError,match='escapes'):plan(run,spec)
 assert cp.read_bytes()==b'keep'
 record={'requested':spec,'attempt_id':'one','output_dir':str(run),'spec_path':str(tmp_path/'spec.json')}
 (run/'submission_receipt.json').write_text(json.dumps({'record':record,'sha256':stable(record)}))
 changed=copy.deepcopy(spec);changed['artifacts']['checkpoint_retention']['keep_last']=2
 with pytest.raises(ValueError,match='policy differs'):prune_owned(run,changed,attempt_id='one')
 assert cp.is_file()


def test_monitor_owns_bounded_log_pump_on_CPU_child(tmp_path,monkeypatch):
 import os,sys,subprocess
 from native_stand.command_v6 import monitor
 spec=limits_spec();spec['evaluation']={};spec['artifacts']={'runtime_log':{'max_bytes':8,'backups':2}}
 path=tmp_path/'spec.json';path.write_text(json.dumps(spec));output=tmp_path/'formal';output.mkdir()
 # Existing owner/settlement functions are intercepted: subprocess executes CPU print only.
 args=['monitor','--spec',str(path),'--phase','formal','--output-dir',str(output),'--attempt-id','one']
 reader,writer=os.pipe();args+=['--handshake-fd',str(writer)]
 monkeypatch.setattr(sys,'argv',args)
 actual=subprocess.Popen;commands=[]
 def cpu_child(command,**kwargs):
  commands.append(command)
  return actual([sys.executable,'-c',"print('x'*100)"],**kwargs)
 monkeypatch.setattr(monitor.subprocess,'Popen',cpu_child)
 monkeypatch.setattr(monitor,'reconcile',lambda *a:{'status':'COMPLETED','reconciled':True})
 (tmp_path/'budget.json').write_text(json.dumps({'attempts':{'one':{'started_unix_s':0,'updates':0}}}))
 monkeypatch.setattr(monitor,'finalize_report',lambda *a:None)
 monkeypatch.setattr(monitor,'notify',lambda *a:None)
 try:assert monitor.main()==0
 finally:os.close(reader)
 assert commands and commands[0][0]!='timeout' # explicit null has no hidden deadline
 assert len(list(tmp_path.glob('formal.runtime.log*')))==3
 assert sum(p.stat().st_size for p in tmp_path.glob('formal.runtime.log*'))<=24
 assert json.loads((output/'monitor_exit.json').read_text())['status']=='COMPLETED'


def test_update_only_submission_package_uses_identity_reference(tmp_path):
 from native_stand.command_v6.tools.submission_preparation import package
 path=tmp_path/'spec.json';spec=limits_spec();spec.update(experiment='cpu',device={'physical_index':0,'uuid':'GPU-fixture'})
 path.write_text(json.dumps(spec));(tmp_path/'budget.json').write_text(json.dumps({'authorization':'UNAUTHORIZED','attempts':{},'used':{'smoke':0,'formal':0},'limits':{'source_eval':1,'smoke':2,'formal':8}}))
 directory=tmp_path/'validation';directory.mkdir();(directory/'identity.json').write_text(json.dumps({'scope':'CPU test record'}))
 report={'passed':True,'tests':[],'schema':{'returncode':0},'plan_only':{'command':['CPU plan'],'returncode':0,'stdout':'{}','run_created':False}}
 result=package(path,directory,report)
 root=Path(result['path']);template=json.loads((root/'authorization_template.json').read_text())
 assert template['max_phase_wall_s'] is None and template['max_online_updates']==10
 assert json.loads((root/'identity.json').read_text())['source_identity_reference']==str(directory/'identity.json')
 assert json.loads((root/'budget.json').read_text())['attempts']=={}
 assert not result['submitted']


def test_student_storage_rejects_conflicting_duplicate_ceiling():
 from native_stand.students.artifacts import storage
 s={'student_training':{'storage_max_bytes':1024},'student_evaluation':{'max_output_bytes':100},'artifacts':{'terminal_reserve_bytes':32,'storage_max_bytes':1024}}
 assert storage(s)['chain_max_bytes']==1024
 s['artifacts']['storage_max_bytes']=2048
 with pytest.raises(ValueError,match='conflicting'):storage(s)


def test_model_validation_requires_explicit_interface_and_resume_state():
 from native_stand.students.model import Student
 data={'actor':Student(True,version='multiskill_mcu_v2').state_dict(),'interface_version':'multiskill_mcu_v2'}
 adapter=ModelAdapter(data)
 assert adapter.validate({'interface_version':'multiskill_mcu_v2'})['actor_output_dim']==6
 with pytest.raises(ValueError,match='interface'):adapter.validate({'interface_version':'multiskill_student_v1'})
 with pytest.raises(ValueError,match='optimizer'):adapter.validate(require_optimizer=True)
 wrong=copy.deepcopy(data);wrong['actor']['mlp.6.weight']=wrong['actor']['mlp.6.weight'][:4]
 with pytest.raises(ValueError,match='six'):ModelAdapter(wrong).validate()
