"""Full same-recipe checkpoint continuation, explicit physical reset separate."""
import random
import numpy as np
import torch

def rng_state():
 return {'python':random.getstate(),'numpy':np.random.get_state(),'torch_cpu':torch.get_rng_state(),'torch_cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None}

def restore_rng(state):
 if set(state)!={'python','numpy','torch_cpu','torch_cuda'}:raise ValueError('training RNG incomplete')
 random.setstate(state['python']);np.random.set_state(state['numpy']);torch.set_rng_state(state['torch_cpu'].cpu())
 if state['torch_cuda'] is not None:
  if not torch.cuda.is_initialized() or len(state['torch_cuda'])!=torch.cuda.device_count():raise ValueError('resume CUDA mapping differs')
  torch.cuda.set_rng_state_all([x.cpu() for x in state['torch_cuda']])

def restore(ppo,data,recipe):
 if data.get('course_resume_version')!='student_full_training_resume_v1' or data['recipe_version']!=recipe['version']:raise ValueError('normal continuation requires same recipe full state')
 if data['interface_version']!='multiskill_mcu_v2' or not data.get('fixed_std'):raise ValueError('resume interface/std differs')
 ppo.actor.load_state_dict(data['actor']);ppo.critic.load_state_dict(data['critic']);ppo.optimizer.load_state_dict(data['optimizer'])
 restore_rng(data['training_rng'])
 return {'cumulative_update':data['cumulative_update'],'recipe_updates':data['recipe_updates'],'physical_state':'NOT_RESTORED; real process env reset recorded','Adam_state_count':len(ppo.optimizer.state),'warmup_repeated':False}
