"""Explicit preparation request; compile sampling separately from immutable scoring."""
import math


def parse_request(data):
    fields={'purpose','level_id','current_family','retained_families','family_weights',
            'smoke_updates','formal_updates','evaluation_updates','wall_s'}
    if (not isinstance(data,dict) or not fields<=set(data) or
            set(data)-fields-{'environment_counts','wheel_mean_auxiliary','support_record_reward','notifications','evaluation_schedule','action_distribution','leg_center_auxiliary','drawback_guidance','retention_regression_policy','actor_update_scope','swing_only','seed','restore_source_rng','cleanup_wall_s'}):
        raise ValueError('Recovery course request fields differ: '+str(fields))
    if 'notifications' in data:
        n=data['notifications']
        if not isinstance(n,dict) or not isinstance(n.get('enabled'),bool) or set(n)-{'enabled','target_session','authorization_note'}:
            raise ValueError('invalid notification declaration')
        if n['enabled'] and (not isinstance(n.get('target_session'),str) or not n['target_session'].strip()):raise ValueError('notification owner required')
    if 'evaluation_schedule' in data:
        e=data['evaluation_schedule']
        if not isinstance(e,dict) or set(e)!={'full_every_updates','checkpoint_every_updates'} or any(type(v) is not int or v<1 for v in e.values()):raise ValueError('invalid evaluation schedule')
    for key in ('purpose','level_id','current_family'):
        if not isinstance(data[key],str) or not data[key].strip():raise ValueError('empty '+key)
    current=data['current_family'];retained=data['retained_families'];weights=data['family_weights']
    if 'actor_update_scope' in data:
        from native_stand.recovery.controlled_ppo import declaration as actor_declaration
        if data['actor_update_scope']!=actor_declaration():raise ValueError('Unknown actor update scope')
    if 'swing_only' in data and (data['swing_only'] is not True or retained or current!='swing_candidate_from_historical_r1'):
        raise ValueError('Swing-only requires single Swing and no retained families')
    if 'retention_regression_policy' in data:
        from native_stand.recovery.regression_policy import declaration as policy_declaration
        if data['retention_regression_policy']!=policy_declaration() or 'drawback_guidance' not in data:
            raise ValueError('Invalid contact-only regression policy request')
    if 'drawback_guidance' in data:
        from native_stand.recovery.drawback_guidance_proposal import declaration as guidance_declaration
        if data['drawback_guidance']!=guidance_declaration() or 'leg_center_auxiliary' in data or 'wheel_mean_auxiliary' in data:
            raise ValueError('Unsupported/conflicting DrawBack guidance request')
    if 'leg_center_auxiliary' in data:
        from native_stand.recovery.leg_center_auxiliary import declaration as leg_declaration
        if data['leg_center_auxiliary']!=leg_declaration() or 'wheel_mean_auxiliary' in data:
            raise ValueError('Unsupported/conflicting leg center request')
    if 'action_distribution' in data:
        from .action_distribution import declaration
        if data['action_distribution']!=declaration() or 'wheel_mean_auxiliary' in data:
            raise ValueError('Unsupported/conflicting course action distribution')
    if 'support_record_reward' in data:
        from native_stand.recovery.support_record_proposal import declaration
        if data['support_record_reward']!=declaration() or current!=declaration()['family'] or 'wheel_mean_auxiliary' in data:
            raise ValueError('Unsupported/conflicting support record request')
    if 'wheel_mean_auxiliary' in data:
        from native_stand.recovery.mean_auxiliary import declaration
        if data['wheel_mean_auxiliary']!=declaration(data['wheel_mean_auxiliary'].get('version')) or current!=declaration()['family']:
            raise ValueError('Unsupported wheel mean auxiliary request')
    if (not isinstance(retained,list) or
            any(not isinstance(f,str) or not f for f in retained) or
            len(set(retained))!=len(retained) or current in retained):
        raise ValueError('Current and retained families must be unique and separate')
    if (not isinstance(weights,dict) or set(weights)!={current,*retained} or
            any(type(w) not in (int,float) or not math.isfinite(w) or w<=0 for w in weights.values()) or
            not math.isclose(sum(weights.values()),1.,abs_tol=1e-12)):
        raise ValueError('Family weights must be positive finite and sum to one')
    if 'environment_counts' in data:
        counts=data['environment_counts']
        if (not isinstance(counts,dict) or set(counts)!=set(weights) or
                any(type(n) is not int or n<1 for n in counts.values())):
            raise ValueError('Fixed environment counts must cover every family')
        total=sum(counts.values())
        if any(not math.isclose(counts[f]/total,weights[f],abs_tol=1e-12) for f in weights):
            raise ValueError('Family weights differ from fixed counts')
    for key in ('smoke_updates','formal_updates'):
        if type(data[key]) is not int or data[key]<1:raise ValueError('positive integer '+key+' required')
    points=data['evaluation_updates']
    if (not isinstance(points,list) or not points or any(type(x) is not int or not 1<=x<=data['formal_updates'] for x in points)
            or points!=sorted(set(points)) or points[-1]!=data['formal_updates']):
        raise ValueError('Evaluation updates must be unique ascending and include formal endpoint')
    wall=data['wall_s']
    if (not isinstance(wall,dict) or set(wall)!={'source_eval','smoke','formal'} or
            any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in wall.values())):
        raise ValueError('Explicit positive phase wall limits required')
    return data


def swing_smoke_contract(policy_dt,settle_max_s,family):
    """Prove a real controlled episode completed, not task-duration success."""
    if not math.isfinite(policy_dt) or policy_dt<=0 or not math.isfinite(settle_max_s) or settle_max_s<0:
        raise ValueError('Explicit smoke clock required')
    return {'required_event':'completed_episode','required_event_duration_s':policy_dt,
            'event_offset_s':settle_max_s,'minimum_event_count':1,
            'required_groups':[{'family':family,'minimum_completed':1,'require_runtime_initial_valid':True}]}
