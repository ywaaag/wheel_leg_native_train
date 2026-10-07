"""Small device-side pose/family episode counters; no per-step host synchronization."""
import torch
from native_stand.command_v6.domain.episode_summary import build


class PoseEpisodeMetrics:
    def __init__(self, poses, device):
        self.poses=poses
        self.values=torch.zeros((len(poses),8),device=device,dtype=torch.float64)

    def reset(self):self.values.zero_()

    def observe(self, pose_indices, *, done, success, timeout, fault, initial_valid, duration):
        done=done.bool()
        values=torch.stack((done,done&success,done&~success&~fault,done&timeout,
            done&fault,done&initial_valid),-1).double()
        self.values[:,:6].index_add_(0,pose_indices,values)
        self.values[:,6].index_add_(0,pose_indices,torch.where(done,duration,0.).double())
        self.values[:,7].scatter_reduce_(0,pose_indices,torch.where(done,duration,0.).double(),
                                        reduce='amax',include_self=True)

    def summary(self):
        rows=[]
        for pose,values in zip(self.poses,self.values.cpu().tolist()):
            completed,success,failure,timeout,fault,valid=map(int,values[:6])
            rows.append(build(completed,values[6]/completed if completed else None,
                values[7] if completed else None,family=pose['family'],pose_id=pose['pose_id'],
                successes=success,task_failures=failure,timeouts=timeout,runtime_faults=fault,
                runtime_initial_valid_episodes=valid,offline_geometry_valid=bool(pose.get('offline_valid',False)),
                policy_recoverable=None,
                scope='stochastic training completed episodes; not independent capability certification'))
        return rows
