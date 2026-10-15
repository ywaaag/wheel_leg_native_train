"""Explicit authorized v4 successor: evidence selection, full restore, new scoring."""
import copy,json,math
from pathlib import Path
from .data import sha
VERSION='motion31_hold_level_successor_v1'
SAFETY=('survival30','height','contact','saturation','closure','clearance','tilt','quality_complete_window','roll_quality','leg_balance_quality','wheel_alignment_quality','joint_mirror_quality')
TRACKING=('tracking','direction','gain','sustained_fraction')

def select(parent_run):
 """Only original, complete raw evaluations tied to one existing checkpoint."""
 run=Path(parent_run).resolve();manifest=json.loads((run/'manifest.json').read_text());spec_path=Path(manifest['spec_path'])
 if sha(spec_path)!=manifest['spec_sha256']:raise ValueError('parent spec identity differs')
 parent=json.loads(spec_path.read_text());terminal=json.loads((run/'chain_terminal_report.json').read_text());book=json.loads(spec_path.with_name('budget.json').read_text())
 if terminal['status'] not in ('COMPLETED','STOPPED_BOUNDED') or terminal.get('failure') or any(r['status']=='RUNNING' for r in book['attempts'].values()):raise ValueError('parent must be settled without runtime fault')
 candidates=json.loads((run/'formal/candidate_registry.json').read_text());audited=[]
 for candidate in candidates:
  c=copy.deepcopy(candidate);folder=run/('source_eval' if c['update']==0 else 'formal');records=c.get('evaluations',[]);errors=[];rows=[]
  if not c.get('complete_matrix') or len(records)!=5:errors.append('incomplete matrix')
  if not Path(c['checkpoint']).is_file() or sha(c['checkpoint'])!=c['sha256']:errors.append('checkpoint absent or SHA mismatch')
  for case,record in zip(parent['student_evaluation']['cases'],records):
   path=folder/record['path'];raw=json.loads(path.read_text())
   if sha(path)!=record['sha256'] or raw.get('checkpoint_sha256')!=c['sha256'] or raw.get('case',{}).get('command')!=case['command'] or raw.get('protocol')!=parent['motion_assessment'] or len(raw.get('per_env',[]))!=8:raise ValueError('parent raw evaluation identity differs: '+str(path))
   rows.extend(raw['per_env'])
  if len(rows)!=40:errors.append('expected40 scored environments')
  if any(not all(e.get('checks',{}).get(k) is True for k in SAFETY) for e in rows):errors.append('physical/posture evidence incomplete or failed')
  nonzero=rows[8:];mae=[e.get('tracking',{}).get('MAE') for e in nonzero]
  if any(not isinstance(v,(float,int)) or not math.isfinite(v) for v in mae):errors.append('missing finite tracking')
  c['selection_errors']=errors;c['per_env']=rows
  c['selection_rank']=[sum(all(e['checks'].get(k) is True for k in TRACKING) for e in nonzero),sum(e['checks'].get('direction') is True for e in nonzero),-max(mae) if mae and all(isinstance(v,(float,int)) for v in mae) else -999.]
  audited.append(c)
 eligible=[c for c in audited if not c['selection_errors']]
 if not eligible:raise ValueError('no fully evaluated physically safe parent checkpoint')
 chosen=max(eligible,key=lambda c:c['selection_rank'])
 return {'version':VERSION,'parent_run':str(run),'parent_spec':str(spec_path),'parent_spec_sha256':sha(spec_path),'parent_terminal_sha256':sha(run/'chain_terminal_report.json'),'parent_ledger_sha256':sha(spec_path.with_name('budget.json')),'selected':chosen,'candidates':[{'update':c['update'],'checkpoint':c['checkpoint'],'sha256':c['sha256'],'rank':c['selection_rank'],'excluded':c['selection_errors']} for c in audited], 'selection_is_not_acceptance':True,'parent_actual_updates':book['used'],'parent_chain_wall_s':terminal['chain_wall_s']}

def apply_assessment(row):
 """Retain original diagnostics, omit parking from this tracking-phase gate only."""
 row['original_full_protocol_accepted']=row['accepted'];row['original_full_protocol_failed_checks']=list(row['failed_checks'])
 row['diagnostic_checks']={'parking':row['checks'].pop('parking',None)}
 row['version']='motion31_hold_level_assessment_v3';row['accepted']=all(row['checks'].values());row['failed_checks']=[k for k,v in row['checks'].items() if not v]
 row['capability_scope']='sustained Motion tracking and zero/physical/posture retention; parking diagnostic; not stationary certification'
 return row

def verify(spec):
 from .motion_tracking_reward import SUCCESSOR_VERSION
 c=spec['motion_training'].get('successor',{})
 if c.get('version')!=VERSION or spec['reward']['version']!=SUCCESSOR_VERSION:raise ValueError('explicit successor recipe missing')
 auth_path=Path(c['authorization_path']);auth=json.loads(auth_path.read_text())
 if sha(auth_path)!=c['authorization_sha256'] or auth['parent_run']!=c['parent_run'] or auth['limits']['total_new_online_updates']!=2000:raise ValueError('successor authorization identity differs')
 review_path=Path(c['selection_path']);review=json.loads(review_path.read_text())
 if sha(review_path)!=c['selection_sha256'] or review['selected']['sha256']!=spec['source_sha256'] or review['selected']['checkpoint']!=spec['source_checkpoint']:raise ValueError('successor selected source differs')
 parent=Path(c['parent_spec']);book=json.loads(parent.with_name('budget.json').read_text());terminal=Path(c['parent_run'])/'chain_terminal_report.json'
 if sha(parent)!=c['parent_spec_sha256'] or sha(terminal)!=review['parent_terminal_sha256'] or sha(parent.with_name('budget.json'))!=review['parent_ledger_sha256'] or any(r['status']=='RUNNING' for r in book['attempts'].values()):raise ValueError('successor parent not frozen and settled')
 if spec['budget']['smoke_updates']!=5 or not 1<=spec['budget']['formal_updates']<=1995 or spec['motion_training']['resume'] or spec['student_training']['train_schedule_s']!=[.5,1.,28.5,0.] or spec['student_training']['parking_s']!=0.:raise ValueError('successor schedule/budget differs')
 if spec['student_training']['warmup_updates_per_phase']!=5:raise ValueError('reward-change Critic adaptation requires declared5 warmup')
 if spec.get('restore_source_rng') is not False:raise ValueError('shared loader RNG must remain off; explicit successor restore owns RNG')
 if sha(spec['source_checkpoint'])!=spec['source_sha256']:raise ValueError('successor checkpoint SHA mismatch')
 import torch
 cp=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
 if cp.get('critic_privileged_version')!='motion_privileged49_v1' or cp.get('recipe_updates')!=c['parent_recipe_updates'] or cp.get('training_recipe',{}).get('reward',{}).get('version')!='student_motion31_quality_reward_v3':raise ValueError('successor source Motion49/version/update differs')
 if not all(k in cp for k in ('actor','critic','optimizer','training_rng','reward_refinement_state')) or not cp.get('fixed_std'):raise ValueError('successor full state missing')
 if {g['lr'] for g in cp['optimizer']['param_groups']}!={spec['ppo']['learning_rate']}:raise ValueError('restored optimizer LR differs')
 if [r['target'] for r in cp['reward_refinement_state']]!=spec['curriculum']['stages'][0]['commands']:raise ValueError('source refinement commands differ')
 return True

def restore(ppo,source,spec,phase):
 """Preserve learned full state; Critic adapts5/4 steps to changed reward, no reset."""
 from .resume import restore_rng
 ppo.actor.load_state_dict(source['actor']);ppo.critic.load_state_dict(source['critic']);ppo.optimizer.load_state_dict(source['optimizer'])
 if {g['lr'] for g in ppo.optimizer.param_groups}!={spec['ppo']['learning_rate']}:raise ValueError('runtime restored LR differs')
 ppo.reward_refinement_state=copy.deepcopy(source['reward_refinement_state']);restore_rng(source['training_rng'])
 return {'source_critic_loaded':True,'source_Adam_loaded':True,'source_RNG_loaded':True,'source_mixture_loaded':True,'reward_changed':True,'physical_state_restored':False,'phase':phase}
