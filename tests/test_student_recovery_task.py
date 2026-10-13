FROZEN_TEST_SCOPE='PORTABLE'
import copy,torch,pytest
from native_stand.students.recovery_task import reward,Certificate,configuration
from native_stand.students.protocol import score

def inputs(n=1):
 return dict(height=torch.ones(n)*.30,h0=torch.ones(n)*.168,angles=torch.zeros(n,2),contacts=torch.ones(n,2)*10,clearance=torch.ones(n)*.1,torque=torch.zeros(n,6),previous_targets=torch.zeros(n,6),executed_targets=torch.zeros(n,6),angular_body=torch.zeros(n,3),velocity_native=torch.zeros(n,3),yaw=torch.zeros(n),entered=torch.zeros(n,dtype=torch.bool),controlled=torch.ones(n,dtype=torch.bool),fault=torch.zeros(n,dtype=torch.bool),entry_event=torch.zeros(n,dtype=torch.bool),success_event=torch.zeros(n,dtype=torch.bool),failure_event=torch.zeros(n,dtype=torch.bool))

def test_reward_dt_units_init_fault_and_no_low_survival():
 k=inputs();r=reward(**k);assert r['total'].item()==pytest.approx(.05)
 k['height'][:]=.42;assert reward(**k)['total'].item()==pytest.approx(.05)
 k['height'][:]=.168;assert reward(**k)['total'].item()==0
 k=inputs();k['contacts'][:]=0;assert reward(**k)['total'].item()==pytest.approx(.02) # flight progress allowed, not standing
 k['entry_event'][:]=True;assert reward(**k)['total'].item()==pytest.approx(1.02)
 k['controlled'][:]=False;assert reward(**k)['total'].item()==0
 k['controlled'][:]=True;k['fault'][:]=True;k['success_event'][:]=True;assert reward(**k)['total'].item()==0
 k=inputs();k['executed_targets'][:]=torch.tensor([.1,.1,10.,.1,.1,10.]);assert reward(**k)['raw'][0,3]==1
 k['torque'][:]=torch.tensor([40,40,5.5,40,40,5.5]);assert reward(**k)['raw'][0,2]==1
 k['angular_body'][:]=torch.tensor([1,100,1]);k['velocity_native'][:]=torch.tensor([1.,.2,20.]);k['yaw'][:]=.3
 assert reward(**k)['raw'][0,4]==0 and reward(**k)['raw'][0,5]==0
 k['entered'][:]=True;r=reward(**k);assert r['raw'][0,4]==1 and r['raw'][0,5]==3
 k['failure_event'][:]=True;assert reward(**k)['events'][0,2]==-1

def trace(clock,seconds=10.2,*,velocity=0.,bad_contact_step=None):
 rows=[];post=[];events=[]
 for i in range(round(seconds/.01)):
  v=torch.tensor([[velocity,0.,0.]]);clock.set_velocity(v)
  contact=torch.ones(1,2)*10
  if i==bad_contact_step:contact[0,0]=0
  pulse,failed,end,fault=clock.observe(torch.tensor([.4]),torch.zeros(1,2),torch.zeros(1),contact,torch.tensor([.1]),torch.zeros(1),torch.zeros(1),active=torch.ones(1,dtype=torch.bool),valid=torch.ones(1,dtype=torch.bool),safety_failed=torch.zeros(1,dtype=torch.bool),fault=torch.zeros(1,dtype=torch.bool))
  s=torch.zeros(39);s[0]=clock.age[0];s[2]=pulse;s[3]=failed;s[6]=.4;s[7]=velocity;s[10:12]=contact[0];s[13]=.1;s[29]=1
  rows.append(s);post.append(torch.zeros(10));events.append([bool(clock.entry_confirmed[0]),bool(clock.hold_window_complete[0]),bool(pulse[0]),bool(failed[0])])
 return torch.stack(rows),torch.stack(post),events

def test_online_certificate_equals_offline_fixed_window_events_once():
 clock=Certificate(1,'cpu');s,p,e=trace(clock)
 assert sum(r[0] for r in e)==1 and sum(r[1] for r in e)==1 and sum(r[2] for r in e)==1
 assert score(s,p,torch.ones(len(s),dtype=torch.bool),policy_time_s=torch.arange(1,len(s)+1)*.01)['accepted']
 # Count persists across rollout chunk; bad sample cannot restart window or grant success.
 clock=Certificate(1,'cpu');s,p,e=trace(clock,bad_contact_step=150)
 assert sum(r[1] for r in e)==1 and not any(r[2] for r in e);assert e[-1][3]
 assert not score(s,p,torch.ones(len(s),dtype=torch.bool),policy_time_s=torch.arange(1,len(s)+1)*.01)['accepted']
 clock=Certificate(1,'cpu');s,p,e=trace(clock,velocity=.51)
 assert sum(r[1] for r in e)==1 and not any(r[2] for r in e)
 assert not score(s,p,torch.ones(len(s),dtype=torch.bool),policy_time_s=torch.arange(1,len(s)+1)*.01)['accepted']
 clock=Certificate(1,'cpu');s,p,e=trace(clock,seconds=10.21);assert sum(r[2] for r in e)==1

def test_deadline_fault_and_cross_rollout_no_early_window():
 clock=Certificate(1,'cpu')
 for i in range(250):
  pulse,failed,end,_=clock.observe(torch.tensor([.17]),torch.zeros(1,2),torch.zeros(1),torch.ones(1,2)*10,torch.ones(1)*.1,torch.zeros(1),torch.zeros(1),active=torch.ones(1,dtype=torch.bool),valid=torch.ones(1,dtype=torch.bool),safety_failed=torch.zeros(1,dtype=torch.bool),fault=torch.zeros(1,dtype=torch.bool))
 assert failed.item() and not pulse.item() and clock.entry.item()<0
 clock.reset(torch.tensor([0]));assert not clock.sent.item() and clock.count.item()==0

def test_recipe_public_config_requires_explicit_effective_reward():
 from native_stand.command_v6.config import validate
 from native_stand.students.requests import validate as student_validate
 from native_stand.students.training_recipe import declaration
 from native_stand.students.mcu_interface import contract
 spec={'interface_version':'multiskill_mcu_v2','student_interface':contract(),'action':{'dim':6,'leg_scale_rad':1.5,'wheel_scale_rad_s':100.},'observation':{'frame_dim':22,'actor_dim':31,'critic_dim':40},'history':{'frames':1,'dim':0,'includes_current':True,'validity_per_frame':False},'control':{},'budget':{'smoke_updates':12,'formal_updates':100},'student_evaluation':{'version':'student_evaluation_v1','cases':[],'max_output_bytes':1}}
 assert 'student first declaration is PPO0 only' in validate(spec)
 spec['student_training']=declaration();spec['student_training']['BC_coefficient']=.1
 assert any('recipe' in e for e in validate(spec))

def test_no_repeat_entry_bonus_or_partial_hold_success():
 clock=Certificate(1,'cpu');s,p,e=trace(clock,seconds=1.)
 assert sum(r[0] for r in e)==1 and not any(r[2] for r in e)
 assert clock.count.item()==80 and clock.entry.item()>0
 # Next interval is holding, even if a single invalid sample occurs: fixed window persists.
 previous=clock.count.item()
 clock.set_velocity(torch.zeros(1,3))
 clock.observe(torch.tensor([.4]),torch.zeros(1,2),torch.zeros(1),torch.tensor([[0.,10.]]),torch.tensor([.1]),torch.zeros(1),torch.zeros(1),active=torch.ones(1,dtype=torch.bool),valid=torch.ones(1,dtype=torch.bool),safety_failed=torch.zeros(1,dtype=torch.bool),fault=torch.zeros(1,dtype=torch.bool))
 assert clock.count.item()==previous+1 and clock.hard_failed.item() and not clock.entry_confirmed.item()

def test_source_earlier_candidate_tie_and_no_height_reward_selection():
 from native_stand.students.training import choose
 rows=[{'checkpoint':'source','update':0,'per_env':[{'accepted':False,'entry_index':None,'valid_hold_prefix_s':0.}]},
       {'checkpoint':'new','update':25,'per_env':[{'accepted':False,'entry_index':None,'valid_hold_prefix_s':0.}]}]
 selection=choose(rows);assert selection['best_overall']['checkpoint']=='source' and selection['accepted_candidate'] is None
 rows[1]['per_env'][0]['entry_index']=20
 assert choose(rows)['best_overall']['checkpoint']=='new'
