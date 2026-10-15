FROZEN_TEST_SCOPE='PORTABLE'
import copy
import pytest,torch
from native_stand.students.motion_guard import configuration,advance,assess,protocol

def record(command,*,bad=False,missing=False):
 rows=[]
 for i in range(8):
  t={'MAE':.8 if bad else .1,'direction':.7 if bad else 1.,'horizontal_steady_p95_mps':.6 if bad else .05,'pitch_hold_abs_max_rad':.03,'roll_hold_abs_max_rad':.00001}
  if missing:t.pop('MAE')
  rows.append({'env':i,'accepted':not bad,'survival_passed':True,'tracking':t,'checks':{}})
 return {'case':{'command':command},'per_env':rows}

def test_guard_adaptation_then_same_command_three_fixed_checks():
 commands=[[.5,0,.34],[-.5,0,.34]];base=[record(c) for c in commands];bad=[record(c,bad=True) for c in commands]
 state,d=advance({},bad,base,250);assert not d['stop'] and list(state['commands'].values())==[0,0]
 for u in (500,750):state,d=advance(state,bad,base,u);assert not d['stop']
 state,d=advance(state,bad,base,1000);assert d['stop']

def test_different_commands_do_not_accumulate_into_global_failure():
 commands=[[.5,0,.34],[-.5,0,.34]];base=[record(c) for c in commands];state={}
 for u,i in ((500,0),(750,1),(1000,0),(1250,1)):
  records=copy.deepcopy(base);records[i]=record(commands[i],bad=True)
  state,d=advance(state,records,base,u);assert not d['stop']
 assert max(state['commands'].values())==1

def test_unknown_neither_promotes_nor_counts_behavior_failure():
 c=[.5,0,.34];base=[record(c)];state,d=advance({},[record(c,missing=True)],base,500)
 assert d['decisions'][0]['evidence']=='UNKNOWN' and not d['decisions'][0]['promotion_allowed'] and not d['stop']
 state,d=advance(state,[record(c,bad=True)],base,750);assert not d['stop']
 with pytest.raises(ValueError,match='advance'):advance(state,base,base,750)

def test_micro_roll_and_small_tracking_fluctuations_do_not_stop():
 c=[.5,0,.34];base=[record(c)];candidate=record(c)
 for row in candidate['per_env']:row['tracking']['roll_hold_abs_max_rad']=.001;row['tracking']['MAE']=.35;row['accepted']=False
 state={}
 for u in (500,750,1000,1250):state,d=advance(state,[candidate],base,u);assert not d['stop']

def test_complete_absolute_maxima_and_failure_window():
 n=3000;state=torch.zeros(n,39);state[:,29]=1;posture=torch.zeros(n,10);posture[:,0]=.03;posture[:,1]=.001;world=torch.zeros(n,3);controlled=torch.ones(n,dtype=torch.bool)
 result={'accepted':False,'checks':{'survival30':True,'roll_source_guard':False},'tracking':{}}
 original=copy.deepcopy(result);r=assess(result,posture,state,controlled,world)
 assert result==original and r['accepted'] and r['tracking']['pitch_hold_abs_max_rad']==pytest.approx(.03)
 posture[1200,0]=.11;r=assess(result,posture,state,controlled,world);assert not r['accepted'] and not r['checks']['pitch_absolute_quality']
 r=assess(result,posture[:2000],state[:2000],controlled[:2000],world[:2000]);assert not r['accepted'] and not r['checks']['absolute_posture_complete_window']
 assert protocol()['schedule_s']==[2.,8.,8.,8.]

def test_runtime_fault_and_survival_paths():
 c=[0.,0.,.34];base=[record(c)];bad=record(c)
 bad['per_env'][0]['runtime_fault']=True
 _,d=advance({},[bad],base,100);assert d['stop']
 bad=record(c)
 for row in bad['per_env'][:3]:row['survival_passed']=False
 state={}
 for u in (500,750,1000):state,d=advance(state,[bad],base,u)
 assert d['stop']


def test_missing_fixed_checkpoint_breaks_consecutive_regression_streak():
 c=[.5,0,.34];base=[record(c)];bad=[record(c,bad=True)]
 state,_=advance({},bad,base,500)
 state,d=advance(state,bad,base,1000)
 assert max(state['commands'].values())==1 and not d['stop']
