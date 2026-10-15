FROZEN_TEST_SCOPE='PORTABLE'
import ast,json
from pathlib import Path
from types import SimpleNamespace
import pytest
from native_stand.students.motion_training import declaration,short_wiring,phase_warmup,protocol
from native_stand.students.motion_tracking_reward import QUALITY_VERSION,reward_fields
from native_stand.students.training_recipe import validate_instance
from native_stand.students.training_evidence import smoke_certificate
from native_stand.students.data import sha

def test_short_profile_changes_only_smoke_warmup_and_cannot_enable_v1():
 r=declaration(reward_version=QUALITY_VERSION);r['smoke_wiring']=short_wiring()
 validate_instance(r,r['source_actor_sha256']);assert phase_warmup(r,'smoke')==4 and phase_warmup(r,'formal')==5
 old=declaration();old['smoke_wiring']=short_wiring()
 with pytest.raises(ValueError):validate_instance(old,old['source_actor_sha256'])

def test_real_evaluator_protocol_expression_has_no_free_spec_reference():
 from native_stand.students.motion_training import protocol as training_protocol
 from native_stand.students.motion_quality import VERSION as QUALITY_TERMINATION_VERSION
 tree=ast.parse(Path('src/native_stand/students/evaluator.py').read_text())
 call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='training_protocol')
 code=compile(ast.Expression(call),'<actual evaluator protocol>','eval')
 for quality in (True,False):
  env=SimpleNamespace(quality_config={'version':QUALITY_TERMINATION_VERSION} if quality else {})
  assert eval(code,{'training_protocol':training_protocol,'QUALITY_TERMINATION_VERSION':QUALITY_TERMINATION_VERSION,'env':env})==protocol(quality=quality)

def test_recovery_accepts_only_exact_zero_ppo_quality_reset_fault():
 from native_stand.students.motion_quality_budget import known_zero_ppo_source_fault
 failure={'exception':"RuntimeError('Inplace update to inference tensor outside InferenceMode is not allowed.extra')",'traceback':'motion_quality.py reset self.ticks[ids]=0'}
 row={'status':'FAILED','actual_updates':0,'failure':failure}
 assert known_zero_ppo_source_fault(row)
 assert not known_zero_ppo_source_fault({**row,'actual_updates':1})
 assert not known_zero_ppo_source_fault({**row,'failure':{**failure,'traceback':'unrelated_module.py'}})
 assert not known_zero_ppo_source_fault({**row,'failure':{'exception':'RuntimeError(nonfinite reward)','traceback':'motion_quality.py self.ticks[ids]=0'}})

def test_smoke5_certificate_needs_actual_actor_step_but_never_claims_full_episode(tmp_path):
 def write(name,value):
  p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
 recipe=declaration(reward_version=QUALITY_VERSION);recipe['smoke_wiring']=short_wiring()
 commands=[[0,0],[.5,0],[-.5,0],[1,0],[-1,0]]
 spec={'source_sha256':'a'*64,'reward':recipe['reward'],'student_training':recipe,'motion_training':{'stage':0},'budget':{'smoke_updates':5},'ppo':{'envs':512,'steps_per_env':128},
  'curriculum':{'stages':[{'commands':commands}]},'student_evaluation':{'cases':[{'command':c+[.34]} for c in commands]},'motion_assessment':protocol(quality=True)}
 write('source_snapshot/spec.json',spec);write('manifest.json',{'spec_sha256':sha(tmp_path/'source_snapshot/spec.json'),'source_sha256':'a'*64})
 write('terminal_report.json',{'status':'COMPLETED','actual_updates':5,'failure':None})
 records=[]
 for i,c in enumerate(commands):
  name=f'evaluation_{i:02}.json';write(name,{'case':{'command':c+[.34]},'protocol':spec['motion_assessment'],'per_env':[{'accepted':False}]*8})
  records.append({'path':name,'sha256':sha(tmp_path/name)})
 write('progress.json',{'actual_updates':5,'actor_parameters_changed':True,'checkpoint_roundtrip_verified':True,'evaluations':records})
 rows=[]
 for u in range(1,6):
  rows.append({'update':u,'controlled_samples':65536,'actor_update_scope':{'valid_actor_samples':65536,'invalid_actor_samples':0,'actor_optimizer_steps':16 if u==5 else 0},'actor_changed_this_update':u==5,'critic_changed_this_update':True,'nonzero_rewards':65536,'episode_completed':0,'BC_loss':0,'BC_gradient_norm':None,'BC_updates':0,'std_unchanged':True,'reward_fields':list(reward_fields(spec['reward'])),'hold_sample_counts':[10]*5,'command_episode_counts':[0]*5})
 def metrics(): (tmp_path/'metrics.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 metrics();cert=smoke_certificate(tmp_path,spec);assert cert['status']=='PASSED',cert['errors']
 assert not cert['coverage']['full_training_episode_verified'] and not cert['coverage']['training_reset_observed']
 rows[-1]['actor_changed_this_update']=False;metrics();assert smoke_certificate(tmp_path,spec)['status']=='FAILED'
