"""Explicit frozen student-to-Motion probe; pure protocol and clock helpers."""
import math
from native_stand.recovery.handoff_protocol import declaration as protocol,duration,prefix_steps
VERSION='student_motion_probe_v1'
KIND='student_prefix_motion'
B250_SHA='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e'

def validate(spec):
 section=spec['student_evaluation'];cases=section['cases']
 if set(section)!={'version','cases','max_output_bytes','handoff_protocol'} or section['version']!=VERSION:raise ValueError('student Motion probe fields differ')
 if section['handoff_protocol']!=protocol():raise ValueError('student Motion probe requires main fixed handoff protocol')
 if not spec.get('evaluation_only') or spec.get('student_training') or spec['budget']['smoke_updates'] or spec['budget']['formal_updates']:raise ValueError('student Motion probe is PPO0 only')
 if spec.get('evaluation',{}).get('envs')!=64 or spec.get('evaluation',{}).get('scored_envs')!=8:raise ValueError('student Motion probe requires64 simulated/8 scored')
 if len(spec['student_teachers'])!=2 or spec['student_teachers'][1]['sha256']!=B250_SHA:raise ValueError('fixed Motion B250 teacher identity required')
 if not cases or cases[0]['kind']!='teacher_normal':raise ValueError('Motion native baseline first required')
 if cases[0]['family']!='motion_native_normal':raise ValueError('Motion native baseline family differs')
 if cases[0]['sha256']!=B250_SHA:raise ValueError('normal baseline must use Motion B250')
 for row in cases:
  if row['kind'] not in ('teacher_normal','teacher_combination',KIND):raise ValueError('unknown student Motion probe kind')
  expected={'case_id','kind','checkpoint','sha256','family','seed','yaw_rad','seconds','role'}|({'switch_s'} if row['kind']==KIND else set())
  if set(row)!=expected:raise ValueError('unknown student Motion probe case fields')
  if row['kind']==KIND:
   prefix_steps(row['switch_s'])
   if row['role']!='RecoveryStudent' or row['family']!='swing_candidate_from_historical_r1':raise ValueError('student prefix initial family/role differs')
   seconds=duration(row['switch_s'],spec['recovery']['initialization']['settle_max_s'])
   if not math.isclose(row['seconds'],seconds,abs_tol=1e-9):raise ValueError('probe duration differs')
  elif row['seconds']!=13.52:raise ValueError('teacher baseline/comparison duration differs')
 for t in spec['student_teachers']:
  if set(t)!={'checkpoint','sha256','spec','spec_sha256'}:raise ValueError('teacher identity fields differ')

def owners(initializing,valid,prefix_count,switch_steps):
 import torch
 active=(~initializing)&valid
 motion=active&(prefix_count>=switch_steps)
 student=active&~motion
 return torch.where(motion,2,torch.where(student,3,0)),student,motion
