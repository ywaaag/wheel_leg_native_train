"""CLI-boundary task assembly for the shared trainer; no Isaac on import."""
import json
import math
from pathlib import Path
import torch
from native_stand.command_v6.tools.evaluation_state import isolated_evaluation,failure_evidence
from native_stand.command_v6.domain.episode_result import episode_result,recovery_episode_mode,requires_stand


REWARD_FIELDS=('lift','upright','effort','action_delta','joint_margin')


def environment(cfg,spec,*,initialization_only=False):
    from native_stand.recovery.runtime import RecoveryEnv
    from native_stand.command_v6.learning import model
    from tensordict import TensorDict
    config=spec['recovery']
    stand=None
    declared=[bool(config.get(name)) for name in ('stand_checkpoint','stand_spec','stand_sha256')]
    if requires_stand(config):
        if not all(declared):
            raise ValueError('Incomplete frozen STAND dependency declaration')
        stand_spec=json.loads(Path(config['stand_spec']).read_text())
        dummy=TensorDict({'policy':torch.zeros(cfg.scene.num_envs,25,device=cfg.sim.device),
            'history':torch.zeros(cfg.scene.num_envs,125,device=cfg.sim.device)},batch_size=[cfg.scene.num_envs])
        # STAND has no PPO object; critic and optimizer are never instantiated.
        stand=model(dummy,actor=True,spec=stand_spec).to(cfg.sim.device)
        checkpoint=torch.load(config['stand_checkpoint'],map_location=cfg.sim.device,weights_only=False)
        stand.load_state_dict(checkpoint['actor'],strict=True)
        stand.eval()
        for parameter in stand.parameters():parameter.requires_grad_(False)
    return RecoveryEnv(cfg,recovery_config=config,
        initialization_only=initialization_only,
        pose_library=json.loads(Path(config['pose_library']).read_text()),stand_policy=stand,
        stage=spec['curriculum']['stages'][0],command_height=spec['control']['height_command_m'],
        reward_config=spec['reward'],schedule_s=spec['curriculum']['schedule_s'])


@isolated_evaluation
def evaluate_actor(actor,wrapped,env,*,seconds,seed,stop_requested=lambda:False,full_trace=False,
                   progress_callback=None,family=None,check_retained=True,target=(0.,0.),
                   scored_envs=8,target_window=None,standing_protocol=None,diagnostics=False,
                   effective_protocol=None):
    """Fixed holdout first episodes, batched tensor evidence; no PPO optimizer."""
    from native_stand.recovery.domain import summarize_episodes,capture_terminal
    old_family,old_split=env.family,env.split
    old_training=env.curriculum_training
    standing=env.recovery_config.get('standing_task')
    from native_stand.command_v6.domain.evidence import (effective_protocol as build_protocol,
        diagnostic_field,validate_effective_protocol,PROTOCOL_FIELDS,observed_protocol,tensor_field_validity)
    if tuple(target)!=(0.,0.):
        raise ValueError('Recovery evaluator supports only zero-command evaluation')
    scoring_protocol=dict(standing['protocol'] if standing else {})
    if standing:scoring_protocol['seconds']=max(scoring_protocol.get('seconds',seconds),seconds)
    if standing_protocol is not None:
        if not isinstance(standing_protocol,dict) or set(standing_protocol)-PROTOCOL_FIELDS:
            raise ValueError('unknown or malformed standing_protocol fields')
        for key,value in scoring_protocol.items():
            if key in standing_protocol and key not in ('seconds','steady_window_s') and standing_protocol[key]!=value:
                raise ValueError('Recovery standing_protocol threshold conflict: '+key)
        if target_window is None and 'steady_window_s' in standing_protocol:
            target_window=standing_protocol['steady_window_s']
    old_diagnostics=env.recovery_config.get('gate_diagnostics',False)
    diagnostic=bool(old_diagnostics or diagnostics)
    scoring_protocol['diagnostics']={'requested':bool(diagnostics),'runtime_spec_enabled':bool(old_diagnostics),
        'enabled':diagnostic,'merge_rule':'CLI request OR runtime spec; restored after evaluation'}
    # The Recovery task owns its thresholds; the generic evaluator supplies timing only.
    window=(target_window if target_window is not None else
            [scoring_protocol.get('steady_window_s',[.5,seconds])[0],seconds])
    if window[0]>=seconds:window=[0.,seconds]
    protocol=effective_protocol or build_protocol(scoring_protocol,requested_seconds=seconds,
        steady_window_s=window,sample_rate_hz=1/env.step_dt,scored_envs=scored_envs,
        termination_semantics='first_episode_pre_reset; early termination fails continuous window')
    validate_effective_protocol(protocol)
    if protocol['requested_seconds']!=seconds or protocol['scored_envs']!=scored_envs:
        raise ValueError('effective protocol differs from evaluator request')
    if abs(protocol['sample_rate_hz']-1/env.step_dt)>1e-8:
        raise ValueError('effective protocol sample rate differs from runtime')
    if any(protocol.get(key)!=value for key,value in scoring_protocol.items() if key not in ('diagnostics','seconds','steady_window_s')):
        raise ValueError('effective protocol threshold differs from Recovery task')
    scoring_protocol=protocol
    env.recovery_config['gate_diagnostics']=diagnostic
    old_continuous=env.continuous_evaluation
    old_timeout=env.fsm.config['timeout_s']
    if standing:
        env.continuous_evaluation=True
        env.fsm.config['timeout_s']=max(old_timeout,seconds+env.step_dt)
    env.curriculum_training=False
    if scored_envs>env.num_envs:raise ValueError('not enough scored environments')
    n=scored_envs
    cpu_rng=torch.get_rng_state()
    cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    torch.manual_seed(seed)
    evaluation_family=family or old_family
    env.select_initial_family(evaluation_family,'holdout')
    obs,_=env.reset()
    initial_xy=env.episode_origin[:n].clone()
    active=torch.ones(n,dtype=torch.bool,device=env.device)
    steps=round(seconds/env.step_dt)
    rows=torch.zeros((steps,n,39),device=env.device)
    valid=torch.zeros((steps,n),dtype=torch.bool,device=env.device)
    terminal=torch.zeros((n,39),device=env.device)
    terminal_control=torch.zeros((n,54),device=env.device)
    terminal_causes=torch.zeros((n,6),device=env.device,dtype=torch.bool)
    terminal_valid=torch.zeros(n,dtype=torch.bool,device=env.device)
    terminal_episode_result=torch.zeros((n,5),device=env.device,dtype=torch.bool)
    has_episode_result=hasattr(env,'episode_result_snapshot')
    gate_rows=torch.zeros((steps,n,20),device=env.device) if diagnostic else None
    control_rows=torch.zeros((steps,n,54),device=env.device) if diagnostic else None
    posture_rows=torch.zeros((steps,n,10),device=env.device) if standing else None
    geometry_rows=torch.zeros((steps,n,13),device=env.device) if standing and hasattr(env,'wheel_geometry_snapshot') else None
    try:
        with torch.inference_mode():
            for index in range(steps):
                if stop_requested():
                    raise failure_evidence(TimeoutError('Recovery evaluation interrupted'),protocol,
                        valid,env.step_dt,env.recovery_snapshot[:n])
                obs,_,done,_,_=env.step(actor(obs))
                # This tensor was written by _get_dones, before any local reset.
                rows[index].copy_(env.recovery_snapshot[:n]);valid[index].copy_(active)
                if standing:posture_rows[index].copy_(env.standing_snapshot[:n])
                if geometry_rows is not None:geometry_rows[index].copy_(env.wheel_geometry_snapshot[:n])
                if diagnostic:
                    gate_rows[index].copy_(env.gate_diagnostic_snapshot[:n])
                    control_rows[index].copy_(env.recovery_control_snapshot[:n])
                if progress_callback is not None and (index==0 or (index+1)%50==0):progress_callback(index+1)
                new=capture_terminal(env.recovery_snapshot[:n],env.recovery_control_snapshot[:n],
                    env.recovery_cause_snapshot[:n],active,done[:n],terminal,terminal_control,terminal_causes)
                if has_episode_result:
                    terminal_episode_result[new]=env.episode_result_snapshot[:n][new]
                terminal_valid |= new
                active &= ~done[:n].bool()
                if bool(env.terminal_causes['nonfinite'].any()) or bool(env.terminal_causes['closure'].any()):
                    raise failure_evidence(RuntimeError('Recovery evaluation runtime fault; pre-reset tensor available'),
                        protocol,valid,env.step_dt,env.recovery_snapshot[:n])
                if not bool(active.any()):break
        values=rows.cpu();mask=valid.cpu();end=terminal.cpu();end_mask=terminal_valid.cpu()
        controls=terminal_control.cpu()
        causes=terminal_causes.cpu()
        terminal_results=terminal_episode_result.cpu()
        gate_values=gate_rows.cpu() if diagnostic else None
        control_values=control_rows.cpu() if diagnostic else None
        posture_values=posture_rows.cpu() if standing else None
        geometry_values=geometry_rows.cpu() if geometry_rows is not None else None
        origins=initial_xy.cpu()
        library=env.pose_library['poses']
        autonomous=env.fsm.config.get('success_mode')=='autonomous_hold'
        episodes=[]
        for i in range(n):
            series=values[:,i][mask[:,i]]
            last=end[i] if end_mask[i] else series[-1]
            pose=library[int(last[5])]
            success=bool(end_mask[i] and last[2])
            runtime=bool(last[4])
            reason=[name for name,flag in zip(env.terminal_causes,causes[i]) if flag]
            if bool(last[30]):reason.append('initialization_rejected')
            if not reason and not success and end_mask[i]:reason.append('recovery_timeout' if autonomous else 'handover_failed_or_recovery_timeout')
            episode={'env_id':i,'family':pose['family'],'seed':pose['seed'],
                'pose_id':pose['pose_id'],'episode_id':int(last[31]),'initial_valid':bool(last[29]),'success':success,
                'recovery_s':float(last[0]-last[1]) if success else None,
                'verify_s':float(last[1]),'handover_failed':bool(last[3] and int(last[32]) in (3,4)),
                'termination_reason':reason,
                'runtime_fault':runtime,'outcome':'success' if success else ('runtime_fault' if runtime else 'task_failure' if end_mask[i] else 'incomplete'),
                'continuous_s':float(last[0]),'height_min_m':float(series[:,6].min()),
                'height_final_m':float(last[6]),'dual_contact_fraction':float((series[:,10:12]>2).all(-1).float().mean()),
                'closure_max_m':float(series[:,12].max()),'ideal_gap_min_m':float(series[:,14].min()),
                'tilt_peak_rad':float(series[:,15].max()),'saturation_fraction_policy':float(series[:,17].mean()),
                'terminal_pre_reset':last.tolist() if end_mask[i] else None,
                'handover_target_rate_peak':last[33:39].tolist(),
                'terminal_control_pre_reset':controls[i].tolist() if end_mask[i] else None}
            if full_trace:episode['compact_trace_100hz']=series.tolist()
            if diagnostic:
                gate_trace=gate_values[:,i][mask[:,i]]
                episode['gate_diagnostics_100hz']=[[value if math.isfinite(value) else None
                    for value in row] for row in gate_trace.tolist()]
                episode['control_diagnostics_100hz']=control_values[:,i][mask[:,i]].tolist()
            else:
                episode['gate_diagnostics_100hz']=None
                episode['control_diagnostics_100hz']=None
            if standing:
                from native_stand.recovery.standing import score_standing
                gate=score_standing(series,posture_values[:,i][mask[:,i]],dt=env.step_dt,
                    requested_s=seconds,protocol={**scoring_protocol,
                        'initial_xy':origins[i].tolist()},
                    runtime_fault=runtime,initial_valid=bool(last[29]),terminated=bool(end_mask[i]))
                episode.update(standing_metrics=gate['metrics'],standing_checks=gate['checks'],
                    standing_failed_checks=gate['failed_checks'],success=gate['accepted'],
                    outcome='runtime_fault' if runtime else 'success' if gate['accepted'] else
                            'task_failure' if end_mask[i] or len(series)==steps else 'incomplete')
                episode['continuous_window_completed']=bool(len(series)==steps and not end_mask[i])
                if geometry_values is not None:
                    from native_stand.recovery.standing import longitudinal_geometry
                    g=geometry_values[:,i][mask[:,i]]
                    offsets=longitudinal_geometry(g[:,:6].reshape(-1,2,3),g[:,6:9]).abs()
                    episode['wheel_geometry']={'mean_offset_m':float(offsets.mean()),
                        'peak_offset_m':float(offsets.max()),'aligned_4cm_fraction':float((offsets<=.04).float().mean()),
                        'finite':bool(torch.isfinite(g).all() and torch.isfinite(offsets).all()),
                        'sampling':'100Hz pre-reset main-wheel centers, horizontal native -rootZ; not contact patches'}
                    if full_trace:episode['wheel_geometry_trace_100hz']=g.tolist()
                if not end_mask[i]:episode['termination_reason']=['evaluation_window']
                if full_trace:episode['posture_trace_100hz']=posture_values[:,i][mask[:,i]].tolist()
            if not full_trace and not episode['success']:
                episode['failure_window_100hz']=series[-100:].tolist()
                if standing:episode['failure_posture_window_100hz']=posture_values[:,i][mask[:,i]][-100:].tolist()
            episodes.append(episode)
        retained_results=[]
        if (standing and standing['protocol'].get('objective')=='survival_level' and
                seconds>=10. and check_retained and env.reverse_curriculum is not None):
            level=next(row for row in env.recovery_config['curriculum']['levels']
                       if row['pose_family']==evaluation_family)
            for retained in level.get('retained_families',[]):
                result=evaluate_actor(actor,wrapped,env,seconds=10.,seed=seed,
                    stop_requested=stop_requested,full_trace=False,family=retained,check_retained=False)
                retained_results.append(result)
            if any(not result['accepted'] for result in retained_results):
                for episode in episodes:
                    episode['success']=False
                    episode['standing_checks']['retained_family']=False
                    episode['standing_failed_checks'].append('retained_family')
                    if episode['outcome']!='runtime_fault':episode['outcome']='task_failure'
        passed=sum(row['success'] for row in episodes)
        episode_mode=getattr(env,'episode_mode',None)
        if episode_mode is None:
            episode_mode=recovery_episode_mode({**env.recovery_config,'fsm':env.fsm.config})
        for i,episode in enumerate(episodes):
            ended=bool(end_mask[i])
            flags=terminal_results[i]
            terminated=bool(flags[0]) if has_episode_result and ended else ended
            truncated=bool(flags[1]) if has_episode_result and ended else False
            if not ended and len(values[:,i][mask[:,i]])==steps:
                truncated=True  # External evaluation cutoff; the runtime did not reset.
            episode['episode_result']=episode_result(terminated=terminated,truncated=truncated,
                certificate_passed=bool(episode['success']),runtime_fault=episode['runtime_fault'],
                task_mode=episode_mode,termination_reason=episode['termination_reason'])
        evaluation_stage=next((i for i,row in enumerate(env.recovery_config.get('curriculum',{}).get('levels',[]))
                               if row['pose_family']==evaluation_family),0)
        protocol=observed_protocol(protocol,[len(values[:,i][mask[:,i]])*env.step_dt for i in range(n)])
        validity=tensor_field_validity(gate_values,mask,[*env.gate_diagnostic_names,'world_vx','world_vy','world_vz',
            'world_wx','world_wy','world_wz','leg_target_jump_rad','wheel_target_jump_rad_s','pre_step_dwell_s'],
            requested=diagnostics,enabled=diagnostic,scope='100Hz pre-reset first episode')
        validity.update(tensor_field_validity(control_values,mask,['control_'+str(i) for i in range(54)],requested=diagnostics,
            enabled=diagnostic,scope='100Hz pre-reset controls; latest held PD torque'))
        if episode_mode=='continuous_holding':
            for name in ('leg_target_jump','wheel_target_jump','leg_target_jump_rad','wheel_target_jump_rad_s'):
                validity[name]=diagnostic_field(None,requested=diagnostics,enabled=False,
                    scope='teacher handover only',missing_reason='not_applicable: continuous_holding skips teacher forward')
        return {'task':'recovery','seed':seed,'per_env':episodes,'accepted':passed==n,
            'effective_protocol':protocol,
            'diagnostic_field_validity':validity,
            'diagnostics_validity':{
                name:diagnostic_field(True if diagnostic else None,requested=diagnostics,
                    enabled=diagnostic,sample_count=int(mask.sum()),scope='100Hz pre-reset first episode')
                for name in ('gate_diagnostics_100hz','control_diagnostics_100hz')},
            'evaluation_family':evaluation_family,'evaluation_curriculum_stage':evaluation_stage,
            'retained_evaluations':retained_results,
            'control_diagnostic_groups':({'q':[0,6],'dq':[6,12],'raw_action':[12,18],
                'clipped_action':[18,24],'target_before_joint_limit':[24,28],
                'target_after_joint_limit':[28,32],'PD_requested_nm':[32,38],
                'physical_clipped_nm':[38,44],'actuator_applied_nm':[44,50],
                'closure_m':[50,54]} if diagnostic else None),
            'control_diagnostic_sampling':('100Hz policy end, latest held PD torque; not a full5ms substep saturation audit' if diagnostic else None),
            'recovery_gate':{'accepted':passed==n,'passed_envs':passed,'scored_envs':n,'per_env':[
                {'env_id':row['env_id'],'failed_checks':row.get('standing_failed_checks',
                    [] if row['success'] else [row['outcome']])} for row in episodes]},
            'passed_envs':passed,'family_results':summarize_episodes(episodes),
            'outcome_counts':{name:sum(row['outcome']==name for row in episodes)
                for name in ('success','task_failure','runtime_fault','incomplete')},
            'evidence_frequency_hz':1/env.step_dt,'stand_model_sha256':env.recovery_config.get('stand_sha256'),
            'success_protocol':{'mode':'autonomous_hold' if autonomous else 'handover',
                'episode_mode':episode_mode,
                'legacy_fsm_mode':env.fsm.config.get('success_mode','handover'),
                'certificate_mode':'full_window' if standing else 'fsm_success',
                'required_stable_s':env.fsm.config['verify_s'],'teacher_control':not autonomous,
                **({'standing_protocol':protocol,'effective_protocol':protocol,'continuous_seconds':seconds} if standing else {})},
            'incomplete_is_failure':False,'initialization':env.initialization_summary(),
            'runtime_initialization_certified':env.recovery_config['runtime_initialization_validated'],
            'gate_diagnostic_fields':[*env.gate_diagnostic_names,'world_vx','world_vy','world_vz',
                'world_wx','world_wy','world_wz','leg_target_jump_rad','wheel_target_jump_rad_s','pre_step_dwell_s'] if diagnostic else None}
    finally:
        pass  # The outer evaluation-state guard also covers reset/setup failures.
