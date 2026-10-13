FROZEN_TEST_SCOPE='PROJECT_DATA'
from pathlib import Path
import json,torch,numpy as np,pytest
from native_stand.students import mcu_interface as m
from native_stand.students.data import sha
ROOT=Path(__file__).resolve().parents[1]
def test_raw_preaction_targets_and_episode_split():
 folder=ROOT/'isolated/student_mcu_v2_teachers_20261011';manifest=json.loads((folder/'manifest.json').read_text());d=torch.load(folder/'RecoveryStudent.pt',weights_only=False)
 assert manifest['interface_version']==m.VERSION and d['x'].shape[1]==31
 assert [len(d['episode'][d['split']==s].unique()) for s in (0,1,2)]==[15,8,8]
 assert (d['x'][:,24]==.8).all() and (d['x'][:,25:]==torch.tensor([0,1,0,1,0,0])).all()
 for ep in manifest['episodes']:
  if ep['role']!='RecoveryStudent':continue
  ix=torch.where(d['episode']==ep['id'])[0];assert d['split'][ix].unique().numel()==1
  run,case,env=ep['name'].split('/');run=ROOT/'runs'/run;env=int(env);raw=json.loads((run/f'evaluation_{int(case):02}.json').read_text());ids=raw['field_schema']['active_indices']
  with np.load(run/raw['trace']['path']) as z:
   # first/transition/last sample of each complete episode, never post-action q
   for k in ix[[0,min(50,len(ix)-1),-1]]:
    t=int(d['sample'][k]);np.testing.assert_allclose(d['x'][k,6:10],z['joint_q_pre'][t,env,ids][list(m.LEGS)]/1.5,atol=1e-6)
    np.testing.assert_allclose(d['x'][k,16:20],z['target_pre'][t,env,:4]/1.5,atol=1e-6)
    np.testing.assert_allclose(d['x'][k,20:22],z['target_pre'][t,env,4:]/100,atol=1e-6)
    np.testing.assert_allclose(d['y'][k,list(m.LEGS)]*1.5,z['control'][t,env,28:32],atol=1e-6)
 assert all(sha(path)==value for path,value in manifest['files'].items())
 assert all(sha(v['path'])==v['sha256'] for v in manifest['teachers'].values())

def test_online_training_rejected_at_public_cpu_boundary():
 # No simulation or optimizer allowed by v2 declaration regardless of authorization.
 from native_stand.students.requests import preflight
 spec=next((ROOT/'configs/experiments').glob('*__mcu_v2_student_independent_ppo0/spec.json')) if list((ROOT/'configs/experiments').glob('*__mcu_v2_student_independent_ppo0/spec.json')) else None
 assert spec is not None, 'real public MCU declaration required for training rejection test'
 result=preflight(spec,ROOT/'isolated/SHOULD_NOT_EXIST_MCU','formal')
 assert any('online PPO' in e for e in result['errors'])

def test_mcu_checkpoint_export_and_old_model_loading():
 from native_stand.students.model import load
 from native_stand.students.ppo import assemble
 for role,folder,deploy in [('RecoveryStudent','recovery_mcu_v2_bc_20261011','recovery_mcu_v2_deploy_20261011'),('MotionZeroStudent','motion_zero_mcu_v2_bc_20261011','motion_zero_mcu_v2_deploy_20261011')]:
  folder=ROOT/'isolated'/folder;actor,cp=load(folder/'best_validation.pt',role);initial=torch.load(folder/'random_initialization.pt',weights_only=False)
  assert all(torch.equal(v,initial['critic'][k]) for k,v in cp['critic'].items())
  torch.testing.assert_close(actor.log_std,initial['actor']['log_std'])
  assert all(sha(path)==expected for path,expected in cp['teacher_sha256'].items())
  export=json.loads((ROOT/'isolated'/deploy/'manifest.json').read_text());assert export['numerical_pass'] and export['actor_parameters']==14630 and export['fp32_weight_bytes']==58520
  with pytest.raises(ValueError,match='reward undefined'):assemble(folder/'best_validation.pt',None)
 import sys
 # Public health/planner really consume the declared v2 checkpoint, not dimension guessing.
 from native_stand.command_v6.tools.health_check import inspect_project
 paths=list((ROOT/'configs/experiments').glob('*__mcu_v2_student_independent_ppo0/spec.json'));assert len(paths)==1
 report=inspect_project(ROOT,spec_path=paths[0],include_processes=False);source=json.loads(paths[0].read_text())['source_checkpoint']
 assert not [f for f in report['findings'] if f.get('path')==source]
 actor,_=load(ROOT/'isolated/recovery_student_bc_20261011/best_validation.pt');assert actor.mlp[0].in_features==1182
