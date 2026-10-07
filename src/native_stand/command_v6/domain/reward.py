"""Command-conditioned standing reward with explicit tensor inputs."""
import torch
from .contract import EFFORT_LIMITS

def compute(root_z, up, vx, vy, yaw, command, contact, effort, action,
            previous_action, leg_q, terminated, *, weights, height_width,
            linear_denominator, yaw_denominator, terminal_penalty, dt=.01,
            action_delta_wheel_factor=1.):
    raw = {
        "upright": up.clamp(0.,1.).square(),
        "height": torch.exp(-((root_z-command[:,2])/height_width).square()),
        "velocity_tracking": torch.exp(-((vx-command[:,0]).square()+vy.square())/linear_denominator
                                       -(yaw-command[:,1]).square()/yaw_denominator),
        "two_wheel_contact": contact.all(-1).float(),
        "effort": (effort/effort.new_tensor(EFFORT_LIMITS)).square().mean(-1),
        "action_delta": ((action-previous_action)*action.new_tensor(
            (1.,1.,action_delta_wheel_factor,1.,1.,action_delta_wheel_factor))).square().mean(-1),
        "joint_margin": torch.relu(leg_q.abs()-.25).square().mean(-1),
    }
    weighted = {name:value*weights[name] for name,value in raw.items()}
    return sum(weighted.values())*dt+terminated.float()*terminal_penalty, raw, weighted
