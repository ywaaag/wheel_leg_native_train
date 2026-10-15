FROZEN_TEST_SCOPE='PORTABLE'
import copy
import pytest
from native_stand.students import motion_forward_course as f
from native_stand.students.motion_course import implementation

def test_forward_slots_whitelist_and_no_backward_yaw():
 for stage in range(3):
  c=f.stage_config(stage);assert sum(c['slot_counts'])==512 and len(c['sampling_slots'])==512
  assert c['slot_counts'][0]==128 and c['slot_counts'][-1]==192 and sum(c['slot_counts'][1:-1])==192
  assert all(v>=0 and yaw==0 for v,yaw in c['commands'])
  assert c['commands'][-1]==[f.TARGETS[stage],0.] and max(v for v,yaw in c['commands'])==f.TARGETS[stage]
  assert implementation(f.VERSION) is f
 with pytest.raises(ValueError):implementation('wrong')

def candidate(stage,update):
 return {'stage':stage,'update':update,'checkpoint':f'/fake/{update}.pt','sha256':str(update),'complete_matrix':True,
  'evaluations':[{'case':{'command':v+[.34]},'path':'raw.json','sha256':'a'*64,'per_env':[{'env':i,'accepted':True} for i in range(8)]} for v in f.commands(stage)]}

def test_two_complete_checks_advance_and_never_final_early():
 s={'stage':0,'stage_started_update':0,'last_evaluation_update':-1,'consecutive_passes':0,'accepted_by_stage':{}}
 s,d=f.advance(s,candidate(0,250));assert not d['advanced']
 s,d=f.advance(s,candidate(0,500));assert d['advanced'] and s['stage']==1 and not d['all_stages_passed']
 c=candidate(1,750);c['evaluations'][-1]['per_env'][0]['accepted']=False
 s,d=f.advance(s,c);assert not d['complete_matrix_passed'] and s['consecutive_passes']==0
 s.update(stage=2,consecutive_passes=1,last_evaluation_update=1250)
 s,d=f.advance(s,candidate(2,1500));assert d['all_stages_passed'] and not d['advanced']

def test_parking_diagnostic_cannot_hide_other_failure():
 original={'version':'old','checks':{'parking':False,'contact':True,'tracking':True},'accepted':False,'failed_checks':['parking']}
 r=f.assess(original);assert r['accepted'] and r['diagnostic_checks']['parking'] is False and original['accepted'] is False
 original['checks']['tracking']=False
 assert not f.assess(original)['accepted']

def test_recipe_explicit_forward_only_old_unchanged():
 from native_stand.students.motion_training import declaration
 from native_stand.students.training_recipe import validate_instance
 from native_stand.students.motion_startup import smoke_profile
 from native_stand.students.motion_tracking_reward import QUALITY_VERSION
 r=declaration(reward_version=QUALITY_VERSION);old=copy.deepcopy(r)
 r.update(course_version=f.VERSION,course_stage=0,smoke_wiring=smoke_profile())
 assert validate_instance(r,r['source_actor_sha256'])==r
 assert validate_instance(old,old['source_actor_sha256'])==old
 r['course_stage']=3;r['stage']=3
 with pytest.raises(ValueError):validate_instance(r,r['source_actor_sha256'])
