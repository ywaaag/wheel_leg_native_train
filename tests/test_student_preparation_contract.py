FROZEN_TEST_SCOPE='PROJECT_DATA'
import importlib.util,json,copy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'configs/experiments/2026_10_11-11_36__mcu_v2_student_independent_ppo0/spec.json'

def preparer():
 spec=importlib.util.spec_from_file_location('student_prepare',ROOT/'scripts/prepare_student_recovery_ppo.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_explicit_parent_permuted_cases_and_zero_write(tmp_path):
 original=json.loads(PARENT.read_text());source=original['source_checkpoint']
 permuted=copy.deepcopy(original);permuted['student_evaluation']['cases'].reverse()
 parent=tmp_path/'parent.json';parent.write_text(json.dumps(permuted));output=tmp_path/'2026_10_11-15_00__student_fixture'
 report=preparer().prepare(parent,source,output=output)
 assert report['case_ids']==['student_native','student_yaw10','student_yaw11','student_yaw12','teacher_combination_native']
 assert report['source_checkpoint'][1]==original['source_sha256'] and report['files_written']==0
 assert not output.exists() and report['requested_changes']


@pytest.mark.parametrize('error',['duplicate','missing','wrongsha'])
def test_incomplete_inputs_fail_without_publish(tmp_path,error):
 parent=tmp_path/'parent.json';data=json.loads(PARENT.read_text());source=data['source_checkpoint']
 if error=='duplicate':data['student_evaluation']['cases'].append(data['student_evaluation']['cases'][0])
 if error=='missing':data['student_evaluation']['cases']=[r for r in data['student_evaluation']['cases'] if r['case_id']!='student_yaw11']
 if error=='wrongsha':source=tmp_path/'fake.pt';source.write_bytes(b'not source')
 parent.write_text(json.dumps(data));output=tmp_path/'2026_10_11-15_01__student_fixture'
 with pytest.raises(ValueError):preparer().prepare(parent,source,output=output,write=True)
 assert not output.exists()

def test_rehearsal_public_declaration_consumes_normal_pose_quota_and_keeps_Swing_gate(tmp_path):
 from native_stand.command_v6.config import validate
 from native_stand.recovery.sampling import fixed_reset_choices
 import torch
 data=json.loads(PARENT.read_text());output=tmp_path/'2026_10_11-17_00__student_rehearsal_fixture'
 preparer().prepare(PARENT,data['source_checkpoint'],output=output,write=True,standing_rehearsal=True)
 s=json.loads((output/'spec.json').read_text());assert validate(s)==[]
 poses=json.loads((output/'poses.json').read_text())['poses'];ids=fixed_reset_choices(poses,s['recovery'],'train',torch.arange(64),64)
 assert [poses[i]['family'] for i in ids[:32]]==['swing_candidate_from_historical_r1']*32
 assert [poses[i]['family'] for i in ids[32:]]==['motion_native_normal']*32
 assert len(s['student_evaluation']['cases'])==6 and s['student_training']['retained_families']==[]
 assert json.loads((output/'budget.json').read_text())['authorization']=='UNAUTHORIZED'

def test_standing_only_fresh_distilled_source_and_full_public_contract(tmp_path):
 from native_stand.command_v6.config import validate
 from native_stand.students.training_recipe import STANDING_RECIPE,STANDING_SOURCE_SHA
 source=ROOT/'isolated/recovery_standing_reset_distilled_20261011/best_validation.pt';out=tmp_path/'2026_10_11-21_00__standing_fixture'
 preparer().prepare(PARENT,source,write=True,output=out,standing_only=True)
 s=json.loads((out/'spec.json').read_text());assert validate(s)==[]
 assert s['source_sha256']==STANDING_SOURCE_SHA and s['student_training']['version']==STANDING_RECIPE
 assert s['recovery']['sampling']=={'version':'family_weights_v1','family_weights':{'motion_native_normal':1.}}
 assert s['budget']['formal_updates']==300 and s['budget']['sample_limit']==312*8192
 assert [r['kind'] for r in s['student_evaluation']['cases']]==['student']*4+['teacher_normal']
 assert [r['family'] for r in s['student_evaluation']['cases']]==['motion_native_normal']*3+['swing_candidate_from_historical_r1','motion_native_normal']

@pytest.mark.parametrize('from_update50',[False,True,'update200'])
def test_standing_source_actual_CPU_optimizer_warmup_then_actor_update(from_update50):
 import torch
 from tensordict import TensorDict
 from native_stand.students.ppo import assemble
 from native_stand.students.training_recipe import declaration,STANDING_RECIPE,MOTION_MIRROR_RECIPE,SLIDING_RECIPE
 from native_stand.recovery.controlled_ppo import KEY
 from native_stand.students.data import sha
 path=ROOT/('runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/model_update_50.pt' if from_update50 else 'isolated/recovery_standing_reset_distilled_20261011/best_validation.pt');before_sha=sha(path)
 if from_update50=='update200':path=ROOT/'runs/2026_10_11-22_43__recovery_standing_motion_mirror_from50/formal/model_update_200.pt';before_sha=sha(path)
 obs=TensorDict({'student_actor':torch.zeros(8,31),'student_critic':torch.zeros(8,40),KEY:torch.ones(8,1,dtype=torch.bool)},batch_size=[8])
 torch.set_num_threads(4);ppo=assemble(path,obs,steps_per_env=1,recipe=declaration(SLIDING_RECIPE if from_update50=='update200' else MOTION_MIRROR_RECIPE if from_update50 else STANDING_RECIPE));assert not ppo.optimizer.state
 initial={k:v.clone() for k,v in ppo.actor.state_dict().items()};std=ppo.actor.log_std.clone()
 for enable in (False,True):
  with torch.inference_mode():
   ppo.act(obs);ppo.process_env_step(obs,torch.arange(8).float(),torch.zeros(8,dtype=torch.bool),{});ppo.compute_returns(obs)
  ppo.actor_update_enabled=enable;ppo.update()
  changed=any(not torch.equal(v,ppo.actor.state_dict()[k]) for k,v in initial.items())
  assert changed==enable
 assert torch.equal(std,ppo.actor.log_std) and sha(path)==before_sha

def test_motion_mirror_preparer_true_update50_lineage_and_no_target_projection(tmp_path):
 from native_stand.command_v6.config import validate
 from native_stand.students.training_recipe import MOTION_MIRROR_RECIPE,UPDATE50_SHA
 source=ROOT/'runs/2026_10_11-20_46__recovery_mcu_v2_standing_from_distilled/formal/model_update_50.pt'
 parent=source.parent/'source_snapshot/spec.json';out=tmp_path/'2026_10_11-23_00__mirror_fixture'
 preparer().prepare(parent,source,write=True,output=out,motion_mirror=True)
 s=json.loads((out/'spec.json').read_text());assert validate(s)==[]
 assert s['source_sha256']==UPDATE50_SHA and s['student_training']['version']==MOTION_MIRROR_RECIPE
 assert not s['reward']['weak_mirror']['action_override'] and s['reward']['motion_zero_tracking']['weight_per_s']==4
 assert s['recovery']['sampling']['family_weights']=={'motion_native_normal':1.}
 assert str(parent) in s['student_dependencies']

def test_velocity_huber_public_preparer_exact_new200_and_primary_contract(tmp_path):
 from native_stand.command_v6.config import validate
 from native_stand.students.training_recipe import SLIDING_RECIPE,UPDATE200_SHA
 source=ROOT/'runs/2026_10_11-22_43__recovery_standing_motion_mirror_from50/formal/model_update_200.pt';parent=source.parent/'source_snapshot/spec.json';out=tmp_path/'2026_10_12-01_00__velocity_fixture'
 preparer().prepare(parent,source,write=True,output=out,velocity_huber=True)
 s=json.load(open(out/'spec.json'));assert validate(s)==[] and s['source_sha256']==UPDATE200_SHA
 assert s['student_training']['version']==SLIDING_RECIPE and s['reward']['motion_zero_tracking']['weight_per_s']==-1
 assert s['reward']['weak_mirror']['weight_per_s']==-.05 and s['budget']['formal_updates']==300
