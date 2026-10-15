"""Identity-bound actual training events; no skill success prerequisite."""
import json
from pathlib import Path
from .data import sha

def smoke_certificate(folder,spec):
 folder=Path(folder);errors=[];inputs={}
 def read(name):
  p=folder/name
  if not p.is_file():errors.append('missing '+name);return {}
  inputs[name]=sha(p);return json.loads(p.read_text())
 progress=read('progress.json');terminal=read('terminal_report.json');manifest=read('manifest.json');frozen=read('source_snapshot/spec.json')
 p=folder/'metrics.jsonl';rows=[json.loads(line) for line in p.read_text().splitlines()] if p.is_file() else [];inputs['metrics.jsonl']=sha(p) if p.is_file() else None
 if frozen!=spec or manifest.get('spec_sha256')!=inputs.get('source_snapshot/spec.json'):errors.append('student smoke spec identity differs')
 if manifest.get('source_sha256')!=spec['source_sha256']:errors.append('student source SHA differs')
 if terminal.get('status')!='COMPLETED' or terminal.get('failure'):errors.append('student smoke engineering failure')
 expected_updates=spec['budget']['smoke_updates']
 motion=spec['student_training']['version']=='student_motion31_training_v1'
 short=motion and bool(spec['student_training'].get('smoke_wiring'))
 if short:
  from .motion_training import short_wiring
  from .motion_startup import smoke_profile
  minimal=bool(spec.get('motion_startup'))
  expected_profile=smoke_profile() if minimal else short_wiring()
  if spec['student_training']['smoke_wiring']!=expected_profile or expected_updates!=5:errors.append('short smoke declaration differs')
  warmup=4
 else:warmup=5
 if progress.get('actual_updates')!=expected_updates or terminal.get('actual_updates')!=expected_updates or len(rows)!=expected_updates:errors.append('student smoke update count')
 if not progress.get('actor_parameters_changed'):errors.append('student Actor update unproven')
 if not short and (not rows or not any(r.get('episode_completed',0)>0 for r in rows)):errors.append('real episode completion/reset missing')
 if not any(r.get('nonzero_rewards',0)>0 for r in rows):errors.append('nonzero task reward missing')
 from native_stand.command_v6.domain.execution_plan import samples_per_update
 sample_count=samples_per_update(spec) if spec.get('motion_training') else 8192
 for r in rows:
  mask=r['actor_update_scope']
  if mask['valid_actor_samples']!=r['controlled_samples'] or mask['valid_actor_samples']+mask['invalid_actor_samples']!=sample_count:errors.append('pre-action actor mask mismatched')
  if not spec.get('student_temporal_regularization') and r['update']<=warmup and (r['actor_changed_this_update'] or mask['actor_optimizer_steps']!=0):errors.append('critic warmup changed Actor')
  if r['BC_loss']!=0 or r['BC_gradient_norm'] is not None or r['BC_updates']!=0 or not r['std_unchanged']:errors.append('BC/std changed')
 if not any(r['update']>warmup and r['actor_changed_this_update'] and r['actor_update_scope']['actor_optimizer_steps']>0 for r in rows):errors.append('warmup-after actual Actor step missing')
 if not any(r['critic_changed_this_update'] for r in rows[:warmup]):errors.append('critic warmup did not update')
 if spec.get('student_temporal_regularization'):
  restored=progress.get('optimizer_initial',{})
  if not all(restored.get(k) for k in ('source_critic_loaded','source_Adam_loaded','source_RNG_loaded')):errors.append('temporal full initialization restore unproven')
  if any(r['actor_update_scope'].get('critic_warmup') for r in rows):errors.append('temporal experiment incorrectly repeated warmup')
  cfg=spec['student_temporal_regularization']
  if any(r['actor_update_scope'].get('temporal_coefficient')!=cfg['coefficient'] for r in rows):errors.append('temporal optimizer hook missing')
  if cfg['arm']=='B' and not any(r['actor_update_scope'].get('temporal_pairs_sampled',0)>0 and (r['actor_update_scope'].get('temporal_weighted_gradient_norm_mean') or 0)>0 for r in rows):errors.append('temporal actual valid pairs/nonzero gradient missing')
 survival=spec['student_training']['version']=='student_standing_survival_quality_v14'
 if motion:
  from .motion_tracking_reward import reward_fields
  if any(r.get('reward_fields')!=list(reward_fields(spec['reward'])) for r in rows):errors.append('Motion reward readback missing')
  groups=len(spec['curriculum']['stages'][0]['commands'])
  if any(sum(r.get('hold_sample_counts',[0]*groups)[i] for r in rows)==0 for i in range(groups)):errors.append('Motion command holding coverage missing')
  if not short and any(sum(r.get('command_episode_counts',[0]*groups)[i] for r in rows)==0 for i in range(groups)):errors.append('Motion command real episode/reset coverage missing')
  if short and spec.get('motion_startup'):
   readback=read('wiring_runtime_readback.json')
   if not all(readback.get(k) for k in ('asset','control','ground')):errors.append('actual smoke runtime readback missing')
   command=progress.get('wiring_command_readback',{})
   if command.get('valid') is not True or command.get('sample_count')!=expected_updates*sample_count:errors.append('actual smoke command/task readback missing')
   if progress.get('independent_capability_evaluation',{}).get('status')!='NOT_RUN':errors.append('minimal smoke capability scope not declared')
  elif short:
   records=progress.get('evaluations',[])
   if len(records)!=groups:errors.append('short smoke independent matrix missing')
   for expected,record in zip(spec['student_evaluation']['cases'],records):
    name=record.get('path','')
    if Path(name).name!=name or not name:errors.append('short smoke evaluation path invalid');continue
    raw=read(name)
    if record.get('sha256')!=inputs.get(name) or raw.get('case',{}).get('command')!=expected['command'] or len(raw.get('per_env',[]))!=8:errors.append('short smoke evaluation identity missing')
    if raw.get('protocol')!=spec['motion_assessment']:errors.append('short smoke evaluation protocol differs')
 if survival:
  if any(len(r.get('reward_fields',[]))!=10 for r in rows):errors.append('v14 named reward summary missing')
 if not progress.get('checkpoint_roundtrip_verified'):errors.append('checkpoint save/load unproven')
 if spec.get('recovery_course'):
  if any(not r['actor_update_scope'].get('critic_control_only') for r in rows):errors.append('course Critic mask not active')
  if spec['recovery_course']['state']['stage']=='B':
   if not any(r.get('course_real_handoffs',0)>0 and sum(r.get('course_control_counts_initial_B50_B250_student',[0]*4)[1:3])>0 for r in rows):errors.append('real teacher-to-student handoff missing')
   if any(r['course_control_counts_initial_B50_B250_student'][3]!=r['controlled_samples'] for r in rows):errors.append('teacher samples included in student mask')
 result={'schema_version':2 if survival else 1,'status':'PASSED' if not errors else 'FAILED','spec_sha256':manifest.get('spec_sha256'),
  'source_sha256':spec['source_sha256'],'actual_updates':progress.get('actual_updates'),'inputs':inputs,'errors':errors,
  'run':str(folder.resolve()),'smoke_plan':{'required_event':'student_update_and_episode','capability_prerequisite':False}}
 if survival:
  result['engineering_status']=result['status']
  result['capability_evidence']={'scope':'stochastic training smoke; independent evaluation required',
   'accepted':False,'normal_timeout_count':sum(r.get('normal_timeout_count',0) for r in rows),
   'longest_completed_episode_s':max((r.get('episode_duration_max_s') or 0 for r in rows),default=None),
   'completed_episodes':sum(r.get('episode_completed',0) for r in rows),
   'ppo_timeout_bootstrap_observed':any(r.get('normal_timeout_count',0)>0 for r in rows),
   'missing_timeout_semantics':'not observed in stochastic smoke; not a skill prerequisite; CPU regression covers bootstrap'}
 if short:
  result['schema_version']=3
  if spec.get('motion_startup'):
   result['independent_capability_evaluation']={'status':'NOT_RUN','reason':'minimal startup validates actual PPO wiring only; formal milestones own capability assessment'}
  result['smoke_plan']={'required_event':'short_actor_critic_wiring','capability_prerequisite':False,'version':spec['student_training']['smoke_wiring']['version']}
  result['coverage']={'scope':'short wiring, not full episode survival','completed_episodes':sum(r.get('episode_completed',0) for r in rows),
   'normal_timeout_count':sum(r.get('normal_timeout_count',0) for r in rows),'training_reset_observed':any(r.get('episode_completed',0)>0 for r in rows),
   'timeout_bootstrap_observed':any(r.get('normal_timeout_count',0)>0 for r in rows),'full_training_episode_verified':False,'independent_evaluation_is_not_training_reset':True}
 return result

def finalize(run,spec,manifest,terminal,progress,metrics,exit_code,destination):
 from native_stand.command_v6.completion import write,identity
 import time
 run=Path(run);destination=Path(destination)
 selection=json.loads((run/'candidate_selection.json').read_text()) if (run/'candidate_selection.json').is_file() else {}
 event=identity({'attempt':manifest.get('attempt_id'),'run':str(run)})[:24]
 report={'event_id':event,'status':terminal.get('status'),'actual_updates':terminal.get('actual_updates',0),'samples':terminal.get('samples',0),'effective_actor_samples':terminal.get('effective_actor_samples',0),'candidate_selection':selection,
  'source_behavior_passed':progress.get('source_behavior_passed'),'source_engineering_valid':progress.get('engineering_valid'),'failure':terminal.get('failure'),'metrics_count':len(metrics),'BC_updates':0,
  'critic_warmup_updates':0 if spec.get('student_storage_resume') or spec.get('student_temporal_regularization') or spec.get('recovery_course',{}).get('resume') or spec.get('motion_training',{}).get('resume') else min(5,terminal.get('actual_updates',0)),'accepted':bool(selection.get('accepted_candidate')),'evaluations':progress.get('evaluations',[]),'source_sha256':spec['source_sha256'],'interface_version':spec['interface_version'],'recipe_version':spec['student_training']['version'],'phase':manifest.get('phase')}
 write(destination/'analysis.json',report)
 title='Motion student bounded PPO block' if spec.get('motion_training') else 'Recovery student bounded PPO phase'
 if spec.get('motion_training'):
  from .motion_training import phase_warmup
  report['critic_warmup_updates']=min(phase_warmup(spec['student_training'],manifest.get('phase')),terminal.get('actual_updates',0))
  report.update(stage=spec['motion_training']['stage'],block_index=spec['motion_training']['block_index'],standing_quality_certified=False,automatic_next_block=False)
  write(destination/'analysis.json',report)
 (destination/'completion_report.md').write_text('# '+title+'\n\n'+json.dumps(report,indent=2)+'\n\nCOMPLETED is lifecycle completion, not skill acceptance. No automatic retry or extension.\n')
 write(destination/'report_ready.json',{'event_id':event,'status':'report_ready','report_sha256':sha(destination/'completion_report.md'),'time':time.time()})
 return report
