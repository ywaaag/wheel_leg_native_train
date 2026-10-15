"""Opt-in evidence transport optimizations; no actions, RNG or optimizer changes."""
import torch

VERSION='student_performance_v1'
def settings(spec):
 defaults={'version':VERSION,'evaluation_gpu_buffer':False,'evaluation_reuse_environment':False,
  'training_gpu_statistics':False,'failure_tail_on_device':False,'trace_buffer_max_bytes':256*2**20}
 cfg=spec.get('performance')
 if cfg is None:return defaults
 if not isinstance(cfg,dict) or set(cfg)-set(defaults):raise ValueError('unknown student performance fields')
 cfg={**defaults,**cfg}
 if cfg['version']!=VERSION or any(type(cfg[k]) is not bool for k in defaults if k not in ('version','trace_buffer_max_bytes')):raise ValueError('invalid student performance version/flags')
 if type(cfg['trace_buffer_max_bytes']) is not int or cfg['trace_buffer_max_bytes']<=0:raise ValueError('positive trace buffer byte limit required')
 if cfg['evaluation_reuse_environment']:
  if spec.get('recovery_course') or any(r['kind']!='student' or r['family']!='motion_native_normal' for r in spec.get('student_evaluation',{}).get('cases',[])):
   raise ValueError('environment reuse only for independent normal student cases')
 return cfg

class DeviceTrace:
 """Preallocated per-field device copies; export only at episode/fault boundary."""
 def __init__(self,steps,max_bytes):
  self.steps=steps;self.max_bytes=max_bytes;self.buffers={};self.counts={};self.allocated_bytes=0;self.host_transfers=0
 def add(self,name,value):
  value=value.detach()
  if name not in self.buffers:
   size=self.steps*value.numel()*value.element_size()
   if self.allocated_bytes+size>self.max_bytes:raise ValueError('evaluation GPU trace byte limit exceeded')
   self.buffers[name]=torch.empty((self.steps,*value.shape),dtype=value.dtype,device=value.device)
   self.counts[name]=0;self.allocated_bytes+=size
  buffer=self.buffers[name];index=self.counts[name]
  if value.shape!=buffer.shape[1:] or value.dtype!=buffer.dtype or value.device!=buffer.device or index>=self.steps:raise ValueError('trace field shape/dtype/device/count differs')
  buffer[index].copy_(value);self.counts[name]+=1
 def export(self,*,completed=None,pre_only=False):
  pre_fields={'actor_input','critic_input','root_pre','joint_q_pre','joint_dq_pre','previous_targets','raw_action','mean','actor_valid'}
  result={}
  for name,value in self.buffers.items():
   n=self.counts[name]
   if pre_only and name not in pre_fields:continue
   if completed is not None:
    if n<completed:continue
    n=completed
   if n:
    result[name]=value[:n].cpu().numpy().copy();self.host_transfers+=1
  return result

class RolloutCounts:
 """Integer counts and exact episode duration samples; one export per rollout."""
 def __init__(self,steps,envs,device):
  self.counts=torch.zeros(8,dtype=torch.long,device=device)
  self.duration=torch.zeros(steps,envs,device=device);self.done=torch.zeros(steps,envs,dtype=torch.bool,device=device);self.step=0
 def observe(self,valid,rewards,dones,state,events,posture,handoffs=None,*,episode_duration_s=None):
  self.counts+=torch.stack((valid.sum(),(rewards!=0).sum(),dones.sum(),events[:,0].sum(),events[:,1].sum(),events[:,2].sum(),
   ((posture[:,2:4]<=.34).all(-1)&valid).sum(),handoffs.sum() if handoffs is not None else torch.zeros((),dtype=torch.long,device=valid.device))).long()
  duration=state[:,0] if episode_duration_s is None else episode_duration_s
  if duration.shape!=valid.shape:raise ValueError('episode duration shape differs')
  self.duration[self.step].copy_(duration);self.done[self.step].copy_(dones);self.step+=1
 def export(self):
  counts=self.counts.cpu().tolist();duration=self.duration[:self.step].cpu().numpy();done=self.done[:self.step].cpu().numpy()
  return counts,duration[done].tolist()

def tail_arrays(tail):
 import numpy as np
 return {k:torch.stack([r[k] for r in tail]).cpu().numpy() if isinstance(tail[0][k],torch.Tensor)
  else np.stack([r[k] for r in tail]) for k in tail[0]}

def reuse_key(row):
 return (row['kind'],row['role'],row['family'])

class EvaluationEnvironment:
 """Owner of a single compatible environment; reset happens in every rollout."""
 def __init__(self,enabled,factory):self.enabled=enabled;self.factory=factory;self.env=None;self.key=None;self.creations=0;self.reuses=0
 def acquire(self,row):
  key=reuse_key(row)
  if self.env is not None and self.enabled and key==self.key:self.reuses+=1;return self.env
  self.close();self.env=self.factory(row);self.key=key;self.creations+=1;return self.env
 def close(self):
  env,self.env=self.env,None
  if env is not None:env.close()
