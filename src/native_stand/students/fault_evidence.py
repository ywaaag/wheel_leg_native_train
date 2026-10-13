"""Named, full-environment pre-reset fault evidence; no safety-policy changes."""
import torch
from native_stand.command_v6.domain.trace_schema import STATE

def capture(state,rewards,components,joint_data=None):
 if state.ndim!=2 or state.shape[1]!=39 or rewards.shape!=(state.shape[0],):raise ValueError('fault evidence shape differs')
 masks={'runtime_fault':state[:,STATE['runtime_fault']].bool(),
        'initial_rejected':state[:,STATE['initial_rejected']].bool(),
        'nonfinite_reward':~torch.isfinite(rewards)}
 bad=torch.stack(tuple(masks.values())).any(0)
 if not bad.any():return None
 if any(v.shape!=(state.shape[0],) for v in components.values()):raise ValueError('full environment fault components missing/misaligned')
 ids=bad.nonzero().flatten()
 result={'env_ids':ids,'state':state[ids].clone(),'reward':rewards[ids].clone(),
         **{k:v[ids].clone() for k,v in masks.items()},
         **{'component_'+k:v[ids].clone() for k,v in components.items()}}
 for k,v in (joint_data or {}).items():
  if v.shape[0]!=state.shape[0]:raise ValueError('fault joint metadata environment axis differs')
  result['joint_evidence_'+k]=v[ids].clone()
 return result
