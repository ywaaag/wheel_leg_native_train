"""Episode-target cohort width selection; no runtime or file access."""
import torch


def linear_width(target_xy, config):
    default = config['linear_error_denominator']
    cohort = config.get('linear_cohort_width')
    if cohort is None:
        return default
    retained = target_xy.new_tensor(cohort['retained_commands'])
    mask = (target_xy[:, None, :] == retained[None, :, :]).all(-1).any(-1)
    return torch.where(mask, target_xy.new_tensor(cohort['retained_denominator']),
                       target_xy.new_tensor(default))
