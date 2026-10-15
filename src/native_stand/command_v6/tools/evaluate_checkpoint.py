"""Independent checkpoint evaluation; no PPO optimizer or rollout storage."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]))
from native_stand.command_v6.domain.evaluation_config import scoring as scoring_configuration
from native_stand.command_v6.tools.evaluation_state import isolated_evaluation,failure_evidence


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recovery_batch_arguments(spec,row):
    if spec.get('task')!='recovery' or spec.get('rollout_probe'):return None
    return {'family':row['family'],'check_retained':False,
            'diagnostic_profile':row['diagnostic_storage']['profile']}


def stop_on_term(_signal,_frame):
    raise KeyboardInterrupt


def protocol_for_spec(spec,seconds,diagnostics=False):
    from native_stand.command_v6.domain.evidence import effective_protocol
    from native_stand.command_v6.domain.evaluation_config import scoring
    recovery=spec.get('task')=='recovery'
    if spec.get('receiver_training'):
        from native_stand.recovery.min_height import protocol
        source=protocol();source.update(protocol_identity='receiver_combination_v1',version='receiver_combination_v1',
            recovery_deadline_s=2.,seconds=seconds,steady_window_s=[0.,seconds])
        return effective_protocol(source,requested_seconds=seconds,steady_window_s=[0.,seconds],
            sample_rate_hz=100.,scored_envs=spec['evaluation']['scored_envs'],
            termination_semantics='first_episode_pre_reset; complete finite task_success terminal allowed; early terminal fails')
    source=(spec.get('recovery',{}).get('standing_task',{}).get('protocol',{})
            if recovery else scoring(spec['evaluation']))
    if recovery and spec['recovery'].get('rising_task'):
        from native_stand.recovery.rising import rise_protocol
        source=rise_protocol(source,spec['recovery']['rising_task'])
    if source:source={**source,'seconds':max(source.get('seconds',seconds),seconds)}
    window=list(source.get('steady_window_s',[.5,seconds]))
    if seconds==spec['evaluation'].get('durability_seconds'):
        window=list(spec['evaluation'].get('durability_steady_window_s',[2.,seconds]))
    elif window[1]>seconds:window=[min(.5,seconds/2),seconds]
    elif recovery and seconds>window[1]:window[1]=seconds
    enabled=bool(diagnostics or (recovery and spec['recovery'].get('gate_diagnostics',False)))
    source={**source,'diagnostics':{'requested':bool(diagnostics),'enabled':enabled,
        'merge_rule':'CLI request OR runtime spec; restored after evaluation'}}
    return effective_protocol(source,requested_seconds=seconds,steady_window_s=window,
        sample_rate_hz=1/spec['control']['policy_dt_s'],scored_envs=spec['evaluation']['scored_envs'],
        motion_window_s=None if recovery else source.get('motion_window_s'),
        parking_window_s=None if recovery else source.get('parking_window_s',
            [seconds-source['stop_window_s'],seconds] if source.get('stop_window_s',0)>0 else None),
        termination_semantics=('first_episode_pre_reset; complete finite task_success terminal allowed; early terminal fails' if source.get('protocol_identity')=='autonomous_rise_min_height_v2' else 'first_episode_pre_reset; early termination fails continuous window'))


def validate_evaluation_request(spec, request):
    """Reject cross-family fields before an evaluator constructs an environment."""
    if spec.get('task')=='recovery':
        from native_stand.command_v6.tools.recovery_batch import validate_request
        return validate_request(spec,request)
    from native_stand.command_v6.domain.evaluation_requests import motion_request
    return motion_request(request)


def batch_protocol(spec, request, diagnostics):
    if request.get('evaluation_mode','full')=='light':
        from native_stand.command_v6.domain.evidence import effective_protocol
        if request['seconds']!=spec['evaluation']['light_seconds']:
            raise ValueError('light request must match declared light duration')
        return effective_protocol({'diagnostics':{'requested':diagnostics,'enabled':diagnostics,
            'merge_rule':'explicit batch request'}},requested_seconds=request['seconds'],
            steady_window_s=spec['evaluation']['light_window_s'],
            sample_rate_hz=1/spec['control']['policy_dt_s'],scored_envs=spec['evaluation']['scored_envs'],
            motion_window_s=None,parking_window_s=None,
            termination_semantics='first_episode_pre_reset; early termination fails continuous window')
    return protocol_for_spec(spec,request['seconds'],diagnostics)


@isolated_evaluation
def evaluate_actor(actor,wrapped,env,*,target,seconds,full_trace,seed=104,scored_envs=8,
                   target_window=(2.,10.),standing_protocol=None,diagnostics=False,stop_requested=None,
                   progress_callback=None,effective_protocol=None,paired_state=False):
    if standing_protocol is not None:
        standing_protocol=scoring_configuration(standing_protocol)
    import torch
    from native_stand.command_v6.domain.protocol import EpisodeBuffer,score,standing_gate,motion_gate,capability_gate
    from native_stand.command_v6.domain.command_schedule import effective
    from native_stand.command_v6.domain.evidence import (effective_protocol as build_protocol,
        diagnostic_field,validate_effective_protocol,observed_protocol,tensor_field_validity)
    protocol=effective_protocol or build_protocol({**(standing_protocol or {}),
        **({'seconds':max(standing_protocol.get('seconds',seconds),seconds)} if standing_protocol is not None else {}),
        'diagnostics':{'requested':bool(diagnostics),'enabled':bool(diagnostics),'merge_rule':'explicit evaluator request'}},requested_seconds=seconds,
        steady_window_s=target_window,sample_rate_hz=1/env.step_dt,scored_envs=scored_envs,
        motion_window_s=(standing_protocol or {}).get('motion_window_s'),
        parking_window_s=(standing_protocol or {}).get('parking_window_s',
            [seconds-standing_protocol['stop_window_s'],seconds] if (standing_protocol or {}).get('stop_window_s',0)>0 else None),
        termination_semantics='first_episode_pre_reset; early termination fails continuous window')
    validate_effective_protocol(protocol)
    if protocol['requested_seconds']!=seconds or protocol['scored_envs']!=scored_envs:
        raise ValueError('effective protocol differs from evaluator request')
    if abs(protocol['sample_rate_hz']-1/env.step_dt)>1e-8:
        raise ValueError('effective protocol sample rate differs from runtime')
    if standing_protocol is not None:
        for key,value in standing_protocol.items():
            if key not in ('steady_window_s','seconds','diagnostics') and protocol.get(key)!=value:
                raise ValueError('effective protocol and standing protocol conflict: '+key)
    target_window=protocol['steady_window_s']
    old_length=env.cfg.episode_length_s
    old_schedule=env.schedule_s
    if protocol.get('protocol_identity') in ('capability_v2', 'motion_absolute_v3'):
        env.schedule_s=protocol['evaluation_schedule_s']
    cpu_rng=torch.get_rng_state()
    cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    old_actor_training=actor.training
    env.set_evaluation_target(*target)
    env.capture_terminal=True
    env.cfg.episode_length_s=max(seconds+env.step_dt,old_length)
    from tensordict import TensorDict
    obs_dict,_=env.reset(seed=seed)
    obs=TensorDict(obs_dict,batch_size=[env.num_envs]).clone()
    n=scored_envs
    buffer=EpisodeBuffer(int(round(seconds/env.step_dt)),n,env.device,dt=env.step_dt)
    diagnostic_rows=torch.zeros(buffer.rows.shape[0],n,54,device=env.device) if diagnostics else None
    diagnostic_valid=torch.zeros(buffer.rows.shape[0],n,dtype=torch.bool,device=env.device) if diagnostics else None
    posture_enabled=bool(getattr(env,'reward_config',{}).get('posture_balance'))
    posture_names=('left_leg_length_m','right_leg_length_m','leg_length_difference_m',
        'wheel_heading_offset_m','wheel_height_difference_m','roll_rad')
    posture_rows=torch.zeros(buffer.rows.shape[0],n,6,device=env.device) if posture_enabled else None
    posture_valid=torch.zeros(buffer.rows.shape[0],n,dtype=torch.bool,device=env.device) if posture_enabled else None
    if paired_state and not (full_trace and diagnostics):raise ValueError('paired state requires full trace/control diagnostics')
    from native_stand.command_v6.domain.paired_state import root_geometry,concatenate,CHANNELS
    paired_rows=torch.empty(buffer.rows.shape[0],n,CHANNELS,device=env.device) if paired_state else None
    paired_episode_ids=env.reset_count[:n].clone().cpu().tolist() if paired_state else None
    actor.eval()
    start=time.monotonic()
    try:
        with torch.inference_mode():
            for _ in range(buffer.rows.shape[0]):
                if stop_requested is not None and stop_requested():
                    raise failure_evidence(TimeoutError('evaluation interrupted by phase budget/termination'),
                        protocol,buffer.valid,env.step_dt,
                        buffer.rows[buffer.index-1] if buffer.index else None)
                actions=actor(obs,stochastic_output=False)
                applied_command=(env.command[:n].clone() if hasattr(env,'command') else effective(env.target_xy[:n],
                    env.episode_length_buf[:n].float()*env.step_dt,
                    height=env.command_height,entry=env.schedule_s[0],
                    ramp=env.schedule_s[1],hold=env.schedule_s[2],exit=env.schedule_s[3]))
                if paired_state:
                    actor_inputs={'policy':obs['policy'][:n].clone(),'history':obs['history'][:n].clone()}
                    pre_geometry=root_geometry(env.robot.data,env.wheel_body_ids,n).clone()
                obs,reward,dones,_=wrapped.step(actions.to(env.device).clone())
                obs=obs.clone()
                data=env.robot.data
                if posture_enabled:
                    geometry=env.measure_posture_geometry()
                    posture_rows[buffer.index].copy_(torch.stack([geometry[k][:n] for k in posture_names],dim=-1))
                    posture_valid[buffer.index].copy_(buffer.active & ~dones[:n].bool() & geometry['valid'][:n])
                if paired_state:
                    paired_rows[buffer.index].copy_(concatenate(actor_inputs,actions[:n],applied_command,
                        pre_geometry,root_geometry(data,env.wheel_body_ids,n)))
                if diagnostics:
                    q=data.joint_pos.torch[:n,env.ids]
                    dq=data.joint_vel.torch[:n,env.ids]
                    pre=env.reference[:n,(0,1,3,4)]+env.action[:n,(0,1,3,4)]*env.cfg.leg_position_scale_rad
                    diagnostic_rows[buffer.index].copy_(torch.cat((q,dq,actions[:n],env.action[:n],pre,
                        env.leg_target[:n],env.leg_target[:n]-q[:,(0,1,3,4)],env.effort_pre[:n],
                        env.effort[:n],data.applied_torque.torch[:n,env.ids]),-1))
                    # No reset-state fallback for terminal diagnostics.
                    diagnostic_valid[buffer.index].copy_(buffer.active & ~dones[:n].bool())
                state=torch.cat((data.root_pos_w.torch[:n],env.vx[:n,None],
                    env.vy[:n,None],env.yaw[:n,None],applied_command[:,:2],
                    env.contact_force[:n],env.effort[:n],
                    env.closure_each[:n].amax(-1,keepdim=True),
                    torch.acos(env.up[:n].clamp(-1.,1.))[:,None]),dim=-1)
                buffer.append(state,dones[:n].bool().reshape(-1),env.terminal_snapshot)
                if progress_callback is not None and (buffer.index==1 or buffer.index%50==0):
                    progress_callback(buffer.index)
                if bool(env.terminal_causes["nonfinite"].any()) or bool(env.terminal_causes["closure"].any()):
                    raise failure_evidence(RuntimeError('evaluation runtime fault'),protocol,
                        buffer.valid,env.step_dt,buffer.rows[buffer.index-1])
        packed=buffer.packed()
        report=score(*packed,dt=env.step_dt,target_window=target_window,
                     requested_steps=buffer.rows.shape[0],
                     full_trace=full_trace,effective_protocol=protocol)
        protocol=observed_protocol(protocol,[row.get('continuous_s',0.) for row in report['per_env']])
        report.update(target=list(target),seconds=seconds,seed=seed,effective_protocol=protocol,
                      evaluation_s=time.monotonic()-start)
        from native_stand.command_v6.domain.evaluation_config import identities
        report['evaluation_identity_components']=identities(protocol)
        if posture_enabled:
            count=buffer.index
            values=posture_rows[:count].cpu()
            validity=posture_valid[:count].cpu()
            times=torch.arange(1,count+1,dtype=torch.float64)*env.step_dt
            from native_stand.command_v6.domain.posture_geometry import diagnostic_window
            posture_axis=diagnostic_window(protocol,target,total_samples=count,dt=env.step_dt)
            window=posture_axis['window_s']
            mask=(times>=window[0]-1e-8)&(times<=window[1]+1e-8)
            report['posture_diagnostics']={'schema_version':'native_posture_geometry_v1',
                'axes':['policy_time','scored_env','channel'],'fields':list(posture_names),
                'sample_rate_hz':1/env.step_dt,'scope':'post-policy state; excludes reset/terminal samples',
                'rows':[[row if valid else None for row,valid in zip(step,valids)]
                    for step,valids in zip(values.tolist(),validity.tolist())],
                'valid':validity.tolist(),'scored_window_s':window,'window_time_axis':posture_axis,'per_env':[]}
            from native_stand.command_v6.domain.posture_geometry import bounded_cost
            for env_id,row in enumerate(report['per_env']):
                selected=values[mask & validity[:,env_id],env_id]
                complete=posture_axis['complete'] and len(selected)==posture_axis['required_samples']
                summary={'env_id':env_id,'complete_window':complete,'samples':len(selected),
                         'window_time_axis':posture_axis}
                for i,name in enumerate(posture_names):
                    summary[name+'_mean']=float(selected[:,i].mean()) if complete else None
                    summary[name+'_abs_mean']=float(selected[:,i].abs().mean()) if complete else None
                if complete:
                    geometry={name:selected[:,i] for i,name in enumerate(posture_names)}
                    geometry['valid']=torch.ones(len(selected),dtype=torch.bool)
                    cost,parts=bounded_cost(geometry,env.reward_config['posture_balance'])
                    summary['posture_cost_mean']=float(cost.mean())
                    summary['posture_component_means']={k:float(v.mean()) for k,v in parts.items()}
                else:
                    summary.update(posture_cost_mean=None,posture_component_means=None)
                row['posture_geometry']=summary
                row['posture_cost_mean']=summary['posture_cost_mean']
                report['posture_diagnostics']['per_env'].append(summary)
        if diagnostics:
            values=diagnostic_rows.cpu().tolist()
            validity=diagnostic_valid.cpu().tolist()
            report['control_diagnostics']={'schema_version':'motion_policy_control_v1',
                'axes':['policy_time','scored_env','channel'],'sampling':'100Hz policy end; torque held from latest5ms PD update',
                'groups':{'q': [0,6],'dq':[6,12],'raw_action':[12,18],'clipped_action':[18,24],
                    'leg_target_before_projection':[24,28],'leg_target_after_projection':[28,32],
                    'leg_position_error':[32,36],'PD_requested_nm':[36,42],
                    'physical_clipped_nm':[42,48],'actuator_applied_nm':[48,54]},
                'rows':[[row if valid else None for row,valid in zip(step,mask)]
                        for step,mask in zip(values,validity)],'valid':validity,
                'terminal_diagnostics_missing':(~diagnostic_valid).any().item()}
        if paired_state:
            from native_stand.command_v6.domain.paired_state import VERSION,AXES,GROUPS
            packed_pairs=paired_rows.cpu().tolist();pair_valid=diagnostic_valid.cpu().tolist()
            report['paired_state']={'schema_version':VERSION,'axes':AXES,'groups':GROUPS,
                'rows':[[row if valid else None for row,valid in zip(step,mask)] for step,mask in zip(packed_pairs,pair_valid)],
                'valid':pair_valid,'actor_sample_phase':'pre_policy_step','post_state_phase':'post_policy_step',
                'measurement_point':'body_COM','wheel_geometry_point':'body_origins; collider centers not inferred',
                'terminal_scope':'pre/post aligned rows exclude reset/terminal rows; terminal evidence separately saved',
                'episode_id_by_env':paired_episode_ids,'policy_index':'row axis; zero-based',
                'sample_rate_hz':1/env.step_dt}
        report['diagnostics_validity']={'control_diagnostics':diagnostic_field(
            True if diagnostics else None,requested=diagnostics,enabled=diagnostics,
            sample_count=int(diagnostic_valid.sum()) if diagnostics else 0,
            scope='100Hz policy end; terminal samples excluded when pre-reset controls unavailable')}
        report['diagnostic_field_validity']=tensor_field_validity(diagnostic_rows,diagnostic_valid,['control_'+str(i) for i in range(54)],
            requested=diagnostics,enabled=diagnostics,
            scope='100Hz policy end; pre-reset controls unavailable for terminal rows')
        if standing_protocol is not None and standing_protocol.get('protocol_identity') in ('capability_v2', 'motion_absolute_v3'):
            report['capability_gate']=capability_gate(report,target,protocol)
        elif (standing_protocol is not None and tuple(target)!=(0.,0.)):
            movement_protocol={**protocol,
                'vx_error_max_mps':max(standing_protocol.get('motion_vx_error_max_mps',.03),abs(target[0])*standing_protocol.get('relative_motion_error_fraction',0.)),
                'yaw_error_max_rad_s':max(standing_protocol.get('motion_yaw_error_max_rad_s',.03),abs(target[1])*standing_protocol.get('relative_motion_error_fraction',0.))}
            report['motion_gate']=motion_gate(report,target,movement_protocol)
        if (standing_protocol is not None and standing_protocol.get('protocol_identity') not in ('capability_v2', 'motion_absolute_v3') and tuple(target)==(0.,0.) and
                seconds>=standing_protocol["seconds"]):
            report["standing_gate"]=standing_gate(report,protocol)
        return report
    finally:
        pass  # Outer guard restores modes, runtime switches and RNG on setup failure too.


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,default=ROOT.parents[2]/"configs/experiments/stand_plane.json")
    parser.add_argument("--checkpoint",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--vx",type=float,default=0.)
    parser.add_argument("--yaw",type=float,default=0.)
    parser.add_argument("--height",type=float,default=None,
                        help="override standing height command for diagnostic evaluation")
    parser.add_argument("--seconds",type=float,default=10.)
    parser.add_argument("--full-trace",action="store_true")
    parser.add_argument("--diagnostics",action="store_true",
                        help="retain compact action/target/PD diagnostics")
    parser.add_argument("--run",action="store_true")
    parser.add_argument('--batch', action='store_true', help='one app, explicit frozen evaluation_requests in spec')
    parser.add_argument('--attempt-id')
    parser.add_argument('--wall-limit-s', type=float)
    parser.add_argument("--diagnostic",action="store_true",
                        help="read-only diagnostic: skip PPO/evaluation ledger reservation")
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    spec=json.loads(args.spec.read_text())
    if args.batch:
        return evaluate_batch(args, spec)
    if args.checkpoint is None:
        parser.error('--checkpoint is required unless --batch')
    if spec["curriculum"]["active_stage"]==0 and (args.vx!=0. or args.yaw!=0.):
        raise ValueError("current standing experiment evaluates zero command only")
    if not args.checkpoint.is_file() or args.seconds<=0 or args.seconds>100:
        raise ValueError("checkpoint or duration invalid")
    from native_stand.command_v6.tools.checkpoint_input import inspect
    checkpoint_info=inspect(args.checkpoint,spec,args.spec)
    height = spec["control"]["height_command_m"] if args.height is None else args.height
    if not 0.2 <= height <= 0.6:
        raise ValueError("height diagnostic must be in [0.2,0.6] m")
    plan={"checkpoint":str(args.checkpoint),**checkpoint_info,
          "spec_sha256":_sha(args.spec),"output":str(args.output),"target":[args.vx,args.yaw,height],
          "seconds":args.seconds,"full_trace":args.full_trace,
          "effective_protocol":protocol_for_spec(spec,args.seconds,args.diagnostics)}
    if not args.run:
        print(json.dumps({**plan,"simulation":0,"ppo":0,"files_written":0},indent=2))
        return
    from native_stand.command_v6.tools.preflight import check
    from native_stand.command_v6.ledger import Ledger
    preflight=check(args.spec,args.output,"evaluate")
    if preflight["status"]!="PASS" and not args.diagnostic:
        raise RuntimeError(f"evaluation preflight failed: {preflight['errors']}")
    ledger=Ledger(args.spec.with_name("budget.json"))
    attempt_id=uuid.uuid4().hex
    if not args.diagnostic:
        ledger.reserve(attempt_id,"evaluate",args.output,approval=preflight)
    started=time.monotonic()
    signal.signal(signal.SIGTERM,stop_on_term)
    env=app=None
    status="FAILED"
    failure=None
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher({"headless":True}).app
        signal.signal(signal.SIGTERM,stop_on_term)
        import torch
        sys.path.insert(0,spec["asset_module_root"])
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from native_stand.command_v6.tools.model_factory import model as build_model
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import
        from native_stand.command_v6.domain.warmstart import expand_state
        asset_import=verify_asset_import(spec)
        cfg=configure_env(CommandEnvCfg(),spec,envs=spec["evaluation"]["envs"],mode="evaluation")
        if spec.get('task')=='recovery':
            from native_stand.recovery.recipe import environment
            env=environment(cfg,spec)
        else:
            from native_stand.command_v6.domain.recipe import resolve
            effective_spec,_=resolve(spec)
            env=CommandEnv(cfg,stage=spec["curriculum"]["stages"][spec['curriculum']['active_stage']],
                           command_height=height,
                           reward_config=effective_spec["reward"],
                           schedule_s=spec["curriculum"]["schedule_s"])
        ground=verify_ground(env,spec)
        control=verify(env)
        wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
        obs=wrapped.get_observations()
        actor=build_model(obs,actor=True,spec=spec).to(env.device)
        checkpoint=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
        if (spec.get('recovery',{}).get('standing_task',{}).get('protocol',{}).get('objective')=='survival_level'
                and checkpoint.get('recovery_curriculum') is not None):
            env.restore_recovery_curriculum(checkpoint['recovery_curriculum'])
        state=checkpoint["actor"]
        if state["mlp.0.weight"].shape[-1]==132:
            if _sha(args.checkpoint)!=spec["source_sha256"]:
                raise RuntimeError("source actor identity differs")
            state=expand_state(state,actor.state_dict())
        from native_stand.command_v6.tools.model_adapter import ModelAdapter
        ModelAdapter({'actor':state}).load(actor,'actor')
        if _sha(args.checkpoint)==spec['source_sha256'] and spec.get('wheel_envelope_conversion'):
            from native_stand.command_v6.domain.warmstart import convert_wheel_envelope
            convert_wheel_envelope(actor,old_scale=spec['wheel_envelope_conversion']['source_scale_rad_s'],
                                  new_scale=spec['action']['wheel_scale_rad_s'])
        protocol=spec['evaluation']
        if args.seconds==protocol.get('durability_seconds'):
            protocol={**protocol,'seconds':args.seconds,'steady_window_s':[2,args.seconds]}
        evaluator=evaluate_actor
        if spec.get('task')=='recovery':
            from native_stand.recovery.recipe import evaluate_actor as evaluator
        from native_stand.command_v6.domain.diagnostic_profiles import storage_plan
        collection=storage_plan(spec,full=True,legacy_full_trace=args.full_trace,legacy_diagnostics=args.diagnostics)
        result=evaluator(actor,wrapped,env,target=(args.vx,args.yaw),
            seconds=args.seconds,**collection['runtime_kwargs'],seed=spec["evaluation"]["seed"],
            scored_envs=spec["evaluation"]["scored_envs"],
            target_window=protocol["steady_window_s"],
            standing_protocol=protocol,
            effective_protocol=plan['effective_protocol'])
        result.update({key:value for key,value in plan.items() if key!='effective_protocol'})
        result['requested_effective_protocol']=plan['effective_protocol']
        result["runtime_control"]=control
        result["ground_readback"]=ground
        result["asset_import_readback"]=asset_import
        args.output.parent.mkdir(parents=True,exist_ok=True)
        if spec.get('artifacts',{}).get('evaluation_trace_encoding')=='evaluation_numeric_npz_v1':
            from native_stand.command_v6.tools.evaluation_storage import write as write_evaluation
            write_evaluation(args.output,result)
        else:
            with args.output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
        status="COMPLETED"
        print(json.dumps({"output":str(args.output),"outcome_counts":result["outcome_counts"]}))
    except KeyboardInterrupt:
        status="STOPPED_BOUNDED"
    except BaseException as exc:
        failure={"exception":repr(exc),"traceback":traceback.format_exc(),
            'evaluation_evidence':getattr(exc,'evaluation_evidence',None)}
        raise
    finally:
        terminal=args.output.with_name(args.output.stem+".terminal.json")
        with terminal.open("x") as stream:
            stream.write(json.dumps({"status":status,"attempt_id":attempt_id,
                "output":str(args.output),"wall_s":time.monotonic()-started,
                "failure":failure},indent=2)+"\n")
        if not args.diagnostic:
            ledger.finalize(attempt_id,args.output,status,reason=failure["exception"] if failure else None,
                            wall_s=time.monotonic()-started)
        if env is not None:
            env.close()
        if app is not None:
            app.close()


def batch_plan(args, spec):
    if spec.get("interface_version") in ("multiskill_student_v1","multiskill_mcu_v2"):
        from native_stand.students.requests import plan
        return plan(args,spec)
    from native_stand.command_v6.tools.preflight import check
    from native_stand.command_v6.domain.recipe import resolve
    from native_stand.command_v6.domain.input_capture import validate as validate_capture
    validate_capture(spec)
    from native_stand.command_v6.tools.checkpoint_input import inspect
    preflight=check(args.spec,args.output,'evaluate',attempt_id=args.attempt_id)
    effective_spec,recipe=resolve(spec)
    if spec.get('motion_handoff'):
        from native_stand.recovery.handoff_evaluator import plan as handoff_plan
        return handoff_plan(args,spec,preflight)
    if spec.get('rollout_probe'):
        from native_stand.command_v6.domain.rollout_probe import validate as validate_probe
        validate_probe(spec)
        info=inspect(Path(spec['source_checkpoint']),spec,args.spec)
        if info['checkpoint_sha256']!=spec['source_sha256']:raise ValueError('Probe source SHA differs')
        return {'preflight':preflight,'requested':spec,'effective_recipe':recipe,
            'execution_identity':preflight['execution_identity'],'requests':[{
                'checkpoint':spec['source_checkpoint'],'sha256':spec['source_sha256'],'target':[0,0],
                'seconds':2.56,'seed':spec['seed'],'family':'mixed_fixed_training_families',
                'role':'frozen_stochastic_rollout','diagnostic_storage':None,'effective_protocol':{'capability_gate':'NOT_RUN'}}],
            'simulation':0,'online_PPO':0,'offline_optimizer_updates':0,'files_written':0}
    requests=spec['evaluation_requests']
    if not requests or spec.get('effective_recipe_version') != 1:
        raise ValueError('batch evaluation requires explicit effective recipe and requests')
    planned=[]
    for row in requests:
        row=validate_evaluation_request(spec, row)
        path=Path(row['checkpoint'])
        info=inspect(path,spec,args.spec)
        if info['checkpoint_sha256'] != row['sha256']:
            raise ValueError('batch checkpoint SHA differs: '+str(path))
        target=row['target']
        if len(target)!=2 or not all(__import__('math').isfinite(v) for v in target):
            raise ValueError('invalid batch target')
        seconds=row['seconds']
        if spec.get('task')=='recovery':
            families={p['family'] for p in json.loads(Path(spec['recovery']['pose_library']).read_text())['poses']}
            from native_stand.recovery.task_protocol import batch_seconds
            required_seconds=batch_seconds(spec)
            if row.get('family') not in families or target!=[0,0] or seconds!=required_seconds:
                raise ValueError('Recovery batch requires known family,zero target,task duration')
        from native_stand.command_v6.domain.diagnostic_profiles import storage_plan
        storage=storage_plan(spec,full=True,request=row,legacy_full_trace=True,legacy_diagnostics=True)
        if storage.get('fields') is not None and spec.get('task')=='recovery' and not spec['recovery'].get('standing_task'):
            storage['fields']=[name for name in storage['fields'] if name not in ('posture','geometry')]
            if set(storage['required_fields'])-set(storage['fields']):
                raise ValueError('Recovery task lacks required posture/geometry runtime fields')
        planned.append({**row,**info,'diagnostic_storage':storage,
            'effective_protocol':batch_protocol(effective_spec,row,True if storage is None else storage['diagnostics'])})
    return {'preflight':preflight,'requested':spec,'effective_recipe':recipe,
            'execution_identity':preflight['execution_identity'],'requests':planned,
            'simulation':0,'online_PPO':0,'offline_optimizer_updates':0,'files_written':0}


def evaluate_batch(args, spec):
    """PPO0 batch adapter under the existing monitor and exact ledger."""
    if spec.get("interface_version") in ("multiskill_student_v1","multiskill_mcu_v2"):
        from native_stand.students.evaluator import execute
        return execute(args,spec)
    if spec.get('motion_handoff'):
        from native_stand.recovery.handoff_evaluator import execute
        return execute(args,spec)
    import os
    from native_stand.command_v6.completion import write
    from native_stand.command_v6.ledger import Ledger
    from native_stand.command_v6.domain.recipe import resolve
    plan=batch_plan(args,spec)
    if not args.run:
        print(json.dumps(plan,indent=2));return
    if plan['preflight']['status']!='PASS':
        raise ValueError(plan['preflight'])
    if not args.attempt_id or not args.wall_limit_s:
        raise ValueError('batch requires supervisor reservation and finite wall bound')
    ledger=Ledger(args.spec.with_name('budget.json'))
    book=json.loads(ledger.path.read_text())
    attempt=book['attempts'].get(args.attempt_id)
    if not attempt or attempt['status']!='RUNNING' or attempt['output_dir']!=str(args.output.resolve()):
        raise ValueError('batch exact reservation differs')
    started=time.monotonic()
    # Reservation time includes supervisor startup; wall never restarts in the child.
    deadline=time.monotonic()+max(0.,args.wall_limit_s-(time.time()-attempt['started_unix_s']))
    app=env=None
    status='FAILED';failure=None;completed=[]
    progress={'status':'STARTING','attempt_id':args.attempt_id,'pid':os.getpid(),
              'actual_updates':0,'samples':0,'completed':completed}
    args.output.mkdir(parents=True,exist_ok=False)
    from native_stand.command_v6.train import record_run_configuration
    snapshot=record_run_configuration(args.output,args.spec)
    write(args.output/'manifest.json',{'attempt_id':args.attempt_id,'phase':'evaluate',
        'pid':os.getpid(),'spec_sha256':_sha(args.spec),'source_sha256':spec['source_sha256'],
        'asset_sha256':spec['asset_sha256'],'source_snapshot_sha256':snapshot,
        'requested':spec,'effective_recipe':plan['effective_recipe'],
        'execution_identity':__import__('native_stand.command_v6.tools.execution_identity',fromlist=['reference']).reference(args.output),'requests':plan['requests'],
        'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),
        'wall_limit_s':args.wall_limit_s,'online_PPO':0,'offline_optimizer_updates':0})
    write(args.output/'progress.json',progress)
    signal.signal(signal.SIGTERM,stop_on_term)
    try:
        sys.path.insert(0,spec['asset_module_root'])
        from isaaclab.app import AppLauncher
        app=AppLauncher({'headless':True,'device':'cuda:0','multi_gpu':False}).app
        signal.signal(signal.SIGTERM,stop_on_term)
        import torch
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.configure import apply,verify_asset_import
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.tools.model_factory import model
        effective_spec,_=resolve(spec)
        cfg=apply(CommandEnvCfg(),effective_spec,envs=spec['evaluation']['envs'],mode='evaluation')
        cfg.sim.device='cuda:0'
        if spec.get('task')=='recovery':
            from native_stand.recovery.recipe import environment
            env=environment(cfg,effective_spec)
        else:
            env=CommandEnv(cfg,stage=spec['curriculum']['stages'][spec['curriculum']['active_stage']],
                command_height=spec['control']['height_command_m'],reward_config=effective_spec['reward'],
                schedule_s=spec['curriculum']['schedule_s'])
        readback={'asset':verify_asset_import(spec),'control':verify(env),'ground':verify_ground(env,spec),
                  'reward':env.reward_config,'schedule_s':env.schedule_s,'device':str(env.device)}
        write(args.output/'runtime_readback.json',readback)
        wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
        actor=model(wrapped.get_observations(),actor=True,spec=spec).to(env.device)
        progress['status']='RUNNING';write(args.output/'progress.json',progress)
        elapsed_items=[]
        for index,row in enumerate(plan['requests']):
            estimate=max(elapsed_items,default=180.)*1.15
            if time.monotonic()+estimate+90.>=deadline:
                status='STOPPED_BOUNDED';failure={'reason':'insufficient time for full next item and cleanup'};break
            if _sha(row['checkpoint'])!=row['sha256']:
                raise ValueError('checkpoint changed after plan')
            saved=torch.load(row['checkpoint'],map_location='cpu',weights_only=False)
            from native_stand.command_v6.tools.model_adapter import ModelAdapter
            ModelAdapter(saved).load(actor,'actor')
            item_start=time.monotonic()
            evaluator=evaluate_actor
            extra={}
            recovery_arguments=recovery_batch_arguments(spec,row)
            if recovery_arguments is not None:
                from native_stand.recovery.recipe import evaluate_actor as evaluator
                extra=recovery_arguments
            recorder=None
            if spec.get('input_capture'):
                from native_stand.command_v6.domain.input_capture import Recorder
                recorder=Recorder(round(row['seconds']/env.step_dt),spec['evaluation']['scored_envs'],env.device,
                    std=saved['actor']['distribution.std_param'].to(env.device),active_indices=env.ids,
                    joint_names=env.robot.joint_names,dt=env.step_dt)
                extra['input_recorder']=recorder
            if spec.get('rollout_probe'):
                from native_stand.command_v6.tools.frozen_rollout_probe import collect
                def evaluator(actor,wrapped,env,**kwargs):
                    return collect(actor,wrapped,env,spec=spec,output=args.output,
                        stop_requested=kwargs['stop_requested'])
                extra={}
            storage=row.get('diagnostic_storage')
            if spec.get('task')!='recovery' and storage and storage['profile']=='paired_state':extra['paired_state']=True
            result=evaluator(actor,wrapped,env,target=tuple(row['target']),
                seconds=row['seconds'],
                full_trace=True if storage is None else storage['full_trace'],seed=row['seed'],scored_envs=8,
                standing_protocol=None if row.get('evaluation_mode')=='light' else scoring_configuration(spec['evaluation']),diagnostics=True if storage is None else storage['diagnostics'],
                effective_protocol=row['effective_protocol'],
                stop_requested=lambda:time.monotonic()>=deadline-90.,**extra)
            result.update(checkpoint=row['checkpoint'],checkpoint_sha256=row['sha256'],
                spec_sha256=_sha(args.spec),asset_sha256=spec['asset_sha256'],
                execution_identity=__import__('native_stand.command_v6.tools.execution_identity',fromlist=['reference']).reference(args.output),runtime_readback=readback)
            result['diagnostic_storage']=storage
            if row.get('evaluation_mode')=='light':
                result['engineering_diagnostic_only']=True
                result['capability_gate']={'accepted':False,'status':'NOT_RUN',
                    'reason':'light engineering diagnostic cannot certify full capability'}
            if spec.get('task')=='recovery' and storage is not None:
                for episode in result['per_env']:
                    missing=set(storage['required_fields'])-set(episode.get('diagnostic_profile_available_fields',[]))
                    if missing:raise ValueError('runtime diagnostic fields unavailable: '+str(sorted(missing)))
            name=f'evaluation_{index:02d}.json'
            if recorder is not None:
                import numpy as np
                arrays=recorder.finish();raw_name=f'input_capture_{index:02d}.npz'
                size=sum(p.stat().st_size for p in args.output.rglob('*') if p.is_file())
                required=sum(a.nbytes for a in arrays.values())+65536+len(json.dumps(result,indent=2).encode())
                if size+required>spec['input_capture']['max_storage_bytes']:
                    raise TimeoutError('Input capture storage ceiling reached; item incomplete')
                with (args.output/raw_name).open('xb') as stream:np.savez(stream,**arrays)
                result['input_capture']={**recorder.metadata(),'path':raw_name,'sha256':_sha(args.output/raw_name),
                    'array_shapes':{k:list(a.shape) for k,a in arrays.items()},'bytes':(args.output/raw_name).stat().st_size}
            if spec.get('artifacts',{}).get('evaluation_trace_encoding')=='evaluation_numeric_npz_v1':
                from .evaluation_storage import write as write_evaluation
                write_evaluation(args.output/name,result)
            else:write(args.output/name,result)
            elapsed_items.append(time.monotonic()-item_start)
            completed.append({'path':name,'checkpoint_sha256':row['sha256'],'target':row['target'],
                'wall_s':elapsed_items[-1],'family':row.get('family'),'seed':row.get('seed'),
                'accepted':(result['recovery_gate'] if spec.get('task')=='recovery' else result['capability_gate'])['accepted']})
            progress.update(completed=completed,last_activity_unix_s=time.time())
            write(args.output/'progress.json',progress)
            group_name=row.get('evaluation_group')
            if group_name and row.get('on_group_failure')=='stop':
                members=[i for i,r in enumerate(plan['requests']) if r.get('evaluation_group')==group_name]
                if index==max(members) and any(not completed[i]['accepted'] for i in members):
                    status='STOPPED_BOUNDED';failure={'reason':'explicit evaluation group failed','group':group_name};break

        else:status='COMPLETED'
    except (KeyboardInterrupt,TimeoutError) as exc:
        status='STOPPED_BOUNDED';failure={'reason':str(exc),'evaluation_evidence':getattr(exc,'evaluation_evidence',None)}
    except BaseException as exc:
        failure={'reason':repr(exc),'traceback':traceback.format_exc(),
                 'evaluation_evidence':getattr(exc,'evaluation_evidence',None)}
    finally:
        terminal={'status':status,'attempt_id':args.attempt_id,'actual_updates':0,'samples':0,
            'online_PPO':0,'offline_optimizer_updates':0,'completed':completed,
            'missing_requests':plan['requests'][len(completed):], 'failure':failure,
            'reason':failure.get('reason') if failure else ('frozen stochastic rollout diagnostic completed' if spec.get('rollout_probe') else 'all requested deterministic evaluations completed'),
            'wall_s':time.time()-attempt['started_unix_s'],'cleanup':'pending; monitor confirms child exit'}
        progress['status']=status
        write(args.output/'progress.json',progress)
        write(args.output/'terminal_report.json',terminal)
        # Monitor finalizes only after child exits, so cleanup is included in accounting.
        if env is not None:env.close()
        if app is not None:app.close(exit_code=1 if status=='FAILED' else 0)
    return 1 if status=='FAILED' else 0


if __name__=="__main__":
    raise SystemExit(main())
