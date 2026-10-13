FROZEN_TEST_SCOPE='PORTABLE'
import copy
import torch
import pytest
from native_stand.students.recovery_task import reward,configuration,SUFFIX_VERSION,CONTACT_SUFFIX_VERSION
from native_stand.students.course import recipe_for,initial_state,SUFFIX_RECIPE,CONTACT_SUFFIX_RECIPE
from native_stand.students.fault_evidence import capture
from native_stand.command_v6.domain.trace_schema import STATE

def inputs():
 return dict(height=torch.tensor([.4]),h0=torch.tensor([.168]),angles=torch.zeros(1,2),contacts=torch.tensor([[0.,4.]]),clearance=torch.ones(1)*.1,torque=torch.zeros(1,6),previous_targets=torch.zeros(1,6),executed_targets=torch.zeros(1,6),angular_body=torch.zeros(1,3),velocity_native=torch.zeros(1,3),yaw=torch.zeros(1),entered=torch.tensor([False]),controlled=torch.tensor([True]),fault=torch.tensor([False]),entry_event=torch.tensor([False]),success_event=torch.tensor([False]),failure_event=torch.tensor([False]),active_leg_q=torch.zeros(1,4))

def test_only_contact_cost_changes_and_only_student_hold_is_penalized():
 base=configuration(SUFFIX_VERSION);new=configuration(CONTACT_SUFFIX_VERSION)
 comparison=copy.deepcopy(new);comparison.pop('hold_contact_deficit');comparison['version']=base['version'];assert comparison==base
 k=inputs();old=reward(**k,reward_configuration=base);r=reward(**k,reward_configuration=new)
 torch.testing.assert_close(old['total'],r['total']) # transition flight unchanged
 k['entered'][:]=True
 old=reward(**k,reward_configuration=base);r=reward(**k,reward_configuration=new)
 assert r['hold_contact_deficit_raw'].item()==.5
 assert r['hold_contact_deficit_density'].item()==pytest.approx(-.1)
 assert (r['total']-old['total']).item()==pytest.approx(-.001)
 for name in ['controlled','fault']:
  k=inputs();k['entered'][:]=True;k[name][:]=False if name=='controlled' else True
  assert reward(**k,reward_configuration=new)['hold_contact_deficit_dt'].item()==0
 k=inputs();k['entered'][:]=True;k['contacts'][:]=4
 assert reward(**k,reward_configuration=new)['hold_contact_deficit_dt'].item()==0

def test_v9_legacy_recipe_remains_default_and_unknown_variant_rejected():
 state=initial_state();state['stage']='B'
 assert recipe_for(state,{})==SUFFIX_RECIPE
 assert recipe_for(state,{'dynamic_recipe':CONTACT_SUFFIX_RECIPE})==CONTACT_SUFFIX_RECIPE
 with pytest.raises(ValueError,match='unknown'):recipe_for(state,{'dynamic_recipe':'arbitrary'})

def test_fault_capture_includes_env_outside_previous_first_eight_and_preserves_rng():
 state=torch.zeros(64,39);rewards=torch.ones(64);state[63,STATE['initial_rejected']]=1
 components={'joint_outside':torch.zeros(64,dtype=torch.bool),'initial_age_s':torch.ones(64)}
 before=torch.get_rng_state().clone();result=capture(state,rewards,components)
 assert torch.equal(before,torch.get_rng_state()) and result['env_ids'].tolist()==[63]
 assert result['initial_rejected'].item() and not result['runtime_fault'].item()
 torch.testing.assert_close(result['state'],state[63:64])
 result['state'].zero_();assert state[63,STATE['initial_rejected']]==1
 state.zero_();rewards[12]=float('nan');assert capture(state,rewards,components)['env_ids'].tolist()==[12]
 state.zero_();rewards.fill_(1);assert capture(state,rewards,components) is None
 state[31,STATE['runtime_fault']]=1
 with pytest.raises(ValueError,match='misaligned'):capture(state,rewards,{'bad':torch.zeros(8)})
