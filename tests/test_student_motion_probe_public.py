"""Actual declared model and public planner boundary, project identities readonly."""
FROZEN_TEST_SCOPE='PROJECT_DATA'
import json,copy,importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest
from native_stand.students import requests
from native_stand.command_v6.config import validate
from native_stand.students.model import load
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/2026_10_11-16_21__student100_motion_b250_local_probe_ppo0/spec.json'

def test_public_plan_actual_source_motion_identity_and_zero_write(tmp_path):
 s=json.loads(SPEC.read_text());assert validate(s)==[]
 from native_stand.command_v6.tools.experiment_preparation import publish
 budget={'authorization':'UNAUTHORIZED','limits':{'evaluate':1},'used':{'evaluate':0},'attempts':{}}
 publish(tmp_path/'declaration',{'spec.json':s,'budget.json':budget},{},completion_marker=True)
 plan=requests.plan(SimpleNamespace(spec=tmp_path/'declaration/spec.json',output=tmp_path/'NOT_RUN',attempt_id=None),s)
 assert plan['preflight']['errors']==['new simulation/PPO budget has not been authorized']
 assert len(plan['requests'])==9 and 'rescue not independent' in plan['effective_recipe']['student_control']
 actor,data=load(s['source_checkpoint'],'RecoveryStudent');assert actor.mlp[0].in_features==31
 assert s['student_teachers'][1]['sha256']=='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'
 assert not (tmp_path/'NOT_RUN').exists()
 for key in ('student_training','unknown'):
  bad=copy.deepcopy(s)
  if key=='student_training':bad[key]={'version':'bad'}
  else:bad['student_evaluation']['cases'][-1]['unknown']=1
  assert validate(bad)


def test_same_student_case_can_repeat_only_unique_ids():
 s=json.loads(SPEC.read_text());assert len({r['checkpoint'] for r in s['student_evaluation']['cases'][2:]})==1
 assert len({r['case_id'] for r in s['student_evaluation']['cases'][2:]})==7
 s['student_evaluation']['cases'][-1]['case_id']=s['student_evaluation']['cases'][2]['case_id'];assert any('duplicate' in e for e in validate(s))
