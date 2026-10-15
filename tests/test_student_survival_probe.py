FROZEN_TEST_SCOPE='PORTABLE'
import torch
from native_stand.students.survival_probe import SurvivalObserver,score

def test_bad_entry_and_quality_never_stop_survival_but_safety_does():
 c=SurvivalObserver(1,'cpu');o=torch.ones(1);yes=o.bool();no=~yes
 c.set_joint(torch.zeros(1,4));c.set_offset(o*.05);c.set_velocity(torch.zeros(1,3))
 for _ in range(3000):
  success,failure,end,fault=c.observe(o*.34,torch.tensor([[.20,0.]]),o*.20,torch.ones(1,2)*20,o*.1,o*0,o*0,active=yes,valid=yes,safety_failed=no,fault=no)
  assert not success and not failure and not end
 _,failure,end,_=c.observe(o*.34,torch.tensor([[.20,0.]]),o*.20,torch.ones(1,2)*20,o*.1,o*0,o*0,active=yes,valid=yes,safety_failed=yes,fault=no)
 assert failure and end

def test_survival_not_quality_and_incomplete_never_passes():
 s=torch.zeros(3000,39);s[:,6]=.34;s[:,10:12]=20;s[:,29]=1
 p=torch.zeros(3000,10);p[:,0]=.20;g=torch.zeros(3000,13);g[:,7]=-1
 r=score(s,p,g,controlled=torch.ones(3000,dtype=torch.bool),valid=torch.ones(3000,dtype=torch.bool))
 assert r['survival_passed'] and not r['quality_screen_passed'] and not r['accepted']
 r=score(s[:-1],p[:-1],g[:-1],controlled=torch.ones(2999,dtype=torch.bool),valid=torch.ones(2999,dtype=torch.bool))
 assert not r['survival_passed']
