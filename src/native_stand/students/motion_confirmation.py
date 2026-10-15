"""File-boundary validator for trained Motion31 three-evaluation-seed PPO0."""
import json
from pathlib import Path
from .data import sha
VERSION='motion31_source_three_seed_confirmation_v1'
SEEDS=[20261014,20261015,20261016]
def verify(spec):
 from .motion_guard import protocol
 from .motion_training import commands
 from .motion_tracking_reward import QUALITY_VERSION
 c=spec.get('motion_confirmation',{})
 if set(c)!={'version','parent_spec','parent_spec_sha256','checkpoint_sha256','seeds'} or c['version']!=VERSION or c['seeds']!=SEEDS:raise ValueError('confirmation schema/seeds differ')
 parent=Path(c['parent_spec']);p=json.loads(parent.read_text())
 if sha(parent)!=c['parent_spec_sha256'] or sha(spec['source_checkpoint'])!=c['checkpoint_sha256'] or spec['source_sha256']!=c['checkpoint_sha256']:raise ValueError('confirmation parent/checkpoint SHA differs')
 if not spec.get('evaluation_only') or any(spec['budget'][k] for k in ('smoke_updates','formal_updates','sample_limit','formal_samples')):raise ValueError('confirmation PPO0 only')
 if spec['reward']!=p['reward'] or spec['reward']['version']!=QUALITY_VERSION or spec['student_training']!=p['student_training']:raise ValueError('confirmation preserves original v3 reward/recipe')
 if spec['motion_assessment']!=protocol() or spec['student_evaluation']['version']!=protocol()['version'] or spec['evaluation']['protocol_identity']!=protocol()['version']:raise ValueError('confirmation effective protocol differs')
 expected=[(seed,v+[.34]) for seed in SEEDS for v in commands(0)]
 rows=spec['student_evaluation']['cases']
 if [(r['seed'],r['command']) for r in rows]!=expected or any(r['checkpoint']!=spec['source_checkpoint'] or r['sha256']!=spec['source_sha256'] or r['family']!='motion_native_normal' or r['role']!='MotionZeroStudent' or r['seconds']!=31.52 for r in rows):raise ValueError('confirmation full15 case matrix differs')
 if spec['evaluation']['scored_envs']!=8 or spec['evaluation']['seconds']!=31.52:raise ValueError('confirmation duration/count differs')
 import torch
 cp=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
 if cp.get('critic_privileged_version')!='motion_privileged49_v1' or cp['training_recipe']['reward']!=spec['reward'] or cp.get('recipe_version')!='student_motion31_training_v1':raise ValueError('trained Motion49 source contract differs')
 for k in ('action','control','ground','observation','history','ppo','student_interface'):
  if spec[k]!=p[k]:raise ValueError('confirmation frozen contract differs: '+k)
 return True
