"""Pure physical-joint control and standing reward calculations."""
import torch

JOINT_NAMES=("left_hip_pitch","left_active_link_pitch","left_wheel_spin",
             "right_hip_pitch","right_active_link_pitch","right_wheel_spin")
LEG_COLUMNS=(0,1,3,4)
WHEEL_COLUMNS=(2,5)
PHYSICAL_LIMITS=(40.,40.,5.5,40.,40.,5.5)


def targets(action,reference,*,leg_scale=.1,wheel_scale=6.,combined_radius=.12):
    if action.ndim!=2 or action.shape[-1]!=6:
        raise ValueError("action must have shape [N,6]")
    clipped=action.clamp(-1.,1.)
    q_target=reference[:,list(LEG_COLUMNS)]+clipped[:,list(LEG_COLUMNS)]*leg_scale
    q_target=q_target.reshape(-1,2,2)
    delta=q_target-reference[:,list(LEG_COLUMNS)].reshape(-1,2,2)
    norm=torch.linalg.vector_norm(delta,dim=-1,keepdim=True)
    delta=delta*(combined_radius/norm.clamp_min(combined_radius))
    q_target=reference[:,list(LEG_COLUMNS)].reshape(-1,2,2)+delta
    wheel_target=clipped[:,list(WHEEL_COLUMNS)]*wheel_scale
    return clipped,q_target.reshape(-1,4),wheel_target


def physical_pd(q,dq,leg_target,wheel_target,*,kp=60.,kd=2.,kv=1.):
    if q.shape!=dq.shape or q.shape[-1]!=6:
        raise ValueError("physical q/dq must have shape [N,6]")
    effort=torch.zeros_like(q)
    effort[:,list(LEG_COLUMNS)]=kp*(leg_target-q[:,list(LEG_COLUMNS)])-kd*dq[:,list(LEG_COLUMNS)]
    effort[:,list(WHEEL_COLUMNS)]=kv*(wheel_target-dq[:,list(WHEEL_COLUMNS)])
    limit=q.new_tensor(PHYSICAL_LIMITS)
    return effort,effort.clamp(-limit,limit)


def frame_observation(angular_body,gravity_body,q,dq,previous_action,reference):
    """22D: body omega 3, body gravity 3, leg q offset 4, joint dq 6, previous 6."""
    return torch.cat((angular_body*.25,gravity_body,
                      (q[:,list(LEG_COLUMNS)]-reference[:,list(LEG_COLUMNS)])*2.,
                      dq*.05,previous_action),dim=-1)


def update_history(history,frame,reset_mask):
    shifted=torch.cat((history[:,frame.shape[1]:],frame),dim=-1)
    return torch.where(reset_mask[:,None],frame.repeat(1,5),shifted)


def stand_reward(root_z,up,vx,vy,yaw,wheel_contact,effort,action,previous_action,
                 leg_q,terminated,*,dt=.01):
    raw={
        "upright":up.clamp(0.,1.).square(),
        "height":torch.exp(-((root_z-.4)/.06).square()),
        "zero_velocity":torch.exp(-(vx.square()+vy.square())/.04-yaw.square()/.09),
        "two_wheel_contact":wheel_contact.all(-1).float(),
        "effort":(effort/effort.new_tensor(PHYSICAL_LIMITS)).square().mean(-1),
        "action_delta":(action-previous_action).square().mean(-1),
        "joint_margin":torch.relu(leg_q.abs()-.25).square().mean(-1),
    }
    weights={"upright":2.,"height":1.,"zero_velocity":1.,
             "two_wheel_contact":.5,"effort":-.02,"action_delta":-.01,
             "joint_margin":-.05}
    weighted={key:value*weights[key] for key,value in raw.items()}
    reward=sum(weighted.values())*dt-terminated.float()
    return reward,raw,weighted
