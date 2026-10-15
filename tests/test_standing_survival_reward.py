FROZEN_TEST_SCOPE='PORTABLE'
import torch,pytest
from native_stand.students.standing_survival_reward import reward,Episode

def state(n=1,dtype=torch.float64):
 z=lambda *s:torch.zeros(*s,dtype=dtype)
 return dict(height=z(n)+.34,angles=z(n,2),velocity_xy=z(n,2),yaw=z(n),contacts=z(n,2)+20,
  leg_q=z(n,4),wheel_offset=z(n),leg_lengths=z(n,2)+.3,angular_pitch_roll=z(n,2),
  applied_torque=z(n,6),previous_targets=z(n,6),executed_targets=z(n,6),
  controlled=torch.ones(n,dtype=torch.bool),valid=torch.ones(n,dtype=torch.bool),
  physical_failure=torch.zeros(n,dtype=torch.bool),fault=torch.zeros(n,dtype=torch.bool))

def test_units_no_double_dt_fault_and_actual_geometry():
 s=state();r=reward(**s)
 assert r['total'].item()==pytest.approx(.085)
 assert torch.equal(r['dt'],r['density']*.01) and r['events'].sum()==0
 for name in ('physical_failure','fault'):
  q=state();q[name][:]=True;assert reward(**q)['total'].item()==0
 q=state();q['leg_lengths'][0,1]=.38
 assert reward(**q)['total']<r['total']
 q=state();q['contacts'].zero_();assert reward(**q)['total']==0

@pytest.mark.parametrize('name,index,value',[('velocity_xy',(0,0),2.285),('velocity_xy',(0,1),.7),
 ('yaw',(0,),.7),('angles',(0,0),.23),('angles',(0,1),.20),('height',(0,),.40),
 ('wheel_offset',(0,),.05),('leg_lengths',(0,0),.38),('leg_q',(0,0),.20),('leg_q',(0,1),.20)])
def test_derivative_and_small_corrective_step_agree(name,index,value):
 s=state();s[name][index]=value;s[name].requires_grad_()
 out=reward(**s)['total'].sum();g=torch.autograd.grad(out,s[name])[0]
 assert torch.isfinite(g).all() and g[index]<0
 q={k:v.detach().clone() for k,v in s.items()};q[name][index]-=1e-5
 assert reward(**q)['total']>out.detach()

def test_far_speed_signal_and_velocity_symmetry():
 for speed in (.3,1.,2.285,2.72):
  s=state();s['velocity_xy'][0,0]=speed;s['velocity_xy'].requires_grad_()
  out=reward(**s)['total'].sum();g=torch.autograd.grad(out,s['velocity_xy'])[0][0,0]
  assert g<0 and g.abs()>1e-5
  q=state();q['velocity_xy'][0,0]=-speed
  assert reward(**q)['total'].item()==pytest.approx(out.item())
 s=state();s['wheel_offset'][0]=.005;s['wheel_offset'].requires_grad_()
 assert torch.autograd.grad(reward(**s)['total'].sum(),s['wheel_offset'])[0].item()==0

def test_episode_does_not_end_on_bad_entry_and_timeout_not_failure():
 e=Episode(2);yes=torch.ones(2,dtype=torch.bool);no=~yes
 for _ in range(2999):
  r=e.observe(controlled=yes,valid=yes,physical_failure=no,fault=no)
  assert not r['terminated'].any() and not r['truncated'].any()
 r=e.observe(controlled=yes,valid=yes,physical_failure=no,fault=no)
 assert r['truncated'].all() and not r['certificate_passed'].any()
 e.reset(torch.tensor([0]));assert e.steps.tolist()==[0,3000]
 r=e.observe(controlled=yes,valid=yes,physical_failure=torch.tensor([True,False]),fault=no)
 assert r['terminated'][0] and not r['truncated'][0]
