"""Standing specialist remains Recovery; acceptance scope cannot imply Swing."""
FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.students.training_recipe import declaration,STANDING_RECIPE,STANDING_SOURCE_SHA
from native_stand.students.training import choose
from native_stand.students.recovery_task import reward

def test_explicit_stance_source_scope_and_observation_contract_unchanged():
 r=declaration(STANDING_RECIPE)
 assert r['source_actor_sha256']==STANDING_SOURCE_SHA and r['training_family']=='motion_native_normal'
 assert r['milestones']==[25,50,100,200,300] and r['BC_coefficient']==0
 assert 'standing_rehearsal' not in r and 'Swing not certified' not in r['protocol']
 assert r['fixed_log_std'] and r['critic']=='new_random' and r['optimizer']=='new_Adam'

def test_standing_candidate_selection_does_not_assert_Swing():
 def c(update,passed):return {'checkpoint':str(update),'update':update,'per_env':[{'accepted':passed,'entry_index':19,'valid_hold_prefix_s':10 if passed else .1}]*24,'capability_scope':'normal standing only; Swing not certified'}
 s=choose([c(0,False),c(25,True),c(50,True)])
 assert s['accepted_candidate']['update']==25 and s['best_overall']['update']==25
 assert s['capability_scope']=='normal standing only; Swing not certified'

def test_normal_healthy_support_reward_with_fixed_height_and_failure_masks():
 n=2;z=torch.zeros(n);b=torch.ones(n,dtype=torch.bool);f=~b;r=declaration(STANDING_RECIPE)
 args=(z+.4,z+.4,torch.zeros(n,2),torch.ones(n,2)*10,z+.01,torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,6),torch.zeros(n,3),torch.zeros(n,3),z,b,b,f,f,f,f)
 x=reward(*args,reward_configuration=r['reward']);torch.testing.assert_close(x['total'],z+.05)
