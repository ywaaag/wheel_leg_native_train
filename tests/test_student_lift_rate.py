"""Finite new cost and chronological diagnostic, old reward remains exact."""
FROZEN_TEST_SCOPE='PORTABLE'
import pytest,torch
from native_stand.students.recovery_task import configuration,NO_FAILURE_VERSION,LIFT_RATE_VERSION,reward,pre_entry_angular_cost
from native_stand.students.training_recipe import declaration,NO_FAILURE_RECIPE,LIFT_RATE_RECIPE
from native_stand.students.history_diagnostic import history_rows

def test_lift_rate_gate_deadband_axes_bounds_and_mask():
 c=configuration(LIFT_RATE_VERSION);h=torch.tensor([.168,.20,.225,.25,.30,.40]);ang=torch.zeros(6,3);ang[:,0]=6
 entered=torch.zeros(6,dtype=torch.bool);valid=~entered;fault=entered
 r=pre_entry_angular_cost(h,ang,entered,valid,fault,c)
 torch.testing.assert_close(r,torch.tensor([0.,0.,4.5,9.,9.,9.]))
 ang[:,0]=3;assert pre_entry_angular_cost(h,ang,entered,valid,fault,c).eq(0).all()
 ang[:,0]=0;ang[:,1]=100;assert pre_entry_angular_cost(h,ang,entered,valid,fault,c).eq(0).all()
 ang[:,0]=100
 assert pre_entry_angular_cost(h,ang,valid,valid,fault,c).eq(0).all()
 assert pre_entry_angular_cost(h,ang,entered,entered,fault,c).eq(0).all()
 assert pre_entry_angular_cost(h,ang,entered,valid,valid,c).eq(0).all()

def test_new_cost_dt_once_does_not_change_existing_terms_or_events():
 z=torch.zeros(1);b=torch.ones(1,dtype=torch.bool);f=~b;ang=torch.tensor([[6.,0.,0.]])
 args=(z+.30,z+.168,torch.zeros(1,2),torch.ones(1,2)*10,z+.01,torch.zeros(1,6),torch.zeros(1,6),torch.zeros(1,6),ang,torch.zeros(1,3),z,f,b,f,f,f,f)
 a=reward(*args,reward_configuration=configuration(NO_FAILURE_VERSION));c=reward(*args,reward_configuration=configuration(LIFT_RATE_VERSION))
 for k in ('raw','weighted_density','continuous_dt','events'):assert torch.equal(a[k],c[k])
 assert (c['total']-a['total']).item()==pytest.approx(-.018)
 assert c['pre_entry_angular_dt'].item()==pytest.approx(-.018)
 v=declaration(LIFT_RATE_RECIPE);old=declaration(NO_FAILURE_RECIPE)
 assert {k for k in old if old[k]!=v[k]}=={'version','reward'}
 assert v['reward']['failure_once']==0 and v['BC_coefficient']==0

def test_history_probe_no_future_no_cross_episode_and_gaps_invalid():
 x=torch.arange(11.).view(-1,1).expand(11,31).clone();data={'x':x,'episode':torch.tensor([0]*5+[1]*6),'sample':torch.tensor([0,1,2,3,4,0,1,2,4,5,6])}
 h,valid=history_rows(data)
 assert valid.tolist()==[False]*4+[True]+[False]*6
 assert h[4,:,0].tolist()==[0.,1.,2.,3.,4.]
 assert h[5].eq(0).all()
 data['sample'][8:]=torch.tensor([3,4,5]);h,valid=history_rows(data)
 assert valid[9] and valid[10] and h[9,:,0].tolist()==[5.,6.,7.,8.,9.]
 with pytest.raises(ValueError):history_rows({'x':torch.zeros(2,1182),'episode':torch.zeros(2),'sample':torch.arange(2)})
