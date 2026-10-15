"""Motion block adapter under the existing public trainer/monitor, no autonomous chain."""
import json,time,sys,traceback
from collections import deque
from pathlib import Path
import torch
from .data import sha
from .artifacts import checkpoint as atomic_checkpoint,secondary,storage
from .training import observations,evaluate_cases
from .evaluator import environment
from .model import load
from .ppo import assemble
from .motion_training import choose
from native_stand.command_v6.completion import write

def _record_optimizer_completion(progress,update,unit,mask_summary):
 """Count real optimizer completion before fallible diagnostics/serialization."""
 progress.update(actual_updates=update,samples=update*unit,
  effective_actor_samples=progress['effective_actor_samples']+mask_summary['effective_actor_update_samples'])

def save(output,spec,ppo,update):
 from .resume import rng_state
 cfg=spec['motion_training'];base=spec['motion_course']['source_recipe_updates'] if spec.get('motion_course') else (cfg.get('successor') or cfg['resume']).get('parent_recipe_updates',0)
 source=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
 data={'interface_version':'multiskill_mcu_v2','role':'MotionZeroStudent','actor':ppo.actor.state_dict(),'critic':ppo.critic.state_dict(),'optimizer':ppo.optimizer.state_dict(),
  'recipe_version':spec['student_training']['version'],'training_recipe':spec['student_training'],'source_sha256':spec['source_sha256'],
  'dataset_sha256':source['dataset_sha256'],'manifest_sha256':source['manifest_sha256'],'asset_sha256':spec['asset_sha256'],'spec_sha256':sha(output/'source_snapshot/spec.json'),
  'source_code_sha256':__import__('native_stand.command_v6.tools.execution_identity',fromlist=['identity']).identity(spec)['location_independent_modules_sha256'],
  'fixed_std':True,'BC_coefficient':0.,'update':update,'recipe_updates':base+update,'critic_privileged_version':'motion_privileged49_v1','training_rng':rng_state(),'motion_block':cfg}
 if hasattr(ppo,'reward_refinement_state'):data['reward_refinement_state']=ppo.reward_refinement_state
 if hasattr(ppo,'motion_course_state'):data['motion_course_state']=ppo.motion_course_state
 path=output/f'model_update_{update}.pt';atomic_checkpoint(path,data);actor,_=load(path,'MotionZeroStudent')
 if not all(torch.equal(v.detach().cpu(),actor.state_dict()[k]) for k,v in ppo.actor.state_dict().items()):raise ValueError('Motion checkpoint roundtrip differs')
 return {'checkpoint':str(path.resolve()),'sha256':sha(path),'update':update,'stage':cfg['stage']}

def execute(args,spec):
 from native_stand.command_v6.ledger import Ledger
 from native_stand.command_v6.train import record_run_configuration,install_stop_handlers,send_handshake
 envs=spec['ppo']['envs'];steps=spec['ppo']['steps_per_env'];unit=envs*steps
 out=args.output_dir;phase=args.phase;book=json.loads(args.spec.with_name('budget.json').read_text());attempt=book['attempts'][args.attempt_id]
 if attempt['status']!='RUNNING' or attempt['output_dir']!=str(out.resolve()):raise ValueError('Motion exact reservation required')
 started=time.monotonic();deadline=attempt['started_unix_s']+spec['budget'][phase+'_wall_s'];env=app=None;failure=None;status='FAILED';sent=False;ppo=None;cleanup=[];tail=deque(maxlen=200)
 progress={'status':'STARTING','phase':phase,'attempt_id':args.attempt_id,'output_dir':str(out.resolve()),'actual_updates':0,'samples':0,'effective_actor_samples':0,'actor_parameters_changed':False,'checkpoint_roundtrip_verified':False,'evaluations':[]}
 def stopped():
  from native_stand.command_v6 import train
  return train.STOP or time.time()>deadline-90
 def guard():
  limit=storage(spec);size=sum(p.stat().st_size for p in out.parent.rglob('*') if p.is_file() and not p.is_symlink())
  if size>limit['chain_max_bytes']-limit['terminal_reserve_bytes']:raise TimeoutError('Motion storage reserve reached')
 try:
  out.mkdir(parents=True,exist_ok=False);record_run_configuration(out,args.spec)
  from .motion_reward_audit import audit as reward_audit
  from . import motion_tracking_reward as reward_source
  snapshot=reward_audit(spec['reward']);snapshot.update(spec_sha256=sha(args.spec),reward_source_sha256=sha(Path(reward_source.__file__)),source_sha256=spec['source_sha256'])
  with (out/'reward_snapshot.json').open('x') as stream:json.dump(snapshot,stream,indent=2,allow_nan=False)
  from native_stand.command_v6.tools.health_check import own_process_start
  import os
  write(out/'manifest.json',{'attempt_id':args.attempt_id,'phase':phase,'pid':os.getpid(),'trainer_pid':os.getpid(),'process_started_unix_s':own_process_start(os.getpid()),'source_sha256':spec['source_sha256'],'spec_sha256':sha(args.spec),'asset_sha256':spec['asset_sha256'],'hapi_session':args.hapi_session,'interface_version':'multiskill_mcu_v2','recipe_version':spec['student_training']['version'],'reward_snapshot_sha256':sha(out/'reward_snapshot.json')})
  write(out/'progress.json',progress);sys.path.insert(0,spec['asset_module_root'])
  from isaaclab.app import AppLauncher
  app=AppLauncher({'headless':True,'device':'cuda:0','multi_gpu':False}).app;install_stop_handlers();torch.manual_seed(spec['seed'])
  actor,source=load(spec['source_checkpoint'],'MotionZeroStudent');actor=actor.to('cuda:0');source_actor_weights={k:v.clone() for k,v in actor.state_dict().items()};cases=spec['student_evaluation']['cases']
  course=bool(spec.get('motion_course'));course_state={'stage':0,'stage_started_update':0,'last_evaluation_update':-1,'consecutive_passes':0,'accepted_by_stage':{}}
  minimal_startup=bool(spec.get('motion_startup'))
  if phase=='source_eval':
   if minimal_startup:
    from .motion_startup import resolve,merge
    reused_records,missing_cases=resolve(spec)
    new_records=evaluate_cases(spec,out,actor,missing_cases,stop=stopped) if missing_cases else []
    records=merge(spec,reused_records,new_records)
    write(out/'source_reuse.json',{'version':spec['motion_startup']['version'],'reused':[r['reuse_reference'] for r in reused_records.values()],'new_evaluations':[{'path':r['path'],'sha256':r['sha256']} for r in new_records],'no_new_simulation_for_reused_commands':True})
   else:records=evaluate_cases(spec,out,actor,cases,stop=stopped)
   progress.update(status='COMPLETED',engineering_valid=True,evaluations=records)
   candidate={'checkpoint':spec['source_checkpoint'],'sha256':spec['source_sha256'],'update':0,'per_env':[e for r in records for e in r['per_env']],'complete_matrix':True,'stage':spec['motion_training']['stage'],'evaluations':records}
   write(out/'candidate_registry.json',[candidate]);write(out/'candidate_selection.json',choose([candidate]));status='COMPLETED'
  else:
   env=environment(spec,'MotionZeroStudent',envs=envs);env.curriculum_training=True;env.select_initial_family('motion_native_normal','train');obs,_=env.reset();obs=observations(env,obs)
   if minimal_startup and phase=='smoke':
    from native_stand.command_v6.runtime.control_readback import verify,verify_ground
    from native_stand.command_v6.runtime.configure import verify_asset_import
    write(out/'wiring_runtime_readback.json',{'asset':verify_asset_import(spec),'control':verify(env),'ground':verify_ground(env,spec),'scope':'actual smoke environment before online sampling'})
   wiring_command_valid=torch.ones((),device=env.device,dtype=torch.bool);wiring_command_samples=0
   ppo=assemble(spec['source_checkpoint'],obs,recipe=spec['student_training']);offset=0
   if course:
    from .motion_course_requests import restore as restore_course
    progress['course_restore']=restore_course(ppo,source,spec,phase)
    env.motion_cohort_mix.copy_(torch.tensor([r['mix'] for r in ppo.reward_refinement_state],device=env.device))
    ppo.motion_course_state=course_state
   refinement=spec['reward'].get('refinement')
   if refinement:
    from .motion_refinement import initial as initial_refinement,advance
    if not course:ppo.reward_refinement_state=initial_refinement(env.stage_spec['commands'])
   if spec['motion_training'].get('successor'):
    from .motion_successor import restore
    progress['successor_restore']=restore(ppo,source,spec,phase)
    env.motion_cohort_mix.copy_(torch.tensor([r['mix'] for r in ppo.reward_refinement_state],device=env.device))
   if spec['motion_training']['resume']:
    from .resume import restore_rng
    ppo.actor.load_state_dict(source['actor']);ppo.critic.load_state_dict(source['critic']);ppo.optimizer.load_state_dict(source['optimizer']);restore_rng(source['training_rng']);offset=source['recipe_updates']
   progress['optimizer_initial']={'source_critic_loaded':bool(offset or spec['motion_training'].get('successor') or course),'source_Adam_loaded':bool(offset or spec['motion_training'].get('successor') or course),'source_RNG_loaded':bool(offset or spec['motion_training'].get('successor') or course),'state_count':len(ppo.optimizer.state),'BC_coefficient':0.}
   reused=spec['motion_training'].get('wiring_reuse') or spec['motion_training'].get('partial_smoke_recovery')
   source_folder=Path(reused['parent_run'])/'source_eval' if reused else out.parent/'source_eval'
   fixed=ppo.actor.log_std.detach().clone();candidates=json.loads((source_folder/'candidate_registry.json').read_text());index=0;limit=spec['budget'][phase+'_updates']
   from .performance import RolloutCounts,settings
   from .motion_statistics import MotionStatistics
   from .motion_tracking_reward import reward_fields,QUALITY_VERSIONS
   names=reward_fields(spec['reward']);quality_enabled=spec['reward']['version'] in QUALITY_VERSIONS
   perf=settings(spec)
   tolerant_guard=spec['motion_training'].get('early_stop_policy');guard_state={}
   retention_baseline=candidates[0]['evaluations']
   if course:
    from .motion_course import implementation
    choose_course=implementation(spec['student_training']['course_version']).choose
    selection_fn=lambda values:choose_course(values,course_state['accepted_by_stage'])
   else:selection_fn=choose
   for update in range(1,limit+1):
    if stopped():status='STOPPED_BOUNDED';break
    guard();start_roll=time.perf_counter();counts=RolloutCounts(steps,envs,env.device);fields=torch.zeros(len(names),device=env.device);dt_fields=torch.zeros_like(fields);slots=torch.zeros(len(env.stage_spec['commands']),device=env.device,dtype=torch.long);hold=torch.zeros_like(slots);episodes=torch.zeros_like(slots);timeouts=torch.zeros((),device=env.device,dtype=torch.long)
    event_sum=torch.zeros(3,device=env.device);quality_counts=torch.zeros(7,device=env.device,dtype=torch.long)
    cohort=MotionStatistics(env.stage_spec['commands'],env.device,schedule_s=spec['student_training']['train_schedule_s'],parking_s=spec['student_training']['parking_s'])
    raw_squared=torch.zeros_like(fields);bounded_tail=torch.zeros(3,device=env.device);eligible_count=torch.zeros((),device=env.device)
    before={k:v.clone() for k,v in ppo.actor.state_dict().items()};critic_before={k:v.clone() for k,v in ppo.critic.state_dict().items()}
    with torch.inference_mode():
     for step in range(steps):
      if stopped():raise TimeoutError('Motion user/wall stop during rollout')
      valid=obs['student_actor_valid'].squeeze(-1) if 'student_actor_valid' in obs else obs[__import__('native_stand.recovery.controlled_ppo',fromlist=['KEY']).KEY].squeeze(-1)
      age=env.rise_hold.episode.steps.float()*.01;command_index=env.command_index.clone()
      if minimal_startup and phase=='smoke':
       actor_obs=obs['student_actor'];expected_command=env.command/actor_obs.new_tensor([4.,4.,.5])
       wiring_command_valid&=(actor_obs[:,22:25]-expected_command).abs().amax()<=1e-6
       wiring_command_valid&=(actor_obs[:,25]==1).all()&(actor_obs[:,26:28]==0).all();wiring_command_samples+=envs
      raw=ppo.act(obs);newobs,reward,terminated,truncated,extras=env.step(raw);done=terminated|truncated
      if perf['failure_tail_on_device']:
       tail.append({'state':env.recovery_snapshot.detach().clone(),'posture':env.standing_snapshot.detach().clone(),
        'geometry':env.wheel_geometry_snapshot.detach().clone(),'control':env.recovery_control_snapshot.detach().clone()})
       if quality_enabled:tail[-1]['quality_termination_causes']=env.motion_quality_snapshot.detach().clone()
      if env.recovery_snapshot[:,4].bool().any() or env.recovery_snapshot[:,30].bool().any() or not torch.isfinite(reward).all():raise RuntimeError('Motion runtime/initialization/nonfinite fault')
      if not torch.equal(valid,env.student_actor_valid):raise RuntimeError('Motion actor scope mismatch')
      storage_reward=reward
      if truncated.any():
       from .standing_survival_task import bootstrap_reward
       if env.student_terminal_critic is None:raise RuntimeError('Motion terminal Critic snapshot missing')
       storage_reward=bootstrap_reward(reward,terminated,truncated,ppo.critic(env.student_terminal_critic).squeeze(-1),gamma=ppo.gamma)
      newobs=observations(env,newobs);ppo.process_env_step(newobs,storage_reward,done,{k:v for k,v in extras.items() if k!='time_outs'});obs=newobs
      s=env.recovery_snapshot;counts.observe(valid,reward,done,s,env.student_event_snapshot,env.standing_snapshot,episode_duration_s=age+.01)
      cohort.observe(command_index,valid,age,env.motion_action_command,s,env.standing_snapshot,env.wheel_geometry_snapshot)
      fields+=env.student_reward_result['raw'].sum(0);dt_fields+=env.student_reward_result['dt'].sum(0);timeouts+=truncated.sum()
      raw_squared+=env.student_reward_result['raw'].square().sum(0)
      event_sum+=env.student_reward_result['events'].sum(0)
      if quality_enabled:quality_counts+=env.motion_quality_snapshot.sum(0)
      eligible=env.student_reward_result['eligible'];eligible_count+=eligible.sum()
      bounded_tail+=((env.student_reward_result['raw'][:,9:12]>=.95)&eligible[:,None]).sum(0)
      slots+=torch.bincount(command_index[valid],minlength=len(slots));start,end=cohort.windows[0];holdmask=valid&(age>=start)&(age<end)
      hold+=torch.bincount(command_index[holdmask],minlength=len(slots))
      episodes+=torch.bincount(command_index[valid&done],minlength=len(slots))
     ppo.compute_returns(obs)
    from .motion_training import phase_warmup
    cnt,durations=counts.export();roll_time=time.perf_counter()-start_roll;ppo.actor_update_enabled=offset+update>phase_warmup(spec['student_training'],phase);start_ppo=time.perf_counter();loss=ppo.update();ppo_time=time.perf_counter()-start_ppo
    _record_optimizer_completion(progress,update,unit,ppo.mask_summary)
    Ledger(args.spec.with_name('budget.json')).charge(args.attempt_id,out)
    changed=any(not torch.equal(v,ppo.actor.state_dict()[k]) for k,v in before.items());critic_changed=any(not torch.equal(v,ppo.critic.state_dict()[k]) for k,v in critic_before.items())
    if not torch.equal(fixed,ppo.actor.log_std) or not all(torch.isfinite(p).all() for m in (ppo.actor,ppo.critic) for p in m.parameters()):raise RuntimeError('Motion std/nonfinite optimizer fault')
    metric={'update':update,'controlled_samples':cnt[0],'nonzero_rewards':cnt[1],'episode_completed':cnt[2],'episode_duration_mean_s':sum(durations)/len(durations) if durations else None,
     'episode_duration_max_s':max(durations,default=None),'normal_timeout_count':int(timeouts),'actor_update_scope':ppo.mask_summary,'actor_changed_this_update':changed,'critic_changed_this_update':critic_changed,
     'BC_loss':0.,'BC_gradient_norm':None,'BC_updates':0,'std_unchanged':True,'reward_fields':list(names),
     'reward_raw_mean':(fields/unit).cpu().tolist(),'reward_raw_std':(raw_squared/unit-(fields/unit).square()).clamp_min(0).sqrt().cpu().tolist(),
     'reward_bounded_tail_fraction':dict(zip(('mirror','wheel_alignment','leg_balance'),(bounded_tail/eligible_count.clamp_min(1)).cpu().tolist())),
     'reward_eligible_samples':int(eligible_count),'reward_dt_mean':(dt_fields/unit).cpu().tolist(),'reward_dt_s':spec['reward']['dt'],'cohort_statistics':cohort.export(),'episode_duration_scope':'episode policy clock; pre-reset, includes transition',
     'command_sample_counts':slots.cpu().tolist(),'hold_sample_counts':hold.cpu().tolist(),'command_episode_counts':episodes.cpu().tolist(),
     'loss':loss,'actual_LR':[g['lr'] for g in ppo.optimizer.param_groups],'wall_s':time.monotonic()-started,'timing':{'rollout_s':roll_time,'PPO_s':ppo_time}}
    if course:
     metric['course']={'stage':course_state['stage'],'stage_name':spec['curriculum']['stages'][0]['name'],'stage_updates':update-course_state['stage_started_update'],'formal_updates_global':update,'source_recipe_updates':spec['motion_course']['source_recipe_updates'],'accepted_stage_count':len(course_state['accepted_by_stage'])}
    if refinement:metric['reward_refinement_state']=ppo.reward_refinement_state
    metric['reward_event_sum']=dict(zip(('success','task_failure','runtime_fault'),event_sum.cpu().tolist()))
    metric['reward_total_per_step']=float((dt_fields.sum()+event_sum.sum())/unit)
    if quality_enabled:
     from .motion_quality import CAUSES
     metric['quality_termination_counts']=dict(zip(CAUSES,quality_counts.cpu().tolist()))
     metric['geometry_high_error_fraction']=metric.pop('reward_bounded_tail_fraction')
    with (out/'metrics.jsonl').open('a') as f:f.write(json.dumps(metric,allow_nan=False)+'\n')
    progress.update(status='RUNNING',actor_parameters_changed=any(not torch.equal(v,ppo.actor.state_dict()[k]) for k,v in source_actor_weights.items()),latest_metric=metric)
    write(out/'progress.json',progress)
    if not sent and args.handshake_fd is not None:
     send_handshake(args.handshake_fd,{'status':'RUNNING','attempt_id':args.attempt_id,'trainer_pid':__import__('os').getpid(),'actual_updates':update,'output_dir':str(out.resolve())});sent=True
    if update in spec['student_training']['milestones'] or update==limit:
     candidate=save(out,spec,ppo,update);progress['latest_checkpoint']={**candidate,'evaluated':False};progress['checkpoint_roundtrip_verified']=True;env.close();env=None
     if minimal_startup and phase=='smoke':
      progress['wiring_command_readback']={'valid':bool(wiring_command_valid),'sample_count':wiring_command_samples,'scope':'all real pre-action Actor command/task observations'}
      progress['independent_capability_evaluation']={'status':'NOT_RUN','reason':'explicit minimal startup; full assessment reserved for formal milestones'}
      candidate.update(per_env=[],complete_matrix=False,evaluations=[])
      progress['latest_checkpoint']={**candidate,'evaluated':False};candidates.append(candidate)
      write(out/'candidate_registry.json',candidates);write(out/'candidate_selection.json',selection_fn(candidates));write(out/'progress.json',progress)
      continue
     records=evaluate_cases(spec,out,ppo.actor,cases,offset=index,stop=stopped,checkpoint=candidate['checkpoint'],source_records=candidates[0]['evaluations']);index+=len(records)
     candidate.update(per_env=[e for r in records for e in r['per_env']],complete_matrix=len(records)==len(cases),evaluations=records)
     progress['latest_checkpoint']={k:candidate[k] for k in ('checkpoint','sha256','update','stage')};progress['latest_checkpoint']['evaluated']=True
     candidates.append(candidate);selection=selection_fn(candidates);write(out/'candidate_registry.json',candidates);write(out/'candidate_selection.json',selection);progress['evaluations']+=records;write(out/'progress.json',progress)
     # Only genuinely passed source capabilities are retention prerequisites.
     retained=[i for i,e in enumerate(candidates[0]['per_env']) if e['accepted']]
     regression=bool(retained) and any(not candidate['per_env'][i]['accepted'] for i in retained)
     progress['retention_failures']=progress.get('retention_failures',0)+1 if regression else 0
     retention_stop=progress['retention_failures']>=2
     if tolerant_guard and phase=='formal':
      from .motion_guard import advance as advance_guard
      if course:
       old_commands={tuple(r['case']['command']) for r in retention_baseline if all(e['accepted'] for e in r['per_env'])}
       old_records=[r for r in records if tuple(r['case']['command']) in old_commands]
       old_baseline=[next(b for b in retention_baseline if b['case']['command']==r['case']['command']) for r in old_records]
       guard_update=update-course_state['stage_started_update']
      else:old_records=records;old_baseline=candidates[0]['evaluations'];guard_update=update
      guard_state,decision=advance_guard(guard_state,old_records,old_baseline,guard_update,tolerant_guard)
      progress['retention_guard']=decision;progress['retention_guard_state']=guard_state;retention_stop=decision['stop']
      write(out/'progress.json',progress)
     course_decision=None
     if course and phase=='formal':
      from .motion_course import implementation
      course_module=implementation(spec['student_training']['course_version'])
      advance_course,effective_spec,extend_mixture=course_module.advance,course_module.effective_spec,course_module.extend_mixture
      course_state,course_decision=advance_course(course_state,candidate);ppo.motion_course_state=course_state
      write(out/'course_progress.json',{'state':course_state,'decision':course_decision,'checkpoint':candidate['checkpoint'],'checkpoint_sha256':candidate['sha256']})
      selection=selection_fn(candidates);write(out/'candidate_selection.json',selection)
     final_confirmed=course_decision['all_stages_passed'] if course_decision else bool(selection['accepted_candidate'])
     if phase=='formal' and (final_confirmed or retention_stop):
      status='STOPPED_BOUNDED';progress['stop_reason']='stage_confirmed' if final_confirmed else 'repeated_certified_source_regression';break
     if refinement and phase=='formal' and update<limit:
      ppo.reward_refinement_state,decisions=advance(ppo.reward_refinement_state,records,refinement)
      progress['reward_refinement_state']=ppo.reward_refinement_state
      write(out/f'reward_refinement_after_{update}.json',{'update':update,'policy':refinement,'next_state':ppo.reward_refinement_state,'decisions':decisions,'evaluation_inputs':[{'path':r['path'],'sha256':r['sha256']} for r in records]})
     if course_decision and course_decision['advanced'] and update<limit:
      retention_baseline=records;guard_state={}
      spec=effective_spec(spec,course_state['stage']);cases=spec['student_evaluation']['cases']
      ppo.reward_refinement_state=extend_mixture(ppo.reward_refinement_state,spec['curriculum']['stages'][0]['commands'])
     if course and phase=='formal' and update-course_state['stage_started_update']>=spec['motion_course']['configuration']['stage_updates_max']:
      status='STOPPED_BOUNDED';progress['stop_reason']='stage_budget_exhausted';break
     if update<limit:
      env=environment(spec,'MotionZeroStudent',envs=envs);env.curriculum_training=True
      if refinement:env.motion_cohort_mix.copy_(torch.tensor([r['mix'] for r in ppo.reward_refinement_state],device=env.device))
      env.select_initial_family('motion_native_normal','train');obs,_=env.reset();obs=observations(env,obs)
   else:status='COMPLETED'
 except BaseException as exc:
  if tail:
   from .artifacts import npz
   secondary(exc,'Motion failure tail',lambda:npz(out/'failure_tail.npz',{k:torch.stack([r[k] for r in tail]).cpu().numpy() for k in tail[0]}))
  failure={'exception':repr(exc),'traceback':traceback.format_exc()};status='STOPPED_BOUNDED' if isinstance(exc,TimeoutError) else 'FAILED'
 finally:
  if ppo is not None and progress['actual_updates'] and not (out/f"model_update_{progress['actual_updates']}.pt").exists():
   latest=secondary(RuntimeError('terminal preservation'),'latest checkpoint',lambda:save(out,spec,ppo,progress['actual_updates']))
   if latest:progress['latest_checkpoint']={**latest,'evaluated':False}
  if progress.get('latest_checkpoint'):
   selection_path=out/'candidate_selection.json'
   if selection_path.exists():
    selected=json.loads(selection_path.read_text());selected['latest_checkpoint']=progress['latest_checkpoint'];write(selection_path,selected)
  stop_kind='user_signal' if __import__('native_stand.command_v6.train',fromlist=['STOP']).STOP else progress.get('stop_reason','budget_or_completion')
  write(out/'progress.json',{**progress,'status':status});write(out/'terminal_report.json',{'status':status,'attempt_id':args.attempt_id,'phase':phase,'actual_updates':progress['actual_updates'],'samples':progress['samples'],'effective_actor_samples':progress['effective_actor_samples'],'evaluations':progress['evaluations'],'failure':failure if status=='FAILED' else None,'budget_interruption':failure if status=='STOPPED_BOUNDED' else None,'stop_kind':stop_kind,'wall_s_before_cleanup':time.monotonic()-started})
  if env is not None:
   try:env.close()
   except BaseException as exc:cleanup.append('env.close: '+repr(exc))
  write(out/'cleanup.json',{'errors':cleanup,'app_close':'pending'})
  if app is not None:
   try:app.close(exit_code=0 if status in ('COMPLETED','STOPPED_BOUNDED') and not cleanup else 1)
   except BaseException as exc:cleanup.append('app.close: '+repr(exc))
  write(out/'cleanup.json',{'errors':cleanup,'app_close':'returned'})
 return 0 if status in ('COMPLETED','STOPPED_BOUNDED') and not cleanup else 1
