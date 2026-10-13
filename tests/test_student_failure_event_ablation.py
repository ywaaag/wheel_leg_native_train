"""Versioned reward intervention; legacy behavior and failure termination remain."""
FROZEN_TEST_SCOPE='PORTABLE'
import copy
import pytest,torch
from native_stand.students.recovery_task import configuration,reward,Certificate,NO_FAILURE_VERSION
from native_stand.students.training_recipe import declaration,NO_FAILURE_RECIPE

def args():
 z=torch.zeros(2);o=torch.ones(2);b=torch.ones(2,dtype=torch.bool);f=~b
 return (o*.17,o*.168,torch.zeros(2,2),torch.ones(2,2)*10,o*.01,torch.zeros(2,6),torch.zeros(2,6),torch.zeros(2,6),torch.zeros(2,3),torch.zeros(2,3),z,f,b,f,f,f,b)

def test_only_failure_reward_changes_and_mask_remains():
 a=reward(*args());b=reward(*args(),reward_configuration=configuration(NO_FAILURE_VERSION))
 for key in ['raw','weighted_density','continuous_dt']:assert torch.equal(a[key],b[key])
 assert torch.equal(b['total']-a['total'],torch.ones(2))
 assert a['events'][:,2].tolist()==[-1.,-1.] and b['events'][:,2].tolist()==[0.,0.]
 invalid=list(args());invalid[12]=torch.zeros(2,dtype=torch.bool)
 assert reward(*invalid,reward_configuration=configuration(NO_FAILURE_VERSION))['total'].eq(0).all()
 bad=configuration(NO_FAILURE_VERSION);bad['success_once']=12
 with pytest.raises(ValueError):reward(*args(),reward_configuration=bad)

def test_recipe_single_variable_and_unknown_rejected():
 a=declaration();b=declaration(NO_FAILURE_RECIPE)
 assert {k for k in a if a[k]!=b[k]}=={'version','reward'}
 assert {k for k in a['reward'] if a['reward'][k]!=b['reward'][k]}=={'version','failure_once'}
 for k in ['source_actor_sha256','warmup_updates_per_phase','BC_coefficient','fixed_log_std','protocol']:assert a[k]==b[k]
 with pytest.raises(ValueError):declaration('unknown')

def test_no_failure_reward_does_not_remove_deadline_or_failed_event():
 c=Certificate(1,'cpu');ones=torch.ones(1,dtype=torch.bool);zeros=~ones
 for _ in range(250):
  success,failed,end,fault=c.observe(torch.tensor([.17]),torch.zeros(1,2),torch.zeros(1),torch.ones(1,2)*10,torch.ones(1)*.01,torch.zeros(1),zeros,active=ones,valid=ones,safety_failed=zeros,fault=zeros)
 assert failed.item() and end.item() and not success.item() and c.task_failure.item()
 assert c.entry.item()<0

def test_evidence_discount_delay_preference_reversed_only_in_saved_return():
 # Timing illustration, not optimizer/physical causal proof.
 gamma=.99
 early_cont=.0744696489;late_cont=.0120086155
 assert early_cont-gamma**65 < late_cont-gamma**249
 assert early_cont > late_cont
