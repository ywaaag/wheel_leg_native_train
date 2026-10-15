"""Manual Motion preview: Isaac GUI keyboard plus optional loopback browser panel.

One command source (``MotionStudentEnv.set_motion_manual_command``) feeds the Actor
observation, the reward snapshot and the telemetry feed, so the GUI keyboard and the
browser panel can never drift apart. Physics, PD, action scale, height command and the
scoring time-phases are untouched; preview writes no project output or ledger entry and
is never a capability certificate.
"""
import json
import os
import sys
import time
import traceback

from native_stand.command_v6.domain.keyboard_command import KeyboardCommand
from native_stand.command_v6.tools.runtime_cleanup import run as cleanup
from .motion_training import PREVIEW_VERSION

MOTION_ROLES = ('MotionStudent', 'MotionZeroStudent')
PREVIEW_EPISODE_LENGTH_S = 1e9
DEFAULT_MAX_SPEED_MPS = 2.0
DEFAULT_MAX_YAW_RAD_S = 1.0
TRAINED_RANGE_MPS = (0.0, 0.5, 1.0)
ACCELERATION_MPS2 = 0.5
YAW_ACCELERATION_RAD_S2 = 1.0
WHEEL_CHANNELS = (2, 5)
KEYS = 'W/S forward-back, Up/Down speed, A/D yaw, Space zero, R reset, Esc exit'


def caps(args):
    """Resolve preview caps; the legacy keyboard defaults are never read here."""
    max_speed = DEFAULT_MAX_SPEED_MPS if getattr(args, 'max_speed', None) is None else float(args.max_speed)
    max_yaw = DEFAULT_MAX_YAW_RAD_S if getattr(args, 'max_yaw_speed', None) is None else float(args.max_yaw_speed)
    if not 0 < max_speed <= 4 or not 0 <= max_yaw <= 4:
        raise ValueError('preview caps must be max_speed in (0,4] and max_yaw_speed in [0,4]')
    return max_speed, max_yaw


def plan(args, spec, data, *, panel, panel_port, role=None):
    """CPU-only identity and preview plan; no Isaac import, no file writes."""
    role = role or data.get('role')
    if role not in MOTION_ROLES:
        raise ValueError('checkpoint role is not a Motion student role: %r' % (role,))
    max_speed, max_yaw = caps(args)
    return {
        'version': PREVIEW_VERSION,
        'interface_version': spec.get('interface_version'),
        'role': role,
        'update': data.get('update'),
        'checkpoint': str(args.checkpoint),
        'checkpoint_sha256': data.get('checkpoint_sha256'),
        'spec': str(args.spec),
        'spec_sha256': data.get('spec_sha256'),
        'family': spec['recovery']['active_family'],
        'height_command_m': spec['student_training']['target_height_m'],
        'episode_length_s': PREVIEW_EPISODE_LENGTH_S,
        'stages_unlocked_commands': spec['curriculum']['stages'][0]['commands'],
        'keyboard': {'max_speed_mps': max_speed, 'max_yaw_rad_s': max_yaw,
                     'acceleration_mps2': ACCELERATION_MPS2, 'yaw_acceleration_rad_s2': YAW_ACCELERATION_RAD_S2,
                     'keys': KEYS, 'trained_range_mps': list(TRAINED_RANGE_MPS), 'yaw_certified': False},
        'panel': {'enabled': bool(panel), 'url': 'http://127.0.0.1:%d/' % panel_port if panel else None,
                  'host': '127.0.0.1', 'port': panel_port if panel else None,
                  'dependency': 'python stdlib only (http.server); no third-party package',
                  'cap_rule': 'browser may only lower the command caps declared on the command line',
                  'csv': 'browser-side download of the session buffer; no project file writes'},
        'scope': 'manual preview on the shared CommandEnv; physics, PD, action scale, height command and scoring'
                 ' unchanged; not capability certification',
        'simulation': 0, 'online_PPO': 0, 'files_written': 0,
    }


def _telemetry(env, controls, count, resets, source, panel_plan):
    data = env.robot.data
    joints = data.joint_vel.torch[0, env.ids]
    torque = data.applied_torque.torch[0, env.ids]
    row = {
        't': round(time.time(), 3), 'steps': count, 'resets': resets, 'source': source,
        'cmd_vx': float(env.command[0, 0]), 'cmd_yaw': float(env.command[0, 1]),
        'speed_gear': float(controls.speed), 'yaw_gear': float(controls.yaw_speed),
        'vx': float(env.vx[0]), 'vy': float(env.vy[0]), 'yaw': float(env.yaw[0]),
        'height': float(env.root_height[0]), 'vz': float(data.root_lin_vel_w.torch[0, 2]),
        'wheel_qdot_l': float(joints[WHEEL_CHANNELS[0]]), 'wheel_qdot_r': float(joints[WHEEL_CHANNELS[1]]),
        'wheel_tau_l': float(torque[WHEEL_CHANNELS[0]]), 'wheel_tau_r': float(torque[WHEEL_CHANNELS[1]]),
    }
    if panel_plan is not None:
        row['panel_requests'] = panel_plan.requests
    return row


def _merge_command(controls, row, dt, keyboard_active, limits):
    """Keyboard gear target while keys are held, otherwise the browser/idle target."""
    if keyboard_active:
        command, source = controls.advance(dt), 'isaac-keyboard'
    else:
        target = (0., 0.) if row is None else (float(row['vx']), float(row['yaw']))
        for index, (goal, rate) in enumerate(zip(target, (controls.acceleration, controls.yaw_acceleration))):
            delta = goal - controls.current[index]
            controls.current[index] += max(-rate * dt, min(rate * dt, delta))
        command = list(controls.current)
        source = 'idle' if row is None or (not row['vx'] and not row['yaw']) else 'browser-panel'
    max_speed, max_yaw = limits
    return [max(-max_speed, min(max_speed, command[0])), max(-max_yaw, min(max_yaw, command[1]))], source


def run(args, spec, role, actor, data, *, panel, panel_port):
    """GUI execution; Isaac imports happen only here, after the CPU plan was printed."""
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.physical_gpu)
    sys.path.insert(0, spec['asset_module_root'])
    from isaaclab.app import AppLauncher
    from native_stand.command_v6.tools.play import keyboard_app_options
    app_options = {**keyboard_app_options(args.physical_gpu), 'headless': False,
                   'visualizer': ['kit'], 'visualizer_explicit': True}
    app = AppLauncher(app_options).app
    family = spec['recovery']['active_family']
    declared_speed, declared_yaw = caps(args)
    controls = KeyboardCommand(min(float(args.speed), declared_speed), min(float(args.yaw_speed), declared_yaw),
                               max_speed=declared_speed, max_yaw_speed=declared_yaw)
    result = {**plan(args, spec, data, panel=panel, panel_port=panel_port, role=role),
              'status': 'STARTING', 'policy_steps': 0, 'task_resets': 0, 'simulation': 1,
              'device_mapping': {'CUDA_VISIBLE_DEVICES': str(args.physical_gpu), 'logical': 'cuda:0',
                                 'renderer_physical_gpu': args.physical_gpu}}
    env = None
    server = None
    panel_plan = None
    subscription = keyboard_api = keyboard_device = window = state_label = None
    started = time.monotonic()
    count = resets = 0
    try:
        from .motion_panel import Plan, start as start_panel, stop as stop_panel
        from .evaluator import environment
        env = environment(spec, role, envs=1, initial_family=family, autonomous_preview=True,
                          preview_episode_length_s=PREVIEW_EPISODE_LENGTH_S)
        env.select_initial_family(family, 'holdout')
        actor = actor.to(env.device).eval()
        obs, _ = env.reset()
        if panel:
            panel_plan = Plan(declared_speed, declared_yaw)
            server, _thread = start_panel(panel_plan, panel_port)
            print('control panel: http://127.0.0.1:%d/' % panel_port, flush=True)
        import carb.input
        import omni.appwindow
        import omni.ui as ui

        def on_key(event):
            if event.type in (carb.input.KeyboardEventType.KEY_PRESS, carb.input.KeyboardEventType.KEY_RELEASE):
                controls.event(event.input.name, event.type == carb.input.KeyboardEventType.KEY_PRESS)
            elif event.type == carb.input.KeyboardEventType.KEY_REPEAT and event.input.name in (
                    'UP', 'DOWN', 'LEFT', 'RIGHT', 'UP_ARROW', 'DOWN_ARROW', 'LEFT_ARROW', 'RIGHT_ARROW'):
                controls.event(event.input.name, True)
            return True

        keyboard_api = carb.input.acquire_input_interface()
        keyboard_device = omni.appwindow.get_default_app_window().get_keyboard()
        subscription = keyboard_api.subscribe_to_keyboard_events(keyboard_device, on_key)
        window = ui.Window('Motion31 manual preview', width=600, height=150)
        with window.frame:
            with ui.VStack():
                ui.Label(KEYS)
                ui.Label('Panel http://127.0.0.1:%d/ | browser may only lower caps' % panel_port if panel
                         else 'Panel disabled (--panel or NATIVE_MOTION_PANEL=1 enables it)')
                ui.Label('Trained range 0/+-0.5/+-1 m/s straight, yaw=0; preview is not certification')
                state_label = ui.Label('cmd vx +0.00 yaw +0.00 | actual vx +0.00 yaw +0.00 | height 0.340')
        try:
            import omni.usd
            from native_stand.command_v6.tools.ground_visual import setup, camera_view
            result.update(setup(omni.usd.get_context().get_stage(), env.sim, style=args.ground_style,
                                extent_m=args.ground_extent_m, grid_spacing_m=args.ground_grid_spacing_m))
        except Exception as error:
            print('[Visual Notice] Visual setup skipped: %s' % error, flush=True)
        from native_stand.command_v6.tools.ground_visual import camera_view
        camera_view(env.sim)
        result['status'] = 'RUNNING'
        print('GUI running: Motion31 manual preview (family %s, role %s); close window or Ctrl-C.' % (family, role),
              flush=True)
        import torch
        with torch.inference_mode():
            while (app.is_running() and (not args.max_policy_steps or count < args.max_policy_steps)
                   and time.monotonic() - started < args.max_wall_seconds and not controls.stop):
                dt = float(env.step_dt)
                row = panel_plan.take() if panel_plan is not None else None
                if row is not None and (row['stop'] or row['center']):
                    controls.pressed.clear()
                    controls.current = [0., 0.]
                limits = (declared_speed, declared_yaw) if row is None else (row['max_speed'], row['max_yaw_speed'])
                command, source = _merge_command(controls, row, dt, bool(controls.pressed), limits)
                env.set_motion_manual_command(*command)
                obs, *_ = env.step(actor(obs))
                count += 1
                if (row is not None and row['reset']) or controls.reset_requested:
                    controls.reset()
                    obs, _ = env.reset()
                    resets += 1
                if bool(env.terminal_causes['nonfinite'].any() or env.terminal_causes['closure'].any()):
                    raise RuntimeError('physical nonfinite or closed-chain fault')
                if panel_plan is not None and count % 2 == 0:
                    panel_plan.publish(_telemetry(env, controls, count, resets, source, panel_plan))
                if count % 10 == 0:
                    state_label.text = ('cmd vx %+.2f yaw %+.2f | actual vx %+.2f yaw %+.2f | height %.3f'
                                        % (float(env.command[0, 0]), float(env.command[0, 1]), float(env.vx[0]),
                                           float(env.yaw[0]), float(env.root_height[0])))
                if count % 200 == 0:
                    root = env.robot.data.root_pos_w.torch[0].cpu().tolist()
                    camera_view(env.sim, root[:2])
                    print(json.dumps({'policy_time_s': count * dt, 'root_pos_w': root, 'task_resets': resets}),
                          flush=True)
        if not app.is_running():
            result['status'] = 'STOPPED_APP'
            result['exit_reason'] = 'SimulationApp.is_running() became false'
        elif controls.stop:
            result['status'] = 'STOPPED_BY_USER'
            result['exit_reason'] = 'Esc or window stop requested'
        elif args.max_policy_steps and count >= args.max_policy_steps:
            result['status'] = 'COMPLETED'
            result['exit_reason'] = 'max_policy_steps reached'
        else:
            result['status'] = 'COMPLETED'
            result['exit_reason'] = 'preview loop ended'
    except KeyboardInterrupt:
        result['status'] = 'STOPPED_BY_USER'
    except BaseException as exc:
        result.update(status='FAILED', exception=repr(exc), traceback=traceback.format_exc())
        print(result['traceback'], file=sys.stderr, flush=True)
        raise
    finally:
        original_error = sys.exception()
        result['policy_steps'] = count
        result['task_resets'] = resets
        result['wall_s'] = time.monotonic() - started
        steps = []
        if subscription is not None:
            steps.append(('keyboard_unsubscribe',
                          lambda: keyboard_api.unsubscribe_to_keyboard_events(keyboard_device, subscription)))
        if window is not None:
            steps.append(('window_close', lambda: setattr(window, 'visible', False)))
        if server is not None:
            steps.append(('panel_stop', lambda: stop_panel(server)))
        if env is not None:
            steps.append(('environment_close', env.close))
        if app is not None:
            steps.append(('app_close', app.close))
        cleanup(steps, primary_error=original_error,
                on_errors=lambda errors: result.update(cleanup_errors=errors))
    print(json.dumps({k: v for k, v in result.items() if k != 'traceback'}, indent=2), flush=True)
    return result
