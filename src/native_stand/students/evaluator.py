"""Student and explicit teacher controls under public supervisor/monitor (PPO0)."""
import copy,json,time,traceback
from pathlib import Path
import numpy as np
from .data import sha
from .requests import plan
from .protocol import score as student_score

def environment(spec,role,*,envs=64,teacher=False,student_handoff=False,initial_family=None,autonomous_preview=False,preview_episode_length_s=None):
    """Imported only after AppLauncher. Shared scene/PD; no student teacher forwards."""
    if autonomous_preview and (envs!=1 or teacher or student_handoff):raise ValueError('autonomous preview requires one student, without handoff/teacher')
    import torch
    from native_stand.command_v6.runtime.env import CommandEnvCfg
    from native_stand.command_v6.runtime.configure import apply
    from native_stand.recovery.handoff_runtime import HandoffEnv
    from .runtime import StudentEnv,TrainingStudentEnv
    motion_training=spec.get('student_training',{}).get('version')=='student_motion31_training_v1'
    cfg=apply(CommandEnvCfg(),spec,envs=envs,mode='evaluation')
    if autonomous_preview and preview_episode_length_s is not None:
        # Manual preview runs until the window closes; scoring time-phases stay untouched.
        cfg.episode_length_s=float(preview_episode_length_s)
    recovery=copy.deepcopy(spec['recovery']);recovery.pop('support_record_reward',None);recovery.pop('drawback_guidance',None)
    library=json.loads(Path(recovery['pose_library']).read_text())
    if initial_family is not None:
        from .requests import evaluation_recovery
        recovery=evaluation_recovery(recovery,library['poses'],initial_family)
    # A sentinel catches any accidental legacy stand-policy execution.
    class ForbiddenTeacher(torch.nn.Module):
        def forward(self,*args,**kwargs):raise RuntimeError('teacher control forbidden in autonomous student environment')
    cls=HandoffEnv if teacher else TrainingStudentEnv if spec.get('student_training') or spec.get('student_survival_probe') or spec.get('student_motion_validation') else StudentEnv
    if student_handoff:
        from .handoff_runtime import StudentMotionProbeEnv
        cls=StudentMotionProbeEnv
    if motion_training:
        from .motion_runtime import MotionStudentEnv
        cls=MotionStudentEnv
        from .motion_tracking_reward import QUALITY_VERSIONS
        if spec['reward']['version'] in QUALITY_VERSIONS:
            from .motion_quality_runtime import QualityMotionStudentEnv
            cls=QualityMotionStudentEnv
    if teacher:cfg.leg_position_scale_rad=1.6
    extra={} if teacher or student_handoff else {'student_role':role,'interface_version':spec.get('interface_version','multiskill_student_v1')}
    if not teacher and not student_handoff and spec.get('student_survival_probe'):
        extra.update(student_reward_configuration=spec['reward'],critic_privileged_version='standing_privileged49_v1',student_command_height=.34)
    if not teacher and not student_handoff and spec.get('student_training'):
        extra['student_reward_configuration']=spec['reward']
        extra['critic_privileged_version']=spec['student_training'].get('critic_privileged_version')
    if motion_training:
        from .standing_survival_reward import configuration as clock_reward
        extra['student_reward_configuration']=clock_reward();extra['critic_privileged_version']='standing_privileged49_v1'
        extra['motion_training_config']=spec['student_training']
    if spec.get('student_motion_validation'):
        extra.update(student_reward_configuration=spec['reward'],critic_privileged_version='standing_privileged49_v1',student_command_height=.34)
    if not teacher and spec.get('student_training',{}).get('target_height_m') is not None:extra['student_command_height']=spec['student_training']['target_height_m']
    if not teacher and not student_handoff and spec.get('student_training',{}).get('standing_rehearsal'):extra['standing_rehearsal_configuration']=spec['student_training']['standing_rehearsal']
    if not teacher and not autonomous_preview and spec.get('recovery_course',{}).get('state',{}).get('stage') in ('B','CONSOLIDATE'):
        from .course_runtime import CourseStudentEnv
        cls=CourseStudentEnv
        extra.update(course_configuration=spec['recovery_course'],teacher_actors=teacher_models(spec,'cuda:0'))
    stage=spec['curriculum']['stages'][0]
    if motion_training:
        from .motion_training import stage_config,preview_stage_config
        if autonomous_preview:
            # One environment: training slots and the unlocked whitelist are never reused.
            stage=preview_stage_config(spec['motion_training']['stage'])
        elif spec.get('motion_course'):
            from .motion_course import implementation
            course_stage=implementation(spec['student_training']['course_version']).stage_config
            stage=course_stage(spec['motion_training']['stage'],envs)
        else:stage=stage_config(spec['motion_training']['stage'],envs)
    env=cls(cfg,recovery_config=recovery,pose_library=library,stand_policy=ForbiddenTeacher(),
        stage=stage,command_height=.36,reward_config={} if spec.get('student_training') or student_handoff else spec['reward'],schedule_s=spec['curriculum']['schedule_s'],**extra)
    if spec.get('student_survival_probe'):
        from .survival_probe import SurvivalObserver
        env.rise_hold=SurvivalObserver(env.num_envs,env.device);env.survival_probe=True
    env.curriculum_training=False
    if spec.get('motion_confirmation') or spec.get('motion_training',{}).get('early_stop_policy'):
        from .motion_guard import protocol as guard_protocol
        forward=spec.get('student_training',{}).get('course_version')=='motion31_forward_progression_v1'
        if forward:
            from .motion_forward_course import protocol as guard_protocol
        if spec['motion_assessment']!=guard_protocol():raise ValueError('absolute posture protocol mismatch')
        env.motion_absolute_protocol=guard_protocol()
        env.motion_forward_course=forward
    from .performance import settings
    env.student_performance=settings(spec)
    if spec.get('student_motion_validation'):
        env.motion_validation=True;env.student_motion_command=[0.,0.,.34]
    if autonomous_preview and motion_training:
        env.enable_motion_preview()
    return env

def teacher_models(spec,device):
    import torch
    from tensordict import TensorDict
    from native_stand.command_v6.tools.model_factory import model
    models=[];dummy=TensorDict({'policy':torch.zeros(64,25,device=device),'history':torch.zeros(64,125,device=device)},batch_size=[64])
    for teacher in spec['student_teachers']:
        frozen=json.loads(Path(teacher['spec']).read_text());m=model(dummy,actor=True,spec=frozen).to(device)
        m.load_state_dict(torch.load(teacher['checkpoint'],map_location=device,weights_only=False)['actor']);m.eval();m.requires_grad_(False);models.append(m)
    return models

def _rollout(env,actor,row,*,teacher=None,stop=None,scored_envs=8):
    """One first episode/env. Student branch never evaluates a teacher."""
    import torch
    from .interface import LEGS
    from native_stand.recovery.domain import Mode
    from native_stand.recovery.motion_handoff import score as teacher_score
    from native_stand.recovery.handoff_protocol import declaration as teacher_protocol
    torch.manual_seed(row['seed']);env.select_initial_family(row['family'],'holdout')
    if teacher:
        env.configure_case({'switch_s':.5 if row['kind']=='teacher_combination' else 0.,'kind':'normal_motion_baseline' if row['kind']=='teacher_normal' else 'recovery_prefix_then_motion'})
        env.configure_randomization({'version':'reset_yaw_v1','root_yaw_rad':row['yaw_rad'],'distribution':'uniform'});env.configure_protocol(teacher_protocol())
    else:
        if getattr(env,'motion_validation',False):env.student_motion_command=row['command']
        if getattr(env,'motion_training_enabled',False):env.set_evaluation_target(*row['command'][:2])
        if row.get('command_height_m') is not None:
            env.student_command_height=row['command_height_m']
        env.student_yaw_amplitude=row['yaw_rad']
        if hasattr(env,'configure_evaluation'):env.configure_evaluation(row['family'],row.get('prefix_s',0.))
    obs,_=env.reset();active=torch.ones(scored_envs,device=env.device,dtype=torch.bool);buffers={};valid=[];n=env.num_envs
    from .performance import DeviceTrace
    perf=getattr(env,'student_performance',{})
    trace=DeviceTrace(round(row['seconds']/.01),perf.get('trace_buffer_max_bytes',256*2**20)) if perf.get('evaluation_gpu_buffer') else None
    env.student_trace_capture={'buffers':buffers,'valid':valid,'device_trace':trace}
    def add(k,v):
        if trace is not None:trace.add(k,v[:scored_envs])
        else:buffers.setdefault(k,[]).append(v[:scored_envs].detach().cpu().numpy().copy())
    with torch.inference_mode():
      for step in range(round(row['seconds']/.01)):
        if stop and stop():raise TimeoutError('Student evaluation wall budget exhausted')
        initial=env.fsm.mode==int(Mode.INITIALIZING);controlled=(~initial)&env.initialization_checked
        if hasattr(env,'actor_valid_pre'):controlled=env.actor_valid_pre()
        action=torch.zeros(n,6,device=env.device)
        if teacher:
            motion=(~initial)&(env.executed_prefix>=env.switch_steps);rec=(~initial)&~motion
            if rec.any():action[rec]=teacher[0]({k:v[rec] for k,v in obs.items()},stochastic_output=False)
            if motion.any():action[motion]=teacher[1]({k:env.motion_obs[k][motion] for k in ('policy','history')},stochastic_output=False)
            add('actor_input',torch.cat((obs['policy'],obs['history']),-1))
        else:
            # Evaluate only student. Sampling is deterministic, no teacher rescue.
            if getattr(env,'motion_training_enabled',False):
                from .motion_training import effective
                expected=effective(env.target_xy,env.rise_hold.episode.steps.float()*.01)
                observed=obs['student_actor']
                if not torch.allclose(observed[:,22:25],expected/expected.new_tensor([4.,4.,.5]),atol=1e-6,rtol=0) or not torch.all(observed[:,25]==1) or not torch.all(observed[:,26]==0):
                    raise RuntimeError('Motion command/Actor readback mismatch')
                add('effective_command_pre',expected)
            if controlled.any():action[controlled]=actor({k:v[controlled] for k,v in obs.items()},stochastic_output=False)
            add('actor_input',obs['student_actor']);add('critic_input',obs['student_critic'])
            if hasattr(env,'compose_training_action'):
                action=env.compose_training_action(action)
                for i,tobs in enumerate(env.teacher_obs):
                    add('teacher_'+str(i)+'_input',torch.cat((tobs['policy'],tobs['history']),-1))
        add('root_pre',env.robot.data.root_state_w.torch);add('joint_q_pre',env.robot.data.joint_pos.torch);add('joint_dq_pre',env.robot.data.joint_vel.torch)
        add('previous_targets',torch.cat((env.executed_leg,env.executed_wheel),-1));add('raw_action',action);add('mean',action);add('actor_valid',controlled[:,None])
        obs,reward,terminated,truncated,_=env.step(action);done=terminated|truncated
        add('state',env.recovery_snapshot);add('posture',env.standing_snapshot);add('control',env.recovery_control_snapshot);add('geometry',env.wheel_geometry_snapshot)
        add('root_post',env.handoff_root_post if teacher else env.student_root_post)
        add('controller',env.handoff_controller[:,None] if teacher else env.course_owner_snapshot[:,None] if hasattr(env,'owner_pre') else controlled[:,None].long()*3)
        if hasattr(env,'owner_pre'):
            add('absolute_control_intervals',env.course_absolute_snapshot[:,None]);add('teacher_intervals',env.course_teacher_snapshot[:,None]);add('handoff_event',env.course_handoff_snapshot[:,None]);add('handoff_state',env.course_handoff_state_snapshot)
        add('termination_causes',env.recovery_cause_snapshot)
        if hasattr(env,'motion_quality_snapshot'):add('quality_termination_causes',env.motion_quality_snapshot)
        if hasattr(env,'student_event_snapshot'):add('student_task_events',env.student_event_snapshot)
        if trace is not None:trace.add('first_episode_valid',active)
        else:valid.append(active.cpu().numpy().copy())
        active&=~done[:scored_envs]
        if getattr(env,'interface_version',None)=='multiskill_mcu_v2':
            from native_stand.command_v6.domain.trace_schema import STATE
            saved=env.recovery_snapshot[:scored_envs]
            if not torch.isfinite(saved).all() or saved[:,STATE['runtime_fault']].bool().any() or saved[:,STATE['initial_rejected']].bool().any():
                raise RuntimeError('MCU evaluation initialization/physical evidence fault; stop matrix without retry')
        if not active.any():break
    if trace is not None:arrays=trace.export()
    else:arrays={k:np.stack(v) for k,v in buffers.items()};arrays['first_episode_valid']=np.stack(valid)
    arrays['policy_time_s']=np.arange(1,len(arrays['first_episode_valid'])+1)*.01
    if getattr(env,'motion_validation',False):
        observed=arrays['actor_input'];expected=np.asarray(row['command'])/np.asarray([4.,4.,.5])
        if not np.allclose(observed[:,:,22:25],expected,atol=1e-6) or not np.all(observed[:,:,25]==1) or not np.all(observed[:,:,26:28]==0):
            raise RuntimeError('Motion command/skill actual Actor input readback differs')
    results=[]
    for eid in range(scored_envs):
        mask=arrays['first_episode_valid'][:,eid];s=torch.tensor(arrays['state'][mask,eid]);p=torch.tensor(arrays['posture'][mask,eid]);clock=torch.tensor(arrays['policy_time_s'][mask],dtype=s.dtype)
        owner=torch.tensor(arrays['controller'][mask,eid,0]);result=teacher_score(s,p,owner==2,policy_time_s=clock) if teacher else student_score(s,p,owner==3,policy_time_s=clock)
        if not teacher and getattr(env,'motion_training_enabled',False):
            from .motion_training import score as motion_training_score
            result=motion_training_score(s,p,torch.tensor(arrays['geometry'][mask,eid]),owner==3,torch.tensor(arrays['root_post'][mask,eid,7:10]),row['command'][:2])
            if hasattr(env,'motion_quality_snapshot'):
                from .motion_quality import score_quality,CAUSES
                result=score_quality(result,s,p,torch.tensor(arrays['geometry'][mask,eid]),owner==3)
                causes=arrays['quality_termination_causes'][mask,eid].any(0)
                result['quality_termination_causes']=[name for name,flag in zip(CAUSES,causes) if flag]
            if getattr(env,'motion_absolute_protocol',None):
                from .motion_guard import assess
                result=assess(result,p,s,owner==3,torch.tensor(arrays['root_post'][mask,eid,7:10]))
                if getattr(env,'motion_forward_course',False):
                    from .motion_forward_course import assess as forward_assess
                    result=forward_assess(result)
        elif not teacher and getattr(env,'motion_validation',False):
            from .motion_validation import score as motion_score
            result=motion_score(s,p,torch.tensor(arrays['geometry'][mask,eid]),owner==3,torch.tensor(arrays['root_post'][mask,eid,7:10]),row['command'])
        elif not teacher and getattr(env,'student_reward_configuration',{}).get('version')=='student_standing_survival_quality_reward_v14':
            from .standing_survival_task import score as quality_score
            result=quality_score(s,p,torch.tensor(arrays['geometry'][mask,eid]),controlled=owner==3,valid=torch.ones(len(s),dtype=torch.bool),world_velocity=torch.tensor(arrays['root_post'][mask,eid,7:10]))
        elif not teacher and getattr(env,'survival_probe',False):
            from .survival_probe import score as survival_score
            result=survival_score(s,p,torch.tensor(arrays['geometry'][mask,eid]),controlled=owner==3,valid=torch.ones(len(s),dtype=torch.bool))
        elif not teacher and hasattr(getattr(env,'rise_hold',None),'standing_height_target'):
            from .standing_certificate import score as standing_score
            result=standing_score(s,p,torch.tensor(arrays['control'][mask,eid]),owner==3,policy_time_s=clock,first_episode_valid=torch.ones(len(s),dtype=torch.bool))
            if hasattr(env.rise_hold,'set_offset'):
                from .standing_certificate import alignment_score
                result=alignment_score(result,torch.tensor(arrays['geometry'][mask,eid]))
                if env.critic_privileged_version:result['version']='student_standing_zero_privileged49_v13'
        if not teacher and row.get('prefix_s',0)>0:result.update(version='student_dynamic_suffix_v1',teacher_prefix_s=row['prefix_s'],independent_Swing_certificate=False)
        if 'student_task_events' in arrays and not getattr(env,'survival_probe',False) and not getattr(env,'motion_validation',False) and not getattr(env,'motion_training_enabled',False):
            online_success=bool(arrays['student_task_events'][mask,eid,2].any())
            if online_success!=result['accepted']:raise RuntimeError('online student full certificate differs from offline score')
            result['online_certificate_matches']=True
        result.update(env=eid,initial_valid=bool(s[:,29].bool().any()),termination_causes=arrays['termination_causes'][mask,eid][-1].tolist())
        results.append(result)
    from .interface import contract
    effective_protocol=__import__('native_stand.recovery.handoff_protocol' if teacher else 'native_stand.students.protocol',fromlist=['declaration']).declaration()
    if not teacher and hasattr(getattr(env,'rise_hold',None),'standing_height_target'):
        from .standing import plan as standing_plan
        effective_protocol={**effective_protocol,**standing_plan(),'version':'student_standing_height034_symmetry_v1'}
        if hasattr(env.rise_hold,'set_offset'):
            effective_protocol.update(version='student_standing_alignment034_v12',target_height_m=.34,wheel_offset_mae_max_m=.02,wheel_offset_p95_max_m=.04)
    if not teacher and getattr(env,'critic_privileged_version',None):
        effective_protocol.update(version='student_standing_zero_privileged49_v13',critic_privileged_version=env.critic_privileged_version)
    if not teacher and row.get('prefix_s',0)>0:effective_protocol={**effective_protocol,'version':'student_dynamic_suffix_v1','teacher_prefix_s':row['prefix_s'],'independent_Swing_certificate':False}
    if getattr(env,'survival_probe',False):
        from .survival_probe import declaration as survival_protocol
        effective_protocol=survival_protocol()
    if not teacher and getattr(env,'student_reward_configuration',{}).get('version')=='student_standing_survival_quality_reward_v14':
        from .standing_survival_task import protocol as quality_protocol
        effective_protocol=quality_protocol()
    if getattr(env,'motion_validation',False):
        from .motion_validation import protocol as motion_protocol
        effective_protocol=motion_protocol()
    if getattr(env,'motion_training_enabled',False):
        from .motion_training import protocol as training_protocol
        from .motion_quality import VERSION as QUALITY_TERMINATION_VERSION
        effective_protocol=training_protocol(quality=getattr(env,'quality_config',{}).get('version')==QUALITY_TERMINATION_VERSION,successor=getattr(env,'motion_quality_reward_config',{}).get('version')=='student_motion31_hold_level_reward_v4')
    if getattr(env,'motion_absolute_protocol',None):effective_protocol=env.motion_absolute_protocol
    if getattr(env,'motion_training_enabled',False):
        from .motion_privileged import contract as reported_contract
    else:
        reported_contract=__import__('native_stand.students.standing_zero_privileged' if getattr(env,'critic_privileged_version',None) else 'native_stand.students.mcu_interface',fromlist=['contract']).contract
    return {'protocol':effective_protocol,'interface':reported_contract() if getattr(env,'interface_version',None)=='multiskill_mcu_v2' else contract(),'field_schema':{'state':'recovery_policy_trace_v1','posture':'recovery_policy_trace_v1','control':'recovery_policy_trace_v1','root':'pos_w3,quat_xyzw4,linear_velocity_w3,angular_velocity_w3','active_indices':env.ids if hasattr(env,'ids') else list(range(6)),'controller':{'initializing':0,'teacher_recovery':1,'teacher_motion':2,'student':3}},'case':row,'per_env':results,'scored_envs':scored_envs,'passed_envs':sum(r['accepted'] for r in results),'accepted':all(r['accepted'] for r in results),'online_PPO':0,'offline_optimizer':0},arrays

def rollout(env,actor,row,*,teacher=None,stop=None,scored_envs=8):
    import torch,sys
    probe=row['kind']=='student_prefix_motion'
    models=([actor,teacher[1]] if probe else list(teacher)) if teacher else [actor]
    modes=[m.training for m in models];cpu_rng=torch.get_rng_state()
    cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None
    saved={name:(hasattr(env,name),getattr(env,name,None)) for name in ('family','split','student_yaw_amplitude','student_command_height','student_motion_command','forced_target','handoff_randomization','switch_steps','case_kind')}
    try:
        for model in models:model.eval()
        if probe:
            from .handoff_rollout import rollout as handoff_rollout
            return handoff_rollout(env,actor,row,teacher[1],stop=stop,scored_envs=scored_envs)
        return _rollout(env,actor,row,teacher=teacher,stop=stop,scored_envs=scored_envs)
    except BaseException as error:
        capture=getattr(env,'student_trace_capture',None)
        trace=capture.get('device_trace') if capture else None
        if trace is not None:
            length=trace.counts.get('first_episode_valid',0)
            if length:
                error.student_partial_arrays=trace.export(completed=length)
                error.student_partial_arrays['policy_time_s']=np.arange(1,length+1)*.01
            else:error.student_pre_action_arrays=trace.export(pre_only=True)
        elif capture and capture['valid']:
            length=len(capture['valid'])
            error.student_partial_arrays={key:np.stack(values[:length]) for key,values in capture['buffers'].items() if len(values)>=length}
            error.student_partial_arrays['first_episode_valid']=np.stack(capture['valid'])
            error.student_partial_arrays['policy_time_s']=np.arange(1,length+1)*.01
        elif capture and capture['buffers']:
            # An exception before the first post-state still has meaningful
            # pre-action evidence; never fabricate a valid executed interval.
            error.student_pre_action_arrays={key:np.stack(values) for key,values in capture['buffers'].items()
                if key in ('actor_input','critic_input','student_actor_input','motion_policy_input','motion_history_input',
                    'motion_previous_raw','motion_previous_clipped','motion_previous_information_loss','motion_previous_outside',
                    'controller_pre','prefix_intervals_pre','switch_event','root_pre','joint_q_pre','joint_dq_pre','previous_targets','raw_action','mean','actor_valid') and values}
        raise
    finally:
        if hasattr(env,'student_trace_capture'):del env.student_trace_capture
        for name,(exists,value) in saved.items():
            if exists:setattr(env,name,value)
            elif hasattr(env,name):delattr(env,name)
        for model,mode in zip(models,modes):model.train(mode)
        torch.set_rng_state(cpu_rng)
        if cuda_rng is not None:torch.cuda.set_rng_state_all(cuda_rng)


def execute(args,spec):
    if spec.get('motion_advantage_probe'):
        from .motion_advantage_probe import execute as execute_probe
        return execute_probe(args,spec)
    p=plan(args,spec)
    if not args.run:print(json.dumps(p,indent=2));return 0
    if p['preflight']['status']!='PASS' or not args.attempt_id or not args.wall_limit_s:raise ValueError('Student public reservation required')
    import torch,sys
    from native_stand.command_v6.completion import write
    from native_stand.command_v6.ledger import Ledger
    from native_stand.command_v6.train import record_run_configuration
    from native_stand.recovery.handoff_evaluator import atomic_result
    from .model import load
    from .performance import settings,EvaluationEnvironment
    perf=settings(spec)
    pool=EvaluationEnvironment(perf['evaluation_reuse_environment'],lambda row:environment(spec,row['role'],teacher=row['kind'] not in ('student','student_prefix_motion'),student_handoff=row['kind']=='student_prefix_motion',initial_family=row['family']))
    book=json.loads(args.spec.with_name('budget.json').read_text());reservation=book['attempts'][args.attempt_id]
    if reservation['status']!='RUNNING' or reservation['output_dir']!=str(args.output.resolve()):raise ValueError('Student exact-ID reservation mismatch')
    deadline=reservation['started_unix_s']+args.wall_limit_s;app=env=None;failure=None;status='FAILED';conditions=[{'index':i,'condition':r,'status':'NOT_RUN'} for i,r in enumerate(p['requests'])];cpu_rng=torch.get_rng_state();cuda_rng=None
    args.output.mkdir(parents=True,exist_ok=False);snapshot=record_run_configuration(args.output,args.spec)
    write(args.output/'manifest.json',{'attempt_id':args.attempt_id,'phase':'evaluate','spec_sha256':sha(args.spec),'source_snapshot_sha256':snapshot,'online_PPO':0,'offline_optimizer_updates':0,'interface_version':spec['interface_version'],'simulated_envs':64,'scored_envs':8})
    if spec.get('motion_confirmation'):
        from .motion_reward_audit import audit as reward_audit
        from . import motion_tracking_reward as reward_source
        snapshot=reward_audit(spec['reward']);snapshot.update(spec_sha256=sha(args.spec),source_sha256=spec['source_sha256'],reward_source_sha256=sha(reward_source.__file__))
        with (args.output/'reward_snapshot.json').open('x') as stream:json.dump(snapshot,stream,indent=2,allow_nan=False)
    if spec.get('student_motion_validation') or spec.get('motion_confirmation'):
        manifest=json.loads((args.output/'manifest.json').read_text());session=spec['authorization']['hapi_session']
        manifest.update(hapi_session=session,spec_path=str(args.spec.resolve()),notification_route={'owner_session':session,'target_session':session})
        write(args.output/'manifest.json',manifest)
    try:
        sys.path.insert(0,spec['asset_module_root'])
        from isaaclab.app import AppLauncher
        app=AppLauncher({'headless':True,'device':'cuda:0','multi_gpu':False}).app
        cuda_rng=torch.cuda.get_rng_state_all();teachers=None
        for index,row in enumerate(p['requests']):
            if time.time()>=deadline-100:status='STOPPED_BOUNDED';break
            conditions[index]['status']='INCOMPLETE';is_probe=row['kind']=='student_prefix_motion';is_teacher=row['kind'] not in ('student','student_prefix_motion')
            setup_started=time.perf_counter();env=pool.acquire(row);setup_wall=time.perf_counter()-setup_started
            from native_stand.command_v6.runtime.configure import verify_asset_import
            from native_stand.command_v6.runtime.control_readback import verify,verify_ground
            write(args.output/f'runtime_readback_{index:02d}.json',{'asset_import':verify_asset_import(spec),'control':verify(env),'ground':verify_ground(env,spec),'active_indices':env.ids,'joint_names':env.robot.joint_names,'reference':env.reference[:8].detach().cpu().tolist(),'interface_version':spec['interface_version'],'evaluation_reset_contract':{'active_family':env.recovery_config['active_family'],'sampling':env.recovery_config['sampling'],'assessment':env.recovery_config['assessment']}})
            if is_teacher or is_probe:
                if teachers is None:teachers=teacher_models(spec,env.device)
            if is_teacher:
                actor=None
            else:actor,_=load(row['checkpoint'],row['role']);actor=actor.to(env.device).eval();actor.requires_grad_(False)
            models=teachers if is_teacher else [actor,teachers[1]] if is_probe else [actor];before=[{k:v.clone() for k,v in m.state_dict().items()} for m in models]
            rollout_started=time.perf_counter()
            payload,arrays=rollout(env,actor,row,teacher=teachers if is_teacher or is_probe else None,stop=lambda:time.time()>=deadline-90)
            rollout_wall=time.perf_counter()-rollout_started
            assert all(all(torch.equal(v,m.state_dict()[k]) for k,v in b.items()) for m,b in zip(models,before))
            payload.update(model_unchanged=True,checkpoint_sha256=sha(row['checkpoint']),
                asset_sha256=spec['asset_sha256'],spec_sha256=sha(args.spec))
            if 'first_episode_valid' in arrays:
                payload.update(simulated_envs=env.num_envs,
                    all_simulated_env_steps=len(arrays['first_episode_valid'])*env.num_envs,
                    scored_env_steps=int(arrays['first_episode_valid'].sum()))
            if is_probe:payload['motion_checkpoint_sha256']=spec['student_teachers'][1]['sha256']
            payload['performance']={**perf,'environment_creations':pool.creations,'environment_reuses':pool.reuses}
            payload['timing']={'environment_acquire_wall_s':setup_wall,'rollout_scoring_transfer_wall_s':rollout_wall}
            if spec.get('motion_confirmation'):
                # Preserve full scoring evidence without repeated full control streams.
                keep={'state','posture','geometry','controller','root_post','first_episode_valid','policy_time_s','effective_command_pre','quality_termination_causes'}
                arrays={k:v for k,v in arrays.items() if k in keep}
                payload['storage_profile']='compact_motion_scoring_proof'
            save_started=time.perf_counter();path=atomic_result(args.output,index,payload,arrays,spec['student_evaluation']['max_output_bytes']);conditions[index].update(status='COMPLETED',result=path.name,passed_envs=payload['passed_envs'],save_wall_s=time.perf_counter()-save_started)
            if not pool.enabled:pool.close();env=None
            if index==0 and spec['student_evaluation']['version']=='student_motion_probe_v1' and payload['passed_envs']!=8:
                status='COMPLETED';break  # Remaining cases stay NOT_RUN, no widened scan.
        else:status='COMPLETED'
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        partial=getattr(exc,'student_partial_arrays',None)
        if partial:
            try:
                path=atomic_result(args.output,index,{'case':row,'status':'INCOMPLETE','accepted':False,'failure':failure},partial,spec['student_evaluation']['max_output_bytes'])
                conditions[index]['result']=path.name
            except BaseException as save_error:failure['partial_save_error']=repr(save_error)
    finally:
        write(args.output/'terminal_report.json',{'status':status,'attempt_id':args.attempt_id,'actual_updates':0,'samples':0,'online_PPO':0,'offline_optimizer_updates':0,'conditions':conditions,'failure':failure})
        # Primary result is saved before cleanup; cleanup never overwrites the error.
        cleanup=[]
        if env is not None:
            try:pool.close()
            except BaseException as exc:cleanup.append(repr(exc))
        torch.set_rng_state(cpu_rng)
        if cuda_rng is not None:torch.cuda.set_rng_state_all(cuda_rng)
        write(args.output/'cleanup.json',{'errors':cleanup,'app_close':'pending'})
        # Kit can exit Python during close: preserve evidence/RNG and the failure code first.
        if app is not None:
            try:app.close(exit_code=0 if status=='COMPLETED' and not cleanup else 1)
            except BaseException as exc:cleanup.append(repr(exc))
        write(args.output/'cleanup.json',{'errors':cleanup,'app_close':'returned'})
    return 0 if status=='COMPLETED' else 1
