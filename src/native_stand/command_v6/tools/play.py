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


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stop_on_term(_signal,_frame):
    raise KeyboardInterrupt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,default=ROOT.parents[2]/"configs/experiments/stand_plane.json")
    parser.add_argument("--checkpoint",type=Path,required=True)
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
    args=parser.parse_args()
    if args.preview and args.output is not None:
        parser.error("--preview does not accept --output")
    if not args.preview and args.output is None:
        parser.error("recorded playback requires --output; use --preview for manual viewing")
    if (args.output is not None and args.output.exists()) or args.max_policy_steps<0 or not args.checkpoint.is_file():
        raise ValueError("output exists, step limit invalid or checkpoint missing")
    spec=json.loads(args.spec.read_text())
    recovery=spec.get('task')=='recovery'
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
                if (key == "colleague_config_path" and not args.strict_identities):
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
          "preview":args.preview,
          "command":[0.,0.,spec["control"]["height_command_m"]],
          "max_policy_steps":args.max_policy_steps,"PPO_updates":0,
          "identity_warnings":identity_warnings}
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
        ledger.reserve(attempt_id,"play",args.output)
    started=time.monotonic()
    env=app=None
    result={**plan,"status":"STARTING","policy_steps":0,"task_resets":0}
    signal.signal(signal.SIGTERM,stop_on_term)
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher({"headless":False,"livestream":0,
                         "visualizer":["kit"],"visualizer_explicit":True}).app
        import torch
        from tensordict import TensorDict
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        sys.path.insert(0,spec["asset_module_root"])
        from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.domain.warmstart import expand_state
        from native_stand.command_v6.learning import model as build_model
        result["asset_import_readback"]=verify_asset_import(
            spec, allow_colleague_config_drift=(args.preview and not args.strict_identities))
        cfg=configure_env(CommandEnvCfg(),spec,envs=1)
        if recovery:
            from native_stand.recovery.recipe import environment
            env=environment(cfg,spec)
            preview_family=spec.get('recovery',{}).get('preview_family',
                spec.get('recovery',{}).get('active_family','R0'))
            env.select_initial_family(preview_family,'holdout')
        else:
            cfg.episode_length_s=1000000.
            env=CommandEnv(cfg,stage=spec["curriculum"]["stages"][0],
                       command_height=spec["control"]["height_command_m"],
                       reward_config=spec["reward"],
                       schedule_s=spec["curriculum"]["schedule_s"])
        result["ground_readback"]=verify_ground(env,spec)
        result["control_readback"]=verify(env)
        env.set_evaluation_target(0.,0.)
        env.capture_terminal=True
        wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
        observation,_=env.reset(seed=spec["evaluation"]["seed"])
        observation=TensorDict(observation,batch_size=[1]).clone()
        actor=build_model(observation,actor=True,spec=spec).to(env.device)
        checkpoint=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
        weights=checkpoint["actor"]
        if weights["mlp.0.weight"].shape[-1]==132:
            if digest(args.checkpoint)!=spec["source_sha256"]:
                raise RuntimeError("source B200 checkpoint identity differs")
            weights=expand_state(weights,actor.state_dict())
        actor.load_state_dict(weights,strict=True)
        if digest(args.checkpoint)==spec['source_sha256'] and spec.get('wheel_envelope_conversion'):
            from native_stand.command_v6.domain.warmstart import convert_wheel_envelope
            convert_wheel_envelope(actor,old_scale=spec['wheel_envelope_conversion']['source_scale_rad_s'],
                                  new_scale=spec['action']['wheel_scale_rad_s'])
        actor.eval()
        try:
            import omni.usd
            stage = omni.usd.get_context().get_stage()
            from native_stand.command_v6.tools.ground_visual import apply, add_lighting
            result["ground_visual"] = apply(
                stage,
                style=args.ground_style,
                extent_m=args.ground_extent_m,
                grid_spacing_m=args.ground_grid_spacing_m,
            )
            result["lighting"] = add_lighting(stage)
        except Exception as e:
            print(f"[Visual Notice] Visual setup skipped: {e}")
        env.sim.set_camera_view(eye=(1.3,1.3,.85),target=(0.,0.,.35))
        result["status"]="RUNNING"
        label=('Recovery autonomous2s stable hold, repeated episodes' if recovery and
            spec['recovery']['fsm'].get('success_mode')=='autonomous_hold' else
            'Recovery R1 low pose -> frozen STAND, repeated episodes' if recovery else 'STAND zero command')
        print(f"GUI running: {label}; close window or Ctrl-C.",flush=True)
        with torch.inference_mode():
            while app.is_running() and (not args.max_policy_steps or result["policy_steps"]<args.max_policy_steps):
                action=actor(observation,stochastic_output=False)
                observation,_,done,_=wrapped.step(action.to(env.device).clone())
                observation=observation.clone()
                result["policy_steps"]+=1
                if bool(env.terminal_causes["nonfinite"].any() or env.terminal_causes["closure"].any()):
                    raise RuntimeError("physical nonfinite or closed-chain fault")
                if bool(done[0]):
                    result["task_resets"]+=1
                if result["policy_steps"]%200==0:
                    root=env.robot.data.root_pos_w.torch[0].cpu().tolist()
                    env.sim.set_camera_view(eye=(root[0]+1.3,root[1]+1.3,.85),
                                            target=(root[0],root[1],.35))
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
        raise
    finally:
        result["wall_s"]=time.monotonic()-started
        if ledger is not None:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open("x") as stream:
                json.dump(result,stream,indent=2)
            ledger.finalize(attempt_id,args.output,result["status"] if result["status"] in
                            ("COMPLETED","FAILED") else "STOPPED_BOUNDED",
                            wall_s=result["wall_s"])
        if env is not None:
            env.close()
        if app is not None:
            app.close()


if __name__=="__main__":
    main()
