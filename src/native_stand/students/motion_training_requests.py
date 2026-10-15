"""Motion training validation and CPU-only task/block budget audit."""
import json
from pathlib import Path
from .data import sha
from .motion_training import VERSION,commands,stage_config,protocol

def validate(spec,*,task_data=None):
 errors=[]
 try:
  if spec.get('motion_course'):
   from .motion_course_requests import verify
   verify(spec);return []
  if spec.get('motion_confirmation'):
   from .motion_confirmation import verify
   verify(spec);return []
  from .training_recipe import validate_instance
  recipe=validate_instance(spec['student_training'],spec['source_sha256'])
  if recipe['version']!=VERSION or spec['reward']!=recipe['reward']:raise ValueError('Motion recipe/reward differs')
  cfg=spec['motion_training']
  required={'version','stage','block_index','spec_path','task_manifest','task_manifest_sha256','resume'}
  if not required<=set(cfg) or set(cfg)-required-{'execution_profile','wiring_reuse','partial_smoke_recovery','prior_consumption','successor','early_stop_policy'} or cfg['version']!=VERSION or cfg['stage']!=recipe['stage']:raise ValueError('Motion block fields differ')
  parallel=cfg.get('execution_profile')=='motion31_parallel512_2000_v1'
  if cfg.get('execution_profile') not in (None,'motion31_parallel512_2000_v1'):raise ValueError('unknown Motion execution profile')
  path=Path(cfg['task_manifest']);task=json.loads(path.read_text()) if task_data is None else task_data
  import hashlib
  actual=sha(path) if task_data is None else hashlib.sha256((json.dumps(task,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
  if actual!=cfg['task_manifest_sha256'] or task['formal_limit']!=2000 or task['source_sha256']!=__import__('native_stand.students.motion_training',fromlist=['SOURCE']).SOURCE:raise ValueError('task scope identity differs')
  max_updates=2000 if parallel else 300;max_wall=64800 if parallel else 14400
  if spec['budget']['formal_updates']>max_updates or spec['budget']['formal_wall_s']>max_wall:raise ValueError('Motion block ceiling exceeded')
  if parallel and (cfg['stage']!=0 or cfg['resume']):raise ValueError('512 experiment is original-source L1 only; no auto unlock/resume')
  if recipe['storage_max_bytes']>2*2**30:raise ValueError('Motion storage limit exceeded')
  expected={'envs':512 if parallel else 64,'steps_per_env':128,'hidden_dims':[128,64,32],'learning_rate':3e-5,'epochs':4,'minibatches':4,'gamma':.99,'lam':.95,'clip':.2,'value_coef':.5,'entropy_coef':.001,'max_grad_norm':1.}
  if spec['ppo']!=expected:raise ValueError('Motion PPO baseline differs')
  if spec['curriculum']['stages']!=[stage_config(cfg['stage'],expected['envs'])] or spec['curriculum']['active_stage']!=0:raise ValueError('fixed Motion slots/whitelist differs')
  cases=spec['student_evaluation']['cases']
  if [r['command'] for r in cases]!=[v+[.34] for v in commands(cfg['stage'])] or any(r['role']!='MotionZeroStudent' or r['family']!='motion_native_normal' for r in cases):raise ValueError('complete Motion assessment matrix differs')
  from .motion_tracking_reward import QUALITY_VERSION,QUALITY_VERSIONS,SUCCESSOR_VERSION
  successor=spec['reward']['version']==SUCCESSOR_VERSION
  quality=spec['reward']['version'] in QUALITY_VERSIONS
  expected_protocol=protocol(quality=quality,successor=successor)
  if cfg.get('early_stop_policy'):
   from .motion_guard import configuration as guard_configuration,protocol as guard_protocol
   if not quality or cfg['early_stop_policy']!=guard_configuration():raise ValueError('explicit Motion guard differs')
   expected_protocol=guard_protocol()
  if spec['motion_assessment']!=expected_protocol:raise ValueError('Motion scoring protocol differs')
  if spec['evaluation']['scored_envs']!=8 or spec['evaluation']['seconds']!=31.52 or spec['evaluation']['protocol_identity']!=expected_protocol['version'] or spec['student_evaluation']['version']!=expected_protocol['version']:raise ValueError('Motion shared evaluation identity differs')
  if successor:
   from .motion_successor import verify
   verify(spec)
  elif quality:
   if not cfg.get('prior_consumption'):raise ValueError('quality v3 requires settled inclusive original consumption')
   from .motion_quality_budget import verify as verify_quality_budget
   verify_quality_budget(spec)
  elif cfg.get('prior_consumption'):raise ValueError('prior consumption requires explicit quality version')
  cadence=250 if cfg.get('early_stop_policy') else 100
  if not recipe['milestones'] or recipe['milestones']!=list(range(cadence,spec['budget']['formal_updates']+1,cadence)):raise ValueError('Motion fixed checkpoint schedule differs')
  if cfg.get('early_stop_policy') and spec['evaluation']['full_every_updates']!=250:raise ValueError('tolerant guard needs250 update evaluation cadence')
  if type(spec['budget']['chain_wall_s']) not in (int,float) or not 0<spec['budget']['chain_wall_s']<=max_wall:raise ValueError('Motion entire block wall ceiling exceeded')
  if spec['source_sha256']!=__import__('native_stand.students.motion_training',fromlist=['SOURCE']).SOURCE and not cfg['resume'] and not cfg.get('successor'):raise ValueError('first Motion block must use original migrated Actor')
  expected_smoke=5 if recipe.get('smoke_wiring') else 50
  if not cfg['resume'] and not cfg.get('wiring_reuse') and not cfg.get('partial_smoke_recovery') and spec['budget']['smoke_updates']!=expected_smoke:raise ValueError('declared first block smoke budget differs')
  if sum(bool(cfg.get(k)) for k in ('resume','wiring_reuse','partial_smoke_recovery'))>1:raise ValueError('Motion continuation mechanisms conflict')
  if cfg['resume'] and spec['budget']['smoke_updates']!=0:raise ValueError('continuation must not repeat smoke')
  if any(k in spec for k in ('student_motion_validation','student_storage_resume','recovery_course','retention')):raise ValueError('incompatible experiment branch')
  audit_task(task,path,cfg,planned_formal=spec['budget']['formal_updates'],allow_planned=task_data is not None)
  if cfg['resume']:verify_continuation(spec)
  if cfg.get('wiring_reuse'):
   from .motion_wiring_recovery import verify
   verify(spec)
  if cfg.get('partial_smoke_recovery'):
   from .motion_wiring_recovery import verify_partial
   verify_partial(spec)
 except (OSError,ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
 return errors

def audit_task(task,path,current,*,planned_formal=0,allow_planned=False):
 used=0;pending=0
 rows=list(task.get('blocks',[]))
 if task.get('registry_dir'):
  for p in sorted(Path(task['registry_dir']).glob('block_*.json')):rows.append(json.loads(p.read_text()))
 if allow_planned and current['block_index'] not in [r['index'] for r in rows]:rows.append({'index':current['block_index'],'spec':current['spec_path']})
 if len({r['index'] for r in rows})!=len(rows) or len({str(Path(r['spec']).resolve()) for r in rows})!=len(rows):raise ValueError('duplicate Motion block budget identity')
 if current['block_index'] not in [r['index'] for r in rows]:raise ValueError('Motion block not registered')
 for row in rows:
  spec_path=Path(row['spec'])
  if not spec_path.exists():
   if row['index']==current['block_index']:pending+=planned_formal
   continue
  ledger=json.loads(spec_path.with_name('budget.json').read_text())
  block_spec=json.loads(spec_path.read_text())
  if block_spec.get('motion_training',{}).get('task_manifest_sha256')!=current['task_manifest_sha256'] or ledger.get('experiment')!=block_spec.get('experiment'):raise ValueError('Motion block ledger/task identity differs')
  if row.get('planned_spec_sha256'):
   marker=json.loads(spec_path.with_name('publication_complete.json').read_text())
   if marker.get('files',{}).get('spec.json')!=row['planned_spec_sha256'] or Path(block_spec['motion_training']['spec_path']).resolve()!=spec_path.resolve() or ledger['limits']['formal']!=block_spec['budget']['formal_updates']:raise ValueError('Motion registration/publication/ledger ceiling differs')
  if any(a['status']=='RUNNING' for a in ledger['attempts'].values()):
   # Existing current attempt is handled by public exact-ID reserved plan.
   if row['index']!=current['block_index']:raise ValueError('previous Motion block still active')
  if ledger['used']['formal']<0 or ledger['used']['formal']>ledger['limits']['formal']:raise ValueError('invalid Motion ledger count')
  if row['index']!=current['block_index'] and ledger['used']['formal']<ledger['limits']['formal'] and not ledger.get('attempts'):raise ValueError('another prepared block remains unsettled')
  used+=ledger['used']['formal']
  if row['index']==current['block_index']:pending+=ledger['limits']['formal']-ledger['used']['formal']
 if used+pending>task['formal_limit']:raise ValueError('task cumulative formal limit exceeded')
 return {'actual_formal_updates':used,'remaining_formal_updates':task['formal_limit']-used}

def verify_continuation(spec):
 """Consume a settled block's real evaluated checkpoint and original wiring."""
 cfg=spec['motion_training'];r=cfg['resume']
 if set(r)!={'parent_spec','parent_spec_sha256','formal_dir','parent_recipe_updates'}:raise ValueError('Motion continuation fields differ')
 parent_path=Path(r['parent_spec']);parent=json.loads(parent_path.read_text());folder=Path(r['formal_dir'])
 if sha(parent_path)!=r['parent_spec_sha256'] or parent['motion_training']['task_manifest_sha256']!=cfg['task_manifest_sha256'] or parent['motion_training']['block_index']+1!=cfg['block_index']:raise ValueError('Motion continuation/task identity differs')
 terminal=json.loads((folder/'terminal_report.json').read_text());book=json.loads(parent_path.with_name('budget.json').read_text())
 if terminal['status'] not in ('COMPLETED','STOPPED_BOUNDED') or terminal.get('failure') or any(a['status']=='RUNNING' for a in book['attempts'].values()):raise ValueError('Motion parent not settled')
 from native_stand.command_v6.wiring import completed_smoke
 if not completed_smoke(book,parent):raise ValueError('Motion original wiring certificate missing')
 selection=json.loads((folder/'candidate_selection.json').read_text());candidate=selection.get('accepted_candidate') or selection.get('best_new')
 if not candidate or not candidate.get('complete_matrix') or candidate['sha256']!=spec['source_sha256'] or Path(candidate['checkpoint']).resolve()!=Path(spec['source_checkpoint']).resolve() or sha(spec['source_checkpoint'])!=spec['source_sha256']:raise ValueError('Motion evaluated continuation source differs')
 cases=parent['student_evaluation']['cases'];records=candidate.get('evaluations',[])
 if len(records)!=len(cases) or len(candidate.get('per_env',[]))!=len(cases)*8:raise ValueError('Motion continuation complete matrix missing')
 for case,record in zip(cases,records):
  path=folder/record['path'];raw=json.loads(path.read_text())
  if path.parent!=folder or sha(path)!=record['sha256'] or raw.get('checkpoint_sha256')!=spec['source_sha256'] or raw.get('protocol')!=parent['motion_assessment'] or raw.get('case',{}).get('command')!=case['command'] or len(raw.get('per_env',[]))!=8:raise ValueError('Motion continuation raw assessment identity differs')
 if parent['device']!=spec['device']:raise ValueError('Motion continuation GPU mapping differs')
 stage=cfg['stage'];old=parent['motion_training']['stage']
 if stage!=old and (stage!=old+1 or not selection.get('accepted_candidate')):raise ValueError('Motion stage unlock lacks repeated previous-stage acceptance')
 import torch
 cp=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
 if cp.get('critic_privileged_version')!='motion_privileged49_v1' or cp.get('recipe_version')!=VERSION or cp.get('recipe_updates')!=r['parent_recipe_updates'] or not all(k in cp for k in ('actor','critic','optimizer','training_rng')):raise ValueError('Motion full continuation state missing')
 if cp['training_recipe']['reward']!=spec['reward'] or {g['lr'] for g in cp['optimizer']['param_groups']}!={spec['ppo']['learning_rate']}:raise ValueError('Motion continuation reward/LR differs')
 return True
