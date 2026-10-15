FROZEN_TEST_SCOPE='PORTABLE'
import copy
from types import SimpleNamespace
import numpy as np
import pytest
import torch
from native_stand.students.performance import DeviceTrace,RolloutCounts,EvaluationEnvironment,settings,tail_arrays

def test_trace_preserves_mutating_sources_dtypes_and_partial_boundaries():
 trace=DeviceTrace(4,10000);x=torch.zeros(2,3);legacy=[]
 for step in range(3):
  x.fill_(step);trace.add('state',x);legacy.append(x.numpy().copy());trace.add('first_episode_valid',torch.tensor([True,step<1]))
 x.fill_(99);trace.add('actor_input',x)
 result=trace.export(completed=3)
 np.testing.assert_array_equal(result['state'],np.stack(legacy));assert result['first_episode_valid'].dtype==np.bool_
 assert 'actor_input' not in result
 assert trace.export(pre_only=True)['actor_input'][0,0,0]==99
 with pytest.raises(ValueError,match='byte'):DeviceTrace(4,1).add('state',x)
 with pytest.raises(ValueError,match='shape'):trace.add('state',torch.zeros(2,4))

def test_rollout_counts_exactly_match_legacy_and_do_not_consume_rng():
 rng=torch.get_rng_state().clone();stats=RolloutCounts(4,3,'cpu');expected=np.zeros(8,dtype=np.int64);duration=[]
 for step in range(4):
  valid=torch.tensor([True,True,False]);reward=torch.tensor([1.,0.,-1.]);done=torch.tensor([step==1,step==3,False]);s=torch.zeros(3,39);s[:,0]=step*.1
  ev=torch.tensor([[True,False,True,False,False],[False,True,False,False,False],[False,False,False,False,False]])
  posture=torch.zeros(3,10);handoff=torch.tensor([False,True,False])
  stats.observe(valid,reward,done,s,ev,posture,handoff)
  expected+=np.array([2,2,int(done.sum()),1,1,1,2,1]);duration+=s[done,0].tolist()
 counts,actual=stats.export();assert counts==expected.tolist() and actual==duration
 assert torch.equal(rng,torch.get_rng_state())

def test_pool_compatibility_and_single_close():
 created=[]
 class Env:
  def __init__(self):self.closed=0
  def close(self):self.closed+=1
 def factory(row):e=Env();created.append(e);return e
 pool=EvaluationEnvironment(True,factory);row={'kind':'student','role':'RecoveryStudent','family':'normal'}
 a=pool.acquire(row);assert pool.acquire({**row,'seed':2}) is a
 b=pool.acquire({**row,'family':'other'});assert b is not a and a.closed==1
 pool.close();pool.close();assert b.closed==1 and pool.creations==2 and pool.reuses==1

def test_profile_default_off_and_reuse_scope_rejected():
 assert not settings({})['evaluation_gpu_buffer']
 with pytest.raises(ValueError,match='unknown'):settings({'performance':{'magic':True}})
 with pytest.raises(ValueError,match='independent'):settings({'performance':{'evaluation_reuse_environment':True},'recovery_course':{'resume':True}})
 old=[{'x':np.array([1,2])},{'x':np.array([3,4])}];new=[{'x':torch.tensor([1,2])},{'x':torch.tensor([3,4])}]
 np.testing.assert_array_equal(tail_arrays(old)['x'],tail_arrays(new)['x'])

class FakeEnv:
 def __init__(self,buffered=False,fault_at=None):
  self.num_envs=2;self.device='cpu';self.interface_version='multiskill_mcu_v2';self.ids=list(range(6));self.n=0;self.fault_at=fault_at
  self.fsm=SimpleNamespace(mode=torch.ones(2,dtype=torch.long)*2);self.initialization_checked=torch.ones(2,dtype=torch.bool)
  self.student_performance={'evaluation_gpu_buffer':buffered,'trace_buffer_max_bytes':100000}
  self.executed_leg=torch.zeros(2,4);self.executed_wheel=torch.zeros(2,2)
  self.robot=SimpleNamespace(data=SimpleNamespace(root_state_w=SimpleNamespace(torch=torch.zeros(2,13)),joint_pos=SimpleNamespace(torch=torch.zeros(2,6)),joint_vel=SimpleNamespace(torch=torch.zeros(2,6))))
  self.recovery_snapshot=torch.zeros(2,39);self.recovery_snapshot[:,29]=1;self.standing_snapshot=torch.zeros(2,10);self.recovery_control_snapshot=torch.zeros(2,54);self.wheel_geometry_snapshot=torch.zeros(2,13);self.student_root_post=torch.zeros(2,13);self.recovery_cause_snapshot=torch.zeros(2,6,dtype=torch.bool)
 def select_initial_family(self,*args):pass
 def reset(self):self.n=0;return {'student_actor':torch.zeros(2,31),'student_critic':torch.zeros(2,49)},{}
 def step(self,action):
  self.n+=1
  if self.n==self.fault_at:raise RuntimeError('fixture physics fault')
  self.recovery_snapshot[:,0]=self.n*.01;self.recovery_snapshot[:,7]=self.n*.1
  self.recovery_control_snapshot[:,0]=self.n
  self.student_root_post[:,0]=self.n
  return {'student_actor':torch.full((2,31),float(self.n)),'student_critic':torch.zeros(2,49)},torch.zeros(2),torch.tensor([self.n==2,False]),torch.zeros(2,dtype=torch.bool),{}

class Actor(torch.nn.Module):
 def forward(self,obs,stochastic_output=False):return torch.zeros(2,6)

def test_real_rollout_legacy_vs_device_buffer_and_rng(monkeypatch):
 from native_stand.students.evaluator import rollout
 import native_stand.students.protocol as protocol
 monkeypatch.setattr(protocol,'score',lambda *a,**kw:{'accepted':False,'entry_index':None})
 row={'kind':'student','family':'normal','seconds':.04,'seed':7,'yaw_rad':0.}
 model=Actor().train();rng=torch.get_rng_state().clone()
 a,old=rollout(FakeEnv(),model,row,scored_envs=2);b,new=rollout(FakeEnv(True),model,row,scored_envs=2)
 assert a==b and torch.equal(rng,torch.get_rng_state()) and model.training
 assert set(old)==set(new)
 for k in old:np.testing.assert_array_equal(old[k],new[k])
 assert new['first_episode_valid'][:,0].tolist()==[True,True,False,False]

def test_real_rollout_fault_keeps_only_complete_intervals(monkeypatch):
 from native_stand.students.evaluator import rollout
 row={'kind':'student','family':'normal','seconds':.04,'seed':7,'yaw_rad':0.}
 errors=[]
 for buffered in (False,True):
  env=FakeEnv(buffered,fault_at=3)
  with pytest.raises(RuntimeError,match='fixture') as failure:rollout(env,Actor(),row,scored_envs=2)
  errors.append(failure.value.student_partial_arrays)
  assert not hasattr(env,'student_trace_capture')
 for k in errors[0]:np.testing.assert_array_equal(errors[0][k],errors[1][k])

@pytest.mark.parametrize('fail',[False,True])
def test_real_training_evaluation_pool_closes_and_restores_rng(tmp_path,monkeypatch,fail):
 import json
 import native_stand.students.training as training
 import sys
 tmp_path=tmp_path/'owned_chain'/'formal';tmp_path.mkdir(parents=True)
 spec={'performance':{'evaluation_reuse_environment':True},'student_evaluation':{'cases':[{'kind':'student','family':'motion_native_normal'}],'max_output_bytes':100000},
  'student_training':{'storage_max_bytes':1000000},'artifacts':{'terminal_reserve_bytes':10000},'asset_sha256':'a'*64}
 (tmp_path/'source_snapshot').mkdir();(tmp_path/'source_snapshot/spec.json').write_text(json.dumps(spec))
 created=[]
 class Env:
  ids=list(range(6));reference=torch.zeros(8,6);robot=SimpleNamespace(joint_names=['joint'])
  def __init__(self):self.closed=0;created.append(self)
  def close(self):self.closed+=1
 monkeypatch.setattr(training,'environment',lambda *a,**k:Env())
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.configure',SimpleNamespace(verify_asset_import=lambda s:{}))
 monkeypatch.setitem(sys.modules,'native_stand.command_v6.runtime.control_readback',SimpleNamespace(verify=lambda e:{},verify_ground=lambda e,s:{}))
 calls=[]
 def rollout(env,actor,row,**kw):
  calls.append(row['case_id']);torch.manual_seed(row['seed'])
  if fail and len(calls)==2:raise RuntimeError('fixture scoring fault')
  return {'per_env':[]},{'state':np.zeros((1,8,39))}
 monkeypatch.setattr(training,'rollout',rollout)
 cases=[{'case_id':str(i),'kind':'student','role':'RecoveryStudent','family':'motion_native_normal','seed':i,'sha256':'b'*64} for i in range(3)]
 rng=torch.get_rng_state().clone()
 if fail:
  with pytest.raises(RuntimeError,match='fixture'):training.evaluate_cases(spec,tmp_path,Actor(),cases)
 else:assert len(training.evaluate_cases(spec,tmp_path,Actor(),cases))==3
 assert len(created)==1 and created[0].closed==1 and torch.equal(rng,torch.get_rng_state())
