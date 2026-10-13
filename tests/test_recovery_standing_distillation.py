"""Standing transfer keeps physical labels and complete episode splits."""
FROZEN_TEST_SCOPE='PROJECT_DATA'
import importlib.util,json,torch
import pytest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('reset_priority',[False,True])
def test_real_dataset_recovery_identity_and_physical_label_preservation(tmp_path,reset_priority):
 s=importlib.util.spec_from_file_location('standing_builder',ROOT/'scripts/prepare_recovery_standing_distillation.py');mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod)
 original=ROOT/'isolated/student_mcu_v2_teachers_20261011';source=ROOT/'isolated/recovery_mcu_v2_bc_20261011/best_validation.pt';out=tmp_path/'new'
 manifest=mod.build(original,source,out,reset_priority=reset_priority);combined=torch.load(out/'RecoveryStudent.pt',weights_only=False);old=torch.load(original/'MotionZeroStudent.pt',weights_only=False);mask=combined['stage']==4
 assert torch.equal(combined['y'][mask],old['y'])
 for k in ('split','episode','sample'):assert torch.equal(combined[k][mask],old[k])
 assert torch.equal(combined['x'][mask,:25],old['x'][:,:25]) and torch.equal(combined['x'][mask,28:],old['x'][:,28:])
 assert (combined['x'][:,25:28]==torch.tensor([0.,1.,0.])).all()
 for a in range(3):
  for b in range(a):assert not set(combined['episode'][combined['split']==a].tolist())&set(combined['episode'][combined['split']==b].tolist())
 assert sum(manifest['sampling_weights'].values())==1
 assert manifest['sampling_weights']['normal_standing']==.5
 if reset_priority:assert manifest['normal_sampling_buckets']=={'first_action':.25,'next19_actions':.5,'remaining_hold':.25,'scope':'inside normal standing half; episode balance unchanged'}

def test_mirror_intervention_keeps_Swing_labels_wheels_and_original_previous_inputs(tmp_path):
 s=importlib.util.spec_from_file_location('standing_builder',ROOT/'scripts/prepare_recovery_standing_distillation.py');mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod)
 original=ROOT/'isolated/student_mcu_v2_teachers_20261011';source=ROOT/'isolated/recovery_mcu_v2_bc_20261011/best_validation.pt';out=tmp_path/'mirror'
 m=mod.build(original,source,out,reset_priority=True,mirror_targets=True)
 new=torch.load(out/'RecoveryStudent.pt',weights_only=False);swing=torch.load(original/'RecoveryStudent.pt',weights_only=False);normal=torch.load(original/'MotionZeroStudent.pt',weights_only=False);mask=new['stage']==4
 assert torch.equal(new['y'][~mask],swing['y']) and torch.equal(new['y'][mask][:,[2,5]],normal['y'][:,[2,5]])
 assert torch.equal(new['x'][mask,:22],normal['x'][:,:22])
 legs=new['y'][mask][:,[0,1,3,4]];assert (legs[:,0]+legs[:,2]).eq(0).all() and (legs[:,1]-legs[:,3]).eq(0).all()
 assert m['normal_target_intervention']['modified_labels_are_not_teacher_verified_actions'] and not m['normal_target_intervention']['runtime_projection']
