"""Explicit command ramp and categorical sampling; no file or env reads."""
import torch


def effective(target, elapsed_s, *, height=.363, entry=.5, ramp=.5, hold=3., exit=.5):
    t = elapsed_s.unsqueeze(-1)
    if exit == 0:
        # Explicit hold-until-timeout recipe; never divide by a zero exit time.
        gain = ((t-entry)/ramp).clamp(0.,1.)
        return torch.cat((target*gain, torch.full_like(target[:, :1], height)), -1)
    gain = torch.minimum(((t-entry)/ramp).clamp(0.,1.),
                         ((entry+ramp+hold+exit-t)/exit).clamp(0.,1.))
    return torch.cat((target*gain, torch.full_like(target[:, :1], height)), -1)


def sample(commands, probabilities, count, *, device, generator=None):
    if len(commands) != len(probabilities):
        raise ValueError("command weights mismatch")
    weights = torch.as_tensor(probabilities, device=device, dtype=torch.float32)
    if not torch.isclose(weights.sum(), weights.new_tensor(1.)) or (weights < 0).any():
        raise ValueError("command probabilities must sum to one")
    indices = torch.multinomial(weights, count, replacement=True, generator=generator)
    values = torch.as_tensor(commands, device=device, dtype=torch.float32)[indices]
    return values, torch.bincount(indices, minlength=len(commands))
