"""Capture a SHA-bound actor-retention reference bundle from native Isaac rollouts."""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def sha(path):
    h=hashlib.sha256(); f=Path(path).open('rb')
    with f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--spec',type=Path,required=True)
    ap.add_argument('--checkpoint',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=10.)
    ap.add_argument('--tail-seconds',type=float,default=7.)
    ap.add_argument('--samples-per-command',type=int,default=64)
    ap.add_argument('--run',action='store_true')
    a=ap.parse_args()
    spec=json.loads(a.spec.read_text())
    if a.output.exists(): raise FileExistsError(a.output)
    plan={'spec':str(a.spec.resolve()),'spec_sha256':sha(a.spec),
          'checkpoint':str(a.checkpoint.resolve()),'checkpoint_sha256':sha(a.checkpoint),
          'commands':[[0.,0.],[.5,0.],[-.5,0.]],'seconds':a.seconds,
          'tail_seconds':a.tail_seconds,'samples_per_command':a.samples_per_command,
          'simulation':0,'files_written':0}
    if not a.run:
        print(json.dumps(plan,indent=2)); return
    import torch
    print('CAPTURE: launching AppLauncher', flush=True)
    from isaaclab.app import AppLauncher
    app=AppLauncher({'headless':True}).app
    print('CAPTURE: AppLauncher ready', flush=True)
    try:
        sys.path.insert(0,spec['asset_module_root'])
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import
        from native_stand.command_v6.learning import model as build_model
        from native_stand.command_v6.domain.warmstart import initialize_state
        from native_stand.command_v6.domain.command_schedule import effective
        cfg=configure_env(CommandEnvCfg(),spec,envs=max(8,spec['ppo']['envs']))
        print('CAPTURE: config ready', flush=True)
        verify_asset_import(spec)
        reward_config=dict(spec['reward'])
        if 'velocity_tracking' not in reward_config:
            reward_config['velocity_tracking']=reward_config.get('linear_velocity_tracking',0.)+reward_config.get('yaw_velocity_tracking',0.)
        env=CommandEnv(cfg,stage=spec['curriculum']['stages'][1],
                       command_height=spec['control']['height_command_m'],
                       reward_config=reward_config,schedule_s=spec['curriculum']['schedule_s'])
        wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
        print('CAPTURE: environment ready', flush=True)
        obs=wrapped.get_observations(); obs=obs.clone()
        actor=build_model(obs,actor=True,spec=spec).to(env.device)
        state=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
        actor.load_state_dict(initialize_state(state['actor'],actor.state_dict(),input_dim=spec['source_input_dim']),strict=True)
        actor.eval(); rows=[]; tail_start=max(0.,a.seconds-a.tail_seconds)
        for command in ((0.,0.),(.5,0.),(-.5,0.)):
            env.set_evaluation_target(*command)
            obs,_=wrapped.reset()
            obs=obs.clone()
            for step in range(round(a.seconds/env.step_dt)):
                age=float(env.episode_length_buf[0]*env.step_dt)
                with torch.inference_mode():
                    action=actor(obs,stochastic_output=False)
                if age>=tail_start:
                    n=min(env.num_envs,a.samples_per_command)
                    actual=env.command[:n,:2]
                    expected=effective(actual.new_tensor(command).expand(n,2),
                        actual.new_full((n,),age),height=env.command_height,
                        entry=env.schedule_s[0],ramp=env.schedule_s[1],
                        hold=env.schedule_s[2],exit=env.schedule_s[3])[:,:2]
                    if not torch.allclose(actual,expected,atol=1e-5) or not torch.allclose(
                            obs['policy'][:n,6:8],expected*expected.new_tensor((2.,.25)),atol=1e-5):
                        raise RuntimeError('reference command label differs from actor observation')
                    rows.append({'command':list(command),'episode_age_s':age,
                        'observations':torch.cat((obs['policy'][:n],obs['history'][:n]),-1).detach().cpu(),
                        'source_mean':action[:n].detach().cpu(),
                        'pose':env.robot.data.root_quat_w.torch[:n].detach().cpu(),
                        'velocity':torch.stack((env.vx[:n],env.vy[:n],env.yaw[:n]),-1).detach().cpu(),
                        'contact':(env.contact_force[:n]>2.).detach().cpu()})
                obs,_,_,_=wrapped.step(action.detach().to(env.device).clone()); obs=obs.clone()
        flat=torch.cat([r['observations'] for r in rows],0)
        commands=torch.tensor([r['command'] for r in rows for _ in range(r['observations'].shape[0])])
        ages=torch.tensor([r['episode_age_s'] for r in rows for _ in range(r['observations'].shape[0])])
        payload={'observations':flat,'commands':commands,'episode_age_s':ages,
                 'source_mean':torch.cat([r['source_mean'] for r in rows],0),
                 'pose':torch.cat([r['pose'] for r in rows],0),
                 'velocity':torch.cat([r['velocity'] for r in rows],0),
                 'contact':torch.cat([r['contact'] for r in rows],0),
                 'min_episode_age_s':tail_start,'metadata':{'source_checkpoint_sha256':sha(a.checkpoint),
                 'spec_sha256':sha(a.spec),'asset_sha256':spec['asset_sha256'],
                 'schedule_s':list(env.schedule_s),'rows':len(rows)}}
        a.output.parent.mkdir(parents=True,exist_ok=True); torch.save(payload,a.output)
        plan.update(files_written=1,simulation=1,reference_sha256=sha(a.output),rows=len(rows))
        print(json.dumps(plan,indent=2))
    except BaseException as exc:
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Isaac's close may terminate the interpreter; keep the original
        # exception visible above for diagnosis.
        app.close()

if __name__=='__main__': main()
