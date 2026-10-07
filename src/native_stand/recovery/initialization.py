"""CPU-testable initialization boundary; no Isaac imports or implicit config."""
import torch


def settlement_joint_indices(joint_names):
    """Exclude only named passive guide-wheel spins; keep linkage and main wheels."""
    indices = [i for i, name in enumerate(joint_names)
               if not (name.startswith('guide_wheel_') and name.endswith('_spin'))]
    if not indices:
        raise ValueError('No joints remain for settlement validation')
    return indices


def zero_initial_velocities(robot, env_ids, joint_count, device):
    """One explicit local reset boundary, not an ongoing stabilizer."""
    robot.write_root_velocity_to_sim_index(
        root_velocity=torch.zeros((len(env_ids), 6), device=device), env_ids=env_ids)
    robot.write_joint_velocity_to_sim_index(
        velocity=torch.zeros((len(env_ids), joint_count), device=device), env_ids=env_ids)
