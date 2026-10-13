"""Native actor/control semantic contract; geometry reporting is a separate frame."""
JOINTS=('left_hip_pitch','left_active_link_pitch','left_wheel_spin',
        'right_hip_pitch','right_active_link_pitch','right_wheel_spin')
VERSION='native_cad_com_v1'


def resolve(spec):
    action=spec['action'];control=spec['control']
    if (spec['observation']['frame_dim']!=25 or spec['history']['frames']!=5 or action['dim']!=6):
        raise ValueError('Native input/action dimensions differ')
    if list(action['order'])!=list(JOINTS) or spec['history'].get('order')!='oldest_to_newest':
        raise ValueError('Native joint/history semantic order differs')
    expected=(.001,.005,.01)
    actual=tuple(control[k] for k in ('physics_dt_s','pd_dt_s','policy_dt_s'))
    if actual!=expected:raise ValueError('Native physics/PD/policy contract differs')
    if list(control['effort_limits_nm'])!=[40,40,5.5,40,40,5.5]:raise ValueError('Native effort limits differ')
    return {'version':VERSION,'actor_frame':'CAD_body','actor_initial_gravity':[0.,-1.,0.],
        'velocity_frame':'CAD_body','measurement_point':'body_COM',
        'velocity_axes':{'vx':'-CAD_z','vy':'-CAD_x','yaw':'CAD_y','up':'-gravity_CAD_y'},
        'root_quaternion_order':'wxyz','root_position_scope':'engine root/link pose; not COM position',
        'world_to_actor':'inverse root body orientation',
        'geometry_reporting_frame':'upright_forward_left_up; never actor input',
        'frame_dim':25,'history_frames':5,'history_order':'oldest_to_newest',
        'actor_input_order':['current_frame','history_125D'],'reset_history':'repeat current frame five times',
        'observation_scales':{'angular':.25,'command':[2.,.25,5.],'leg_delta':2.,'joint_dq':.05},
        'joint_order':list(JOINTS),'joint_position_reference':'native reset reference, not virtual-leg mapping',
        'action_clip':[-1.,1.],'leg_target_scale_rad':action['leg_scale_rad'],
        'leg_pair_radius_rad':action['leg_pair_radius_rad'],'wheel_target_scale_rad_s':action['wheel_scale_rad_s'],
        'physics_PD_policy_dt_s':list(actual),'effort_limits_nm':list(control['effort_limits_nm']),
        'PD':{k:control[k] for k in ('leg_kp','leg_kd','wheel_kv')},
        'transmission':'joint torque Nm = motor command * signed gear; no compensation',
        'dynamic_pairing_required':['actor_policy_25D','actor_history_125D','root_quaternion_wxyz',
            'root_position_w','COM_linear_velocity_w','angular_velocity_w','actual_command',
            'raw_action','clipped_action','leg_target_rad','wheel_target_rad_s','PD_requested_nm',
            'physical_clipped_nm','actuator_applied_nm','episode_id','policy_index','valid_pre_reset']}


def compare(expected,actual):
    """Shape agreement alone never validates semantics; unknown keys cannot PASS."""
    rows=[]
    for key,value in expected.items():
        if key not in actual:status='UNKNOWN'
        else:status='PASS' if actual[key]==value else 'DIFFERENT'
        rows.append({'field':key,'expected':value,'actual':actual.get(key),'status':status})
    return {'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'NOT_PASS','fields':rows}
