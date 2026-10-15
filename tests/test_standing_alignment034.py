"""Versioned standing reward and physical geometry certificate, CPU only."""
FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.standing_alignment import configuration,REWARD,RECIPE,SOURCE
from native_stand.students.recovery_task import reward,configuration as reward_config
from native_stand.students.standing_certificate import AlignmentCertificate,alignment_score


def evaluate(h=.34,q=None,offset=0.,v=0.,fault=False):
 z=torch.zeros(1);o=torch.ones(1);z6=torch.zeros(1,6);yes=torch.ones(1,dtype=torch.bool);no=~yes
 q=torch.zeros(1,4) if q is None else torch.tensor([q])
 return reward(o*h,o*.4,torch.zeros(1,2),torch.ones(1,2)*20,o*.1,z6,z6,z6,torch.zeros(1,3),torch.tensor([[v,0.,0.]]),z,yes,yes,yes if fault else no,no,no,no,reward_configuration=configuration(),active_leg_q=q,wheel_heading_offset=o*offset)


def test_dense_reward_optimum_units_and_no_event_loophole():
 good=evaluate();wrong_height=evaluate(h=.4);scissor=evaluate(offset=.2);asym=evaluate(q=[.5,.5,.5,-.5]);moving=evaluate(v=1.)
 assert all(good['total']>x['total'] for x in (wrong_height,scissor,asym,moving))
 assert torch.equal(good['alignment_dt'],good['alignment_density']*.01)
 assert torch.equal(good['events'],torch.zeros(1,3))
 assert evaluate(fault=True)['total']==0
 assert evaluate(offset=.4)['alignment_raw'][0,2]>scissor['alignment_raw'][0,2]
 assert reward_config(REWARD)==configuration()


def test_online_geometry_certificate_does_not_accept_longitudinal_mismatch():
 c=AlignmentCertificate(1,'cpu');yes=torch.ones(1,dtype=torch.bool);no=~yes;o=torch.ones(1)
 c.set_joint(torch.zeros(1,4));c.set_offset(o*.1);c.set_velocity(torch.zeros(1,3))
 for _ in range(1020):
  success,failure,end,fault=c.observe(o*.34,torch.zeros(1,2),torch.zeros(1),torch.ones(1,2)*20,o*.1,o*0,no.float(),active=yes,valid=yes,safety_failed=no,fault=no)
 assert end and failure and not success


def test_versioned_recipe_budget_source_and_legacy_unchanged():
 from native_stand.students.training_recipe import declaration
 r=declaration(RECIPE);assert r['source_actor_sha256']==SOURCE and r['target_height_m']==.34
 assert r['milestones'][-1]==988 and r['warmup_updates_per_phase']==5
 with pytest.raises(ValueError):declaration(RECIPE,'0'*64)
 assert reward_config()['version']=='student_recovery_reward_v1'


def test_physical_runtime_wiring_is_explicit():
 from native_stand.command_v6.tools.test_resources import source_file
 runtime=source_file('students/runtime.py').read_text()
 assert "wheel_heading_offset=getattr(self.rise_hold,'offset',None)" in runtime
 assert 'self.rise_hold.set_offset(longitudinal_geometry(centers,gravity))' in runtime


def test_online_perfect_standing_matches_offline_geometry_gate():
 c=AlignmentCertificate(1,'cpu');yes=torch.ones(1,dtype=torch.bool);no=~yes;o=torch.ones(1)
 c.set_joint(torch.zeros(1,4));c.set_offset(o*0);c.set_velocity(torch.zeros(1,3))
 for _ in range(1020):
  success,failure,end,fault=c.observe(o*.34,torch.zeros(1,2),torch.zeros(1),torch.ones(1,2)*20,o*.1,o*0,no.float(),active=yes,valid=yes,safety_failed=no,fault=no)
 assert success and end and not failure
 result={'hold_complete':True,'hold_index_half_open':[0,1000],'checks':{'height':True},'accepted':True}
 g=torch.zeros(1000,13);g[:,7]=-1
 assert alignment_score(result,g)['accepted']
 g[:,2]=.1
 assert not alignment_score(result,g)['accepted']


def test_acceptance_requires_two_complete_checkpoints():
 from native_stand.students.training import choose
 def candidate(u):
  return {'update':u,'standing_alignment_repeat_required':True,'checkpoint':str(u),'sha256':str(u),'per_env':[{'accepted':True,'entry_index':0,'valid_hold_prefix_s':10.,'hold_complete':True} for _ in range(24)]}
 assert choose([candidate(100)])['accepted_candidate'] is None
 assert choose([candidate(100),candidate(200)])['accepted_candidate'] is not None

def test_final_assessment_respects_declared_tasks():
 from native_stand.students.training_recipe import final_assessment_cases,declaration
 recipe=declaration(RECIPE)
 students=[{'case_id':'normal_native','family':'motion_native_normal'},
           {'case_id':'normal_yaw10','family':'motion_native_normal'}]
 cases=final_assessment_cases(recipe,students)
 assert len(cases)==4 and all(c['family']=='motion_native_normal' for c in cases)
 assert [c['seed'] for c in cases[1:]]==recipe['final_seeds']
 students.append({'case_id':'student_native','family':'swing_candidate_from_historical_r1'})
 assert final_assessment_cases(recipe,students)[-1]['case_id']=='final_Swing_regression'
 with pytest.raises(KeyError):final_assessment_cases(recipe,students[1:])
