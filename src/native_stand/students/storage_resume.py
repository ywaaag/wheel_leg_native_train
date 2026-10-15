"""Restricted same-recipe storage-fault continuation; no permission or quota grant."""
import json
from pathlib import Path
import torch
from .data import sha

VERSION='student_v14_storage_resume_v1'
RETRY_VERSION='student_v14_storage_resume_retry_v2'

def verify(spec):
 c=spec['student_storage_resume']
 fields={'version','parent_spec','inputs','parent_formal_updates','historical_online_updates','original_online_limit','rng_semantics'}
 retry=c.get('version')==RETRY_VERSION
 if set(c)!=(fields|{'retry_spec','source_eval_dir'} if retry else fields) or c['version'] not in (VERSION,RETRY_VERSION):raise ValueError('storage resume schema differs')
 for path,digest in c['inputs'].items():
  if sha(path)!=digest:raise ValueError('storage resume evidence SHA differs: '+path)
 parent=Path(c['parent_spec']);old=json.loads(parent.read_text());book=json.loads(parent.with_name('budget.json').read_text())
 claims=parent.parent.parent/'.student_storage_resume_publications'
 claim=claims/(sha(parent)+'.json')
 claimed_experiment=Path(c['retry_spec']).parent.name if retry else spec['experiment']
 if claim.is_file() and Path(json.loads(claim.read_text())['destination']).name!=claimed_experiment:raise ValueError('parent recovery already published under another experiment')
 if str(parent) not in c['inputs'] or str(parent.with_name('budget.json')) not in c['inputs']:raise ValueError('parent identity not bound')
 if any(row['status']=='RUNNING' for row in book['attempts'].values()):raise ValueError('parent attempt still running')
 formal=[row for row in book['attempts'].values() if row['phase']=='formal']
 if len(formal)!=1 or formal[0]['status']!='FAILED':raise ValueError('exact failed formal required')
 folder=Path(formal[0]['output_dir']);terminal_path=folder/'terminal_report.json';terminal=json.loads(terminal_path.read_text())
 if str(terminal_path) not in c['inputs'] or terminal.get('failure',{}).get('exception')!="RuntimeError('Handoff storage cap exceeded')":raise ValueError('unsupported fault, not a general resume bypass')
 n=c['parent_formal_updates'];used=book['used']['smoke']+book['used']['formal'];limit=book['limits']['smoke']+book['limits']['formal']
 if n!=terminal['actual_updates'] or n!=formal[0]['updates'] or n!=book['used']['formal'] or used!=c['historical_online_updates'] or limit!=c['original_online_limit']:raise ValueError('parent accounting differs')
 if spec['budget']['smoke_updates']!=0 or spec['budget']['formal_updates']!=limit-used:raise ValueError('remaining quota differs')
 checkpoint=folder/f'model_update_{n}.pt'
 if spec['source_checkpoint']!=str(checkpoint) or str(checkpoint) not in c['inputs'] or spec['source_sha256']!=c['inputs'][str(checkpoint)]:raise ValueError('resume checkpoint identity differs')
 from native_stand.command_v6.wiring import validate_persisted_certificate
 smoke=[row for row in book['attempts'].values() if row['phase']=='smoke']
 if len(smoke)!=1 or smoke[0]['status']!='COMPLETED':raise ValueError('completed original smoke required')
 if validate_persisted_certificate(smoke[0]['output_dir'],old)['status']!='PASSED':raise ValueError('original wiring evidence not valid')
 # Only identity, output, authorization, cadence and remaining budget may change.
 def behavior(s):
  import copy
  x=copy.deepcopy(s)
  for k in ('experiment','artifacts','authorization','notifications','source_checkpoint','source_sha256','student_dependencies','budget','student_storage_resume','performance'):x.pop(k,None)
  for row in x['student_evaluation']['cases']:
   row.pop('checkpoint');row.pop('sha256')
  for k in ('source_actor_sha256','milestones'):x['student_training'].pop(k,None)
  return x
 if behavior(spec)!=behavior(old):raise ValueError('storage recovery changes behavior recipe')
 from .performance import settings
 settings(spec)
 if c['rng_semantics']!='restore_if_present_else_explicit_seed_reset':raise ValueError('explicit RNG limitation required')
 if retry:verify_reused_source(spec)
 return {'status':'VERIFIED','historical_online_updates':used,'remaining_online_updates':limit-used,'capability_accepted':False}

def verify_reused_source(spec):
 c=spec['student_storage_resume'];path=Path(c['retry_spec']);prior=json.loads(path.read_text());book=json.loads(path.with_name('budget.json').read_text())
 def bound(p):
  if str(p) not in c['inputs'] or sha(p)!=c['inputs'][str(p)]:raise ValueError('retry evidence not bound: '+str(p))
 bound(path);bound(path.with_name('budget.json'))
 if prior.get('student_storage_resume',{}).get('version')!=VERSION:raise ValueError('only one zero-PPO lifecycle retry supported')
 if book['used']['formal']!=0 or book['used']['smoke']!=0 or len(book['attempts'])!=1:raise ValueError('retry already consumed PPO or unexpected attempts')
 attempt=next(iter(book['attempts'].values()));folder=Path(c['source_eval_dir']);chain=folder.parent/'chain_terminal_report.json';bound(chain)
 if json.loads(chain.read_text()).get('failure')!="ValueError('invalid RunState transition SOURCE_EVAL->FORMAL')":raise ValueError('unsupported retry failure')
 if attempt['phase']!='source_eval' or attempt['status']!='COMPLETED' or Path(attempt['output_dir'])!=folder:raise ValueError('retry source attempt differs')
 for name in ('manifest.json','terminal_report.json','progress.json','candidate_registry.json','source_snapshot/spec.json'):bound(folder/name)
 manifest=json.loads((folder/'manifest.json').read_text());terminal=json.loads((folder/'terminal_report.json').read_text())
 if manifest['spec_sha256']!=sha(path) or manifest['source_sha256']!=spec['source_sha256'] or terminal['status']!='COMPLETED' or terminal.get('failure'):raise ValueError('retry source identity/status differs')
 if json.loads((folder/'source_snapshot/spec.json').read_text())!=prior:raise ValueError('source frozen spec differs')
 for key in ('reward','control','action','ground','termination','student_interface','student_training','student_evaluation','recovery','ppo','seed'):
  if prior[key]!=spec[key]:raise ValueError('reused source behavior differs: '+key)
 records=terminal['evaluations']
 if len(records)!=len(spec['student_evaluation']['cases']):raise ValueError('source evaluation incomplete')
 for expected,record in zip(spec['student_evaluation']['cases'],records):
  raw=folder/record['path'];bound(raw);d=json.loads(raw.read_text())
  if d['case']!=expected or record['case']!=expected or d['checkpoint_sha256']!=spec['source_sha256'] or d['spec_sha256']!=sha(path):raise ValueError('source case/checkpoint/spec differs')
  if d['protocol']!=spec['student_training']['protocol']:raise ValueError('source protocol differs')
  es=d['per_env']
  if len(es)!=8 or sorted(e['env'] for e in es)!=list(range(8)) or not all(e.get('initial_valid') and e.get('online_certificate_matches') for e in es):raise ValueError('source env evidence incomplete')
  archive=folder/d['trace']['path'];bound(archive)
  if sha(archive)!=d['trace']['sha256']:raise ValueError('source trace SHA differs')
 claim=path.parent.parent/'.student_storage_resume_retry_publications'/(sha(path)+'.json')
 if claim.exists() and Path(json.loads(claim.read_text())['destination']).name!=spec['experiment']:raise ValueError('retry already published')

def restore(ppo,data,spec):
 verify(spec)
 if data['recipe_version']!='student_standing_survival_quality_v14' or data['update']!=spec['student_storage_resume']['parent_formal_updates']:raise ValueError('checkpoint recipe/update differs')
 if not data.get('fixed_std') or data.get('critic_privileged_version')!='standing_privileged49_v1':raise ValueError('checkpoint interface/std differs')
 ppo.actor.load_state_dict(data['actor']);ppo.critic.load_state_dict(data['critic']);ppo.optimizer.load_state_dict(data['optimizer'])
 if any(g['lr']!=spec['ppo']['learning_rate'] for g in ppo.optimizer.param_groups):raise ValueError('restored LR differs')
 for parameter,state in ppo.optimizer.state.items():
  for k in ('exp_avg','exp_avg_sq'):
   if state[k].shape!=parameter.shape or not torch.isfinite(state[k]).all():raise ValueError('Adam shape/nonfinite state')
 if data.get('training_rng'):
  from .resume import restore_rng
  restore_rng(data['training_rng'])
 else:
  import random,numpy as np
  random.seed(spec['seed']);np.random.seed(spec['seed']);torch.manual_seed(spec['seed'])
  if torch.cuda.is_initialized():torch.cuda.manual_seed_all(spec['seed'])
 return {'source_actor_loaded':True,'source_critic_loaded':True,'source_Adam_loaded':True,'source_std_loaded':True,
  'source_RNG_loaded':bool(data.get('training_rng')),'RNG_limitation':'old checkpoint lacks RNG; declared seed initialized by trainer' if not data.get('training_rng') else None,
  'parent_formal_updates':data['update'],'warmup_repeated':False,'physical_state':'new environment reset; no PhysX restoration'}
