"""Bounded tensor transport benchmark, no Isaac/model/optimizer/training."""
import argparse,json,time
import numpy as np
import torch
from native_stand.students.performance import DeviceTrace

def benchmark(device='cpu',steps=128,repeats=3):
 if steps<1 or steps>3152 or repeats<1 or repeats>5:raise ValueError('bounded benchmark size required')
 device=torch.device(device)
 # Representative eight-scored-env schemas; retain bool/int/float dtypes.
 fields={'actor_input':31,'critic_input':49,'root_pre':13,'root_post':13,'joint_q_pre':16,'joint_dq_pre':16,'previous_targets':6,'raw_action':6,'mean':6,'actor_valid':1,'state':39,'posture':10,'control':54,'geometry':13,'controller':1,'termination_causes':6,'student_task_events':5}
 values={k:torch.arange(8*v,device=device,dtype=torch.float32).reshape(8,v) for k,v in fields.items()}
 values['actor_valid']=values['actor_valid'].bool();values['termination_causes']=values['termination_causes'].bool();values['controller']=values['controller'].long()
 values['first_episode_valid']=torch.ones(8,device=device,dtype=torch.bool)
 def sync():
  if device.type=='cuda':torch.cuda.synchronize(device)
 def old():
  rows={k:[] for k in values}
  for _ in range(steps):
   for k,v in values.items():rows[k].append(v.cpu().numpy().copy())
  return {k:np.stack(v) for k,v in rows.items()}
 def new():
  trace=DeviceTrace(steps,256*2**20)
  for _ in range(steps):
   for k,v in values.items():trace.add(k,v)
  return trace.export()
 old_result=old();new_result=new()
 for k in values:np.testing.assert_array_equal(old_result[k],new_result[k])
 times={'legacy':[],'device_buffer':[]}
 for _ in range(repeats):
  for label,fn in [('legacy',old),('device_buffer',new)]:
   sync();start=time.perf_counter();result=fn();sync();times[label].append(time.perf_counter()-start)
 import statistics
 med={k:statistics.median(v) for k,v in times.items()}
 return {'device':str(device),'steps':steps,'fields':len(values),'scored_envs':8,'timings_s':times,'median_s':med,'transport_speedup':med['legacy']/med['device_buffer'],
  'logical_host_transfer_calls':{'legacy':steps*len(values),'device_buffer':len(values)},'arrays_exact_equal':True,
  'scope':'synthetic representative tensor transport only; no PhysX stepping, inference, PPO or end-to-end speedup claim','simulation':0,'optimizer_updates':0}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',default='cpu');p.add_argument('--steps',type=int,default=128);p.add_argument('--repeats',type=int,default=3);a=p.parse_args();print(json.dumps(benchmark(a.device,a.steps,a.repeats),indent=2))
