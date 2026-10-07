"""Single bounded v6 recipe; all file/budget inputs are checked before Isaac."""
import argparse
import hashlib
import json
import errno
import os
from pathlib import Path
import shutil
import signal
import sys
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from native_stand.command_v6.config import PHASES,schedule,evaluation_seconds
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.tools.preflight import check,digest
from native_stand.command_v6.completion import evaluation_identity, plan as runtime_plan, choose

STOP=False


def _signal(_number,_frame):
    global STOP
    STOP=True


def install_stop_handlers():
    """Call after AppLauncher, whose constructor replaces signal handlers."""
    signal.signal(signal.SIGTERM,_signal)
    signal.signal(signal.SIGINT,_signal)


def send_handshake(fd,payload):
    try:
        os.write(fd,(json.dumps(payload)+"\n").encode())
        return True
    except BrokenPipeError:
        return False
    except OSError as exc:
        if exc.errno==errno.EPIPE:
            return False
        raise


def _write(path,data):
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data,indent=2)+"\n")
    os.replace(tmp,path)


def settle_attempt(output,progress,report,ledger,attempt_id):
    """Persist exact-attempt evidence and accounting before any Kit shutdown."""
    if output.is_dir():
        _write(output/'progress.json',progress)
        _write(output/'terminal_report.json',report)
    failure=report.get('failure')
    ledger.finalize(attempt_id,output,report['status'],
        reason=failure['exception'] if failure else report.get('early_stop_reason'),
        exit_code=report['exit_code'],wall_s=report['wall_s'])


def close_app(app, failed):
    # Installed SimulationApp fast shutdown can exit before main returns.
    app.close(exit_code=1 if failed else 0)


def _snapshot(output,spec_path):
    paths={"spec.json":spec_path,"train.py":ROOT/"train.py",
           "config.py":ROOT/"config.py","ledger.py":ROOT/"ledger.py",
           "launcher.py":ROOT/"launcher.py",
           "monitor.py":ROOT/"monitor.py",
           "completion.py":ROOT/"completion.py",
           "preflight.py":ROOT/"tools/preflight.py",
           "control_readback.py":ROOT/"runtime/control_readback.py",
           "domain_contract.py":ROOT/"domain/contract.py",
           "domain_schedule.py":ROOT/"domain/command_schedule.py",
           "domain_reward.py":ROOT/"domain/reward.py",
           "tracking_width.py":ROOT/"domain/tracking_width.py",
           "domain_metrics.py":ROOT/"domain/metrics.py",
           "episode_curriculum.py":ROOT/'domain/episode_curriculum.py',
           "task_curriculum.py":ROOT/'domain/task_curriculum.py',
           "domain_protocol.py":ROOT/"domain/protocol.py",
           "domain_evidence.py":ROOT/'domain/evidence.py',
           "selected_diagnostics.py":ROOT/'domain/selected_diagnostics.py',
           "wiring.py":ROOT/'wiring.py',
           "submission.py":ROOT/'submission.py',
           "domain_warmstart.py":ROOT/"domain/warmstart.py",
           "learning.py":ROOT/"learning.py",
           "runtime_env.py":ROOT/"runtime/env.py",
           "runtime_configure.py":ROOT/"runtime/configure.py",
           "evaluate_checkpoint.py":ROOT/"tools/evaluate_checkpoint.py",
           "evaluation_state.py":ROOT/'tools/evaluation_state.py',
           "checkpoint_input.py":ROOT/"tools/checkpoint_input.py",
           "play.py":ROOT/"tools/play.py",
           "native_env.py":ROOT.parent/"env.py",
           "native_contract.py":ROOT.parent/"contract.py",
           "native_control_readback.py":ROOT.parent/"control_readback.py"}
    spec=json.loads(spec_path.read_text())
    if spec.get('retention',{}).get('enabled'):
        paths['domain_retention.py']=ROOT/'domain/retention.py'
    if spec.get('task')=='recovery':
        paths.update({f'recovery_{path.name}':path for path in (ROOT.parent/'recovery').glob('*.py')})
        paths['frozen_stand_spec.json']=Path(spec['recovery']['stand_spec'])
        paths['recovery_poses.json']=Path(spec['recovery']['pose_library'])
    folder=output/"source_snapshot"
    folder.mkdir()
    identity={}
    for name,path in paths.items():
        shutil.copy2(path,folder/name)
        identity[name]=digest(path)
    return identity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,default=ROOT.parents[2]/"configs/experiments/stand_plane.json")
    parser.add_argument("--phase",choices=PHASES,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--attempt-id",default=None)
    parser.add_argument("--handshake-fd",type=int,default=None,help=argparse.SUPPRESS)
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--hapi-session",default=None)
    args=parser.parse_args()
    plan=check(args.spec,args.output_dir,args.phase,attempt_id=args.attempt_id)
    if not args.run:
        print(json.dumps(plan,indent=2))
        return 0 if plan["status"]=="PASS" else 2
    if plan["status"]!="PASS":
        raise RuntimeError(f"preflight failed: {plan['errors']}")
    spec=json.loads(args.spec.read_text())
    attempt_id=args.attempt_id or uuid.uuid4().hex
    ledger=Ledger(args.spec.with_name("budget.json"))
    current=json.loads(args.spec.with_name('budget.json').read_text())['attempts'].get(attempt_id)
    if current is None:
        ledger.reserve(attempt_id,args.phase,args.output_dir)
    elif (current['status']!='RUNNING' or current['phase']!=args.phase or
          current['output_dir']!=str(args.output_dir.resolve())):
        raise ValueError('reserved attempt identity differs')
    output=args.output_dir
    app=env=None
    actor=critic=ppo=None
    started=time.monotonic()
    phase_wall=spec['budget'][args.phase+'_wall_s']
    if phase_wall is None:phase_wall=float('inf')
    progress={"status":"STARTING","phase":args.phase,"stage":"manifest",
              "pid":os.getpid(),"attempt_id":attempt_id,"output_dir":str(output.resolve()),
              "actual_updates":0,"samples":0,"latest_metric":None,"evaluations":[],
              "latest_checkpoint":None,"best_standing_candidate":None,
              "accepted_by_stage":{},"final_capability_certificate":None}
    outcome="FAILED"
    failure=None
    handshake_sent=False

    def handshake(payload):
        nonlocal handshake_sent
        if args.handshake_fd is not None and not handshake_sent:
            progress["handshake_delivered"]=send_handshake(args.handshake_fd,payload)
            handshake_sent=True
    signal.signal(signal.SIGTERM,_signal)
    try:
        output.mkdir(parents=True,exist_ok=False)
        identity=_snapshot(output,args.spec)
        evaluator_sha=__import__('hashlib').sha256((digest(ROOT/'domain/protocol.py')+
            digest(ROOT/'domain/evidence.py')+
            digest(ROOT/'tools/evaluation_state.py')+
            digest(ROOT/'tools/evaluate_checkpoint.py')+
            (''.join(digest(ROOT.parent/'recovery'/name) for name in
                ('recipe.py','domain.py','standing.py','selection.py'))
             if spec.get('recovery',{}).get('standing_task') else '')).encode()).hexdigest()
        eval_identity=evaluation_identity(spec,evaluator_sha)
        book=json.loads(args.spec.with_name('budget.json').read_text())
        source_runs=[row['output_dir'] for row in book['attempts'].values()
                     if row['phase']=='source_eval' and row['status']=='COMPLETED']
        source_baseline_run=(source_runs[-1] if source_runs else None) if (
            spec.get('task')!='recovery' or spec.get('recovery',{}).get('standing_task')) else None
        _write(output/"manifest.json",{"experiment":spec["experiment"],
            "task":spec.get('task','stand'),
            "frozen_stand_checkpoint":spec.get('recovery',{}).get('stand_checkpoint'),
            "frozen_stand_sha256":spec.get('recovery',{}).get('stand_sha256'),
            "attempt_id":attempt_id,"phase":args.phase,"pid":os.getpid(),
            "process_started_unix_s":__import__('native_stand.command_v6.tools.health_check',fromlist=['own_process_start']).own_process_start(os.getpid()),
            "spec_sha256":digest(args.spec),"source_sha256":spec["source_sha256"],
            "asset_sha256":spec["asset_sha256"],"seed":spec["seed"],
            "source_asset_sha256":spec.get("source_asset_sha256",spec["asset_sha256"]),
            "asset_module_sha256":spec["asset_module_sha256"],
            "colleague_config_sha256":spec["colleague_config_sha256"],
            "ground":spec["ground"],
            "source_snapshot_sha256":identity,"interpreter":sys.executable,
            "envs":spec["ppo"]["envs"],"steps_per_env":spec["ppo"]["steps_per_env"],
            "evaluator_sha256":evaluator_sha,"hapi_session":args.hapi_session,
            "source_baseline_run":source_baseline_run,
            "preparation_probe_runs":source_runs if spec.get('task')=='recovery' else [],
            "run_plan":runtime_plan(spec,args.phase)})
        registry=[]
        baseline_registry=[]
        if source_baseline_run and spec.get('recovery',{}).get('standing_task'):
            baseline_registry=[row for row in json.loads(
                (Path(source_baseline_run)/'candidate_registry.json').read_text())
                if row.get('role')=='source' and row.get('identity')==eval_identity]
        standing_regression=None
        if spec.get('recovery',{}).get('standing_task'):
            from native_stand.recovery.standing import StandingRegression
            standing_regression=StandingRegression(confirmed=bool(
                choose(baseline_registry,None,eval_identity)['accepted_candidate']))
        _write(output/'candidate_registry.json',registry)
        _write(output/"progress.json",progress)
        progress["stage"]="app_launcher"
        from isaaclab.app import AppLauncher
        app=AppLauncher({"headless":True}).app
        # AppLauncher installs its own SIGTERM callback, which closes Kit before
        # our finally block can settle the attempt. Install the task handler last.
        install_stop_handlers()
        import torch
        sys.path.insert(0,spec["asset_module_root"])
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from native_stand.command_v6.runtime.env import CommandEnv,CommandEnvCfg
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.runtime.configure import apply as configure_env,verify_asset_import
        from native_stand.command_v6.learning import model as build_model
        from native_stand.command_v6.domain.warmstart import (initialize_state,initialize_adam,
            clear_first_moment,convert_wheel_envelope,seed_training,preserve_rng_state)
        from native_stand.command_v6.domain.retention import load_reference,balanced_subset,attach_optimizer_retention,RetentionBatch
        from native_stand.command_v6.domain.metrics import RolloutMetrics
        from native_stand.command_v6.domain.contract import EFFORT_LIMITS
        from native_stand.command_v6.tools.evaluate_checkpoint import evaluate_actor
        from native_stand.command_v6.domain.task_curriculum import TaskProgression
        from native_stand.command_v6.domain.protocol import motion_gate
        task_config=spec['curriculum'].get('task_progression')
        task_manager=TaskProgression(task_config) if task_config else None
        last_confirmation=0
        stage_start_update=0
        progress["asset_import_readback"]=verify_asset_import(spec)
        rng_info=seed_training(spec["seed"])
        progress["rng_initialization"]=rng_info
        cfg=configure_env(CommandEnvCfg(),spec,envs=spec["ppo"]["envs"])
        stage=0 if args.phase=="source_eval" else spec["curriculum"]["active_stage"]
        progress["stage"]="environment_init"
        if spec.get('task')=='recovery':
            from native_stand.recovery.recipe import environment,evaluate_actor
            env=environment(cfg,spec)
        else:
            stage_reward=dict(spec['reward'])
            if spec['evaluation'].get('protocol_identity')=='capability_v2':
                stage_reward['linear_error_denominator']=spec['reward']['stage_linear_denominators'][str(stage)]
                stage_reward['yaw_error_denominator']=spec['reward']['stage_yaw_denominators'][str(stage)]
            env=CommandEnv(cfg,stage=spec["curriculum"]["stages"][stage],
                           command_height=spec["control"]["height_command_m"],
                           reward_config=stage_reward,
                           schedule_s=spec["curriculum"]["schedule_s"])
        progress["ground_readback"]=verify_ground(env,spec)
        progress["control_readback"]=verify(env)
        wrapped=RslRlVecEnvWrapper(env,clip_actions=1.)
        obs=wrapped.get_observations()
        actor=build_model(obs,actor=True,spec=spec).to(env.device)
        source=None
        if spec.get('initialization','warmstart')!='random':
            source=torch.load(spec["source_checkpoint"],map_location="cpu",weights_only=False)
            actor.load_state_dict(initialize_state(source["actor"],actor.state_dict(),input_dim=spec.get('source_input_dim',132)),strict=True)
        progress['initialization_s']=time.monotonic()-started
        if args.phase=="source_eval":
            if source is not None and spec.get('wheel_envelope_conversion'):
                progress['wheel_conversion']=convert_wheel_envelope(actor,
                    old_scale=spec['wheel_envelope_conversion']['source_scale_rad_s'],
                    new_scale=spec['action']['wheel_scale_rad_s'])
            progress["stage"]="source_evaluation"
            evaluation_start=time.monotonic()
            def baseline_handshake(step):
                if step==1 and spec.get('cohort_width_ab'):
                    _write(output/'progress.json',progress)
                    handshake({'status':'RUNNING','attempt_id':attempt_id,
                        'trainer_pid':os.getpid(),'actual_updates':0,
                        'stage':'source_evaluation','physics_steps':1,'output_dir':str(output.resolve())})
            result=evaluate_actor(actor,wrapped,env,target=(0.,0.),
                seconds=evaluation_seconds(spec,full=True) if spec['evaluation'].get('protocol_identity')=='capability_v2' else 10.,
                full_trace=True,seed=spec["evaluation"]["seed"],
                scored_envs=spec["evaluation"]["scored_envs"],
                target_window=spec["evaluation"]["steady_window_s"],
                standing_protocol=spec["evaluation"],diagnostics=(spec.get('diagnostics',{}).get('enabled',bool(spec.get('diagnostics')))),
                stop_requested=lambda:STOP or time.monotonic()-started>=phase_wall-30,
                progress_callback=baseline_handshake if spec.get('cohort_width_ab') else None)
            progress['source_evaluation_s']=time.monotonic()-evaluation_start
            source_gate=result.get('capability_gate',result.get('standing_gate',result.get('recovery_gate')))
            result.update(checkpoint_sha256=spec["source_sha256"],spec_sha256=digest(args.spec))
            _write(output/"evaluation_source.json",result)
            registry.append({'role':'source','kind':'full','checkpoint':spec['source_checkpoint'],
                'checkpoint_sha256':spec['source_sha256'],'update':0,'identity':eval_identity,
                'evaluation':'evaluation_source.json','result':{**result,'per_env':[
                    {key:value for key,value in row.items() if key not in (
                        'trace','compact_trace_100hz','posture_trace_100hz',
                        'gate_diagnostics_100hz','control_diagnostics_100hz','failure_window_100hz')}
                    for row in result['per_env']]}})
            _write(output/'candidate_registry.json',registry)
            progress["evaluations"].append({"target":[0.,0.],"path":"evaluation_source.json",
                "source_pass":source_gate["accepted"],
                "outcome_counts":result["outcome_counts"]})
            progress["source_pass"] = source_gate["accepted"]
            progress["source_gate"] = source_gate
            for command in spec.get('source_evaluation_commands',[]):
                if command==[0,0]:
                    continue
                result=evaluate_actor(actor,wrapped,env,target=command,
                    seconds=evaluation_seconds(spec,full=True),full_trace=True,
                    seed=spec['evaluation']['seed'],scored_envs=spec['evaluation']['scored_envs'],
                    target_window=spec['evaluation']['motion_window_s'],
                    standing_protocol=spec['evaluation'],
                    stop_requested=lambda:STOP or time.monotonic()-started>=phase_wall-30)
                result.update(checkpoint_sha256=spec['source_sha256'],spec_sha256=digest(args.spec))
                label=f'evaluation_source_{command[0]}_{command[1]}.json'
                _write(output/label,result)
                gate=result['capability_gate']
                registry.append({'role':'source','kind':'full','checkpoint':spec['source_checkpoint'],
                    'checkpoint_sha256':spec['source_sha256'],'update':0,'identity':eval_identity,
                    'evaluation':label,'result':{**result,'per_env':[
                        {key:value for key,value in row.items() if key!='trace'} for row in result['per_env']]}})
                _write(output/'candidate_registry.json',registry)
                progress['evaluations'].append({'target':command,'path':label,
                    'source_pass':gate['accepted'],'outcome_counts':result['outcome_counts']})
                if command in spec.get('source_required_commands',[]):
                    progress['source_pass'] &= gate['accepted']
                _write(output/'progress.json',progress)
            progress['source_evaluation_s']=time.monotonic()-evaluation_start
            outcome="COMPLETED"
        else:
            from rsl_rl.algorithms import PPO
            from rsl_rl.storage import RolloutStorage
            critic=build_model(obs,actor=False,spec=spec).to(env.device)
            if source is not None:
                critic.load_state_dict(initialize_state(source["critic"],critic.state_dict(),input_dim=spec.get('source_input_dim',132)),strict=True)
            storage=RolloutStorage("rl",env.num_envs,spec["ppo"]["steps_per_env"],obs,[6],env.device)
            ppo=PPO(actor,critic,storage,num_learning_epochs=spec["ppo"]["epochs"],
                num_mini_batches=spec["ppo"]["minibatches"],clip_param=.2,
                gamma=spec["ppo"]["gamma"],lam=spec["ppo"]["lam"],value_loss_coef=.5,
                entropy_coef=spec["ppo"]["entropy_coef"],
                learning_rate=spec["ppo"]["learning_rate"],max_grad_norm=1.,
                use_clipped_value_loss=False,schedule="fixed",desired_kl=.01,device=env.device)
            if source is not None:
                old_named=[("actor."+n,p) for n,p in source["actor"].items()]+[("critic."+n,p) for n,p in source["critic"].items()]
                new_named=[("actor."+n,p) for n,p in actor.named_parameters()]+[("critic."+n,p) for n,p in critic.named_parameters()]
                initialize_adam(source["optimizer"],ppo.optimizer,old_named,new_named,
                            input_dim=spec.get('source_input_dim',132), learning_rate=spec["ppo"]["learning_rate"])
            if source is not None and spec.get('wheel_envelope_conversion'):
                progress['wheel_conversion']=convert_wheel_envelope(actor,critic,ppo.optimizer,
                    old_scale=spec['wheel_envelope_conversion']['source_scale_rad_s'],
                    new_scale=spec['action']['wheel_scale_rad_s'])
            cleared = clear_first_moment(ppo.optimizer) if spec['ppo'].get('clear_adam_first_moment', False) else 0
            progress["optimizer_initial"]={
                "source_lr":source["optimizer"]["param_groups"][0]["lr"] if source is not None else None,
                "spec_lr":spec["ppo"]["learning_rate"],
                "effective_lr":ppo.optimizer.param_groups[0]["lr"],
                "state_count":len(ppo.optimizer.state),
                "first_moment_cleared":bool(cleared),
                "first_moment_tensors_cleared":cleared}
            retention_cfg=spec.get("retention")
            reference_eligible_count=None
            standing_retention=None
            stand_retention_cfg=spec.get('recovery',{}).get('standing_task',{}).get('retention')
            if stand_retention_cfg and stand_retention_cfg.get('enabled'):
                if source is None:raise ValueError('standing retention requires strict source actor')
                from native_stand.recovery.standing import StandingRetention
                teacher=build_model(obs,actor=True,spec=spec).to(env.device)
                teacher.load_state_dict(source['actor'],strict=True)
                standing_retention=StandingRetention(actor,teacher,
                    coefficient=stand_retention_cfg['coefficient'],
                    max_samples=stand_retention_cfg['max_samples_per_rollout'],max_grad_norm=1.,
                    schedule=stand_retention_cfg.get('schedule'),
                    channels=stand_retention_cfg.get('channels','all'),
                    gradient_diagnostics=stand_retention_cfg.get('gradient_diagnostics',False),
                    save_gradient_updates=stand_retention_cfg.get('save_gradient_updates',[]))
                ppo.optimizer.register_step_pre_hook(standing_retention.before_step)
                progress['standing_retention']={**stand_retention_cfg,'teacher_sha256':spec['source_sha256'],
                    'input':'pre-action real policy25/history125; exact zero command and near-standing height',
                    'action_semantics':'source and student use identical physical target scaling'}
            if retention_cfg and retention_cfg.get("enabled"):
                if source is None:
                    raise RuntimeError("retention requires a source checkpoint")
                source_actor=build_model(obs,actor=True,spec=spec).to(env.device)
                source_actor.load_state_dict(initialize_state(source["actor"],
                    source_actor.state_dict(),input_dim=spec.get("source_input_dim",132)),strict=True)
                source_actor.eval()
                reference=load_reference(retention_cfg["reference_path"],
                    expected_sha256=retention_cfg["reference_sha256"])
                reference_eligible_count=len(reference.observations)
                reference=balanced_subset(reference,int(retention_cfg['samples_per_command']))
                reference=RetentionBatch(reference.observations.to(env.device),
                    reference.commands.to(env.device),reference.episode_age_s.to(env.device),reference.metadata)
                attach_optimizer_retention(ppo,source_actor,reference,lam=float(retention_cfg["lambda"]))
                progress["retention"]={"enabled":True,"lambda":float(retention_cfg["lambda"]),
                    "reference":reference.metadata}
            rng_info=seed_training(spec["seed"],source=source,
                restore_source_rng=bool(spec.get("restore_source_rng",False)))
            progress["rng_initialization"]=rng_info
            if (source is not None and spec.get("task")=="recovery"
                    and spec.get("restore_recovery_curriculum",True)):
                recovery_state=source.get("recovery_curriculum")
                if recovery_state is not None and hasattr(env,"restore_recovery_curriculum"):
                    progress["recovery_curriculum_restore"]=env.restore_recovery_curriculum(recovery_state)
            obs,_=wrapped.reset()
            obs=obs.clone()
            if obs["policy"].shape[-1]!=25 or obs["history"].shape[-1]!=125:
                raise RuntimeError("policy/history observation shape differs")
            progress["status"]="RUNNING"
            progress["stage"]="rollout"
            _write(output/"progress.json",progress)
            max_updates=spec["budget"]["formal_updates"] if args.phase=="formal" else spec["budget"]["smoke_updates"]
            current_book=json.loads(args.spec.with_name('budget.json').read_text())
            max_updates=min(max_updates,current_book['limits'][args.phase]-current_book['used'][args.phase])
            initial_actor=[parameter.detach().clone() for parameter in actor.parameters()] if args.phase=='smoke' else None
            critic_warmup_updates=int(spec['ppo'].get('critic_warmup_updates', 0))
            actor_trainability=[(p,p.requires_grad) for p in actor.parameters()]
            if critic_warmup_updates:
                for parameter,_ in actor_trainability:
                    parameter.requires_grad_(False)
                progress['critic_warmup']={'updates':critic_warmup_updates,'active':True}
            pending_serialization=0.
            for update in range(1,max_updates+1):
                phase_wall=(spec["budget"]["smoke_wall_s"] if args.phase=="smoke"
                            else spec["budget"]["formal_wall_s"])
                if phase_wall is None:phase_wall=float('inf')
                if STOP or time.monotonic()-started>=phase_wall-60:
                    outcome="STOPPED_BOUNDED"
                    break
                reward_fields=(("lift","upright","effort","action_delta","joint_margin")
                    if spec.get('task')=='recovery' else ("upright","height","velocity_tracking",
                    "two_wheel_contact","effort","action_delta","joint_margin"))
                if spec.get('task')=='recovery' and spec['recovery'].get('settling_reward'):
                    fields=('settling_linear','settling_angular') if spec['recovery']['settling_reward'].get('kind')=='pseudo_huber' else ('settling_motion',)
                    reward_fields=(*reward_fields,*fields)
                    if 'settling_yaw_weight' in spec['recovery']['settling_reward']:
                        reward_fields=(*reward_fields,'settling_yaw')
                if spec.get('task')=='recovery' and 'height_overshoot' in spec['reward']:
                    reward_fields=(*reward_fields,'height_overshoot')
                if spec.get('task')=='recovery' and 'pitch_level' in spec['reward']:
                    reward_fields=(*reward_fields,'pitch_level')
                if spec.get('task')=='recovery' and 'roll_level' in spec['reward']:
                    reward_fields=(*reward_fields,'roll_level')
                if spec.get('task')=='recovery':
                    reward_fields=(*reward_fields,*tuple(name for name in
                        ('support','low_height_wheel_spin','leg_symmetry','support_balance',
                         'support_region','slip_proxy','wheel_longitudinal_offset') if name in spec['reward']))
                    if spec['recovery'].get('standing_task'):
                        from native_stand.recovery.standing import REWARD_FIELDS
                        reward_fields=(*reward_fields,*REWARD_FIELDS)
                metric=RolloutMetrics(reward_fields,
                    ("nonfinite","closure","height","tilt","body_contact","joint_safety"),
                    env.num_envs,env.device)
                rollout_start=time.monotonic()
                command_begin=env.command_counts.clone()
                env.begin_task_rollout()
                from native_stand.command_v6.domain.selected_diagnostics import selected,storage_summary,GradientSummary,summarize_tensor,PolicyUpdateSummary
                diagnostics_selected=selected(spec,update)
                diagnostic_config=spec.get('diagnostics',{})
                if retention_cfg and retention_cfg.get('enabled'):
                    ppo._record_retention_diagnostics=diagnostics_selected and diagnostic_config.get('record_retention_summary',False)
                    ppo._reference_gradient=None
                reward_total=torch.zeros((),device=env.device) if diagnostics_selected else None
                diagnostic_durations=[]
                diagnostic_counts=torch.zeros(3,device=env.device,dtype=torch.long) if diagnostics_selected else None
                if standing_retention is not None:
                    standing_retention.begin_rollout(update,phase=args.phase)
                    standing_retention.gradient_diagnostics=(stand_retention_cfg.get('gradient_diagnostics',False) or
                        diagnostics_selected and diagnostic_config.get('record_retention_summary',False))
                inference_host_s=0.
                with torch.inference_mode():
                    for _ in range(spec["ppo"]["steps_per_env"]):
                        t=time.monotonic()
                        if standing_retention is not None:
                            eligible=((env.command[:,:2]==0.).all(-1) &
                                (env.root_height>=stand_retention_cfg['height_min_m']) &
                                (env.root_height<=stand_retention_cfg['height_max_m']) &
                                env.initialization_checked)
                            metadata=(torch.cat((env.episode_length_buf[:,None]*env.step_dt,env.command[:,:2]),-1)
                                if diagnostics_selected and diagnostic_config.get('record_retention_summary') else None)
                            standing_retention.capture(obs,eligible,metadata=metadata)
                        action=ppo.act(obs)
                        inference_host_s+=time.monotonic()-t
                        episode_before=env.episode_length_buf.clone()
                        obs,reward,dones,extras=wrapped.step(action.to(env.device).clone())
                        obs=obs.clone()
                        if diagnostics_selected:
                            reward_total.add_(reward.sum())
                            diagnostic_durations.append(torch.where(dones.bool().reshape(-1),
                                (episode_before+1)*env.step_dt,torch.nan))
                            done_mask=dones.bool().reshape(-1)
                            if spec.get('task')=='recovery':
                                diagnostic_counts.add_(torch.stack((env.recovery_snapshot[:,2].bool().sum(),
                                    env.recovery_snapshot[:,3].bool().sum(),torch.zeros((),device=env.device,dtype=torch.long))))
                            else:
                                timeouts=extras.get('time_outs',torch.zeros_like(done_mask)).bool().reshape(-1)
                                diagnostic_counts.add_(torch.stack((torch.zeros((),device=env.device,dtype=torch.long),
                                    (done_mask & ~timeouts).sum(),timeouts.sum())))
                        if not bool(torch.isfinite(reward).all()) or not bool(torch.isfinite(obs["policy"]).all()):
                            raise RuntimeError("nonfinite rollout reward or observation")
                        if bool(env.terminal_causes["nonfinite"].any()) or bool(env.terminal_causes["closure"].any()):
                            raise RuntimeError("native physics runtime fault")
                        motion=None
                        if env.episode_tracker is not None:
                            motion=env.training_motion
                        metric.add(env.reward_raw,env.reward_weighted,env.terminal_causes,
                            env.contact_force>2.,env.closure_each,env.effort,EFFORT_LIMITS,
                            (episode_before+1).double()*env.step_dt,dones.bool(),motion)
                        ppo.process_env_step(obs,reward,dones,extras)
                    ppo.compute_returns(obs)
                rollout_s=time.monotonic()-rollout_start
                selected_summary=storage_summary(storage) if selected(spec,update) and spec.get('diagnostics',{}).get('record_ppo_summary') else None
                gradient_observer=GradientSummary(actor,critic,ppo.optimizer) if selected_summary is not None else None
                policy_probe=PolicyUpdateSummary(actor,storage,ppo.clip_param) if selected_summary is not None else None
                t=time.monotonic()
                try:losses=ppo.update()
                finally:
                    if gradient_observer is not None:gradient_observer.close()
                ppo_s=time.monotonic()-t
                if critic_warmup_updates and update >= critic_warmup_updates:
                    for parameter,requires_grad in actor_trainability:
                        parameter.requires_grad_(requires_grad)
                    progress['critic_warmup']['active']=False
                    progress['critic_warmup']['released_after_update']=update
                    critic_warmup_updates=0
                progress["actual_updates"]=ledger.charge(attempt_id,output)
                progress["samples"]=progress["actual_updates"]*env.num_envs*spec["ppo"]["steps_per_env"]
                values={name:float(value) for name,value in losses.items()}
                if retention_cfg and retention_cfg.get('enabled'):
                    values['retention_raw']=ppo._last_retention_raw
                    values['retention_weighted']=ppo._last_retention_loss
                if not all(bool(torch.isfinite(parameter).all()) for parameter in actor.parameters()):
                    raise RuntimeError('nonfinite actor parameters')
                if not all(__import__("math").isfinite(value) for value in values.values()):
                    raise RuntimeError("nonfinite PPO loss")
                summary=metric.summary()
                task_summary=env.task_rollout_summary()
                if diagnostics_selected:
                    durations=torch.cat(diagnostic_durations)
                    durations=durations[torch.isfinite(durations)]
                    retention_summary=None
                    if standing_retention is not None and diagnostic_config.get('record_retention_summary'):
                        metadata=standing_retention.selected_metadata
                        retention_summary={'eligible':int(standing_retention.eligible_count) if standing_retention.eligible_count is not None else None,
                            'selected':standing_retention.selected,
                            'episode_age':summarize_tensor(metadata[:,0]) if metadata is not None else None,
                            'command_counts':(torch.unique(metadata[:,1:3],dim=0,return_counts=True)[1].cpu().tolist() if metadata is not None else None),
                            'commands':(torch.unique(metadata[:,1:3],dim=0).cpu().tolist() if metadata is not None else None),
                            'channel_mse':standing_retention.channel_error.cpu().tolist() if standing_retention.channel_error is not None else None,
                            'gradient_comparison':standing_retention.summary().get('gradient_comparison')}
                    elif retention_cfg and retention_cfg.get('enabled') and diagnostic_config.get('record_retention_summary'):
                        with torch.no_grad():
                            from tensordict import TensorDict
                            ref_obs=TensorDict({'policy':reference.observations[:,:25],
                                'history':reference.observations[:,25:]},batch_size=[len(reference.observations)])
                            channel_error=(actor(ref_obs,stochastic_output=False)-
                                source_actor(ref_obs,stochastic_output=False)).square().mean(0)
                        commands,counts=torch.unique(reference.commands,dim=0,return_counts=True)
                        gradient_probe=getattr(ppo,'_reference_gradient',None)
                        gradient_values=gradient_probe.cpu().tolist() if gradient_probe is not None else None
                        retention_summary={'eligible':reference_eligible_count,'selected':len(reference.observations),
                            'episode_age':summarize_tensor(reference.episode_age_s),'commands':commands.cpu().tolist(),
                            'command_counts':counts.cpu().tolist(),'channel_mse':channel_error.cpu().tolist(),
                            'scope':'frozen reference selection; channel error measured after actual update',
                            'gradient_comparison':({name:value if __import__('math').isfinite(value) else None
                                for name,value in zip(('ppo_actor_norm','bc_raw_norm','bc_weighted_norm','cosine',
                                    'weighted_norm_ratio','reference_weighted_norm','reference_norm_ratio'),gradient_values)}
                                if gradient_values is not None else None),
                            'gradient_scope':'first real optimizer step; PPO+entropy after clipping, reference BC before addition'}
                    _write(output/f'diagnostics_update_{update}.json',{'update':update,
                        'provenance':'online selected update','reward_total':float(reward_total.cpu()),
                        'rollout':summary if diagnostic_config.get('record_reward_components') else None,
                        'episode_duration':summarize_tensor(durations),'task_counts':task_summary.get('counts') if isinstance(task_summary,dict) else None,
                        'event_counts':dict(zip(('success','failure','timeout'),diagnostic_counts.cpu().tolist())),
                        'event_semantics':'Recovery timeout is task failure; native timeout is reported independently',
                        'policy_update':policy_probe.summary(actor) if policy_probe is not None else None,
                        'storage':selected_summary,'gradients':gradient_observer.summary() if gradient_observer is not None else None,
                        'retention':retention_summary,'losses':values})
                if standing_retention is not None:
                    task_summary['standing_retention']=standing_retention.summary()
                    if (update in stand_retention_cfg.get('save_gradient_updates',[]) and
                            standing_retention.gradient_payload is not None):
                        payload={**standing_retention.gradient_payload,'update':update,'phase':args.phase,
                            'source_sha256':spec['source_sha256'],'spec_sha256':digest(args.spec)}
                        torch.save(payload,output/f'bc_gradient_update_{update}.pt')
                episode_summary=env.collect_episode_curriculum()
                if episode_summary:
                    with (output/'curriculum_windows.jsonl').open('a') as handle:
                        for window in episode_summary['windows']:
                            handle.write(json.dumps({'update':update,**window})+'\n')
                    progress['episode_curriculum']=episode_summary['state']
                progress["latest_metric"]={"update":update,"rollout_s":rollout_s,
                    "policy_inference_host_s":inference_host_s,"ppo_s":ppo_s,
                    "evaluation_s":0.,"serialization_s":pending_serialization,
                    "samples_per_s":env.num_envs*spec["ppo"]["steps_per_env"]/rollout_s,
                    "losses":values,"rollout":summary,
                    "episode_curriculum":episode_summary,
                    "task_stage":(env.reverse_curriculum.stage
                                   if spec.get('task')=='recovery' and env.reverse_curriculum is not None
                                   else stage),"task_metrics":task_summary,
                    "command_counts":env.command_counts.cpu().tolist(),
                    "command_sample_counts":(env.command_counts-command_begin).cpu().tolist()}
                if spec.get('task')=='recovery':
                    progress['latest_metric']['recovery_initialization']=env.initialization_summary()
                plan=schedule(update,args.phase,spec["evaluation"])
                if args.phase=='smoke' and update==max_updates:
                    plan['light']=True
                if spec.get('straight_high_speed_course') and args.phase=='smoke' and update==max_updates:
                    plan['full']=True
                if task_manager is not None and args.phase=='formal' and update==max_updates:
                    plan['full']=True
                if (spec.get('task')=='recovery' and args.phase=='formal' and update==max_updates
                        and spec['evaluation'].get('full_at_final')):
                    plan['full']=True
                if task_manager is not None:
                    progress['task_curriculum']=task_manager.state()
                    if (args.phase=='formal' and stage==0 and update>=task_config['earliest_confirmation_update']
                            and update-last_confirmation>=task_config['confirmation_spacing_updates']
                            and episode_summary and any(x['passed'] for x in episode_summary['windows'])
                            and update%spec['evaluation']['full_every_updates']<
                                spec['evaluation']['full_every_updates']-task_config['merge_nearby_updates']):
                        plan['full']=True
                serialization_s=0.
                if plan["checkpoint"] or plan['full'] or plan['light'] or update==max_updates:
                    save_start=time.monotonic()
                    path=output/spec["artifacts"]["checkpoint_name"].format(update=update)
                    torch.save({"actor":actor.state_dict(),"critic":critic.state_dict(),
                        "optimizer":ppo.optimizer.state_dict(),"cpu_rng":torch.get_rng_state(),
                        "cuda_rng":torch.cuda.get_rng_state_all(),"update":update,
                        "source_sha256":spec["source_sha256"],
                        "spec_sha256":digest(args.spec),"asset_sha256":spec["asset_sha256"],
                        "parameter_names":{'actor':list(dict(actor.named_parameters())),
                                           'critic':list(dict(critic.named_parameters()))},
                        "task_curriculum":task_manager.state() if task_manager else None,
                        "recovery_curriculum":(env.recovery_curriculum_checkpoint_state()
                            if spec.get('task')=='recovery' and hasattr(env,'recovery_curriculum_checkpoint_state') else None)},path)
                    progress["latest_checkpoint"]={"path":str(path),"sha256":digest(path),
                        "update":update}
                    inventory=json.loads((output/'checkpoint_inventory.json').read_text()) if (output/'checkpoint_inventory.json').is_file() else []
                    inventory.append(progress['latest_checkpoint'])
                    _write(output/'checkpoint_inventory.json',inventory)
                    serialization_s+=time.monotonic()-save_start
                if plan["light"] or plan["full"]:
                    progress['stage']='milestone_evaluation'
                    t=time.monotonic()
                    serialization_before_eval=serialization_s
                    evaluations=[]
                    task_cases=[]
                    for command in spec["curriculum"]["stages"][stage]["commands"]:
                        if spec.get('straight_high_speed_course'):
                            eval_identity={**eval_identity,'course_stage':stage,
                                'capability_commands':spec['curriculum']['stages'][stage]['commands']}
                        with preserve_rng_state():
                            result=evaluate_actor(actor,wrapped,env,target=command,
                            seconds=evaluation_seconds(spec,full=plan['full']),
                            full_trace=(plan['full'] and (not spec.get('recovery',{}).get('standing_task') or
                                                         update==max_updates)),seed=spec["evaluation"]["seed"],
                            scored_envs=spec["evaluation"]["scored_envs"],
                            target_window=((spec['evaluation'].get('motion_window_s',[2.,8.]) if command!=[0,0] else spec["evaluation"]["steady_window_s"]) if plan["full"]
                                           else spec["evaluation"]["light_window_s"]),
                            standing_protocol=spec["evaluation"] if plan["full"] else None,
                                stop_requested=lambda:STOP or time.monotonic()-started>=phase_wall-60)
                        if (spec.get('recovery',{}).get('standing_task') and plan['full'] and
                                env.reverse_curriculum is not None):
                            from native_stand.command_v6.domain.evidence import resolve_gate
                            validated=resolve_gate(result,'recovery',expected_envs=spec['evaluation']['scored_envs'],
                                expected_protocol=eval_identity['effective_protocols']['zero'])
                            if not validated['candidate_eligible']:
                                raise RuntimeError('evaluation evidence identity fault: '+str(validated))
                            env.reverse_curriculum.confirm_evaluation(stage=env.reverse_curriculum.stage,
                                accepted=result['accepted'],continuous_s=spec['evaluation']['seconds'])
                        if standing_regression is not None:
                            retained=result.get('retained_evaluations',[])
                            retention_accepted=all(row['accepted'] for row in retained) if retained else result['accepted']
                            stop_regression=standing_regression.observe(accepted=retention_accepted,
                                full=plan['full'],continuous_s=evaluation_seconds(spec,full=plan['full']))
                            progress['standing_regression']={'confirmed':standing_regression.confirmed,
                                'consecutive_failures':standing_regression.failures,
                                'scope':'retained_R0' if retained else 'current_family'}
                            if stop_regression:
                                progress['early_stop_reason']='standing regressed in two consecutive full evaluations'
                        if command!=[0,0] and plan['full'] and spec['evaluation'].get('protocol_identity')!='capability_v2':
                            movement_protocol={**spec['evaluation'],
                                'vx_error_max_mps':max(spec['evaluation']['motion_vx_error_max_mps'],abs(command[0])*spec['evaluation'].get('relative_motion_error_fraction',0)),
                                'yaw_error_max_rad_s':max(spec['evaluation']['motion_yaw_error_max_rad_s'],abs(command[1])*spec['evaluation'].get('relative_motion_error_fraction',0))}
                            result['motion_gate']=motion_gate(result,command,movement_protocol)
                        from native_stand.command_v6.domain.evidence import resolve_gate
                        gate_task=('recovery' if result.get('task')=='recovery' else
                            'capability' if spec['evaluation'].get('protocol_identity')=='capability_v2' else
                            'standing' if command==[0,0] else 'motion')
                        gate_evidence=resolve_gate(result,gate_task,expected_envs=spec['evaluation']['scored_envs'],
                            expected_protocol=eval_identity.get('effective_protocols',{}).get('zero' if command==[0,0] else 'motion') if plan['full'] else None)
                        if plan['full'] and not gate_evidence['candidate_eligible']:
                            raise RuntimeError('evaluation evidence identity fault: '+str(gate_evidence))
                        gate=(result.get('recovery_gate') if result.get('task')=='recovery' else result.get('capability_gate') if spec['evaluation'].get('protocol_identity')=='capability_v2'
                              else result.get('standing_gate') if command==[0,0] else result.get('motion_gate'))
                        if gate is not None:
                            task_cases.append({'command':command,'gate':gate})
                        label=f"evaluation_{update}_{command[0]}_{command[1]}.json"
                        result.update(checkpoint=str(path.resolve()),checkpoint_sha256=digest(path),
                            source_sha256=spec['source_sha256'],asset_sha256=spec['asset_sha256'],
                            spec_sha256=digest(args.spec))
                        write_start=time.monotonic()
                        _write(output/label,result)
                        registry.append({'role':'candidate','kind':('full' if plan['full'] else 'light') if command==[0,0] or spec['evaluation'].get('protocol_identity')=='capability_v2' else 'motion',
                            'checkpoint':str(path),'checkpoint_sha256':digest(path),'update':update,
                            'identity':eval_identity,'evaluation':label,'result':{**result,'per_env':[
                                {key:value for key,value in row.items() if key not in (
                                    'trace','compact_trace_100hz','posture_trace_100hz',
                                    'gate_diagnostics_100hz','control_diagnostics_100hz','failure_window_100hz',
                                    'failure_posture_window_100hz')}
                                for row in result['per_env']]}})
                        _write(output/'candidate_registry.json',registry)
                        serialization_s+=time.monotonic()-write_start
                        evaluations.append({"command":command,"path":label,
                            "outcome_counts":result["outcome_counts"],
                            "standing_gate":result.get("standing_gate"),"gate_evidence":gate_evidence})
                        local_selection=choose(registry+baseline_registry,progress['latest_checkpoint'],eval_identity)
                        best=local_selection['best_observed_candidate']
                        progress['best_standing_candidate']=({key:best[key] for key in
                            ('checkpoint','checkpoint_sha256','update','accepted','passed_envs')} if best else None)
                    progress["evaluations"].append({"update":update,
                        "kind":"full" if plan["full"] else "light","cases":evaluations})
                    if task_manager is not None and plan['full']:
                        last_confirmation=update
                        event=task_manager.confirm(update,task_cases,
                            new_commands=spec['curriculum']['stages'][stage]['boundary'],
                            episode_length_s=env.episode_windows.config['lengths_s'][env.episode_windows.level]
                            if env.episode_windows else env.cfg.episode_length_s)
                        with (output/'task_confirmations.jsonl').open('a') as handle:
                            handle.write(json.dumps(event)+'\n')
                        progress['task_curriculum']=task_manager.state()
                        if stage>0 and event['passed']:
                            progress['best_motion_candidate']={'checkpoint':str(path),'sha256':digest(path),
                                'stage':stage,'update':update,'cases':task_cases}
                            progress['accepted_by_stage'][str(stage)]={'checkpoint':str(path),
                                'sha256':digest(path),'stage':stage,'update':update,'cases':task_cases}
                        if event.get('promoted'):
                            stage=event['next_stage']
                            stage_start_update=update
                            env.change_stage(spec['curriculum']['stages'][stage],
                                linear_denominator=spec['reward']['stage_linear_denominators'][str(stage)],
                                yaw_denominator=spec['reward']['stage_yaw_denominators'][str(stage)])
                        if event['stop']:
                            progress['early_stop_reason']='learned or zero-command regression in consecutive full confirmations'
                        if event['stage']==task_config['max_enabled_stage'] and event['passed'] and not spec.get('cohort_width_ab'):
                            if spec.get('straight_high_speed_course'):
                                final_cases=[]
                                for final_seed in spec['evaluation']['final_evaluation_seeds']:
                                    for final_command in spec['curriculum']['stages'][stage]['commands']:
                                        with preserve_rng_state():
                                            final_result=evaluate_actor(actor,wrapped,env,target=final_command,
                                                seconds=evaluation_seconds(spec,full=True),full_trace=True,
                                                seed=final_seed,scored_envs=spec['evaluation']['scored_envs'],
                                                target_window=spec['evaluation']['motion_window_s'] if final_command!=[0,0] else spec['evaluation']['steady_window_s'],
                                                standing_protocol=spec['evaluation'],
                                                stop_requested=lambda:STOP or time.monotonic()-started>=phase_wall-60)
                                        label=f'final_seed_{final_seed}_{final_command[0]}_{final_command[1]}.json'
                                        final_result.update(checkpoint_sha256=digest(path),spec_sha256=digest(args.spec),
                                            evaluator_sha256=evaluator_sha,seed=final_seed)
                                        _write(output/label,final_result)
                                        final_cases.append({'seed':final_seed,'command':final_command,
                                            'evaluation':label,'gate':final_result['capability_gate']})
                                progress['final_capability_certificate']={'checkpoint':str(path),'sha256':digest(path),
                                    'accepted':all(case['gate']['accepted'] for case in final_cases),'cases':final_cases}
                                _write(output/'final_capability_certificate.json',progress['final_capability_certificate'])
                            progress['early_stop_reason']=('final multi-seed certification failed' if
                                spec.get('straight_high_speed_course') and not progress['final_capability_certificate']['accepted']
                                else 'all capability stages independently passed')
                        if (not event.get('promoted') and update-stage_start_update>=
                                task_config.get('max_updates_per_stage',max_updates)):
                            progress['early_stop_reason']='stage update budget exhausted'
                    if plan['full'] and spec.get('safety_stop_commands'):
                        protected={tuple(command) for command in spec['safety_stop_commands']}
                        for case in task_cases:
                            if tuple(case['command']) in protected and not case['gate']['accepted']:
                                progress['early_stop_reason']=f"protected command failed: {case['command']}"
                            if tuple(case['command'])==(0.5,0.) and any(
                                    'command_direction' in row['failed_checks']
                                    for row in case['gate']['per_env']):
                                progress['early_stop_reason']='forward command direction regressed'
                    progress["latest_metric"]["evaluation_s"]=time.monotonic()-t-(serialization_s-serialization_before_eval)
                    obs,_=wrapped.reset()
                    obs=obs.clone()
                progress["stage"]="rollout"
                t=time.monotonic()
                progress['latest_metric'].update(actual_update=progress['actual_updates'],
                    cumulative_samples=progress['samples'],
                    optimizer_learning_rates=[group['lr'] for group in ppo.optimizer.param_groups])
                if initial_actor is not None:
                    progress['actor_parameters_changed']=any(bool((before!=after).any())
                        for before,after in zip(initial_actor,actor.parameters()))
                progress['latest_metric']['serialization_s']=serialization_s
                _write(output/"progress.json",progress)
                progress['latest_metric']['serialization_s']=serialization_s+time.monotonic()-t
                update_elapsed=sum(progress['latest_metric'][key] for key in
                                   ('rollout_s','ppo_s','evaluation_s','serialization_s'))
                progress['latest_metric']['update_end_to_end_samples_per_s']=summary['samples']/update_elapsed
                with (output/'metrics.jsonl').open('a') as handle:
                    handle.write(json.dumps(progress['latest_metric'],allow_nan=False)+'\n')
                if update==1:
                    handshake({"status":"RUNNING","attempt_id":attempt_id,
                        "trainer_pid":os.getpid(),"actual_updates":1,
                        "output_dir":str(output.resolve())})
                pending_serialization=0.
                if progress.get('early_stop_reason'):
                    outcome='STOPPED_BOUNDED'
                    break
            else:
                outcome="COMPLETED"
        progress["status"]=outcome
        progress["stage"]="finished"
    except BaseException as exc:
        if getattr(exc,'evaluation_evidence',None) is not None:
            progress['interrupted_evaluation']=exc.evaluation_evidence
        if isinstance(exc,TimeoutError) and (STOP or time.monotonic()-started>=phase_wall-60):
            progress['early_stop_reason']=str(exc)
            outcome='STOPPED_BOUNDED'
            progress['status']=outcome
        else:
            failure={"exception":repr(exc),"traceback":traceback.format_exc(),
                     "failure_stage":progress["stage"],
                     "evaluation_evidence":getattr(exc,'evaluation_evidence',None)}
            progress.update(status="FAILED",**failure)
            outcome="FAILED"
    finally:
        if (output.is_dir() and outcome=='STOPPED_BOUNDED' and ppo is not None and
                progress['actual_updates']>0 and (progress['latest_checkpoint'] is None or
                progress['latest_checkpoint']['update']!=progress['actual_updates'])):
            update=progress['actual_updates']
            path=output/spec['artifacts']['checkpoint_name'].format(update=update)
            torch.save({'actor':actor.state_dict(),'critic':critic.state_dict(),'optimizer':ppo.optimizer.state_dict(),
                'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all(),'update':update,
                'source_sha256':spec['source_sha256'],'spec_sha256':digest(args.spec),
                'asset_sha256':spec['asset_sha256'],'episode_curriculum':progress.get('episode_curriculum'),
                'recovery_curriculum':(env.recovery_curriculum_checkpoint_state()
                    if spec.get('task')=='recovery' and env is not None and hasattr(env,'recovery_curriculum_checkpoint_state') else None)},path)
            progress['latest_checkpoint']={'path':str(path),'sha256':digest(path),'update':update}
            inventory=json.loads((output/'checkpoint_inventory.json').read_text()) if (output/'checkpoint_inventory.json').is_file() else []
            inventory.append(progress['latest_checkpoint'])
            _write(output/'checkpoint_inventory.json',inventory)
        report={"status":outcome,"attempt_id":attempt_id,"phase":args.phase,
                "exit_code":1 if failure else 0,
                "actual_updates":progress["actual_updates"],"samples":progress["samples"],
                "wall_s":time.monotonic()-started,"failure":failure,
                "source_evaluation_s":progress.get('source_evaluation_s'),
                "initialization_s":progress.get('initialization_s'),
                "episode_curriculum":progress.get('episode_curriculum'),
                "evaluations":progress["evaluations"],
                "interrupted_evaluation":progress.get('interrupted_evaluation'),
                "latest_checkpoint":progress["latest_checkpoint"],
                "task_curriculum":progress.get('task_curriculum'),
                "best_motion_candidate":progress.get('best_motion_candidate'),
                "accepted_by_stage":progress.get('accepted_by_stage'),
                "final_capability_certificate":progress.get('final_capability_certificate'),
                "early_stop_reason":progress.get('early_stop_reason'),
                "best_standing_candidate":progress["best_standing_candidate"]}
        report['stop_kind']='user_signal' if STOP else ('exception' if failure else 'budget_or_completion')
        settle_attempt(output,progress,report,ledger,attempt_id)
        handshake({"status":outcome,"attempt_id":attempt_id,
            "trainer_pid":os.getpid(),"actual_updates":progress["actual_updates"],
            "output_dir":str(output.resolve()),"terminal_report":str(output/"terminal_report.json")})
        if args.handshake_fd is not None:
            os.close(args.handshake_fd)
        if env is not None:
            env.close()
        if app is not None:
            close_app(app, failure is not None)
    if failure:
        raise RuntimeError(failure["exception"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
