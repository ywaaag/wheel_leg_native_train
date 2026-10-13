"""Policy-rate paired actor input and root/wheel state layout, no state reconstruction."""
VERSION='motion_paired_state_v1'
AXES=['policy_time','scored_env','channel']
GROUPS={'actor_policy_25D':[0,25],'actor_history_125D':[25,150],'raw_action':[150,156],
        'actual_command':[156,159],'pre_root_position_w':[159,162],'pre_root_quaternion_wxyz':[162,166],
        'pre_COM_linear_velocity_w':[166,169],'pre_angular_velocity_w':[169,172],
        'pre_wheel_body_origins_w':[172,178],'post_root_position_w':[178,181],
        'post_root_quaternion_wxyz':[181,185],'post_COM_linear_velocity_w':[185,188],
        'post_angular_velocity_w':[188,191],'post_wheel_body_origins_w':[191,197]}
CHANNELS=197


def concatenate(obs,action,command,pre,post):
    import torch
    result=torch.cat((obs['policy'],obs['history'],action,command,pre,post),-1)
    if result.shape[-1]!=CHANNELS:raise ValueError('Paired state channel mismatch')
    return result


def root_geometry(data,wheels,n):
    """Read actual engine arrays; body origin is not claimed to be collider center."""
    import torch
    return torch.cat((data.root_pos_w.torch[:n],data.root_quat_w.torch[:n],
        data.root_lin_vel_w.torch[:n],data.root_ang_vel_w.torch[:n],
        data.body_pos_w.torch[:n,wheels].reshape(n,6)),-1)
