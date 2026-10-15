"""Bounded recovery preparation probes; --help/plan never import Isaac.

R0: frozen STAND near-standing takeover. initial: explicit zero-effort settle.
Neither mode performs PPO or certifies a Recovery policy's ability.
"""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from native_stand.recovery.preflight import check,digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--mode',choices=('r0','initial','checkpoint'),required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--seconds',type=float,default=None)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--handshake-fd',type=int,default=None)
    parser.add_argument('--budget-phase',choices=('source_eval','smoke','formal','evaluate'))
    args=parser.parse_args()
    spec=json.loads(args.spec.read_text());config=spec['recovery']
    seconds=args.seconds if args.seconds is not None else (18. if args.mode=='checkpoint' else 10. if args.mode=='r0' else 1.05)
    if seconds<=0 or seconds>(18. if args.mode=='checkpoint' else 10. if args.mode=='r0' else 2.):parser.error('Probe duration outside frozen bound')
    if args.mode=='r0' and seconds!=10.:parser.error('R0 requires the complete10s takeover protocol')
    plan=check(args.spec,args.output_dir)
    if args.mode=='checkpoint':
        if args.checkpoint is None:parser.error('checkpoint mode requires --checkpoint')
        from native_stand.command_v6.tools.checkpoint_input import inspect
        info=inspect(args.checkpoint,spec,Path(spec['diagnostic_source_spec']))
        if info['checkpoint_sha256']!=spec['diagnostic_checkpoint_sha256']:
            raise ValueError('Diagnostic checkpoint SHA differs')
        plan.update(checkpoint_identity=info)
    plan.update(mode=args.mode,seconds=seconds,policy_steps=round(seconds/.01),
        initialization_controller='zero active effort during passive settle',ppo_updates=0)
    if not args.run:
        print(json.dumps(plan,indent=2));return 0 if plan['cpu_valid'] else 2
    if not plan['cpu_valid']:raise RuntimeError(plan['errors'])
    if args.mode=='initial' and not config['geometry_definition_confirmed']:
        raise RuntimeError('Confirm guide-supported low family geometry before initial probe')
    from native_stand.command_v6.ledger import Ledger
    from native_stand.command_v6 import train
    ledger=Ledger(args.spec.with_name('budget.json'));attempt=uuid.uuid4().hex
    ledger_phase=args.budget_phase or ('evaluate' if args.mode=='checkpoint' else 'source_eval')
    ledger.reserve(attempt,ledger_phase,args.output_dir)
    started=time.monotonic();app=env=None;outcome='FAILED';failure=None
    handshake_sent=False
    def progressed(steps):
        nonlocal handshake_sent
        import os
        progress={'status':'RUNNING','phase':args.mode,'policy_steps':steps,'sim_time_s':steps*.01,
            'ppo_updates':0,'pid':os.getpid(),'output_dir':str(args.output_dir.resolve())}
        train._write(args.output_dir/'progress.json',progress)
        if args.handshake_fd is not None and not handshake_sent:
            train.send_handshake(args.handshake_fd,progress);handshake_sent=True
    try:
        args.output_dir.mkdir(parents=True,exist_ok=False)
        snapshots=train.record_run_configuration(args.output_dir,args.spec)
        train._write(args.output_dir/'manifest.json',{'attempt_id':attempt,'phase':'source_eval',
            'mode':args.mode,'task':'recovery_preparation','plan':plan,'source_snapshot_sha256':snapshots,
            'stand_sha256':config['stand_sha256'],'asset_sha256':spec['asset_sha256'],'ppo_updates':0})
        from isaaclab.app import AppLauncher
        app=AppLauncher({'headless':True}).app
        train.install_stop_handlers()
        import torch
        sys.path.insert(0,spec['asset_module_root'])
        from native_stand.command_v6.runtime.configure import apply,verify_asset_import
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.tools.model_factory import model
        from native_stand.command_v6.tools.evaluate_checkpoint import evaluate_actor
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from native_stand.recovery.recipe import environment
        identity=verify_asset_import(spec)
        torch.manual_seed(spec['evaluation']['seed'])
        cfg=apply(CommandEnvCfg(),spec,envs=spec['evaluation']['envs'])
        if args.mode=='r0':
            stand_spec=json.loads(Path(config['stand_spec']).read_text())
            # A narrow task adapter: full closed-chain candidate, no passive/random reset arrays.
            library=json.loads(Path(config['pose_library']).read_text())
            candidates=[row for row in library['poses'] if row['family']=='R0' and row['split']=='holdout' and row['offline_valid']]
            class TakeoverProbe(CommandEnv):
                def _reset_idx(self,env_ids):
                    super()._reset_idx(env_ids)
                    ids=torch.arange(self.num_envs,device=self.device) if env_ids is None else env_ids.long()
                    if not hasattr(self,'history'):return
                    selected=[candidates[int(index)%len(candidates)] for index in range(len(ids))]
                    q=torch.tensor([[row['joint_pos'].get(name,0.) for name in self.robot.joint_names]
                        for row in selected],device=self.device)
                    pose=torch.tensor([[0.,0.,row['root_height_m'],*row['root_quaternion_xyzw']]
                        for row in selected],device=self.device)
                    pose[:,:3]+=self.scene.env_origins[ids]
                    self.robot.write_root_pose_to_sim_index(root_pose=pose,env_ids=ids)
                    self.robot.write_joint_position_to_sim_index(position=q,env_ids=ids)
            cfg.leg_position_scale_rad=.5;cfg.leg_pair_radius_rad=0.;cfg.wheel_speed_scale_rad_s=100.
            cfg.fall_root_height_m=stand_spec['termination']['fall_root_height_m']
            cfg.active_leg_angle_max_rad=stand_spec['termination']['active_leg_angle_max_rad']
            cfg.episode_length_s=max(11.,seconds+1)
            env=TakeoverProbe(cfg,stage=spec['curriculum']['stages'][0],command_height=.4,
                reward_config=stand_spec['reward'],schedule_s=spec['curriculum']['schedule_s'])
            control_readback=verify(env);ground_readback=verify_ground(env,spec)
            wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
            actor=model(wrapped.get_observations(),actor=True,
                spec=json.loads(Path(config['stand_spec']).read_text())).to(env.device)
            actor.load_state_dict(torch.load(config['stand_checkpoint'],map_location='cpu',weights_only=False)['actor'],strict=True)
            actor.eval()
            for parameter in actor.parameters():parameter.requires_grad_(False)
            result=evaluate_actor(actor,wrapped,env,target=(0.,0.),seconds=seconds,full_trace=True,
                seed=spec['evaluation']['seed'],scored_envs=8,target_window=(2.,seconds),
                standing_protocol={**spec['evaluation'],'seconds':seconds},stop_requested=lambda:train.STOP,
                diagnostics=True,progress_callback=progressed)
            result['pose_ids']=[row['pose_id'] for row in candidates]
            result['role']='R0 provisional handover-domain probe, not broad certification'
        elif args.mode=='checkpoint':
            from native_stand.recovery.recipe import evaluate_actor as evaluate_recovery
            env=environment(cfg,spec)
            control_readback=verify(env);ground_readback=verify_ground(env,spec)
            wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
            actor=model(wrapped.get_observations(),actor=True,spec=spec).to(env.device)
            actor.load_state_dict(torch.load(args.checkpoint,map_location='cpu',weights_only=False)['actor'],strict=True)
            actor.eval()
            result=evaluate_recovery(actor,wrapped,env,seconds=seconds,seed=spec['evaluation']['seed'],
                full_trace=True,stop_requested=lambda:train.STOP,progress_callback=progressed)
            result.update(checkpoint_sha256=digest(args.checkpoint),checkpoint=str(args.checkpoint.resolve()),ppo_updates=0)
        else:
            env=environment(cfg,spec,initialization_only=True)
            control_readback=verify(env);ground_readback=verify_ground(env,spec)
            if env.reverse_curriculum is not None:
                env.curriculum_training=False
                family_results=[]
                for level in config['curriculum']['levels']:
                    for split in ('train','holdout'):
                        env.select_initial_family(level['pose_family'],split);env.reset()
                        counts_before=env.initial_rejects.clone()
                        for step in range(round(seconds/env.step_dt)):
                            if train.STOP:break
                            env.step(torch.zeros(env.num_envs,6,device=env.device))
                            if bool(env.initialization_checked.all()) or bool((env.initial_rejects>counts_before).any()):break
                        passed=bool(env.initialization_checked.all() and not (env.initial_rejects>counts_before).any()
                            and not env.recovery_snapshot[:,4].bool().any())
                        family_results.append({'family':level['pose_family'],'split':split,'passed':passed,
                            'policy_steps':step+1,'pre_reset_state':env.recovery_snapshot.cpu().tolist(),
                            'causes':env.recovery_cause_snapshot.cpu().tolist()})
                        progressed(step+1)
                        if not passed:break
                    if not passed:break
                result={'family_results':family_results,'passed':len(family_results)==2*len(config['curriculum']['levels']) and all(r['passed'] for r in family_results),
                    'initialization':env.initialization_summary(),'ppo_updates':0,
                    'initialization_control':'explicit per-pose initialization; direct zero reset R0/R1, passive settle R2/R3'}
                result.update(control_readback=control_readback,ground_readback=ground_readback,dependency_readback=identity)
                train._write(args.output_dir/'result.json',result)
                outcome='STOPPED_BOUNDED' if train.STOP else 'COMPLETED'
                return 0
            env.select_initial_family('R1','holdout');env.reset()
            tensor=torch.zeros((round(seconds/env.step_dt),8,39),device=env.device)
            valid=torch.zeros(tensor.shape[:2],device=env.device,dtype=torch.bool)
            active=torch.ones(8,device=env.device,dtype=torch.bool)
            for step in range(tensor.shape[0]):
                if train.STOP:break
                # Finish as soon as settling is decided, before Recovery controls a step.
                if bool(env.initialization_checked.all()) or bool(env.initial_rejects.sum()>0):break
                actions=torch.zeros(env.num_envs,6,device=env.device)
                _,_,done,_,_=env.step(actions)
                if step==0 or (step+1)%50==0:progressed(step+1)
                tensor[step].copy_(env.recovery_snapshot[:8]);valid[step].copy_(active)
                active &= ~done[:8].bool()
                if bool(env.terminal_causes['nonfinite'].any()) or bool(env.terminal_causes['closure'].any()):
                    raise RuntimeError('Initialization runtime fault; pre-reset snapshot retained')
            result={'initialization':env.initialization_summary(),
                'all_env_pre_reset_state':env.recovery_snapshot.cpu().tolist(),
                'all_env_pre_reset_control':env.recovery_control_snapshot.cpu().tolist(),
                'all_env_pre_reset_causes':env.recovery_cause_snapshot.cpu().tolist(),
                'all_env_terminal_valid':env.recovery_snapshot_valid.cpu().tolist(),
                'samples':tensor.cpu().tolist(),
                'valid':valid.cpu().tolist(),'geometry_semantics':'ideal primitive ground clearance, not PhysX contact distance',
                'ppo_updates':0,'validated_envs':env.num_envs,
                'passed':bool(env.initialization_checked.all() and env.initial_rejects.sum()==0)}
        result['control_readback']=control_readback;result['ground_readback']=ground_readback
        result['dependency_readback']=identity
        train._write(args.output_dir/'result.json',result)
        outcome='STOPPED_BOUNDED' if train.STOP else 'COMPLETED'
    except BaseException as exc:
        failure=repr(exc)
        if env is not None and hasattr(env,'recovery_snapshot'):
            train._write(args.output_dir/'partial_pre_reset.json',{'state':env.recovery_snapshot.cpu().tolist(),
                'control':env.recovery_control_snapshot.cpu().tolist(),'terminal_valid':env.recovery_snapshot_valid.cpu().tolist()})
    finally:
        terminal={'status':outcome,'attempt_id':attempt,'phase':ledger_phase,'mode':args.mode,
            'actual_updates':0,'samples':0,'wall_s':time.monotonic()-started,'failure':failure,
            'exit_code':1 if failure else 0,'stop_kind':'user_signal' if train.STOP else 'completion_or_failure'}
        if args.output_dir.is_dir():train._write(args.output_dir/'terminal_report.json',terminal)
        ledger.finalize(attempt,args.output_dir,outcome,exit_code=terminal['exit_code'],reason=failure,wall_s=terminal['wall_s'])
        if env is not None:env.close()
        if app is not None:train.close_app(app,bool(failure))
    return 1 if failure else 0


if __name__=='__main__':raise SystemExit(main())
