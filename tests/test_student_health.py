FROZEN_TEST_SCOPE='PROJECT_DATA'
from pathlib import Path
import json
from native_stand.command_v6.tools.health_check import checkpoint_metadata,inspect_project
ROOT=Path(__file__).resolve().parents[1]
def test_student_metadata_and_real_public_health_boundary():
 spec=ROOT/'configs/experiments/2026_10_11-00_55__student_independent_swing_ppo0/spec.json'
 row=json.loads(spec.read_text());metadata=checkpoint_metadata(row['source_checkpoint'])
 assert metadata['actor_input_shape']==[256,1182] and metadata['critic_input_shape']==[256,1191]
 assert metadata['interface_version']=='multiskill_student_v1'
 result=inspect_project(ROOT,spec_path=spec,include_processes=False)
 findings=result.get('findings',[])
 assert not [f for f in findings if f.get('path')==row['source_checkpoint']],findings
