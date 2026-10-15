"""File-boundary verification for one explicitly authorized progressive course."""
import json
from pathlib import Path
from .data import sha
from .motion_course import configuration,stage_config,commands,VERSION

def verify(spec):
 from .motion_guard import configuration as guard,protocol
 from .motion_tracking_reward import configuration as reward,QUALITY_VERSION
 from .training_recipe import validate_instance
 from .motion_training import short_wiring
 c=spec['motion_course']
 if c.get('configuration',{}).get('version')=='motion31_forward_progression_v1':
  from .motion_forward_requests import verify
  return verify(spec)
 if set(c)!={'configuration','source_parent_spec','source_parent_spec_sha256','confirmation_spec','confirmation_spec_sha256','confirmation_run','source_recipe_updates'} or c['configuration']!=configuration():raise ValueError('explicit progressive course differs')
 parent=Path(c['source_parent_spec']);confirmation=Path(c['confirmation_spec']);run=Path(c['confirmation_run'])
 if sha(parent)!=c['source_parent_spec_sha256'] or sha(confirmation)!=c['confirmation_spec_sha256']:raise ValueError('course provenance differs')
 p=json.loads(parent.read_text());v=json.loads(confirmation.read_text());terminal=json.loads((run/'terminal_report.json').read_text());book=json.loads(confirmation.with_name('budget.json').read_text())
 if terminal['status']!='COMPLETED' or terminal.get('failure') or any(a['status']=='RUNNING' for a in book['attempts'].values()):raise ValueError('three seed confirmation not settled')
 if spec['source_checkpoint']!=v['source_checkpoint'] or spec['source_sha256']!=v['source_sha256'] or sha(spec['source_checkpoint'])!=spec['source_sha256']:raise ValueError('certified source differs')
 conditions=terminal['conditions']
 if len(conditions)!=15:raise ValueError('complete three seed proof required')
 for case,row in zip(v['student_evaluation']['cases'],conditions):
  path=run/row['result']
  if path.parent!=run or Path(row['result']).name!=row['result']:raise ValueError('confirmation evidence path invalid')
  raw=json.loads(path.read_text())
  if row['status']!='COMPLETED' or raw['checkpoint_sha256']!=spec['source_sha256'] or raw['protocol']!=protocol() or raw['case']!=case or raw.get('spec_sha256')!=sha(confirmation) or len(raw['per_env'])!=8 or not all(e['accepted'] for e in raw['per_env']):raise ValueError('source120/120 proof missing')
 if not 0<spec['budget']['formal_updates']<=1995 or spec['budget']['smoke_updates']!=5 or spec['budget']['sample_limit']!=(spec['budget']['formal_updates']+5)*65536:raise ValueError('inclusive2000 course budget differs')
 if spec['budget']['chain_wall_s']!=64800 or spec['budget']['formal_wall_s']!=57600:raise ValueError('course wall guard differs')
 if spec['reward']!=reward(QUALITY_VERSION) or spec['student_training']['reward']!=spec['reward']:raise ValueError('v3 reward preserved required')
 r=validate_instance(spec['student_training'],spec['source_sha256'])
 expected_wiring=short_wiring()
 if spec.get('motion_startup'):
  from .motion_startup import smoke_profile,resolve
  expected_wiring=smoke_profile();resolve(spec)
 if r.get('course_stage')!=0 or r.get('course_version')!=VERSION or r.get('smoke_wiring')!=expected_wiring:raise ValueError('course recipe explicit stage differs')
 if spec['motion_training'].get('early_stop_policy')!=guard() or spec['motion_assessment']!=protocol():raise ValueError('absolute scoring/retention differs')
 if spec['curriculum']['stages']!=[stage_config(0)] or spec['student_training']['milestones']!=list(range(250,1996,250)):raise ValueError('course sampling/cadence differs')
 if spec['student_evaluation']['version']!=protocol()['version'] or [r['command'] for r in spec['student_evaluation']['cases']]!=[v+[.34] for v in commands(0)]:raise ValueError('initial course7case matrix differs')
 for k in ('action','control','ground','observation','history','ppo','student_interface'):
  if spec[k]!=p[k]:raise ValueError('course contract drift:'+k)
 import torch
 cp=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
 if cp.get('recipe_updates')!=c['source_recipe_updates'] or cp.get('critic_privileged_version')!='motion_privileged49_v1' or not all(k in cp for k in ('actor','critic','optimizer','training_rng','reward_refinement_state')):raise ValueError('source full state required')
 if {g['lr'] for g in cp['optimizer']['param_groups']}!={3e-5}:raise ValueError('source Adam LR differs')
 return True

def restore(ppo,source,spec,phase):
 import copy
 from .resume import restore_rng
 ppo.actor.load_state_dict(source['actor']);ppo.critic.load_state_dict(source['critic']);ppo.optimizer.load_state_dict(source['optimizer']);restore_rng(source['training_rng'])
 from .motion_course import implementation
 course=implementation(spec.get('student_training',{}).get('course_version',VERSION))
 ppo.reward_refinement_state=course.extend_mixture(source['reward_refinement_state'],course.commands(0))
 return {'source_critic_loaded':True,'source_Adam_loaded':True,'source_RNG_loaded':True,'source_mixture_loaded':True,'phase':phase,'physical_state_restored':False,'warmup':'shortsmoke4critic+1actor; formal first5critic adaptation to new tasks; counted in budget'}
