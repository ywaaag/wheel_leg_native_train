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
from native_stand.command_v6.tools.evaluation_state import isolated_evaluation,failure_evidence


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stop_on_term(_signal,_frame):
    raise KeyboardInterrupt


def protocol_for_spec(spec,seconds,diagnostics=False):
    from native_stand.command_v6.domain.evidence import effective_protocol
    recovery=spec.get('task')=='recovery'
    source=(spec.get('recovery',{}).get('standing_task',{}).get('protocol',{})
            if recovery else spec['evaluation'])
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
        termination_semantics='first_episode_pre_reset; early termination fails continuous window')


@isolated_evaluation
def evaluate_actor(actor,wrapped,env,*,target,seconds,full_trace,seed=104,scored_envs=8,
                   target_window=(2.,10.),standing_protocol=None,diagnostics=False,stop_requested=None,
                   progress_callback=None,effective_protocol=None):
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
    if protocol.get('protocol_identity')=='capability_v2':
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
                applied_command=effective(env.target_xy[:n],
                    env.episode_length_buf[:n].float()*env.step_dt,
                    height=env.command_height,entry=env.schedule_s[0],
                    ramp=env.schedule_s[1],hold=env.schedule_s[2],exit=env.schedule_s[3])
                obs,reward,dones,_=wrapped.step(actions.to(env.device).clone())
                obs=obs.clone()
                data=env.robot.data
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
        if diagnostics:
            values=diagnostic_rows.cpu().tolist()
            validity=diagnostic_valid.cpu().tolist()
            report['control_diagnostics']={'sampling':'100Hz policy end; torque held from latest5ms PD update',
                'groups':{'q': [0,6],'dq':[6,12],'raw_action':[12,18],'clipped_action':[18,24],
                    'leg_target_before_projection':[24,28],'leg_target_after_projection':[28,32],
                    'leg_position_error':[32,36],'PD_requested_nm':[36,42],
                    'physical_clipped_nm':[42,48],'actuator_applied_nm':[48,54]},
                'rows':[[row if valid else None for row,valid in zip(step,mask)]
                        for step,mask in zip(values,validity)],'valid':validity,
                'terminal_diagnostics_missing':(~diagnostic_valid).any().item()}
        report['diagnostics_validity']={'control_diagnostics':diagnostic_field(
            True if diagnostics else None,requested=diagnostics,enabled=diagnostics,
            sample_count=int(diagnostic_valid.sum()) if diagnostics else 0,
            scope='100Hz policy end; terminal samples excluded when pre-reset controls unavailable')}
        report['diagnostic_field_validity']=tensor_field_validity(diagnostic_rows,diagnostic_valid,['control_'+str(i) for i in range(54)],
            requested=diagnostics,enabled=diagnostics,
            scope='100Hz policy end; pre-reset controls unavailable for terminal rows')
        if standing_protocol is not None and standing_protocol.get('protocol_identity')=='capability_v2':
            report['capability_gate']=capability_gate(report,target,protocol)
        elif (standing_protocol is not None and tuple(target)!=(0.,0.)):
            movement_protocol={**protocol,
                'vx_error_max_mps':max(standing_protocol.get('motion_vx_error_max_mps',.03),abs(target[0])*standing_protocol.get('relative_motion_error_fraction',0.)),
                'yaw_error_max_rad_s':max(standing_protocol.get('motion_yaw_error_max_rad_s',.03),abs(target[1])*standing_protocol.get('relative_motion_error_fraction',0.))}
            report['motion_gate']=motion_gate(report,target,movement_protocol)
        if (standing_protocol is not None and standing_protocol.get('protocol_identity')!='capability_v2' and tuple(target)==(0.,0.) and
                seconds>=standing_protocol["seconds"]):
            report["standing_gate"]=standing_gate(report,protocol)
        return report
    finally:
        pass  # Outer guard restores modes, runtime switches and RNG on setup failure too.


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,default=ROOT.parents[2]/"configs/experiments/stand_plane.json")
    parser.add_argument("--checkpoint",type=Path,required=True)
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
    parser.add_argument("--diagnostic",action="store_true",
                        help="read-only diagnostic: skip PPO/evaluation ledger reservation")
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    spec=json.loads(args.spec.read_text())
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
        ledger.reserve(attempt_id,"evaluate",args.output)
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
        from native_stand.command_v6.learning import model as build_model
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import
        from native_stand.command_v6.domain.warmstart import expand_state
        asset_import=verify_asset_import(spec)
        cfg=configure_env(CommandEnvCfg(),spec,envs=spec["evaluation"]["envs"])
        if spec.get('task')=='recovery':
            from native_stand.recovery.recipe import environment
            env=environment(cfg,spec)
        else:
            env=CommandEnv(cfg,stage=spec["curriculum"]["stages"][0],
                           command_height=height,
                           reward_config=spec["reward"],
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
        actor.load_state_dict(state,strict=True)
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
        result=evaluator(actor,wrapped,env,target=(args.vx,args.yaw),
            seconds=args.seconds,full_trace=args.full_trace,seed=spec["evaluation"]["seed"],
            scored_envs=spec["evaluation"]["scored_envs"],
            target_window=protocol["steady_window_s"],
            standing_protocol=protocol,diagnostics=args.diagnostics,
            effective_protocol=plan['effective_protocol'])
        result.update({key:value for key,value in plan.items() if key!='effective_protocol'})
        result['requested_effective_protocol']=plan['effective_protocol']
        result["runtime_control"]=control
        result["ground_readback"]=ground
        result["asset_import_readback"]=asset_import
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("x") as stream:
            stream.write(json.dumps(result,indent=2)+"\n")
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


if __name__=="__main__":
    main()
