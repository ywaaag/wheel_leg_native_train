"""GUI preview using the same plane scene, actor input and physical controller."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]))


def keyboard_app_options(physical_gpu):
    from native_stand.command_v6.domain.gui_device import resolve
    return resolve(physical_gpu)['app_options']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stop_on_term(_signal,_frame):
    raise KeyboardInterrupt


def configure_recovery_preview(env,spec,*,family=None):
    """Single selected holdout family; never reuse fixed training slot quotas."""
    from native_stand.command_v6.runtime.execution_mode import apply
    family=family or spec['recovery'].get('preview_family',spec['recovery'].get('active_family','R0'))
    return apply(env,'preview',envs=1,family=family)['family']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,default=ROOT.parents[2]/"configs/experiments/stand_plane.json")
    parser.add_argument("--checkpoint",type=Path,required=True)
    parser.add_argument('--handoff-condition',type=int,default=None,
                        help='Preview an exact motion_handoff case index using both frozen policies')
    parser.add_argument("--output",type=Path)
    parser.add_argument("--preview",action="store_true",
                        help="Repeatable manual GUI: no project output or budget ledger writes")
    parser.add_argument("--ground-style",choices=("grid","solid","none"),default="grid",
                        help="GUI-only ground appearance; physics plane is unchanged (default: grid)")
    parser.add_argument("--ground-extent-m",type=float,default=128.0,
                        help="GUI visual ground extent in meters (default: 128)")
    parser.add_argument("--ground-grid-spacing-m",type=float,default=1.0,
                        help="GUI grid spacing in meters (default: 1)")
    parser.add_argument("--strict-identities",action="store_true",
                        help="Reject preview when the external colleague YAML changed")
    parser.add_argument("--max-policy-steps",type=int,default=0,
                        help="0 keeps preview running until the GUI closes")
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--preview-family",help="Explicit Recovery holdout family for single-environment preview")
    parser.add_argument("--diagnostic-initialization",action="store_true",help="Student GUI only: preview a legal pose-library family outside the assessment matrix; no capability certification")
    parser.add_argument('--keyboard',action='store_true',help='Motion preview only: W/S commands, smooth release to zero')
    parser.add_argument('--physical-gpu',type=int,choices=(0,1),default=None)
    parser.add_argument('--speed',type=float,default=1.)
    parser.add_argument('--yaw-speed',type=float,default=0.)
    # None keeps every legacy default intact while the Motion student preview resolves its own caps.
    parser.add_argument('--max-speed',type=float,default=None)
    parser.add_argument('--max-yaw-speed',type=float,default=None)
    parser.add_argument('--max-wall-seconds',type=float,default=600.)
    parser.add_argument('--panel',action='store_true',
                        help='Motion student preview only: serve the loopback browser control panel')
    parser.add_argument('--panel-port',type=int,default=None,
                        help='Motion student preview only: panel port (default 8765)')
    args=parser.parse_args()
    legacy_max_speed=2. if args.max_speed is None else args.max_speed
    legacy_max_yaw=0. if args.max_yaw_speed is None else args.max_yaw_speed
    controls=None
    if args.keyboard:
        if not args.preview:parser.error('--keyboard requires --preview')
        from native_stand.command_v6.domain.keyboard_command import KeyboardCommand
        controls=KeyboardCommand(args.speed,args.yaw_speed,max_speed=legacy_max_speed,max_yaw_speed=legacy_max_yaw)
        if not 0<args.max_wall_seconds<=7200:parser.error('max-wall-seconds must be in (0,7200]')
    if args.preview and args.output is not None:
        parser.error("--preview does not accept --output")
    if not args.preview and args.output is None:
        parser.error("recorded playback requires --output; use --preview for manual viewing")
    if (args.output is not None and args.output.exists()) or args.max_policy_steps<0 or not args.checkpoint.is_file():
        raise ValueError("output exists, step limit invalid or checkpoint missing")
    spec=json.loads(args.spec.read_text())
    if (args.panel or args.panel_port is not None) and not args.preview:
        parser.error('--panel requires --preview (no ledger or output writes)')
    if (args.panel or args.panel_port is not None) and spec.get('interface_version') not in ('multiskill_student_v1','multiskill_mcu_v2'):
        parser.error('--panel is implemented for the Motion student preview only')
    if spec.get('interface_version') in ('multiskill_student_v1','multiskill_mcu_v2'):
        from native_stand.students.play import execute
        return execute(args,spec)
    recovery=spec.get('task')=='recovery'
    handoff_row=None
    if args.handoff_condition is not None:
        if not args.preview or not recovery or args.keyboard:
            parser.error('--handoff-condition requires Recovery --preview without keyboard')
        from native_stand.recovery.handoff_requests import validate as validate_handoff
        validate_handoff(spec)
        cases=spec['motion_handoff']['cases']
        if not 0<=args.handoff_condition<len(cases):parser.error('handoff condition index out of range')
        handoff_row=cases[args.handoff_condition]
        if digest(args.checkpoint)!=handoff_row['sha256']:
            raise ValueError('handoff Recovery checkpoint differs from selected condition')
        for key in ('motion_checkpoint','motion_spec'):
            if digest(spec['motion_handoff'][key])!=spec['motion_handoff'][key.replace('checkpoint','sha256').replace('spec','spec_sha256')]:
                raise ValueError('handoff Motion identity differs: '+key)
        if args.preview_family and args.preview_family!=handoff_row['family']:
            raise ValueError('handoff preview family differs from selected condition')
        args.preview_family=handoff_row['family']
    if args.physical_gpu is None:args.physical_gpu=spec.get('device',{}).get('physical_index',1)
    import os
    from native_stand.command_v6.domain.gui_device import resolve as resolve_gui_device
    device_plan=resolve_gui_device(args.physical_gpu,os.environ.get('CUDA_VISIBLE_DEVICES'))
    if recovery and controls is not None:parser.error('--keyboard is Motion only')
    if args.preview_family and (not recovery or not args.preview):parser.error('--preview-family requires Recovery --preview')
    if recovery and not args.preview:
        raise ValueError('Recovery GUI requires --preview: no training ledger or output writes')
    from native_stand.command_v6.config import validate
    if validate(spec):
        raise ValueError("experiment spec invalid")
    identity_warnings=[]
    if args.preview:
        # Validate frozen inputs without reading/reserving a training ledger.
        for key,identity in (("source_checkpoint","source_sha256"),
                             ("asset_path","asset_sha256"),
                             ("asset_module_path","asset_module_sha256"),
                             ("colleague_config_path","colleague_config_sha256")):
            if key == "source_checkpoint" and spec.get("initialization", "warmstart") == "random":
                continue
            if digest(spec[key]) != spec[identity]:
                if (key == "colleague_config_path" and not args.strict_identities and controls is None):
                    identity_warnings.append({"key":key,"expected_sha256":spec[identity],
                                              "actual_sha256":digest(spec[key])})
                    continue
                raise ValueError(f"{key} SHA differs")
        if spec["interpreter"] != sys.executable:
            raise ValueError("interpreter differs from frozen spec")
        if recovery:
            config=spec['recovery']
            for key,identity in (("stand_checkpoint","stand_sha256"),
                                 ("stand_spec","stand_spec_sha256"),
                                 ("pose_library","pose_library_sha256")):
                if digest(config[key])!=config[identity]:
                    raise ValueError(f'Recovery {key} SHA differs')
    from native_stand.command_v6.tools.checkpoint_input import inspect
    checkpoint_info=inspect(args.checkpoint,spec,args.spec)
    plan={"checkpoint":str(args.checkpoint),**checkpoint_info,
          "spec_sha256":digest(args.spec),"output":str(args.output) if args.output else None,
          "preview":args.preview,"execution_mode":"preview" if args.preview else "evaluation",
          "device_mapping":device_plan,
          "command":[0.,0.,spec["control"]["height_command_m"]],
          "max_policy_steps":args.max_policy_steps,"PPO_updates":0,
          "identity_warnings":identity_warnings}
    from native_stand.command_v6.tools.preview_plan import model_identity,recovery_selection,command as preview_command
    family=None
    if recovery:
        selection=recovery_selection(spec,family=args.preview_family)
        family=selection['family']
        plan['reset_plan']=selection
    plan['model_contract']=model_identity(spec,args.checkpoint,family=family)
    if handoff_row is not None:
        plan['handoff']={'condition_index':args.handoff_condition,'condition':handoff_row,
            'motion_sha256':spec['motion_handoff']['motion_sha256'],
            'scope':'same-state direct switch; GUI only, not a new capability certificate'}
    if args.preview:plan['commands']=preview_command(args.spec,args.checkpoint,args.physical_gpu,family=family)
    if recovery:
        plan['recovery_preview']={'asset_path':spec['asset_path'],'asset_sha256':spec['asset_sha256'],
            'pose_library':spec['recovery']['pose_library'],
            'pose_library_sha256':spec['recovery']['pose_library_sha256'],
            'family':family,
            'checkpoint_sha256':digest(args.checkpoint),
            'scope':'policy GUI; initial pose taken from this spec, no separate asset config'}
    if controls is not None:
        plan['keyboard']={'max_speed_mps':legacy_max_speed,'max_yaw_rad_s':legacy_max_yaw,
            'physical_gpu':args.physical_gpu,'max_wall_s':args.max_wall_seconds,
            'logical_cuda':'cuda:0','renderer_physical_gpu':args.physical_gpu,
            'yaw_certified':False,'keys':'W/S, Up/Down, A/D, Left/Right, Space, R, Esc'}
    if not args.run:
        print(json.dumps({**plan,"simulation":0,"files_written":0},indent=2))
        return
    from native_stand.command_v6.tools.preflight import check
    from native_stand.command_v6.ledger import Ledger
    import uuid
    ledger=None
    if not args.preview:
        preflight=check(args.spec,args.output,"play")
        if preflight["status"]!="PASS":
            raise RuntimeError(f"play preflight failed: {preflight['errors']}")
        ledger=Ledger(args.spec.with_name("budget.json"))
        attempt_id=uuid.uuid4().hex
        ledger.reserve(attempt_id,"play",args.output,approval=preflight)
    started=time.monotonic()
    env=app=None
    keyboard_api=keyboard_device=subscription=window=None
    result={**plan,"status":"STARTING","policy_steps":0,"task_resets":0}
    signal.signal(signal.SIGTERM,stop_on_term)
    try:
        os.environ.update(device_plan['environment'])
        from isaaclab.app import AppLauncher
        if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
            raise RuntimeError('Launch GUI from a desktop terminal')
        app_options={"headless":False,"livestream":0,
                     "visualizer":["kit"],"visualizer_explicit":True,**device_plan['app_options']}
        app=AppLauncher(app_options).app
        import torch
        from tensordict import TensorDict
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        sys.path.insert(0,spec["asset_module_root"])
        from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.domain.warmstart import expand_state
        from native_stand.command_v6.tools.model_factory import model as build_model
        result["asset_import_readback"]=verify_asset_import(
            spec, allow_colleague_config_drift=(args.preview and not args.strict_identities and controls is None))
        cfg=configure_env(CommandEnvCfg(),spec,envs=1,mode='preview' if args.preview else 'evaluation')
        cfg.sim.device='cuda:0'
        if recovery:
            if handoff_row is not None:
                from native_stand.recovery.handoff_runtime import HandoffEnv
                motion_spec=json.loads(Path(spec['motion_handoff']['motion_spec']).read_text())
                dummy=TensorDict({'policy':torch.zeros(1,25,device='cuda:0'),
                    'history':torch.zeros(1,125,device='cuda:0')},batch_size=[1])
                motion_actor=build_model(dummy,actor=True,spec=motion_spec).to('cuda:0')
                motion_actor.load_state_dict(torch.load(spec['motion_handoff']['motion_checkpoint'],
                    map_location='cuda:0',weights_only=False)['actor'],strict=True)
                motion_actor.eval();motion_actor.requires_grad_(False)
                env=HandoffEnv(cfg,recovery_config=spec['recovery'],
                    pose_library=json.loads(Path(spec['recovery']['pose_library']).read_text()),
                    stand_policy=motion_actor,stage=spec['curriculum']['stages'][0],
                    command_height=.36,reward_config=spec['reward'],schedule_s=spec['curriculum']['schedule_s'])
                env.configure_case(handoff_row)
                env.configure_protocol(spec['motion_handoff']['protocol'])
                if spec['motion_handoff'].get('initialization_randomization'):
                    env.configure_randomization(spec['motion_handoff']['initialization_randomization'])
            else:
                from native_stand.recovery.recipe import environment
                env=environment(cfg,spec)
            configure_recovery_preview(env,spec,family=family)
        else:
            cfg.episode_length_s=1000000.
            preview_env=CommandEnv
            if controls is not None:
                from native_stand.command_v6.runtime.interactive_env import InteractiveCommandEnv
                preview_env=InteractiveCommandEnv
            env=preview_env(cfg,stage=spec["curriculum"]["stages"][0],
                       command_height=spec["control"]["height_command_m"],
                       reward_config=spec["reward"],
                       schedule_s=spec["curriculum"]["schedule_s"])
        result["ground_readback"]=verify_ground(env,spec)
        result["control_readback"]=verify(env)
        env.set_evaluation_target(0.,0.)
        from native_stand.command_v6.runtime.execution_mode import apply as apply_mode
        apply_mode(env,'preview' if args.preview else 'evaluation',envs=1,
            family=plan.get('recovery_preview',{}).get('family'))
        wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
        observation,_=env.reset(seed=handoff_row['seed'] if handoff_row else spec["evaluation"]["seed"])
        observation=TensorDict(observation,batch_size=[1]).clone()
        actor=build_model(observation,actor=True,spec=spec).to(env.device)
        checkpoint=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
        weights=checkpoint["actor"]
        from native_stand.command_v6.tools.model_adapter import ModelAdapter
        if ModelAdapter(checkpoint).describe()['actor_input_shape'][-1]==132:
            if digest(args.checkpoint)!=spec["source_sha256"]:
                raise RuntimeError("source B200 checkpoint identity differs")
            weights=expand_state(weights,actor.state_dict())
        ModelAdapter({'actor':weights}).load(actor,'actor')
        if digest(args.checkpoint)==spec['source_sha256'] and spec.get('wheel_envelope_conversion'):
            from native_stand.command_v6.domain.warmstart import convert_wheel_envelope
            convert_wheel_envelope(actor,old_scale=spec['wheel_envelope_conversion']['source_scale_rad_s'],
                                  new_scale=spec['action']['wheel_scale_rad_s'])
        actor.eval()
        if controls is not None:
            import carb.input
            import omni.appwindow
            import omni.ui as ui
            keyboard_api=carb.input.acquire_input_interface()
            keyboard_device=omni.appwindow.get_default_app_window().get_keyboard()
            def on_key(event):
                if event.type in (carb.input.KeyboardEventType.KEY_PRESS,carb.input.KeyboardEventType.KEY_RELEASE):
                    controls.event(event.input.name,event.type==carb.input.KeyboardEventType.KEY_PRESS)
                elif event.type==carb.input.KeyboardEventType.KEY_REPEAT and event.input.name in (
                        'UP','DOWN','LEFT','RIGHT','UP_ARROW','DOWN_ARROW','LEFT_ARROW','RIGHT_ARROW'):
                    controls.event(event.input.name,True)
                return True
            subscription=keyboard_api.subscribe_to_keyboard_events(keyboard_device,on_key)
            window=ui.Window('Native Motion Keyboard',width=460,height=125)
            with window.frame:
                with ui.VStack():
                    ui.Label('W/S forward/back | arrows speed | Space stop | R reset | Esc exit')
                    ui.Label('Yaw disabled by default; preview is not capability certification')
                    motion_label=ui.Label('Command 0 | Actual 0 m/s')
        try:
            import omni.usd
            stage = omni.usd.get_context().get_stage()
            from native_stand.command_v6.tools.ground_visual import setup
            result.update(setup(
                stage, env.sim,
                style=args.ground_style,
                extent_m=args.ground_extent_m,
                grid_spacing_m=args.ground_grid_spacing_m,
            ))
        except Exception as e:
            print(f"[Visual Notice] Visual setup skipped: {e}")
        from native_stand.command_v6.tools.ground_visual import camera_view
        camera_view(env.sim)
        result["status"]="RUNNING"
        label=('Motion keyboard preview' if controls is not None else 'Recovery autonomous2s stable hold, repeated episodes' if recovery and
            spec['recovery']['fsm'].get('success_mode')=='autonomous_hold' else
            'Recovery R1 low pose -> frozen STAND, repeated episodes' if recovery else 'STAND zero command')
        if handoff_row is not None:
            label=f"Swing -> Recovery {handoff_row['recovery']} {handoff_row['switch_s']:.2f}s -> Motion B250; repeated episodes"
        print(f"GUI running: {label}; close window or Ctrl-C.",flush=True)
        with torch.inference_mode():
            while app.is_running() and (not args.max_policy_steps or result["policy_steps"]<args.max_policy_steps):
                if controls is not None:
                    if controls.stop or time.monotonic()-started>=args.max_wall_seconds:break
                    if controls.reset_requested:
                        controls.reset()
                        observation,_=wrapped.reset()
                        observation=observation.clone()
                    command=controls.advance(env.step_dt)
                    env.manual_command[:,:2]=env.manual_command.new_tensor(command)
                    from native_stand.command_v6.domain.keyboard_command import synchronize_observation
                    synchronize_observation(observation,env.history,command)
                if handoff_row is not None:
                    from native_stand.recovery.domain import Mode
                    initializing=env.fsm.mode==int(Mode.INITIALIZING)
                    motion_on=(~initializing)&(env.executed_prefix>=env.switch_steps)
                    recovery_on=(~initializing)&~motion_on
                    action=torch.zeros((1,6),device=env.device)
                    if recovery_on.any():action[recovery_on]=actor(observation[recovery_on],stochastic_output=False)
                    if motion_on.any():
                        mo=env.motion_obs
                        action[motion_on]=motion_actor(TensorDict({'policy':mo['policy'][motion_on],
                            'history':mo['history'][motion_on]},batch_size=[int(motion_on.sum())]),stochastic_output=False)
                else:
                    action=actor(observation,stochastic_output=False)
                observation,_,done,_=wrapped.step(action.to(env.device).clone())
                observation=observation.clone()
                result["policy_steps"]+=1
                if bool(env.terminal_causes["nonfinite"].any() or env.terminal_causes["closure"].any()):
                    raise RuntimeError("physical nonfinite or closed-chain fault")
                if bool(done[0]):
                    result["task_resets"]+=1
                    if controls is not None:controls.reset()
                if controls is not None and result['policy_steps']%10==0:
                    motion_label.text=f'Speed {controls.speed:.2f} | Cmd {command[0]:+.2f} | Actual {float(env.vx[0]):+.2f} m/s'
                if result["policy_steps"]%200==0:
                    root=env.robot.data.root_pos_w.torch[0].cpu().tolist()
                    camera_view(env.sim,root[:2])
                    print(json.dumps({"policy_time_s":result["policy_steps"]*.01,
                                      "root_pos_w":root,"task_resets":result["task_resets"]}),flush=True)
        if not app.is_running():
            result["status"]="STOPPED_APP"
            result["exit_reason"]="SimulationApp.is_running() became false"
            print("GUI stopped because SimulationApp.is_running() became false; "
                  "this is not an episode termination.",flush=True)
        elif args.max_policy_steps and result["policy_steps"] >= args.max_policy_steps:
            result["status"]="COMPLETED"
            result["exit_reason"]="max_policy_steps reached"
        else:
            result["status"]="COMPLETED"
            result["exit_reason"]="playback loop ended"
    except KeyboardInterrupt:
        result["status"]="STOPPED_BY_USER"
    except BaseException as exc:
        result.update(status="FAILED",exception=repr(exc),traceback=traceback.format_exc())
        # Kit fast shutdown can prevent the interpreter's deferred traceback.
        print(result['traceback'],file=sys.stderr,flush=True)
        raise
    finally:
        from native_stand.command_v6.tools.runtime_cleanup import run as cleanup
        original_error=sys.exception()
        result["wall_s"]=time.monotonic()-started
        def persist():
            if ledger is None:return
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open("x") as stream:json.dump(result,stream,indent=2)
            ledger.finalize(attempt_id,args.output,result["status"] if result["status"] in
                            ("COMPLETED","FAILED") else "STOPPED_BOUNDED",wall_s=result["wall_s"])
        steps=[]
        if subscription is not None:steps.append(('keyboard_unsubscribe',lambda:keyboard_api.unsubscribe_to_keyboard_events(keyboard_device,subscription)))
        if window is not None:steps.append(('window_close',lambda:setattr(window,'visible',False)))
        # Persist the primary failure before Kit.close can terminate Python.
        steps.append(('persist_result',persist))
        if env is not None:steps.append(('environment_close',env.close))
        if app is not None:steps.append(('app_close',app.close))
        cleanup(steps,primary_error=original_error,on_errors=lambda errors:result.update(cleanup_errors=errors))


if __name__=="__main__":
    main()
