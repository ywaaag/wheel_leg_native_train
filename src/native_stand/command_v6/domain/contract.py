"""Pure native physical-joint observation and action calculations."""
import torch

LEG_COLUMNS = (0, 1, 3, 4)
WHEEL_COLUMNS = (2, 5)
EFFORT_LIMITS = (40., 40., 5.5, 40., 40., 5.5)


def projection_fraction(action, *, leg_scale, combined_radius):
    """Requested pair projection occupancy; zero means explicitly disabled."""
    if combined_radius <= 0.:
        return action.new_zeros(action.shape[0])
    delta = (action.clamp(-1., 1.)[:, LEG_COLUMNS] * leg_scale).reshape(-1, 2, 2)
    return (torch.linalg.vector_norm(delta, dim=-1) > combined_radius).float().mean(-1)


def frame(angular_body, gravity_body, command, q, dq, previous_action, reference):
    if q.shape[-1] != 6 or command.shape != (q.shape[0], 3):
        raise ValueError("physical state or command shape differs")
    result = torch.cat((angular_body * .25, gravity_body,
        command * command.new_tensor((2., .25, 5.)),
        (q[:, LEG_COLUMNS] - reference[:, LEG_COLUMNS]) * 2.,
        dq * .05, previous_action), dim=-1)
    if result.shape[-1] != 25:
        raise ValueError("frame is not 25D")
    return result


def history(previous, current, reset):
    if previous.shape != (current.shape[0], 125) or current.shape[-1] != 25:
        raise ValueError("expected 5x25 history and 25D frame")
    shifted = torch.cat((previous[:, 25:], current), dim=-1)
    return torch.where(reset[:, None], current.repeat(1, 5), shifted)


def targets(action, reference, *, leg_scale=.1, combined_radius=.12, wheel_scale=6.):
    if action.shape[-1] != 6:
        raise ValueError("action must be 6D")
    clipped = action.clamp(-1., 1.)
    delta = (clipped[:, LEG_COLUMNS] * leg_scale).reshape(-1, 2, 2)
    # A zero radius explicitly disables the legacy pair projection.  Keeping
    # this branch here makes the action contract an intentional choice instead
    # of relying on a 0/0-like numeric side effect.
    if combined_radius > 0.:
        norm = torch.linalg.vector_norm(delta, dim=-1, keepdim=True)
        delta *= (combined_radius / norm.clamp_min(combined_radius))
    legs = reference[:, LEG_COLUMNS] + delta.reshape(-1, 4)
    wheels = clipped[:, WHEEL_COLUMNS] * wheel_scale
    return clipped, legs, wheels


def effort(q, dq, leg_target, wheel_target, *, leg_kp=60., leg_kd=2., wheel_kv=1.):
    requested = torch.zeros_like(q)
    requested[:, LEG_COLUMNS] = leg_kp * (leg_target-q[:, LEG_COLUMNS])-leg_kd * dq[:, LEG_COLUMNS]
    requested[:, WHEEL_COLUMNS] = wheel_kv * (wheel_target-dq[:, WHEEL_COLUMNS])
    limits = q.new_tensor(EFFORT_LIMITS)
    return requested, requested.clamp(-limits, limits)
