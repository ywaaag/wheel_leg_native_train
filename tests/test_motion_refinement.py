FROZEN_TEST_SCOPE='PORTABLE'
import copy
import pytest
import torch
from native_stand.students.motion_refinement import initial,advance
from native_stand.students.motion_tracking_reward import configuration,reward,REFINEMENT_VERSION
from native_stand.students.motion_training import declaration
from native_stand.students.training_recipe import validate_instance
from test_motion31_training import inputs

def records(policy,good=True):
 return [{'case':{'command':[v,0.,.34]},'per_env':[{'checks':{k:good for k in policy['required_checks']},
  'tracking':{'MAE':.1,'gain':1.,'direction':1.}} for _ in range(8)]} for v in (0.,.5,-.5)]

def test_refinement_requires_two_complete_safe_same_command_evaluations_and_keeps_wide_floor():
 policy=configuration(REFINEMENT_VERSION)['refinement'];s=initial([[0.,0.],[.5,0.],[-.5,0.]])
 rng=torch.get_rng_state().clone()
 s,_=advance(s,records(policy),policy);assert [r['mix'] for r in s]==[0,0,0]
 s,_=advance(s,records(policy),policy);assert [r['mix'] for r in s]==[0,.25,.25]
 for _ in range(20):s,_=advance(s,records(policy),policy)
 assert [r['mix'] for r in s]==[0,.75,.75] and torch.equal(rng,torch.get_rng_state())
 broken=records(policy);broken[1]['per_env'][0]['checks']['contact']=False
 next_s,d=advance(s,broken,policy);assert next_s[1]['mix']==.75 and next_s[1]['consecutive_eligible']==0 and not d[1]['eligible']
 with pytest.raises(ValueError):advance(s,broken[::-1],policy)
 missing=records(policy);missing[2]['per_env']=missing[2]['per_env'][:7]
 _,d=advance(s,missing,policy);assert not d[2]['eligible']

def test_v1_unchanged_zero_unchanged_and_v2_finite_nonzero_tail_gradient():
 cfg=configuration(REFINEMENT_VERSION)
 for c in (0.,.5,-.5):
  data=inputs(c+.1,c)
  old=reward(**data);broad=reward(**data,config=cfg,linear_narrow_mix=torch.zeros(3))
  torch.testing.assert_close(old['total'],broad['total'])
  narrow=reward(**data,config=cfg,linear_narrow_mix=torch.ones(3)*.75)
  if c==0:torch.testing.assert_close(old['total'],narrow['total'])
  else:assert narrow['total'].max()<old['total'].min()
 data=inputs(-2.,1.);data['velocity']=data['velocity'].clone().requires_grad_()
 result=reward(**data,config=cfg,linear_narrow_mix=torch.ones(3)*.75);result['total'].sum().backward()
 assert data['velocity'].grad[:,0].gt(0).all() and torch.isfinite(data['velocity'].grad).all()
 with pytest.raises(ValueError):reward(**inputs(),linear_narrow_mix=torch.zeros(3))

def test_explicit_v2_recipe_and_real_reward_audit():
 from native_stand.students.motion_reward_audit import audit
 recipe=declaration(reward_version=REFINEMENT_VERSION);validate_instance(recipe,recipe['source_actor_sha256'])
 report=audit(recipe['reward']);assert len(report['declared_refinement_curves'])==52
 bad=copy.deepcopy(recipe);bad['reward']['refinement']['maximum_mix']=1.
 with pytest.raises(ValueError):validate_instance(bad,bad['source_actor_sha256'])

def test_runner_initialization_and_change_predicate_do_not_shadow_weights():
 """Execute actual initialization/predicate AST slices, without importing Isaac."""
 import ast
 from pathlib import Path
 from types import SimpleNamespace
 tree=ast.parse(Path('src/native_stand/students/motion_runner.py').read_text())
 execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
 predicate=next(n.value for n in ast.walk(execute) if isinstance(n,ast.keyword) and n.arg=='actor_parameters_changed')
 # The generator's .items() owner is the actual runner weight baseline variable.
 generator=next(n for n in ast.walk(predicate) if isinstance(n,ast.GeneratorExp))
 owner=generator.generators[0].iter.func.value.id
 assignment=next(n for n in ast.walk(execute) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==owner for t in n.targets))
 imp=next(n for n in ast.walk(execute) if isinstance(n,ast.ImportFrom) and n.module=='motion_refinement')
 namespace={'torch':torch,'actor':torch.nn.Linear(2,1)};namespace['ppo']=SimpleNamespace(actor=namespace['actor'])
 exec(compile(ast.Module(body=[assignment],type_ignores=[]),'<runner init>','exec'),namespace)
 # Resolve the actual import bindings, including aliases, in the same namespace.
 from native_stand.students import motion_refinement
 for a in imp.names:namespace[a.asname or a.name]=getattr(motion_refinement,a.name)
 assert eval(compile(ast.Expression(predicate),'<runner changed>','eval'),namespace) is False
 with torch.no_grad():namespace['actor'].weight.add_(1)
 assert eval(compile(ast.Expression(predicate),'<runner changed>','eval'),namespace) is True

def test_optimizer_completion_survives_later_diagnostic_exception():
 from native_stand.students.motion_runner import _record_optimizer_completion
 progress={'actual_updates':0,'samples':0,'effective_actor_samples':0}
 try:
  _record_optimizer_completion(progress,1,65536,{'effective_actor_update_samples':0})
  raise AttributeError('simulated diagnostic failure after real critic update')
 except AttributeError:pass
 assert progress=={'actual_updates':1,'samples':65536,'effective_actor_samples':0}
