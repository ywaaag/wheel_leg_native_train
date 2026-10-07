"""Device-side rollout aggregates; one host transfer per update."""
import torch


class RolloutMetrics:
    def __init__(self, names, causes, num_envs, device):
        self.names = tuple(names)
        self.causes = tuple(causes)
        self.num_envs = num_envs
        self.raw = torch.zeros(len(names), device=device, dtype=torch.float64)
        self.weighted = torch.zeros_like(self.raw)
        self.terminations = torch.zeros(len(causes), device=device, dtype=torch.int64)
        self.contact = torch.zeros((), device=device, dtype=torch.int64)
        self.saturated = torch.zeros((), device=device, dtype=torch.int64)
        self.closure_max = torch.zeros((), device=device)
        self.steps = 0
        self.episode_count = torch.zeros((), device=device, dtype=torch.int64)
        self.episode_seconds_sum = torch.zeros((), device=device, dtype=torch.float64)
        self.episode_seconds_max = torch.zeros((), device=device, dtype=torch.float64)
        self.motion_sum=torch.zeros(5,device=device,dtype=torch.float64)
        self.motion_peak=torch.zeros(2,device=device,dtype=torch.float64)
        self.motion_samples=0

    def add(self, raw, weighted, causes, contact, closure, effort, limits, episode_seconds=None, episode_done=None, motion=None):
        if set(raw) != set(self.names) or set(causes) != set(self.causes):
            raise ValueError("rollout metric fields changed")
        self.raw += torch.stack([raw[n].double().sum() for n in self.names])
        self.weighted += torch.stack([weighted[n].double().sum() for n in self.names])
        self.terminations += torch.stack([causes[n].long().sum() for n in self.causes])
        self.contact += contact.all(-1).long().sum()
        self.saturated += (effort.abs() >= effort.new_tensor(limits)-1e-4).any(-1).long().sum()
        self.closure_max = torch.maximum(self.closure_max, closure.amax())
        self.steps += 1
        if episode_seconds is not None:
            durations=episode_seconds*episode_done
            self.episode_count += episode_done.long().sum()
            self.episode_seconds_sum += durations.sum()
            self.episode_seconds_max = torch.maximum(self.episode_seconds_max,durations.max())
        if motion is not None:
            self.motion_sum+=motion.double().sum(0)
            self.motion_peak=torch.maximum(self.motion_peak,motion[:,3:5].double().amax(0))
            self.motion_samples+=self.num_envs

    def summary(self):
        if self.steps == 0:
            raise ValueError("empty rollout")
        denom = self.steps*self.num_envs
        packed = torch.cat((self.raw/denom,self.weighted/denom,self.terminations.double(),
                            (self.contact.double()/denom).reshape(1),
                            (self.saturated.double()/denom).reshape(1),
                            self.closure_max.double().reshape(1), self.episode_count.double().reshape(1),
                            self.episode_seconds_sum.reshape(1),self.episode_seconds_max.reshape(1),
                            self.motion_sum/max(1,self.motion_samples),self.motion_peak)).cpu().tolist()
        n, m = len(self.names), len(self.causes)
        return {"samples":denom,"raw_mean":dict(zip(self.names,packed[:n])),
                "weighted_mean":dict(zip(self.names,packed[n:2*n])),
                "termination_count":dict(zip(self.causes,map(int,packed[2*n:2*n+m]))),
                "dual_contact_fraction":packed[2*n+m],
                "saturation_fraction":packed[2*n+m+1],
                "closure_max_m":packed[2*n+m+2],
                "episodes":{"completed":int(packed[2*n+m+3]),
                    "mean_duration_s":packed[2*n+m+4]/packed[2*n+m+3] if packed[2*n+m+3] else None,
                    "max_duration_s":packed[2*n+m+5] if packed[2*n+m+3] else None},
                'motion':dict(zip(('mean_abs_vx_mps','mean_abs_yaw_rad_s','mean_height_m',
                    'mean_tilt_rad','mean_episode_excursion_m','peak_tilt_rad','max_episode_excursion_m'),
                    packed[2*n+m+6:])) if self.motion_samples else None}
