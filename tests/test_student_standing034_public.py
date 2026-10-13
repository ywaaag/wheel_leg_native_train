FROZEN_TEST_SCOPE='PROJECT_DATA'
import copy,json
from pathlib import Path
from native_stand.students.course_io import prepare_block
from native_stand.command_v6.config import validate
ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'isolated/recovery_standing034_symmetry_20261012/task/task_manifest.json'

def test_public_preparer_consumes_normal_task_height_reward_and_budgets(tmp_path):
 out=tmp_path/'2026_10_12-23_50__standing_fixture';r=prepare_block(TASK,output=out,write_files=True)
 s=json.loads((out/'spec.json').read_text());assert validate(s)==[]
 assert s['control']['height_command_m']==.34 and s['student_training']['target_height_m']==.34
 assert s['student_training']['reward']['weak_mirror']['squared_cap'] is None
 assert s['budget']['formal_updates']==300 and s['budget']['smoke_updates']==12
 assert s['budget']['formal_wall_s']==10800 and s['budget']['sample_limit']==2555904
 assert s['recovery_course']['state']['stage']=='A' and not s['recovery_course']['early_end_allowed']
 assert len([r for r in s['student_evaluation']['cases'] if r['family']=='motion_native_normal' and r['kind']=='student'])==4
 for field in ('target_height_m','version'):
  mutated=copy.deepcopy(s);mutated['student_training'][field]='wrong';assert validate(mutated)
 mutated=copy.deepcopy(s);mutated['recovery_course']['state']['stage']='B';assert validate(mutated)

def test_continuation_preparation_keeps_same_recipe_and_finite_no_smoke(tmp_path):
 import torch
 from native_stand.students.training_recipe import declaration
 from native_stand.students.standing import RECIPE
 from native_stand.students.course import initial_state
 from native_stand.students.data import sha
 task=json.loads(TASK.read_text());parent=json.loads(Path(task['source_parent']).read_text())
 # CPU-only declaration fixture; no forged simulation certificate or attempts.
 cp=tmp_path/'saved.pt';cp.write_bytes(b'CPU checkpoint identity fixture')
 state=initial_state();state['cumulative_updates']=312
 out=tmp_path/'2026_10_12-23_51__standing_resume_fixture'
 r=prepare_block(TASK,source={'checkpoint':str(cp),'sha256':sha(cp)},state=state,resume=True,smoke_evidence={'folder':str(tmp_path/'oldsmoke'),'sha256':'a'*64},output=out,write_files=True)
 s=json.loads((out/'spec.json').read_text());assert validate(s)==[]
 assert s['budget']['smoke_updates']==0 and s['budget']['smoke_wall_s']==0 and s['budget']['formal_wall_s']==11700
 assert s['restore_source_rng'] is True and s['recovery_course']['resume'] is True
 assert s['student_training']['version']==RECIPE and s['budget']['sample_limit']==2457600
