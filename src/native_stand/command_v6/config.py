"""Pure schema validation for the only v6 spec shape."""
import math

REQUIRED = ("experiment", "version", "source_checkpoint", "source_sha256",
            "asset_path", "asset_sha256", "interpreter", "seed", "observation",
            "history", "action", "control", "reward", "curriculum",
            "evaluation", "ppo", "budget", "artifacts", "ground", "termination")
PHASES = ("source_eval", "smoke", "formal")
SIM_PHASES = ("evaluate", "play")


def validate(spec):
    if spec.get("interface_version") in ("multiskill_student_v1","multiskill_mcu_v2"):
        from native_stand.students.requests import validate as validate_student
        return validate_student(spec)
    if spec.get("interface_version") not in (None,"legacy150D"):
        return ["Unknown interface version"]
    errors = [f"missing {key}" for key in REQUIRED if key not in spec]
    if spec.get("artifacts",{}).get("evaluation_trace_encoding") not in (None,"evaluation_numeric_npz_v1"):
        errors.append("Unknown evaluation trace encoding")
    if spec.get('action_distribution'):
        from .domain.action_distribution import validate as validate_distribution
        try:validate_distribution(spec)
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
    if spec.get('receiver_training'):
        from native_stand.recovery.receiver_contract import validate as validate_receiver
        try:validate_receiver(spec)
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
    if spec.get('motion_handoff'):
        from native_stand.recovery.handoff_requests import validate as validate_handoff
        try:validate_handoff(spec)
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
    if spec.get('rollout_probe'):
        from .domain.rollout_probe import validate as validate_probe
        try:validate_probe(spec)
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
    try:
        from .domain.submission_contract import authorization
        authorization(spec)
    except ValueError as exc:
        errors.append(str(exc))
    if errors:
        return errors
    try:
        from .domain.resource_policy import resolve_resources
        resolve_resources(spec)
    except (ValueError,TypeError) as exc:errors.append(str(exc))
    try:
        from .domain.execution_plan import smoke_plan
        smoke_plan(spec)
    except (KeyError,ValueError,TypeError) as exc:errors.append('wiring smoke plan invalid: '+str(exc))
    try:
        from .domain.recipe import resolve
        resolve(spec)
    except (ValueError, KeyError, TypeError) as exc:
        errors.append('effective recipe: ' + str(exc))
    try:
        from .domain.selected_diagnostics import configuration
        configuration(spec)
    except (TypeError,ValueError) as exc:
        errors.append(str(exc))
    if spec["version"] != 6 or not isinstance(spec["seed"], int):
        errors.append("version or seed differs")
    obs, hist, action = spec["observation"], spec["history"], spec["action"]
    if obs.get("frame_dim") != 25 or hist.get("frames") != 5 or hist.get("dim") != 125:
        errors.append("25D/5x25 observation contract differs")
    if obs.get("scales") != [.25,1.,2.,.25,5.,2.,.05,1.]:
        errors.append("native observation scales differ")
    if action.get("dim") != 6 or len(action.get("order", [])) != 6:
        errors.append("6D action contract differs")
    action_contract=(action.get("leg_scale_rad"), action.get("leg_pair_radius_rad"))
    allowed_actions=((.1,.12),(.5,0.),(1.6,0.)) if spec.get('task')=='recovery' else ((.1,.12),(.5,0.))
    if action_contract not in allowed_actions or action.get('wheel_scale_rad_s') not in (6.,100.):
        errors.append("frozen native physical-joint action scaling differs")
    control = spec["control"]
    ground = spec.get("ground",{})
    if (ground.get("collider")!="plane" or ground.get("height_m")!=0. or
            ground.get("normal_axis")!="Z" or
            ground.get("width_m")!=128. or ground.get("length_m")!=128. or
            ground.get("material_path")!="/World/native_ground_material" or
            [ground.get(k) for k in ("static_friction","dynamic_friction","restitution")] != [.5,.5,0.]):
        errors.append("frozen plane collider or material differs")
    if spec.get('initialization','warmstart') not in ('warmstart','random'):
        errors.append('initialization must be warmstart or random')
    if any(not spec.get(k) for k in ("asset_module_root","asset_module_path",
                                   "asset_module_sha256","colleague_config_path",
                                   "colleague_config_sha256")):
        errors.append("colleague asset module or YAML identity missing")
    if [control.get(k) for k in ("physics_dt_s","pd_dt_s","policy_dt_s")] != [.001,.005,.01]:
        errors.append("physics/PD/policy periods differ")
    if [control.get(k) for k in ("leg_kp","leg_kd","wheel_kv","closure_fault_m")] != [60.,2.,1.,.005] or control.get('height_command_m') not in (.36,.363,.40):
        errors.append("standing PD, height or closure contract differs")
    if control.get("effort_limits_nm") != [40,40,5.5,40,40,5.5]:
        errors.append("physical effort limits differ")
    termination=spec["termination"]
    termination_expected=[0.,.5,200.,3.1] if spec.get('task')=='recovery' else [.2,.5,200.,.5]
    if [termination.get(k) for k in ("fall_root_height_m","minimum_up_cos","body_contact_max_n","active_leg_angle_max_rad")] != termination_expected:
        errors.append("frozen task failure threshold differs")
    reward=spec["reward"]
    if spec.get('motion_posture') is not None:
        try:
            from .domain.posture_geometry import validate_task
            validate_task(spec)
        except (ValueError,KeyError,TypeError) as exc:
            errors.append('motion posture: '+str(exc))
    if spec.get('task')=='recovery' and not spec.get('receiver_training'):
        if any(not isinstance(reward.get(k),(int,float)) for k in
            ('lift','upright','effort','action_delta','joint_margin','success_once','failure_once')):
            errors.append('Recovery reward fields missing')
    elif any(reward.get(k) is None for k in ("upright","height","velocity_tracking",
            "two_wheel_contact","effort","action_delta","joint_margin",
            "height_width_m","linear_error_denominator","yaw_error_denominator","terminal_penalty")):
        errors.append("standing reward formula inputs missing")
    elif any(reward[k]<=0 for k in ("height_width_m","linear_error_denominator","yaw_error_denominator")):
        errors.append("standing reward widths must be positive")
    cohort=reward.get('linear_cohort_width')
    if cohort is not None:
        if (cohort.get('retained_commands')!=[[0,0],[.5,0],[-.5,0]] or
                cohort.get('retained_denominator')!=.04 or
                reward['linear_error_denominator']!=1. or not (spec.get('cohort_width_ab') or spec.get('straight_high_speed_course') or spec.get('receiver_training'))):
            errors.append('cohort-width A/B contract differs')
    evaluation = spec["evaluation"]
    try:
        from .domain.diagnostic_profiles import storage_plan
        storage_plan(spec,full=True,legacy_full_trace=False)
        for saved_update in evaluation.get('full_trace_updates',[]):
            storage_plan(spec,update=saved_update,full=True,legacy_full_trace=False)
    except (ValueError,KeyError,TypeError) as exc:
        errors.append('evaluation storage plan: '+str(exc))
    checkpoint = evaluation.get("checkpoint_every_updates")
    light = evaluation.get("light_every_updates")
    full = evaluation.get("full_every_updates")
    if any(not isinstance(x,int) or x<=0 or x%10 == 0 and x<50 for x in (checkpoint,full)) or (light!=0 and (not isinstance(light,int) or light<50)):
        errors.append("evaluation/checkpoint schedule too frequent or invalid")
    if full and light and full % light and not spec.get('recovery',{}).get('standing_task'):
        errors.append("full evaluation must align with light evaluation")
    if evaluation.get("scored_envs",0) > evaluation.get("envs",0):
        errors.append("scored env count exceeds layout")
    if evaluation.get("scored_envs")!=8:
        errors.append("standing source gate requires eight scored environments")
    stages = spec["curriculum"].get("stages", [])
    episode=spec['curriculum'].get('episode_curriculum')
    if episode is not None:
        if (episode.get('lengths_s')!=[6,10,20,30] or episode.get('episodes_per_window')!=128 or
                episode.get('consecutive_windows')!=2 or 'gates' not in episode):
            errors.append('episode curriculum shape differs from authorization')
        gates=episode.get('gates',{})
        names=('normal_timeout_min','metric_episode_pass_min','vx_abs_max_mps',
               'yaw_abs_max_rad_s','excursion_max_m','tilt_max_rad','dual_contact_min',
               'saturation_max','closure_max_m')
        if any(not isinstance(gates.get(name),(int,float)) or gates[name]<=0 for name in names):
            errors.append('episode curriculum gates missing or invalid')
        expected_height=[.39,.41] if control['height_command_m']==.4 else [.34,.38]
        if gates.get('normal_timeout_min')!=.95 or gates.get('metric_episode_pass_min')!=.95 or gates.get('height_m')!=expected_height:
            errors.append('episode curriculum acceptance differs')
    active_stage=spec["curriculum"].get("active_stage")
    if (not isinstance(active_stage,int) or active_stage<0 or active_stage>=len(stages) or
            (stages and stages[0].get("commands")!=[[0,0]])):
        errors.append("active stage invalid or stage 0 is not zero-command standing")
    if not stages or [row.get("id") for row in stages] != list(range(len(stages))):
        errors.append("stage IDs must be contiguous")
    for row in stages:
        commands, weights = row.get("commands", []), row.get("weights", [])
        if len(commands) != len(weights) or any(len(c)!=2 for c in commands):
            errors.append(f"stage {row.get('id')} command shape differs")
        if not weights or any(w<0 for w in weights) or not math.isclose(sum(weights),1.,abs_tol=1e-6):
            errors.append(f"stage {row.get('id')} weights invalid")
        minimum_zero=spec['curriculum'].get('minimum_zero_fraction',.4)
        if row.get("id") and (commands[0] != [0,0] or weights[0] < minimum_zero):
            errors.append(f"stage {row.get('id')} lacks required zero command fraction")
        if any(abs(c[0])>.2 or abs(c[1])>.2 for c in commands) and spec['curriculum'].get('task_progression') and action['wheel_scale_rad_s']==6.:
            errors.append('unverified commands exceed frozen action envelope')
        from .domain.command_sampling import resolve as sampling_plan
        try:sampling_plan(row,spec['ppo']['envs'])
        except (ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
        slots=row.get('sampling_slots')
        if slots is not None and (len(slots)!=64 or any(not isinstance(index,int) or index<0 or index>=len(commands) for index in slots)):
            errors.append(f"stage {row.get('id')} sampling slots invalid")
    if spec.get('initialization','warmstart')=='warmstart' and spec.get('source_input_dim',132) not in (132,150):
        errors.append('source input dimension must be explicit132 or150')
    if action['wheel_scale_rad_s']==100. and spec.get('task')!='recovery':
        conversion=spec.get('wheel_envelope_conversion',{})
        if (spec.get('source_input_dim')!=150 or
                (conversion.get('source_scale_rad_s'), conversion.get('destination_scale_rad_s'))
                not in ((6.,100.),(100.,100.))):
            errors.append('100rad/s envelope requires explicit native source calibration')
    if spec.get('task')=='recovery':
        from native_stand.recovery.validation import validate_recovery
        errors.extend(validate_recovery(spec))
    ppo, budget = spec["ppo"], spec["budget"]
    trace_updates=evaluation.get('full_trace_updates',[])
    if (not isinstance(trace_updates,list) or
            any(type(u) is not int or u<1 or u>budget.get('formal_updates',0) or
                not (u%evaluation['full_every_updates']==0 or
                     u in evaluation.get('unlock_full_updates',[])) for u in trace_updates)):
        errors.append('full_trace_updates must select declared full formal milestones')
    if ppo.get("envs",0)<=0 or ppo.get("steps_per_env",0)<=0 or ppo.get("learning_rate",0)<=0:
        errors.append("PPO sizing or learning rate invalid")
    if spec.get('evaluation_only'):
        if budget.get('formal_updates')!=0 or budget.get('smoke_updates')!=0:
            errors.append('evaluation-only recipe cannot allocate PPO updates')
    elif spec.get('engineering_recovery'):
        from .tools.motion_recovery_certificate import VERSION
        ref=spec['engineering_recovery']
        if (spec.get('task')=='recovery' or ref.get('version')!=VERSION or budget.get('smoke_updates')!=0 or
                budget.get('source_eval_updates')!=0 or not 1<=budget.get('formal_updates',0)<=50 or
                not 0<budget.get('formal_wall_s',0) or not spec.get('restore_source_rng') or
                spec.get('source_input_dim')!=150 or not ref.get('sha256') or not ref.get('single_use_id')):
            errors.append('Restricted Motion engineering recovery declaration invalid')
    elif (budget.get("formal_updates",0)<1 or budget.get("smoke_updates",0)<1 or
            budget.get("source_eval_wall_s",0)<=30 or budget.get("smoke_wall_s",0)<=60 or
            (budget.get("formal_wall_s",0) is not None and budget.get("formal_wall_s",0)<=120)):
        errors.append("PPO update limits invalid")
    warmup = ppo.get("critic_warmup_updates", 0)
    formal_updates = budget.get("formal_updates", 0)
    if (not isinstance(warmup, int) or warmup < 0 or
            (warmup > 0 and formal_updates > 0 and warmup >= formal_updates)):
        errors.append("critic_warmup_updates must be a nonnegative integer below formal_updates")
    if ppo.get("clear_adam_first_moment", False) not in (True, False):
        errors.append("clear_adam_first_moment must be boolean")
    return errors


def schedule(update, phase, evaluation):
    if phase != "formal":
        return {"checkpoint":False,"light":False,"full":False}
    result={"checkpoint":update % evaluation["checkpoint_every_updates"] == 0,
            "light":bool(evaluation["light_every_updates"] and update % evaluation["light_every_updates"] == 0),
            "full":update % evaluation["full_every_updates"] == 0 or
                   update in evaluation.get('unlock_full_updates', [])}
    if evaluation.get('protocol_identity')=='motion_absolute_v3':
        frequency=evaluation.get('zero_every_updates',25)
        if type(frequency) is not int or frequency<1:raise ValueError('zero_every_updates invalid')
        result['zero_only']=update%frequency==0 and not result['full']
        if result['zero_only']:result['full']=True
    return result


def evaluation_seconds(spec, *, full):
    if spec.get('recovery',{}).get('standing_task'):
        return spec['evaluation']['seconds'] if full else spec['evaluation']['light_seconds']
    if spec.get('task')=='recovery':
        return spec['recovery']['fsm']['timeout_s']+spec['recovery']['initialization']['settle_max_s']+.01
    return spec['evaluation'].get('seconds',10.) if full else spec['evaluation']['light_seconds']
