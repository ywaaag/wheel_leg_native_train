"""Streaming full-episode standing gates, with explicit time-limit semantics."""
import torch


class HoldingEpisode:
    CHECK_NAMES = ('valid_state', 'steady_samples', 'height_mean', 'height_fraction',
                   'dual_contact', 'mean_pitch', 'mean_roll', 'peak_pitch',
                   'peak_roll', 'peak_tilt', 'closure', 'saturation')
    METRIC_NAMES = ('duration_s', 'steady_sample_count', 'height_mean_m',
                    'height_in_range_fraction', 'dual_contact_fraction',
                    'mean_abs_pitch_rad', 'mean_abs_roll_rad', 'peak_abs_pitch_rad',
                    'peak_abs_roll_rad', 'peak_tilt_rad', 'closure_peak_m',
                    'saturation_fraction_policy')

    def __init__(self, num_envs, device, *, dt, protocol):
        self.protocol = protocol
        self.dt = dt
        self.steps_required = round(protocol['seconds']/dt)
        self.steps = torch.zeros(num_envs, device=device, dtype=torch.long)
        self.count = torch.zeros_like(self.steps)
        self.sums = torch.zeros(num_envs, 5, device=device, dtype=torch.float64)
        self.peaks = torch.zeros(num_envs, 4, device=device)
        self.saturation = torch.zeros(num_envs, device=device, dtype=torch.float64)
        self.valid = torch.ones(num_envs, device=device, dtype=torch.bool)
        self.rollout_outcomes = torch.zeros(5, device=device, dtype=torch.long)
        self.rollout_gate_failures = torch.zeros(len(self.CHECK_NAMES), device=device, dtype=torch.long)
        self.rollout_metrics = torch.zeros(len(self.METRIC_NAMES), device=device, dtype=torch.float64)
        self.rollout_metric_count = torch.zeros_like(self.rollout_metrics, dtype=torch.long)
        self.rollout_metric_max = torch.full_like(self.rollout_metrics, -float('inf'))

    def begin_rollout(self):
        self.rollout_outcomes.zero_()
        self.rollout_gate_failures.zero_()
        self.rollout_metrics.zero_()
        self.rollout_metric_count.zero_()
        self.rollout_metric_max.fill_(-float('inf'))

    def reset(self, ids):
        self.steps[ids] = 0
        self.count[ids] = 0
        self.sums[ids] = 0
        self.peaks[ids] = 0
        self.saturation[ids] = 0
        self.valid[ids] = True

    def observe(self, height, contact, angles, tilt, closure, saturated, *, active, valid):
        self.steps.add_(active.long())
        p = self.protocol
        time = self.steps*self.dt
        steady = active & (time >= p['steady_window_s'][0]-1e-5) & (time <= p['steady_window_s'][1]+1e-5)
        low, high = p['height_m']
        values = torch.stack((height, ((height >= low) & (height <= high)).float(),
                              (contact > 2.).all(-1).float(), angles[:, 0].abs(),
                              angles[:, 1].abs()), -1)
        peaks = torch.cat((angles.abs(), tilt[:, None], closure[:, None]), -1)
        finite = torch.isfinite(values).all(-1) & torch.isfinite(peaks).all(-1)
        self.valid &= ~active | (valid & finite)
        self.count.add_(steady.long())
        self.sums.add_(torch.where(steady[:, None], values.double(), 0.))
        self.peaks.copy_(torch.maximum(self.peaks, torch.where(active[:, None], peaks, 0.)))
        self.saturation.add_((saturated & active).double())

    def certificate_checks(self):
        p = self.protocol
        mean = (self.sums/self.count.clamp_min(1)[:, None]).float().double()
        peaks = self.peaks.double()
        low, high = p['height_m']
        saturation = (self.saturation/self.steps.clamp_min(1)).float().double()
        checks = torch.stack((self.valid, self.count > 0,
            (mean[:, 0] >= low) & (mean[:, 0] <= high),
            mean[:, 1] >= p['height_fraction_min'], mean[:, 2] >= p['dual_contact_min'],
            mean[:, 3] <= p['level_mean_max_rad'], mean[:, 4] <= p['level_mean_max_rad'],
            peaks[:, 0] <= p['level_peak_max_rad'], peaks[:, 1] <= p['level_peak_max_rad'],
            peaks[:, 2] <= p['peak_tilt_max_rad'], peaks[:, 3] <= p['closure_max_m'],
            saturation <= p['saturation_max']), -1)
        metrics = torch.cat(((self.steps*self.dt).double()[:, None],
                             self.count.double()[:, None], mean, peaks, saturation[:, None]), -1)
        return checks, metrics

    def outcome(self, *, failed, fault):
        # A certificate failure at the deadline remains a time limit.
        timeout = (self.steps >= self.steps_required) & ~failed & ~fault
        checks, _ = self.certificate_checks()
        accepted = checks.all(-1)
        return timeout, timeout & accepted

    def record_outcomes(self, *, terminated, truncated, fault):
        """Reduce episode-end evidence on-device; serialization is once per update."""
        checks, metrics = self.certificate_checks()
        certificate = truncated & checks.all(-1)
        completed = terminated | truncated
        self.rollout_outcomes.add_(torch.stack((completed.long().sum(),
            truncated.long().sum(), certificate.long().sum(),
            (terminated & ~fault).long().sum(), fault.long().sum())))
        self.rollout_gate_failures.add_((~checks & truncated[:, None]).long().sum(0))
        finite = torch.isfinite(metrics) & completed[:, None]
        self.rollout_metrics.add_(torch.where(finite, metrics, 0.).sum(0))
        self.rollout_metric_count.add_(finite.long().sum(0))
        self.rollout_metric_max.copy_(torch.maximum(self.rollout_metric_max,
            torch.where(finite, metrics, -float('inf')).amax(0)))

    def rollout_summary(self):
        packed = torch.cat((self.rollout_outcomes.double(), self.rollout_gate_failures.double(),
            self.rollout_metrics, self.rollout_metric_count.double(), self.rollout_metric_max)).cpu().tolist()
        names = ('completed_episodes', 'normal_timeouts', 'certificate_passed',
                 'physical_failures', 'runtime_faults')
        counts = dict(zip(names, map(int, packed[:5])))
        n = len(self.CHECK_NAMES)
        failures = dict(zip(self.CHECK_NAMES, map(int, packed[5:5+n])))
        m = len(self.METRIC_NAMES)
        sums = packed[5+n:5+n+m]
        samples = packed[5+n+m:5+n+2*m]
        peaks = packed[5+n+2*m:]
        metrics = {name: {'mean': total/count if count else None,
                         'max': peak if count else None, 'sample_count': int(count)}
                   for name, total, count, peak in zip(self.METRIC_NAMES, sums, samples, peaks)}
        return {'scope': 'stochastic training episode ends, pre-reset; not independent evaluation',
                'counts': counts, 'certificate_evaluated_episodes': counts['normal_timeouts'],
                'failed_gate_counts': failures, 'metrics': metrics,
                'sampling': 'policy-rate tensor reductions; saturation is held latest PD torque'}
