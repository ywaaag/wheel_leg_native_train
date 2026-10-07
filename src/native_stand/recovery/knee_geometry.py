"""Pure geometry helpers for the Recovery knee-extension guard.

The guard compares the relative orientation of the authored upper/lower leg
rigid bodies. It is a target/initialization safety envelope, not a replacement
for USD joint limits or a fabricated force.
"""
import torch


def relative_body_angle(quat_a_xyzw: torch.Tensor, quat_b_xyzw: torch.Tensor) -> torch.Tensor:
    """Return shortest relative orientation angle in radians for xyzw quaternions."""
    a = quat_a_xyzw / quat_a_xyzw.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    b = quat_b_xyzw / quat_b_xyzw.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    # |dot| identifies the shortest quaternion arc and avoids sign ambiguity.
    dot = (a * b).sum(dim=-1).abs().clamp(0.0, 1.0)
    return 2.0 * torch.acos(dot)


def extension_guard(angle_rad: torch.Tensor, limit_rad: float, tolerance_rad: float = 1e-3):
    """Return (allowed, excess) without applying forces or changing physics."""
    if limit_rad <= 0.0 or tolerance_rad < 0.0:
        raise ValueError("limit_rad must be positive and tolerance_rad nonnegative")
    excess = (angle_rad - (limit_rad + tolerance_rad)).clamp_min(0.0)
    return excess <= 0.0, excess
