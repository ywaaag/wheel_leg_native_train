"""Current-Actor wheel mean regularization on valid adjacent rollout inputs."""
import torch
VERSION='student_wheel_temporal_v1'

def declaration(arm):
 if arm not in ('A','B'):raise ValueError('unknown temporal arm')
 return {'version':VERSION,'arm':arm,'coefficient':0. if arm=='A' else .01,'max_pairs_per_minibatch':256,'pair_seed':20261012,'wheel_scale_rad_s':100.,'difference_scale_rad_s':10.,'scope':'same_episode_10ms_student_hold_adjacent','both_means_gradient':True}

def pairs(observations,student,entered,episode,time_s,done):
 if observations.ndim!=3 or observations.shape[-1]!=31:raise ValueError('temporal requires time/env/31D')
 shape=observations.shape[:2]
 if any(v.shape!=shape for v in (student,entered,episode,time_s,done)):raise ValueError('temporal metadata misaligned')
 valid=student[1:]&student[:-1]&entered[1:]&entered[:-1]&~done[:-1]&~done[1:]&(episode[1:]==episode[:-1])&((time_s[1:]-time_s[:-1]-.01).abs()<2e-6)
 if not torch.isfinite(observations).all() or not torch.isfinite(time_s).all():raise ValueError('nonfinite temporal inputs')
 return observations[:-1][valid].detach().clone(),observations[1:][valid].detach().clone()

class Regularizer:
 def __init__(self,configuration,device):
  if configuration!=declaration(configuration.get('arm')):raise ValueError('temporal configuration differs')
  self.cfg=configuration;self.generator=torch.Generator(device=device).manual_seed(configuration['pair_seed']);self.previous=self.current=None
 def set_pairs(self,previous,current):
  if previous.shape!=current.shape or previous.ndim!=2 or previous.shape[-1]!=31:raise ValueError('temporal pair shapes differ')
  self.previous=previous.detach();self.current=current.detach()
 def loss(self,actor):
  zero=next(actor.parameters()).new_zeros(())
  if not self.cfg['coefficient'] or self.previous is None or not len(self.previous):return zero,0
  n=min(len(self.previous),self.cfg['max_pairs_per_minibatch'])
  ids=torch.randperm(len(self.previous),generator=self.generator,device=self.previous.device)[:n]
  # Pure mean bypasses the PPO distribution cache and draws no policy samples.
  left=actor.mean(self.previous[ids])[:,[2,5]];right=actor.mean(self.current[ids])[:,[2,5]]
  return ((100.*right-100.*left)/10.).square().mean(),n
