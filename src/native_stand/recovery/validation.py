"""Pure recovery config requirements; file identity checks live in preflight."""


def validate_recovery(spec):
    config=spec.get('recovery',{})
    required=('stand_checkpoint','stand_sha256','stand_spec','stand_frozen','pose_library',
        'pose_library_sha256','stand_spec_sha256','fsm','gate','initialization','contacts')
    errors=[f'recovery missing {key}' for key in required if key not in config]
    if errors:return errors
    if not config['stand_frozen'] or spec.get('initialization') not in ('random','warmstart'):
        errors.append('Recovery learns a new policy; STAND must remain immutable')
    fsm=config['fsm']
    if fsm.get('success_mode','handover') not in ('handover','autonomous_hold'):
        errors.append('Unknown Recovery success mode')
    autonomous=fsm.get('success_mode')=='autonomous_hold'
    if fsm.get('verify_s')!=(2. if autonomous else 5.) or not 0.<fsm.get('blend_s',0.)<=1. or not 0.<fsm.get('gate_dwell_s',0.)<=1.:
        errors.append('Recovery handover/5s verification contract differs')
    if autonomous:
        expected_legacy={'height_m':[.38,.42],'tilt_max_rad':.2,'linear_speed_max_mps':.05,
                  'angular_speed_max_rad_s':.3,'dual_contact_min_n':2.,'chassis_clearance_min_m':.25}
        height_command=spec.get('control',{}).get('height_command_m',.40)
        expected_height=[.34,.38] if height_command==.36 else [.38,.42]
        expected_horizontal={'height_m':expected_height,'tilt_max_rad':.12,'linear_speed_max_mps':.3,
                  'angular_speed_max_rad_s':.3,'dual_contact_min_n':2.,'chassis_clearance_min_m':.25}
        standing=config.get('standing_task')
        level_only=bool(standing and standing.get('protocol',{}).get('objective')=='survival_level')
        expected_standing={**expected_horizontal,'tilt_max_rad':.1,
                           'linear_speed_max_mps':.05,'angular_speed_max_rad_s':.1}
        expected_level={'objective':'survival_level','height_m':expected_height,
            'tilt_max_rad':.18,'dual_contact_min_n':2.,'chassis_clearance_min_m':.25}
        if level_only and config.get('autonomous_stability')!=expected_level:
            errors.append('Survival/level online success protocol differs')
        if not level_only and config.get('autonomous_stability') not in (
                (expected_legacy,expected_horizontal,expected_standing) if standing else
                (expected_legacy,expected_horizontal)):
            errors.append('Autonomous stability protocol differs')
        reward=config.get('settling_reward',{})
        if (reward.get('kind')!='pseudo_huber' or reward.get('height_full_m',0)<=reward.get('height_start_m',0)
                or reward.get('linear_scale_mps',0)<=0 or reward.get('angular_scale_rad_s',0)<=0
                or reward.get('settling_linear_weight',0)>(0 if level_only else -1e-30)
                or reward.get('settling_angular_weight',0)>(0 if level_only else -1e-30)):
            errors.append('Autonomous settling reward invalid')
        if 'settling_yaw_weight' in reward:
            import math
            if (not isinstance(reward['settling_yaw_weight'], (int, float)) or
                    not math.isfinite(reward['settling_yaw_weight']) or
                    reward['settling_yaw_weight'] > (0 if level_only else -1e-30) or
                    not isinstance(reward.get('yaw_scale_rad_s'), (int, float)) or
                    not math.isfinite(reward['yaw_scale_rad_s']) or reward['yaw_scale_rad_s'] <= 0 or
                    not config.get('standing_task')):
                errors.append('Independent canonical yaw cost requires standing task and finite negative weight/positive scale')
    if fsm.get('timeout_s',0.)<=fsm.get('verify_s',5.)+fsm.get('blend_s',0.):
        errors.append('Recovery timeout cannot contain handover and verification')
    if spec['action']['wheel_scale_rad_s']!=100. or spec['action']['leg_scale_rad']!=1.6:
        errors.append('Recovery explicit action normalization differs')
    if spec['curriculum'].get('episode_curriculum') is not None:
        errors.append('Standing timeout curriculum cannot be applied to Recovery')
    if spec['termination'].get('joint_limit_mode')!='usd_authored':
        errors.append('Recovery must retain actual per-joint USD limits')
    original=['robot','left_wheel','right_wheel','guide_wheel_lower_*']
    linkage=['*_active_link','*_long_link','*_node_link','*_parallel_link','*_upper_leg','*_lower_leg']
    patterns=config['contacts'].get('allowed_candidate')
    if patterns!=original and not (patterns==original+linkage and
            config['contacts'].get('linkage_support_user_confirmed') is True):
        errors.append('Unvalidated support-body classification change')
    if config['initialization'].get('mode')!='passive_settle':
        errors.append('Recovery requires explicit bounded passive settling')
    gate_modes=[config.get('settling_reward',{}).get('gate_mode','height')]
    gate_modes.extend(spec['reward'].get(axis+'_level_gate_mode','height') for axis in ('pitch','roll'))
    if any(mode not in ('height','unconditional') for mode in gate_modes):
        errors.append('Unknown Recovery reward gate mode')
    if config.get('standing_task'):
        import math
        from native_stand.recovery.standing import REWARD_FIELDS
        standing=config['standing_task']
        reward=standing.get('reward',{})
        if reward.get('gate_mode','height') not in ('height','unconditional'):
            errors.append('Unknown standing reward gate mode')
        names=('height_width_m','vertical_scale_mps','level_angular_scale_rad_s',
               'mirror_scale_rad','leg_length_scale_m','wheel_difference_scale_rad_s')
        if (any(not isinstance(reward.get(n),(int,float)) or not math.isfinite(reward[n]) or
                reward[n]<=0 for n in names) or
                reward.get('gate_full_m',0)<=reward.get('gate_start_m',0)):
            errors.append('Standing reward scales/gate invalid')
        weights=reward.get('weights',{})
        if (set(weights)!=set(REWARD_FIELDS) or any(not isinstance(v,(int,float)) or not math.isfinite(v)
                for v in weights.values()) or weights.get('standing_height',0)<=0 or
                any(weights.get(n,0)>(0 if level_only else -1e-30)
                    for n in REWARD_FIELDS if n!='standing_height')):
            errors.append('Standing reward weights invalid')
        if reward.get('mirror_deadband_rad',-1)<0:
            errors.append('Standing mirror deadband invalid')
        if not math.isfinite(reward.get('mirror_deadband_rad',float('nan'))):
            errors.append('Standing mirror deadband must be finite')
        protocol=standing.get('protocol',{})
        positive=('seconds','peak_tilt_max_rad','closure_max_m','saturation_max',
                  'dual_contact_min','level_mean_max_rad','level_peak_max_rad','height_fraction_min')
        if not level_only:
            positive+=('excursion_max_m','vx_abs_max_mps','vy_abs_max_mps','yaw_abs_max_rad_s',
                       'mirror_error_max_rad','leg_length_difference_max_m','support_difference_max')
        if protocol.get('objective','stationary') not in ('stationary','survival_level'):
            errors.append('Unknown standing objective')
        if (any(not isinstance(protocol.get(n),(int,float)) or not math.isfinite(protocol[n]) or
                protocol[n]<=0 for n in positive) or protocol.get('height_m')!=[.34,.38] or
                protocol.get('steady_window_s')!=[2.,10.] or protocol.get('seconds')!=10.):
            errors.append('Standing continuous protocol invalid')
        fractions=('height_fraction_min','dual_contact_min','saturation_max')
        if not level_only:fractions+=('support_difference_max',)
        if any(not 0<protocol.get(n,0)<=1 for n in fractions):
            errors.append('Standing fractions must be in (0,1]')
        if level_only:
            removed=('vx_abs_max_mps','vy_abs_max_mps','yaw_abs_max_rad_s','excursion_max_m',
                     'mirror_error_max_rad','leg_length_difference_max_m','support_difference_max')
            if any(name in protocol for name in removed):
                errors.append('Survival/level protocol must remove obsolete acceptance gates')
            if (protocol.get('version')!='survival_level_v1' or
                    protocol.get('level_mean_max_rad')!=.10 or protocol.get('level_peak_max_rad')!=.15 or
                    protocol.get('peak_tilt_max_rad')!=.18):
                errors.append('Survival/level frozen horizontal limits differ')
            if (any(config['settling_reward'].get(n,0)!=0 for n in
                    ('settling_linear_weight','settling_angular_weight','settling_yaw_weight')) or
                    any(weights.get(n)!=0 for n in ('mirror_posture','leg_length_balance','wheel_difference')) or
                    any(spec['reward'].get(n,0)!=0 for n in
                        ('wheel_longitudinal_offset','leg_symmetry','support_balance','slip_proxy'))):
                errors.append('Survival/level recipe still contains motion or symmetry costs')
        if (spec['evaluation'].get('seconds')!=protocol.get('seconds') or
                spec['evaluation'].get('steady_window_s')!=protocol.get('steady_window_s')):
            errors.append('Standing evaluator and protocol duration differ')
        if 'wheel_longitudinal_offset' in spec.get('reward',{}):
            value=spec['reward']['wheel_longitudinal_offset']
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value>=0:
                errors.append('Wheel longitudinal cost must have finite negative weight')
            for key in ('wheel_longitudinal_deadband_m','wheel_longitudinal_scale_m'):
                value=spec['reward'].get(key)
                if (not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or
                        (key.endswith('scale_m') and value<=0)):
                    errors.append('Wheel longitudinal geometry reward scale invalid')
        retention=standing.get('retention',{})
        if retention.get('enabled'):
            from native_stand.recovery.standing import retention_coefficient
            try:
                retention_coefficient(retention.get('coefficient',0.),retention.get('schedule',{'kind':'constant'}),0)
            except (ValueError,TypeError):
                errors.append('Standing retention schedule invalid')
            if retention.get('channels','all') not in ('all','wheels'):
                errors.append('Standing retention channels invalid')
            if not isinstance(retention.get('gradient_diagnostics',False),bool):
                errors.append('Standing gradient diagnostics must be boolean')
            updates=retention.get('save_gradient_updates',[])
            if not isinstance(updates,list) or any(not isinstance(u,int) or u<1 for u in updates):
                errors.append('Standing gradient payload update list invalid')
        if retention.get('enabled') and (spec.get('source_input_dim')!=150 or
                not math.isfinite(retention.get('coefficient',float('nan'))) or
                retention.get('coefficient',0)<=0 or
                not isinstance(retention.get('max_samples_per_rollout'),int) or
                retention.get('max_samples_per_rollout',0)<1 or
                retention.get('height_min_m',0)>=retention.get('height_max_m',0)):
            errors.append('Standing retention requires strict150D source and valid bounds')
        anchors=standing.get('hip_anchors_root_m',[])
        if (len(anchors)!=2 or any(not isinstance(anchor,list) or len(anchor)!=3 or
                any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in anchor) for anchor in anchors)):
            errors.append('Standing hip geometry must be explicit')
        curriculum=config.get('curriculum',{})
        cap=curriculum.get('max_enabled_stage')
        if (not isinstance(cap,int) or not 0<=cap<len(curriculum.get('levels',[])) or
                curriculum.get('full_confirmations_required')!=2):
            errors.append('Standing curriculum requires an explicit stage cap and two full confirmations')
        for index, level in enumerate(curriculum.get('levels',[])):
            fraction=level.get('retained_fraction',0.)
            if (not isinstance(fraction,(int,float)) or not math.isfinite(fraction) or not 0<=fraction<1 or
                    (fraction and (not index or not level.get('retained_families')))):
                errors.append('Standing curriculum rehearsal configuration invalid')
    return errors
