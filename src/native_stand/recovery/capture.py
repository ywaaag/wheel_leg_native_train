"""Manual Recovery pose GUI. No policy/PPO. Plan mode has no side effects."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import signal
import time
import uuid

from native_stand.recovery.capture_controls import Controls,LEG_NAMES


def write_new(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,default=Path('configs/tools/recovery_capture.json'))
    parser.add_argument('--output-dir',type=Path,required=True,help='New manual collection directory; never training ledger')
    parser.add_argument('--pose-id',default='train_R1_0')
    parser.add_argument('--initial-pose',type=Path,default=None,
        help='Previously captured pose JSON to reload instead of the pose library entry')
    parser.add_argument('--step-rad',type=float,default=.02)
    parser.add_argument('--max-wall-seconds',type=float,default=1800.,help='Manual session bound, including initialization; PPO0')
    parser.add_argument('--settle-before-save-s',type=float,default=3.0,
        help='Passive settling time before each save; then explicitly zero velocities')
    parser.add_argument('--run',action='store_true',help='Open one-env Isaac GUI; without this flag CPU plan only')
    args=parser.parse_args()
    config=json.loads(args.spec.read_text());base_path=Path(config['base_spec'])
    if hashlib.sha256(base_path.read_bytes()).hexdigest()!=config['base_spec_sha256']:
        raise ValueError('Manual capture base spec identity changed')
    spec=json.loads(base_path.read_text())
    spec['colleague_config_sha256']=config['colleague_config_sha256']
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    for key in ('asset','asset_module','colleague_config'):
        path=Path(spec[key+'_path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=spec[key+'_sha256']:errors.append(f'{key} identity differs')
    if args.output_dir.exists():errors.append('Output directory already exists')
    if errors:raise ValueError(errors)
    if not 0.<args.max_wall_seconds<=7200.:raise ValueError('Wall limit must be (0,7200] seconds')
    library_path=Path(spec['recovery']['pose_library'])
    if hashlib.sha256(library_path.read_bytes()).hexdigest()!=spec['recovery']['pose_library_sha256']:
        raise ValueError('Pose library identity changed')
    library=json.loads(library_path.read_text())
    if args.initial_pose is not None:
        pose=json.loads(args.initial_pose.read_text())
        if pose.get('asset_sha256')!=spec['asset_sha256']:
            raise ValueError('Initial pose asset identity differs')
        if not isinstance(pose.get('joint_pos'),dict):
            raise ValueError('Initial pose has no joint_pos')
        pose['pose_id']=pose.get('pose_id',args.initial_pose.stem)
    else:
        matches=[p for p in library['poses'] if p['pose_id']==args.pose_id and p['offline_valid']]
        if len(matches)!=1:raise ValueError('Pose ID missing/invalid/nonunique')
        pose=matches[0]
    limits=library['joint_limits_rad']
    missing=[name for name in LEG_NAMES if name not in pose['joint_pos']]
    if missing:raise ValueError(f'Initial pose missing active joints: {missing}')
    controls=Controls([limits[n] for n in LEG_NAMES],[pose['joint_pos'][n] for n in LEG_NAMES],args.step_rad)
    plan={'task':'manual_recovery_pose_collection','output_dir':str(args.output_dir.resolve()),
        'asset_sha256':spec['asset_sha256'],'spec_sha256':hashlib.sha256(args.spec.read_bytes()).hexdigest(),
        'pose_id':pose.get('pose_id',args.pose_id),'initial_pose_path':str(args.initial_pose.resolve()) if args.initial_pose else None,
        'max_wall_seconds':args.max_wall_seconds,
        'settle_before_save_s':args.settle_before_save_s,'ppo_updates':0,
        'policy_loaded':False,'training_ledger_modified':False,'mode':'PASSIVE',
        'leg_names':LEG_NAMES,'joint_limits_rad':[limits[n] for n in LEG_NAMES],
        'physics_dt_s':spec['control']['physics_dt_s'],'pd_dt_s':spec['control']['pd_dt_s'],
        'ground':spec['ground'],'manual_candidates_are_not_runtime_certified':True}
    if not args.run:
        print(json.dumps({**plan,'simulation':0,'files_written':0},indent=2));return 0
    # This is an explicitly requested manual collection session, not Recovery training authorization.
    started=time.monotonic();env=app=None;window=None;subscription=None;input_api=None;keyboard=None
    status='FAILED';failure=None;steps=0;saved=0;stop=False;settle_steps_remaining=0
    def on_term(*unused):
        nonlocal stop
        stop=True
    args.output_dir.mkdir(parents=True,exist_ok=False)
    snapshot=args.output_dir/'source_snapshot';snapshot.mkdir()
    sources=(args.spec,base_path,Path(spec['colleague_config_path']),library_path,Path(__file__),Path(__file__).with_name('capture_controls.py'),Path(__file__).with_name('capture_runtime.py'))
    if args.initial_pose is not None:sources=sources+(args.initial_pose,)
    for source in sources:
        shutil.copy2(source,snapshot/source.name)
    write_new(snapshot/'resolved_spec.json',spec)
    write_new(args.output_dir/'manifest.json',{**plan,'started_local':datetime.now().astimezone().isoformat(),
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()}})
    def capture(reason):
        nonlocal saved
        if env is None:return
        import torch
        d=env.robot.data
        # One contiguous state transfer; saving is user-triggered, never every physics step.
        packed=torch.cat((d.root_state_w.torch[0],d.joint_pos.torch[0],d.joint_vel.torch[0],
            env.effort_pre[0],env.effort[0],d.applied_torque.torch[0,env.ids],
            env.closure_each[0],env.sensor.data.net_forces_w.torch[0].flatten(),
            d.body_pos_w.torch[0].flatten(),d.body_quat_w.torch[0].flatten())).detach().cpu().tolist()
        offset=0
        def take(n):
            nonlocal offset
            values=packed[offset:offset+n];offset+=n;return values
        nj=len(env.robot.joint_names);nb=len(env.robot.body_names);ns=len(env.sensor.body_names)
        root=take(13);q=take(nj);dq=take(nj)
        request=take(6);clipped=take(6);applied=take(6);closure=take(4);forces=take(ns*3)
        positions=take(nb*3);quats=take(nb*4)
        finite=all(__import__('math').isfinite(v) for v in packed)
        def clean(value):
            if isinstance(value,float) and not __import__('math').isfinite(value):return None
            if isinstance(value,list):return [clean(v) for v in value]
            if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
            return value
        gaps=env.gaps.detach().cpu().tolist() if hasattr(env,'gaps') else None
        chassis=[g for g,s in zip(gaps or [],env.shapes) if s['body']=='robot']
        stable=(finite and env.executed_mode=='PASSIVE' and max(abs(v) for v in dq)<.3
            and max(abs(v) for v in root[7:10])<.05 and max(abs(v) for v in root[10:13])<.1)
        record={'record_id':uuid.uuid4().hex,'reason':reason,'timestamp':datetime.now().astimezone().isoformat(),
            'physics_steps':steps*env.cfg.decimation,'sim_time_s':steps*env.step_dt,
            'asset_sha256':spec['asset_sha256'],'spec_sha256':plan['spec_sha256'],
            'mode':env.executed_mode,'requested_mode':controls.mode,'episode_id':int(env.reset_count[0]),
            'paused':controls.paused,'active_joint_order':[env.robot.joint_names[i] for i in env.ids],
            'target_leg_names':LEG_NAMES,'target_leg_rad':env.leg_target[0].cpu().tolist(),
            'requested_leg_rad':controls.targets.copy(),'wheel_target_rad_s':[0.,0.],
            'joint_names':env.robot.joint_names,'joint_pos':dict(zip(env.robot.joint_names,q)),
            'joint_vel':dict(zip(env.robot.joint_names,dq)),
            'root_position_w':root[:3],'root_quaternion_xyzw':root[3:7],
            'root_linear_velocity_w':root[7:10],'root_angular_velocity_w':root[10:13],
            'root_height_m':root[2],'chassis_ideal_clearance_m':min(chassis) if chassis else None,
            'PD_request_nm':request,'physical_clipped_nm':clipped,'actual_applied_nm':applied,
            'closure_each_m':closure,'sensor_force_w':dict(zip(env.sensor.body_names,[forces[i:i+3] for i in range(0,len(forces),3)])),
            'body_pose_w':{name:{'position':positions[3*i:3*i+3],'quaternion_xyzw':quats[4*i:4*i+4]} for i,name in enumerate(env.robot.body_names)},
            'ideal_geometry_gaps_m':dict(zip([s['path'] for s in env.shapes],gaps)) if gaps else None,
            'runtime_fault':env.fault,'finite':finite,'instantaneous_settle_candidate':stable,
            'accepted_training_initial_state':None,'self_interbody_penetration':'UNKNOWN',
            'COM_height':'UNKNOWN','screenshot':'NOT_CAPTURED',
            'geometry_semantics':'Ideal primitive clearance; not solver contact distance. Instantaneous low velocity does not establish sustained settling.'}
        write_new(args.output_dir/f'pose_{saved:04d}_{record["record_id"][:8]}.json',clean(record));saved+=1
        print(f'Saved {saved}: {controls.mode}, root={root[2]:.4f}m; manual candidate only',flush=True)
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher({'headless':False,'livestream':0,'visualizer':['kit'],'visualizer_explicit':True}).app
        signal.signal(signal.SIGTERM,on_term);signal.signal(signal.SIGINT,on_term)
        import sys
        sys.path.insert(0,spec['asset_module_root'])
        import torch
        import omni.ui as ui
        import omni.appwindow
        import carb.input
        from native_stand.env import NativeStandCfg
        from native_stand.command_v6.runtime.configure import apply,verify_asset_import
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.recovery.capture_runtime import CaptureEnv
        identity=verify_asset_import(spec)
        cfg=apply(NativeStandCfg(),spec,envs=1);cfg.episode_length_s=1e9;cfg.episode_curriculum=None
        env=CaptureEnv(cfg,pose=pose,controls=controls,geometry=library['collision_geometry'],limits=limits)
        env.reset(seed=spec['seed'])
        write_new(args.output_dir/'control_readback.json',{'ownership':verify(env),'ground':verify_ground(env,spec),'dependency':identity})
        from native_stand.command_v6.tools.ground_visual import apply as apply_ground_visual, add_lighting
        apply_ground_visual(env.sim.stage,style='grid',extent_m=128.0,grid_spacing_m=1.0)
        add_lighting(env.sim.stage)
        env.sim.set_camera_view(eye=(1.2,1.2,.65),target=(0.,0.,.2))
        window=ui.Window('Recovery pose capture (rad)',width=480,height=410)
        models=[]
        with window.frame:
            with ui.VStack(spacing=6):
                ui.Label('1-4 select joint; Up/Down +/- target; Space motor mode')
                ui.Label('S save | P pause | R reset | Esc exit; click viewport for keys')
                for i,name in enumerate(LEG_NAMES):
                    ui.Label(name)
                    slider=ui.FloatSlider(min=limits[name][0],max=limits[name][1],step=.01)
                    slider.model.set_value(controls.targets[i]);models.append(slider.model)
                    slider.model.add_value_changed_fn(lambda m,i=i:controls.set(i,m.as_float))
                mode_label=ui.Label('PASSIVE: all six active efforts zero')
                with ui.HStack():
                    ui.Button('Adjust PD',clicked_fn=lambda:setattr(controls,'mode','ADJUST'))
                    ui.Button('Passive zero effort',clicked_fn=lambda:setattr(controls,'mode','PASSIVE'))
                with ui.HStack():
                    ui.Button('Save pose',clicked_fn=lambda:setattr(controls,'save_requested',True))
                    ui.Button('Reset low pose',clicked_fn=lambda:setattr(controls,'reset_requested',True))
                    ui.Button('Pause / resume',clicked_fn=lambda:setattr(controls,'paused',not controls.paused))
                status_label=ui.Label('Manual candidates require validation; no policy/PPO')
        app_window=omni.appwindow.get_default_app_window()
        if app_window is None:raise RuntimeError('No GUI keyboard window')
        keyboard=app_window.get_keyboard();input_api=carb.input.acquire_input_interface()
        def on_key(event,*unused):
            if event.type==carb.input.KeyboardEventType.KEY_PRESS:
                controls.key(event.input.name)
                for i,model in enumerate(models):model.set_value(controls.targets[i])
            return True
        subscription=input_api.subscribe_to_keyboard_events(keyboard,on_key)
        print(f'GUI capture ready. Save folder: {args.output_dir}; PPO0; default PASSIVE',flush=True)
        timeline_paused=False
        while app.is_running() and not stop and not controls.stop and time.monotonic()-started<args.max_wall_seconds:
            if controls.reset_requested:
                controls.mode='PASSIVE';env.reset();steps=0;controls.reset_requested=False
                for i,name in enumerate(LEG_NAMES):
                    controls.set(i,pose['joint_pos'][name]);models[i].set_value(controls.targets[i])
            if controls.paused!=timeline_paused:
                if controls.paused:env.sim.pause()
                else:env.sim.play()
                timeline_paused=controls.paused
            if settle_steps_remaining>0:
                controls.mode='PASSIVE';controls.paused=False
                if timeline_paused:
                    env.sim.play();timeline_paused=False
                env.step(torch.zeros((1,6),device=env.device));steps+=1
                settle_steps_remaining-=1
                if settle_steps_remaining==0:
                    ids=torch.tensor([0],device=env.device)
                    env.robot.write_root_velocity_to_sim_index(
                        root_velocity=torch.zeros((1,6),device=env.device),env_ids=ids)
                    env.robot.write_joint_velocity_to_sim_index(
                        velocity=torch.zeros_like(env.robot.data.joint_vel.torch),env_ids=ids)
                    capture('manual_save_after_passive_settle')
            elif controls.paused:app.update()
            else:
                env.step(torch.zeros((1,6),device=env.device));steps+=1
            if controls.save_requested and settle_steps_remaining==0:
                if args.settle_before_save_s < 0:
                    raise ValueError('--settle-before-save-s must be nonnegative')
                settle_steps_remaining=max(0,int(round(args.settle_before_save_s/env.step_dt)))
                controls.save_requested=False
                if settle_steps_remaining==0:capture('manual_save')
            mode_label.text=f'{controls.mode} | selected: {LEG_NAMES[controls.selected]} | paused={controls.paused}'
            if steps%50==0:status_label.text=f't={steps*.01:.2f}s | root={float(env.root_height[0]):.3f}m | saved={saved}'
        status='STOPPED_BY_USER' if stop or controls.stop or not app.is_running() else 'WALL_LIMIT'
    except BaseException as exc:
        failure=repr(exc)
        if env is not None:
            try:capture('runtime_fault' if env.fault else 'exception')
            except Exception as save_error:failure+=f'; capture failed: {save_error!r}'
        print(f'Capture stopped: {failure}',flush=True)
    finally:
        if subscription is not None:input_api.unsubscribe_to_keyboard_events(keyboard,subscription)
        if window is not None:window.visible=False
        close_errors=[]
        if env is not None:
            try:env.close()
            except Exception as exc:close_errors.append(repr(exc))
        if app is not None:
            try:app.close()
            except Exception as exc:close_errors.append(repr(exc))
        write_new(args.output_dir/'terminal_report.json',{'status':status,'failure':failure,'close_errors':close_errors,
            'wall_s':time.monotonic()-started,'pose_records':saved,'ppo_updates':0,'training_ledger_modified':False})
    return 1 if failure else 0


if __name__=='__main__':raise SystemExit(main())
