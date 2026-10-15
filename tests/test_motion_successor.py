FROZEN_TEST_SCOPE='PORTABLE'
import copy,json
import pytest
import torch
from native_stand.students.motion_tracking_reward import configuration,QUALITY_VERSION,SUCCESSOR_VERSION
from native_stand.students.motion_training import declaration,effective,protocol,short_wiring
from native_stand.students.motion_successor import apply_assessment

def test_old_declaration_unchanged_new_explicit_recipe():
 old=declaration(reward_version=QUALITY_VERSION);new=declaration(reward_version=SUCCESSOR_VERSION)
 assert old['train_schedule_s']==[.5,1.,25.5,1.] and old['parking_s']==2
 assert new['train_schedule_s']==[.5,1.,28.5,0.] and new['parking_s']==0
 from native_stand.students.training_recipe import validate_instance
 new['smoke_wiring']=short_wiring();assert validate_instance(new,new['source_actor_sha256'])==new
 a=configuration(QUALITY_VERSION);b=configuration(SUCCESSOR_VERSION)
 assert a['weights'][5]==2 and b['weights'][5]==4
 assert a['posture_tail']['weights']==[-.5,-.5] and b['posture_tail']['weights']==[-1,-1]
 assert a['quality_termination']==b['quality_termination'] and a['refinement']==b['refinement']

def test_no_parking_commands_remain_at_target_until_timeout():
 cfg=declaration(reward_version=SUCCESSOR_VERSION);targets=torch.tensor([[1.,0.],[-1.,0.],[0.,0.]])
 for age in (0.,.5,1.,1.5,27.,29.99,30.):
  command=effective(targets,torch.full((3,),age),training=True,config=cfg)
  assert torch.isfinite(command).all() and (command[:,2]==.34).all()
  if age>=1.5:assert torch.equal(command[:,:2],targets)
 # Independent original evaluation retains its braking windows.
 at=effective(targets,torch.full((3,),29.),config=cfg)
 assert torch.equal(at[:,:2],torch.zeros_like(targets))
 from native_stand.command_v6.domain.command_schedule import effective as base
 for age in (0.,1.5,30.,30.01):
  v=base(targets,torch.full((3,),age),height=.34,entry=.5,ramp=1.,hold=28.5,exit=0.)
  assert torch.isfinite(v).all()
  if age>=1.5:assert torch.equal(v[:,:2],targets)

def test_reward_snapshot_matches_actual_new_weights_and_gradients():
 from native_stand.students.motion_reward_audit import audit
 r=audit(configuration(SUCCESSOR_VERSION))
 assert r['named_weights']['upright']==4 and r['named_weights']['pitch_excess']==-1
 old=audit(configuration(QUALITY_VERSION))
 for axis in ('pitch','roll'):
  a=next(v for v in old['curves'] if v['signal']==axis and v['error']==.3)
  b=next(v for v in r['curves'] if v['signal']==axis and v['error']==.3)
  assert b['weighted_density']==pytest.approx(2*a['weighted_density'])
  assert b['state_error_derivative']==pytest.approx(2*a['state_error_derivative']) and b['state_error_derivative']<0
 for v in r['curves']:
  if v['signal'].startswith('linear') and v['error']>0:assert v['state_error_derivative']<0

def test_parking_diagnostic_never_hides_tracking_or_source_guard_failure():
 row={'accepted':False,'failed_checks':['parking'],'checks':{'parking':False,'tracking':True}}
 apply_assessment(row);assert row['accepted'] and row['diagnostic_checks']['parking'] is False
 assert row['original_full_protocol_failed_checks']==['parking']
 row={'accepted':False,'failed_checks':['tracking','parking'],'checks':{'parking':False,'tracking':False,'pitch_source_guard':False}}
 apply_assessment(row);assert not row['accepted'] and 'tracking' in row['failed_checks'] and 'pitch_source_guard' in row['failed_checks']
 assert protocol(quality=True,successor=True)['schedule_s']==protocol(quality=True)['schedule_s']

def test_runtime_uses_explicit_config_weights_and_preserves_mixture():
 import ast
 from pathlib import Path
 root=Path(__file__).resolve().parents[1]/'src/native_stand/students'
 runtime=(root/'motion_quality_runtime.py').read_text();ast.parse(runtime)
 assert 'reward_config=self.motion_quality_reward_config' in runtime
 runner=(root/'motion_runner.py').read_text();ast.parse(runner)
 assert "progress['successor_restore']=restore(ppo,source,spec,phase)" in runner
 assert "env.motion_cohort_mix.copy_" in runner
