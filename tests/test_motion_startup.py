FROZEN_TEST_SCOPE='PORTABLE'
import copy,json
from pathlib import Path
import numpy as np
from native_stand.students.data import sha
from native_stand.students.motion_startup import build,resolve,merge,smoke_profile,VERSION

def spec_fixture(tmp_path):
 physical={k:{'fixed':True} for k in ('action','control','ground','observation','history','student_interface')}
 spec={**physical,'source_sha256':'a'*64,'asset_sha256':'b'*64,'motion_assessment':{'version':'fixture'},'student_evaluation':{'cases':[]},'student_training':{'smoke_wiring':smoke_profile()}}
 for i,c in enumerate((0.,.5,1.5)):
  spec['student_evaluation']['cases'].append({'case_id':str(i),'command':[c,0.,.34],'seed':1,'family':'motion_native_normal','yaw_rad':0.,'seconds':31.52})
 folder=tmp_path/'old';(folder/'source_snapshot').mkdir(parents=True);(folder/'source_snapshot/spec.json').write_text(json.dumps(physical))
 for i,case in enumerate(spec['student_evaluation']['cases'][:2]):
  trace=folder/f'trace_{i:02}.npz';np.savez_compressed(trace,state=np.zeros((3,8,39)))
  d={'case':case,'checkpoint_sha256':spec['source_sha256'],'asset_sha256':spec['asset_sha256'],'protocol':spec['motion_assessment'],'spec_sha256':sha(folder/'source_snapshot/spec.json'),'per_env':[{'env':j,'accepted':True} for j in range(8)],'model_unchanged':True,'trace':{'path':trace.name,'sha256':sha(trace)}}
  (folder/f'evaluation_{i:02}.json').write_text(json.dumps(d))
 return spec,folder

def test_exact_source_reuse_only_missing_endpoint_and_order(tmp_path):
 spec,folder=spec_fixture(tmp_path);original=copy.deepcopy(spec);plan=build(spec,[folder]);assert spec==original and len(plan['references'])==2 and plan['missing_commands']==[[1.5,0.,.34]]
 spec['motion_startup']=plan;records,missing=resolve(spec);assert len(records)==2 and len(missing)==1
 new=[{'case':missing[0],'path':'new.json','sha256':'c'*64,'per_env':[]}];all_records=merge(spec,records,new)
 assert [r['case']['command'] for r in all_records]==[r['command'] for r in spec['student_evaluation']['cases']]
 assert all_records[0]['reused'] and all_records[2]['path']=='new.json'

def test_source_protocol_checkpoint_and_physics_conflicts_not_reused(tmp_path):
 spec,folder=spec_fixture(tmp_path)
 for key in ('source_sha256','asset_sha256','motion_assessment','control'):
  changed=copy.deepcopy(spec);changed[key]='different' if 'sha' in key else {'different':True}
  assert build(changed,[folder])['references']==[]

def test_source_drift_rejected_and_default_old_short_profile_unchanged(tmp_path):
 import pytest
 spec,folder=spec_fixture(tmp_path);spec['motion_startup']=build(spec,[folder]);p=folder/'evaluation_00.json';p.write_text(p.read_text()+' ')
 with pytest.raises(ValueError,match='identity'):resolve(spec)
 from native_stand.students.motion_training import short_wiring
 assert short_wiring()['version']=='motion31_quality_short_wiring5_v1' and 'independent_evaluation_no_runtime_fault' in short_wiring()['mandatory']
 assert 'independent_evaluation_no_runtime_fault' not in smoke_profile()['mandatory']

def test_minimal_certificate_actual_actor_update_readback_required_no_full_eval(tmp_path):
 from native_stand.students.training_evidence import smoke_certificate
 from native_stand.students.motion_training import declaration
 from native_stand.students.motion_tracking_reward import QUALITY_VERSION,reward_fields
 recipe=declaration(reward_version=QUALITY_VERSION);recipe.update(course_version='motion31_straight_yaw_progression_v1',course_stage=0,smoke_wiring=smoke_profile())
 from native_stand.students.training_recipe import validate_instance
 assert validate_instance(recipe,recipe['source_actor_sha256'])==recipe
 def write(name,d):
  p=tmp_path/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d))
 spec={'source_sha256':'a'*64,'student_training':recipe,'reward':recipe['reward'],'motion_startup':{'version':VERSION},'motion_training':{'stage':0},'budget':{'smoke_updates':5},'ppo':{'envs':512,'steps_per_env':128},'curriculum':{'stages':[{'commands':[[0,0],[.5,0],[-.5,0]]}]}}
 write('source_snapshot/spec.json',spec);write('manifest.json',{'spec_sha256':sha(tmp_path/'source_snapshot/spec.json'),'source_sha256':'a'*64});write('terminal_report.json',{'status':'COMPLETED','actual_updates':5,'failure':None})
 progress={'actual_updates':5,'actor_parameters_changed':True,'checkpoint_roundtrip_verified':True,'evaluations':[],'wiring_command_readback':{'valid':True,'sample_count':327680},'independent_capability_evaluation':{'status':'NOT_RUN'}};write('progress.json',progress)
 write('wiring_runtime_readback.json',{'asset':{'fixture':True},'control':{'fixture':True},'ground':{'fixture':True}})
 rows=[{'update':u,'controlled_samples':65536,'actor_update_scope':{'valid_actor_samples':65536,'invalid_actor_samples':0,'actor_optimizer_steps':16 if u==5 else 0},'actor_changed_this_update':u==5,'critic_changed_this_update':True,'nonzero_rewards':65536,'episode_completed':0,'BC_loss':0,'BC_gradient_norm':None,'BC_updates':0,'std_unchanged':True,'reward_fields':list(reward_fields(spec['reward'])),'hold_sample_counts':[1,1,1],'command_episode_counts':[0,0,0]} for u in range(1,6)]
 (tmp_path/'metrics.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));cert=smoke_certificate(tmp_path,spec);assert cert['status']=='PASSED',cert['errors']
 assert not cert['coverage']['full_training_episode_verified']
 progress['wiring_command_readback']['valid']=False;write('progress.json',progress);assert smoke_certificate(tmp_path,spec)['status']=='FAILED'
 progress['wiring_command_readback']['valid']=True;write('progress.json',progress);(tmp_path/'wiring_runtime_readback.json').unlink();assert smoke_certificate(tmp_path,spec)['status']=='FAILED'
