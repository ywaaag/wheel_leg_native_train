"""Explicit Motion31 frozen-rollout diagnostic; never an optimizer update or gate."""
import copy
import json
from pathlib import Path

VERSION = 'motion31_frozen_advantage_probe_v1'


def declaration(parent, parent_sha):
    return {'version': VERSION, 'parent_spec': str(Path(parent).resolve()),
            'parent_spec_sha256': parent_sha, 'prelude_steps': 800,
            'rollouts': 1, 'steps_per_rollout': 128, 'envs': 512,
            'optimizer_updates': 0, 'max_storage_bytes': 128 * 2**20,
            'wall_s': 600, 'sampling': 'existing_ControlledPPO_act',
            'physical_reset': 'fresh reset; no historical simulator state restored'}


def validate(spec):
    from .data import sha
    c = spec['motion_advantage_probe']
    parent = Path(c['parent_spec'])
    if sha(parent) != c['parent_spec_sha256'] or c != declaration(parent, sha(parent)):
        raise ValueError('Motion advantage probe declaration/parent SHA differs')
    original = json.loads(parent.read_text())
    from .requests import validate as validate_parent
    errors = validate_parent(original)
    if errors:
        raise ValueError('Probe parent invalid: ' + str(errors))
    allowed = {'experiment', 'evaluation_only', 'motion_advantage_probe', 'authorization',
               'notifications', 'execution_source_root', 'budget', 'artifacts'}
    if set(spec) - set(original) - allowed or any(spec.get(k) != v for k, v in original.items() if k not in allowed):
        raise ValueError('Probe must preserve parent physical/reward/PPO/command/recipe contract')
    expected_budget = copy.deepcopy(original['budget'])
    expected_budget.update(source_eval_updates=0, smoke_updates=0, formal_updates=0,
                           sample_limit=0, formal_samples=0, evaluation_wall_s=600, chain_wall_s=600)
    if spec['budget'] != expected_budget or spec.get('evaluation_only') is not True:
        raise ValueError('Probe must have zero optimizer budget and600s ceiling')
    expected_artifacts = {**original['artifacts'], 'run_name': spec['experiment']}
    if spec['artifacts'] != expected_artifacts or spec['notifications'].get('enabled') is not False:
        raise ValueError('Probe artifacts/notification declaration differs')
    if original.get('motion_course', {}).get('configuration', {}).get('version') != 'motion31_straight_yaw_progression_v1':
        raise ValueError('Probe requires the exact initial seven-cohort course')
    if original['ppo']['envs'] != 512 or original['ppo']['steps_per_env'] != 128:
        raise ValueError('Probe PPO dimensions differ')
    if sha(spec['source_checkpoint']) != spec['source_sha256']:
        raise ValueError('Probe source changed')
    return True


def collect(env, spec, *, stopped):
    """Real stochastic rollout using the training bootstrap/mask; no update calls."""
    import torch
    from .model import load
    from .ppo import assemble
    from .training import observations
    from .motion_course_requests import restore
    from .standing_survival_task import bootstrap_reward
    from native_stand.recovery.controlled_ppo import KEY
    from native_stand.command_v6.tools.frozen_rollout_probe import tree_equal
    c = spec['motion_advantage_probe']
    env.curriculum_training = True
    env.select_initial_family('motion_native_normal', 'train')
    torch.manual_seed(spec['seed'])
    obs, _ = env.reset()
    obs = observations(env, obs)
    ppo = assemble(spec['source_checkpoint'], obs, recipe=spec['student_training'])
    _, saved = load(spec['source_checkpoint'], 'MotionZeroStudent')
    restored = restore(ppo, saved, spec, 'diagnostic_no_optimizer')
    env.motion_cohort_mix.copy_(torch.tensor([r['mix'] for r in ppo.reward_refinement_state], device=env.device))
    before = [copy.deepcopy(m.state_dict()) for m in (ppo.actor, ppo.critic, ppo.optimizer)]
    modes = (ppo.actor.training, ppo.critic.training)
    ppo.actor.train(); ppo.critic.train()
    rows = {}; reward_names = None; prelude_counts = torch.zeros(3, device=env.device, dtype=torch.long)
    def put(name, value):
        rows.setdefault(name, []).append(value.detach().clone())
    try:
        with torch.inference_mode():
            for step in range(c['prelude_steps'] + c['steps_per_rollout']):
                if stopped():
                    raise TimeoutError('Motion frozen diagnostic wall/stop reached')
                capture = step >= c['prelude_steps']
                valid = obs[KEY].squeeze(-1)
                if capture:
                    put('actor_input', obs['student_actor']); put('critic_input', obs['student_critic'])
                    put('actor_valid', valid); put('target', env.target_xy)
                    put('command', env.command); put('command_index', env.command_index)
                    put('episode_age_s', env.rise_hold.episode.steps.float() * .01)
                action = ppo.act(obs)
                if capture:
                    put('action_raw', action); put('action_mean', ppo.actor.output_mean)
                    put('action_std', ppo.actor.output_std)
                newobs, reward, terminated, truncated, extras = env.step(action)
                done = terminated | truncated
                state = env.recovery_snapshot
                if state[:,4].bool().any() or state[:,30].bool().any() or not torch.isfinite(reward).all():
                    raise RuntimeError('Motion runtime/initialization/nonfinite fault')
                if not torch.equal(valid, env.student_actor_valid):
                    raise RuntimeError('Motion pre-action actor mask changed')
                storage_reward = reward
                if truncated.any():
                    if env.student_terminal_critic is None:
                        raise RuntimeError('Missing pre-reset terminal Critic')
                    storage_reward = bootstrap_reward(reward, terminated, truncated,
                        ppo.critic(env.student_terminal_critic).squeeze(-1), gamma=ppo.gamma)
                if capture:
                    result = env.student_reward_result
                    reward_names = list(__import__('native_stand.students.motion_tracking_reward', fromlist=['reward_fields']).reward_fields(spec['reward']))
                    put('reward_environment', reward); put('terminated', terminated); put('truncated', truncated)
                    put('reward_raw', result['raw']); put('reward_dt', result['dt']); put('reward_events', result['events'])
                    put('state_pre_reset', state); put('posture_pre_reset', env.standing_snapshot)
                    put('geometry_pre_reset', env.wheel_geometry_snapshot)
                    put('control_pre_reset', env.recovery_control_snapshot)
                else:
                    prelude_counts += torch.stack((valid.sum(), terminated.sum(), truncated.sum()))
                newobs = observations(env, newobs)
                ppo.process_env_step(newobs, storage_reward, done, {k:v for k,v in extras.items() if k != 'time_outs'})
                obs = newobs
                if not capture and ((step+1) % 128 == 0 or step+1 == c['prelude_steps']):
                    ppo.storage.clear()
            ppo.compute_returns(obs)
            st = ppo.storage
            data = {k:torch.stack(v) for k,v in rows.items()}
            data.update(value=st.values.clone(), returns=st.returns.clone(),
                        advantage_raw=(st.returns-st.values).clone(), advantage_normalized=st.advantages.clone(),
                        old_log_prob=st.actions_log_prob.clone(), storage_reward=st.rewards.clone(),
                        bootstrap_last_value=ppo.critic(obs).clone())
        unchanged = all(tree_equal(b, m.state_dict()) for b,m in zip(before, (ppo.actor,ppo.critic,ppo.optimizer)))
        if not unchanged:
            raise RuntimeError('Frozen Actor/Critic/Adam changed')
        if any(not torch.isfinite(v).all() for v in data.values()):
            raise RuntimeError('Nonfinite probe array')
        if sum(v.numel()*v.element_size() for v in data.values()) > c['max_storage_bytes']:
            raise ValueError('Uncompressed capture exceeds declaration')
        arrays = {k:v.cpu().numpy().copy() for k,v in data.items()}
        return arrays, {'version':VERSION, 'optimizer_updates':0, 'frozen_state_unchanged':unchanged,
            'restore':restored, 'reward_names':reward_names, 'cohort_mix':ppo.reward_refinement_state,
            'prelude_steps':c['prelude_steps'], 'captured_steps':128, 'envs':512,
            'captured_transitions':65536, 'simulated_transitions':(800+128)*512,
            'prelude_counts':dict(zip(('actor_valid','terminated','truncated'),prelude_counts.cpu().tolist())),
            'axis_semantics':'time,env,feature; snapshots pre-reset; observations pre-action',
            'capability_gate':{'status':'NOT_RUN','accepted':False},
            'limitations':'one source rollout on new cohorts; not historical rollout or optimizer replay; fresh reset'}
    finally:
        ppo.actor.train(modes[0]); ppo.critic.train(modes[1])


def execute(args, spec):
    """Called only by shared evaluator after exact-ID supervisor reservation."""
    import time
    import sys
    import traceback
    import torch
    from .requests import plan
    from .data import sha
    from native_stand.command_v6.completion import write
    from native_stand.command_v6.train import record_run_configuration
    from .artifacts import npz
    p = plan(args, spec)
    if not args.run:
        print(json.dumps(p, indent=2)); return 0
    if p['preflight']['status'] != 'PASS' or not args.attempt_id:
        raise ValueError('Motion probe requires public exact-ID reservation')
    book=json.loads(args.spec.with_name('budget.json').read_text()); a=book['attempts'][args.attempt_id]
    if a['status']!='RUNNING' or a['output_dir']!=str(args.output.resolve()):
        raise ValueError('Probe reservation mismatch')
    deadline=a['started_unix_s']+600
    app=env=None; failure=None; status='FAILED'; report=None
    args.output.mkdir(parents=True,exist_ok=False)
    record_run_configuration(args.output,args.spec)
    write(args.output/'manifest.json',{'attempt_id':args.attempt_id,'phase':'evaluate',
        'spec_sha256':sha(args.spec),'source_sha256':spec['source_sha256'],'asset_sha256':spec['asset_sha256'],
        'online_PPO':0,'offline_optimizer_updates':0,'simulated_envs':512})
    from .motion_reward_audit import audit
    from . import motion_tracking_reward
    snapshot=audit(spec['reward']);snapshot.update(spec_sha256=sha(args.spec),source_sha256=spec['source_sha256'],reward_source_sha256=sha(motion_tracking_reward.__file__))
    write(args.output/'reward_snapshot.json',snapshot)
    try:
        sys.path.insert(0,spec['asset_module_root'])
        from isaaclab.app import AppLauncher
        app=AppLauncher({'headless':True,'device':'cuda:0','multi_gpu':False}).app
        from .evaluator import environment
        env=environment(spec,'MotionZeroStudent',envs=512)
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        write(args.output/'runtime_readback.json',{'control':verify(env),'ground':verify_ground(env,spec)})
        arrays,report=collect(env,spec,stopped=lambda:time.time()>deadline-90)
        npz(args.output/'rollout.npz',arrays)
        if (args.output/'rollout.npz').stat().st_size > spec['motion_advantage_probe']['max_storage_bytes']:
            raise ValueError('Compressed capture exceeds declaration')
        report.update(spec_sha256=sha(args.spec),source_sha256=spec['source_sha256'],
            capture={'path':'rollout.npz','sha256':sha(args.output/'rollout.npz'),
                     'array_shapes':{k:list(v.shape) for k,v in arrays.items()}})
        write(args.output/'probe_result.json',report); status='COMPLETED'
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    finally:
        write(args.output/'terminal_report.json',{'status':status,'attempt_id':args.attempt_id,
            'actual_updates':0,'online_PPO':0,'offline_optimizer_updates':0,'failure':failure,
            'samples':0,'diagnostic_transitions':report.get('captured_transitions',0) if report else 0})
        cleanup=[]
        if env is not None:
            try:env.close()
            except BaseException as exc:cleanup.append(repr(exc))
        write(args.output/'cleanup.json',{'errors':cleanup})
        if app is not None:app.close(exit_code=0 if status=='COMPLETED' and not cleanup else 1)
    return 0 if status=='COMPLETED' else 1
