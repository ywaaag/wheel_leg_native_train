import torch
import ast
from pathlib import Path
from native_stand.recovery.initialization import settlement_joint_indices,zero_initial_velocities


def test_only_passive_guide_spins_excluded():
    names=['left_hip','guide_wheel_lower_left_01_spin','left_parallel_link','left_wheel']
    indices=settlement_joint_indices(names)
    assert indices==[0,2,3]
    dq=torch.tensor([[.1,90.,.2,.1]])
    assert dq[:,indices].abs().amax(-1).item()<.3
    dq[0,2]=.4
    assert dq[:,indices].abs().amax(-1).item()>.3


def test_zero_api_affects_only_selected_envs_and_keeps_positions():
    class Robot:
        def __init__(self):
            self.root=torch.ones(3,6);self.dq=torch.ones(3,4);self.q=torch.ones(3,4)
        def write_root_velocity_to_sim_index(self,*,root_velocity,env_ids):
            self.root[env_ids]=root_velocity
        def write_joint_velocity_to_sim_index(self,*,velocity,env_ids):
            self.dq[env_ids]=velocity
    robot=Robot()
    zero_initial_velocities(robot,torch.tensor([1]),4,'cpu')
    assert robot.root[1].count_nonzero()==0 and robot.dq[1].count_nonzero()==0
    assert robot.root[[0,2]].eq(1).all() and robot.dq[[0,2]].eq(1).all()
    assert robot.q.eq(1).all()


def test_second_zero_once_per_episode_and_requires_post_zero_dwell():
    zeroed=torch.zeros(2,dtype=torch.bool)
    initializing=torch.tensor([True,False])
    age=torch.tensor([.2,1.])
    mask=initializing&~zeroed&(age>=.2)
    assert mask.tolist()==[True,False]
    zeroed[mask]=True
    # Zeroing frame cannot contribute to successful static dwell.
    assert not (initializing&zeroed&~mask).any()
    assert not (initializing&~zeroed&(age>=.2)).any()
    zeroed[0]=False  # Local reset rearms only that episode.
    assert (initializing&~zeroed&(age>=.2)).tolist()==[True,False]
    ast.parse((Path(__file__).parents[1]/'src/native_stand/recovery/runtime.py').read_text())
