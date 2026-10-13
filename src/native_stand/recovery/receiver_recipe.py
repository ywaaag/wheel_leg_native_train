"""Public trainer assembly and same-episode receiver evaluation."""
import json
from pathlib import Path
import torch
from tensordict import TensorDict
from native_stand.command_v6.tools.evaluation_state import isolated_evaluation
from .motion_handoff import score
from .domain import Mode

def environment(cfg,spec):
    from .receiver_runtime import ReceiverEnv
    from native_stand.command_v6.tools.model_factory import model
    c=spec['receiver_training'];rec_spec=json.loads(Path(c['recovery_spec']).read_text())
    dummy=TensorDict({'policy':torch.zeros(cfg.scene.num_envs,25,device=cfg.sim.device),
        'history':torch.zeros(cfg.scene.num_envs,125,device=cfg.sim.device)},batch_size=[cfg.scene.num_envs])
    recovery=model(dummy,actor=True,spec=rec_spec).to(cfg.sim.device)
    recovery.load_state_dict(torch.load(c['recovery_checkpoint'],map_location=cfg.sim.device,weights_only=False)['actor'],strict=True)
    motion_spec=json.loads(Path(c['motion_spec']).read_text())
    original_motion=model(dummy,actor=True,spec=motion_spec).to(cfg.sim.device)
    original_motion.load_state_dict(torch.load(c['motion_checkpoint'],map_location=cfg.sim.device,weights_only=False)['actor'],strict=True)
    original_motion.eval();original_motion.requires_grad_(False)
    # Shared Recovery physical code retains its injected stand dependency, never forwards it.
    env=ReceiverEnv(cfg,receiver_config=c,recovery_actor=recovery,motion_reward_config=spec['receiver_reward'],
        recovery_config=spec['recovery'],pose_library=json.loads(Path(spec['recovery']['pose_library']).read_text()),
        stand_policy=recovery,stage=spec['curriculum']['stages'][0],command_height=.40,
        reward_config=spec['receiver_reward'],schedule_s=spec['curriculum']['schedule_s'])
    from native_stand.command_v6.runtime.execution_mode import apply
    apply(env,getattr(cfg,'native_execution_mode','training'))
    env.receiver_spec=spec
    env.original_motion_actor=original_motion
    return env

@isolated_evaluation
def evaluate_actor(actor,wrapped,env,*,seconds,seed,scored_envs=8,target=(0.,0.),
                   stop_requested=lambda:False,**kwargs):
    if list(target)!=[0.,0.]:raise ValueError('Receiver evaluation commands must be zero; original Motion return is separate')
    results=[]
    for family in env.receiver_config['evaluation_families']:
        env.curriculum_training=False;env.select_initial_family(family,'holdout')
        torch.manual_seed(seed)
        if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
        obs,_=wrapped.reset();active=torch.ones(scored_envs,device=env.device,dtype=torch.bool)
        states=[];postures=[];controllers=[];valid=[]
        controls=[];geometries=[];inputs=[];ownership_rows=[]
        record=bool(kwargs.get('full_trace') or kwargs.get('diagnostics'))
        for step in range(round(seconds/.01)):
            if stop_requested():raise TimeoutError('Receiver evaluation budget/stop')
            with torch.inference_mode():
                actor_valid=env.actor_valid_pre()
                initial=env.fsm.mode==int(Mode.INITIALIZING)
                ctrl_before=torch.where(initial,0,torch.where(actor_valid,2,1))
                if record:
                    actual_input=torch.cat((obs['policy'],obs['history']),-1)
                    prefix=~actor_valid&~initial
                    rec_input=torch.cat((env.recovery_observation['policy'],env.recovery_observation['history']),-1)
                    actual_input=torch.where(prefix[:,None],rec_input,actual_input)
                    inputs.append(actual_input[:scored_envs].cpu().clone())
                    from .handoff_ownership import phase_metadata
                    phase,elapsed=phase_metadata(ctrl_before,env.initial_age,env.executed_prefix,
                        env.rise_hold.motion_age,env.rise_hold.entry,env.rise_hold.count)
                    ownership_rows.append(torch.stack((torch.full_like(elapsed,(step+1)*.01),ctrl_before.float(),
                        actor_valid.float(),phase.float(),elapsed),-1)[:scored_envs].cpu().clone())
                requested=actor(obs,stochastic_output=False)
                executed=env.compose_training_action(requested)
                if record:
                    ownership_rows[-1]=torch.cat((ownership_rows[-1],executed[:scored_envs].cpu().clone(),
                        executed[:scored_envs].clamp(-1,1).cpu().clone()),-1)
                obs,_,done,_=wrapped.step(executed.clone())
            states.append(env.recovery_snapshot[:scored_envs].detach().cpu().clone())
            postures.append(env.standing_snapshot[:scored_envs].detach().cpu().clone())
            controllers.append(env.handoff_controller[:scored_envs].detach().cpu().clone())
            valid.append(active.detach().cpu().clone());active&=~done[:scored_envs].bool().reshape(-1)
            if record:
                controls.append(env.recovery_control_snapshot[:scored_envs].detach().cpu().clone())
                geometries.append(env.wheel_geometry_snapshot[:scored_envs].detach().cpu().clone())
            if not active.any():break
        st=torch.stack(states);po=torch.stack(postures);ctrl=torch.stack(controllers);masks=torch.stack(valid)
        per=[]
        for i in range(scored_envs):
            mask=masks[:,i];s=st[mask,i];p=po[mask,i];time=torch.arange(1,len(s)+1,dtype=torch.float32)*.01
            result=score(s,p,ctrl[mask,i]==2,policy_time_s=time,configuration=env.receiver_config['protocol'])
            result.update(env_id=i,continuous_s=len(s)*.01,outcome='success' if result['accepted'] else 'task_failure',
                          runtime_fault=bool(s[:,4].bool().any()),initial_valid=bool(s[:,29].bool().any()))
            if record:
                result.update(compact_trace_100hz=s.tolist(),posture_trace_100hz=p.tolist(),
                    control_diagnostics_100hz=torch.stack(controls)[mask,i].tolist(),
                    wheel_geometry_trace_100hz=torch.stack(geometries)[mask,i].tolist(),
                    actor_input_trace_100hz=torch.stack(inputs)[mask,i].tolist(),
                    control_diagnostics={'columns':['policy_time_s','controller','receiver_actor_valid','scoring_phase','pre_action_phase_elapsed_s']+
                        ['actual_policy_raw_'+str(j) for j in range(6)]+['wrapper_clipped_'+str(j) for j in range(6)],
                        'rows':torch.stack(ownership_rows)[mask,i].tolist(),
                        'controller_codes':{'initialization':0,'frozen_Recovery':1,'receiver':2},
                        'action_order':'left_hip,left_active,left_wheel,right_hip,right_active,right_wheel',
                        'snapshot_raw_action_note':'control_diagnostics_100hz raw_action is wrapper-clipped; actual raw policy output is in these named rows',
                        'switch_reason':'native_normal_direct' if family=='motion_native_normal' else '50controlled_Recovery_intervals'})
            per.append(result)
        results.append({'family':family,'per_env':per,'accepted':all(p['accepted'] for p in per),
                        'passed_envs':sum(p['accepted'] for p in per)})
    primary=results[0]
    combined=[]
    for i,p in enumerate(primary['per_env']):
        row=dict(p);row['failed_checks']=list(p['failed_checks'])
        if not results[1]['per_env'][i]['accepted']:row['failed_checks'].append('normal_zero_regression')
        row['accepted']=not row['failed_checks'];combined.append(row)
    accepted=all(p['accepted'] for p in combined)
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    effective=protocol_for_spec(env.receiver_spec,seconds)
    from native_stand.command_v6.domain.evidence import observed_protocol
    effective=observed_protocol(effective,[p['continuous_s'] for p in primary['per_env']])
    gate={'accepted':accepted,'passed_envs':sum(p['accepted'] for p in combined),'per_env':combined,
          'checks':{'Swing':results[0]['accepted'],'normal':results[1]['accepted']}}
    original_return=[]
    # New first episodes: candidate completes its10s hold, then frozen Motion drives.
    # Defer only the physical end-of-window reset; offline certificate is unchanged.
    for command in env.receiver_config['motion_return_commands']:
        env.select_initial_family('swing_candidate_from_historical_r1','holdout')
        env.rise_hold.defer_completion=True
        env.motion_command=torch.zeros((env.num_envs,3),device=env.device);env.motion_command[:,2]=.40
        try:
            torch.manual_seed(seed);obs,_=wrapped.reset()
            active=torch.ones(scored_envs,device=env.device,dtype=torch.bool)
            driving=torch.zeros(env.num_envs,device=env.device,dtype=torch.bool)
            drive_count=torch.zeros(env.num_envs,device=env.device,dtype=torch.long)
            drive_sum=torch.zeros((env.num_envs,3),device=env.device)
            handoff_states=[[] for _ in range(scored_envs)]
            handoff_postures=[[] for _ in range(scored_envs)]
            handoff_controllers=[[] for _ in range(scored_envs)]
            for step in range(round((seconds+5.)/.01)):
                if stop_requested():raise TimeoutError('Original Motion return budget/stop')
                with torch.inference_mode():
                    driving|=env.rise_hold.count>=1000
                    env.return_to_original=driving.clone()
                    # Update current command fields without clearing history.
                    env.motion_command[driving,:2]=env.motion_command.new_tensor(command)
                    current=obs.clone();current['policy'][driving,6]=command[0]*2.
                    current['policy'][driving,7]=command[1]*.25
                    requested=actor(current,stochastic_output=False)
                    if driving.any():requested[driving]=env.original_motion_actor(current[driving],stochastic_output=False)
                    executed=env.compose_training_action(requested)
                    obs,_,done,_=wrapped.step(executed)
                for i in range(scored_envs):
                    if active[i] and not driving[i]:
                        handoff_states[i].append(env.recovery_snapshot[i].detach().cpu().clone())
                        handoff_postures[i].append(env.standing_snapshot[i].detach().cpu().clone())
                        handoff_controllers[i].append(env.handoff_controller[i].detach().cpu().clone())
                controlled=driving[:scored_envs]&active&(drive_count[:scored_envs]<500)
                drive_count[:scored_envs]+=controlled
                sample=env.recovery_snapshot[:scored_envs]
                drive_sum[:scored_envs]+=torch.stack((sample[:,7]-command[0],sample[:,8],sample[:,9]-command[1]),-1).abs()*controlled[:,None]
                active&=~done[:scored_envs].bool().reshape(-1)
                if ((drive_count[:scored_envs]>=500)|~active).all():break
            rows=[]
            for i in range(scored_envs):
                n=int(drive_count[i]);errors=(drive_sum[i]/max(n,1)).cpu().tolist()
                if handoff_states[i]:
                    prefix=torch.stack(handoff_states[i]);po=torch.stack(handoff_postures[i]);controllers=torch.stack(handoff_controllers[i])
                    certificate=score(prefix,po,controllers==2,policy_time_s=torch.arange(1,len(prefix)+1)*.01,
                        configuration=env.receiver_config['protocol'])
                else:certificate={'accepted':False,'failed_checks':['missing_candidate_prefix']}
                rows.append({'env_id':i,'original_motion_intervals':n,'error_means':errors,
                    'candidate_hold_certificate':certificate,
                    'accepted':certificate['accepted'] and n>=500 and bool(active[i]) and errors[0]<=.3 and errors[1]<=.02 and errors[2]<=.03})
            original_return.append({'command':command,'per_env':rows,'passed_envs':sum(r['accepted'] for r in rows),
                'scope':'candidate same-episode hold -> originalMotion5s; diagnostic basic motion, not high speed certification'})
        finally:
            env.rise_hold.defer_completion=False
            del env.motion_command
            if hasattr(env,'return_to_original'):del env.return_to_original
    return {'task':'recovery','accepted':accepted,'per_env':combined,'recovery_gate':gate,
        'effective_protocol':effective,'receiver_protocol':env.receiver_config['protocol'],
        'evaluation_family':primary['family'],'retained_evaluations':results[1:],
        'receiver_assessments':results,'outcome_counts':{'runtime_fault':sum(p['runtime_fault'] for r in results for p in r['per_env']),
            'task_failure':sum(not p['accepted'] for p in primary['per_env']), 'success':primary['passed_envs']},
        'receiver_training_events':env.receiver_summary(),
        'original_motion_return':original_return}
