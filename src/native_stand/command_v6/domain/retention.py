"""Actor behavior-retention primitives for fixed, already-qualified commands."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import torch


@dataclass(frozen=True)
class RetentionBatch:
    observations: torch.Tensor
    commands: torch.Tensor
    episode_age_s: torch.Tensor
    metadata: dict


def load_reference(path, *, expected_sha256=None) -> RetentionBatch:
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("reference observation SHA differs from spec")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    batch = RetentionBatch(payload["observations"].float(), payload["commands"].float(),
                           payload["episode_age_s"].float(), payload.get("metadata", {}))
    batch = replace(batch, metadata={**batch.metadata, "path": str(path), "sha256": digest})
    validate_reference(batch, min_episode_age_s=float(payload.get("min_episode_age_s", 0.0)))
    validate_observed_commands(batch)
    return batch


def command_mask(commands: torch.Tensor, allowed=((0.0, 0.0), (0.5, 0.0), (-0.5, 0.0))) -> torch.Tensor:
    """Return the exact command whitelist mask; future commands are excluded."""
    if commands.ndim != 2 or commands.shape[-1] != 2:
        raise ValueError("commands must have shape [N, 2]")
    mask = torch.zeros(commands.shape[0], dtype=torch.bool, device=commands.device)
    for vx, yaw in allowed:
        mask |= (commands[:, 0] == vx) & (commands[:, 1] == yaw)
    return mask


def validate_reference(batch: RetentionBatch, *, min_episode_age_s: float = 0.0) -> None:
    n = batch.observations.shape[0]
    if batch.observations.ndim != 2 or n == 0:
        raise ValueError("reference observations must be a non-empty [N, D] tensor")
    if batch.commands.shape != (n, 2) or batch.episode_age_s.shape != (n,):
        raise ValueError("reference metadata shape mismatch")
    if not torch.all(command_mask(batch.commands)):
        raise ValueError("reference contains a command outside 0/+0.5/-0.5")
    counts = [(batch.commands == batch.commands.new_tensor(c)).all(-1).sum().item()
              for c in ((0., 0.), (.5, 0.), (-.5, 0.))]
    if len(set(counts)) != 1 or counts[0] == 0:
        raise ValueError(f"reference commands are not balanced: {counts}")
    if not bool((batch.episode_age_s >= min_episode_age_s).all()):
        raise ValueError("reference does not cover the required episode tail")


def validate_observed_commands(batch: RetentionBatch) -> None:
    from .command_schedule import effective
    schedule = batch.metadata.get('schedule_s')
    if batch.observations.shape[1] != 150 or not isinstance(schedule, list) or len(schedule) != 4:
        raise ValueError('reference lacks 150D observations or frozen command schedule')
    expected = effective(batch.commands, batch.episode_age_s,
        entry=schedule[0], ramp=schedule[1], hold=schedule[2], exit=schedule[3])[:, :2]
    observed = batch.observations[:, 6:8] / batch.observations.new_tensor((2., .25))
    if not torch.allclose(observed, expected, atol=1e-4):
        raise ValueError('reference command labels differ from actor observations')


def balanced_subset(batch: RetentionBatch, samples_per_command: int) -> RetentionBatch:
    if samples_per_command < 1:
        raise ValueError('retention samples_per_command must be positive')
    indices = []
    for command in ((0., 0.), (.5, 0.), (-.5, 0.)):
        matches = torch.nonzero((batch.commands == batch.commands.new_tensor(command)).all(-1)).flatten()
        if matches.numel() < samples_per_command:
            raise ValueError('reference has too few samples for a command')
        positions = torch.linspace(0, matches.numel()-1, samples_per_command).round().long()
        indices.append(matches[positions])
    selected = torch.cat(indices)
    return RetentionBatch(batch.observations[selected], batch.commands[selected],
        batch.episode_age_s[selected], {**batch.metadata, 'samples_per_command': samples_per_command})


def behavior_retention_loss(actor, source_actor, observations: torch.Tensor) -> torch.Tensor:
    """MSE between actor distribution means; source output is detached."""
    if isinstance(observations, torch.Tensor):
        from tensordict import TensorDict
        observations=TensorDict({'policy':observations[:, :25], 'history':observations[:, 25:]},
                                batch_size=[observations.shape[0]])
    current = actor(observations, stochastic_output=False)
    with torch.no_grad():
        target = source_actor(observations, stochastic_output=False).detach()
    if current.shape != target.shape:
        raise ValueError("source and candidate actor output shapes differ")
    return (current - target).square().mean()


def attach_optimizer_retention(ppo, source_actor, reference: RetentionBatch, *, lam: float):
    """Inject retention gradient immediately before PPO's existing optimizer step.

    This leaves the installed rsl_rl PPO implementation and critic objective intact.
    """
    if lam < 0 or not torch.isfinite(torch.tensor(lam)):
        raise ValueError("retention lambda must be finite and non-negative")
    validate_reference(reference)
    original_step = ppo.optimizer.step

    def step(*args, **kwargs):
        if lam:
            raw = behavior_retention_loss(ppo.actor, source_actor, reference.observations)
            if getattr(ppo,'_record_retention_diagnostics',False) and getattr(ppo,'_reference_gradient',None) is None:
                parameters=[p for p in ppo.actor.parameters() if p.requires_grad]
                before=[p.grad.detach().clone() if p.grad is not None else torch.zeros_like(p) for p in parameters]
                gradients=torch.autograd.grad(raw,parameters,retain_graph=True,allow_unused=True)
                gradients=[g.detach() if g is not None else torch.zeros_like(p) for p,g in zip(parameters,gradients)]
                from native_stand.recovery.standing import gradient_comparison
                ppo._reference_gradient=gradient_comparison(before,gradients,lam,lam)
            loss = lam * raw
            loss.backward()
            torch.nn.utils.clip_grad_norm_(ppo.actor.parameters(), ppo.max_grad_norm)
            ppo._last_retention_raw = float(raw.detach())
            ppo._last_retention_loss = float(loss.detach())
        else:
            ppo._last_retention_raw = 0.0
            ppo._last_retention_loss = 0.0
        result = original_step(*args, **kwargs)
        return result

    ppo.optimizer.step = step
    ppo.retention_lambda = float(lam)
    return ppo
