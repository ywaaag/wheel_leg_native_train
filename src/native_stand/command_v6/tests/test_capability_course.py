import torch

from native_stand.command_v6.domain.protocol import capability_gate
from native_stand.command_v6.domain.task_curriculum import TaskProgression


def test_capability_gate_uses_hold_and_zero_speed_not_drift():
    protocol = dict(scored_envs=1,steady_window_s=[2.,6.],motion_window_s=[2.,6.],
        closure_max_m=.005,peak_tilt_max_rad=.2,dual_contact_min=.95,
        standing_height_m=[.34,.46])
    rows = torch.zeros(1000,18)
    rows[:,2] = .4
    rows[:,8:10] = 3.
    rows[:,3] = .033
    rows[:,0] = torch.arange(1000)*.033*.01
    result = dict(seconds=10.,dt=.01,per_env=[dict(env_id=0,outcome='completed',
        continuous_s=10.,trace=rows.tolist(),closure_max_m=0.,peak_tilt_rad=0.,
        dual_contact_fraction=1.,height_steady_mean_m=.4,net_drift_m=.33)])
    assert capability_gate(result,[0,0],protocol)['passed_envs']==1
    rows[200:601,3] = .5
    result['per_env'][0]['trace'] = rows.tolist()
    assert capability_gate(result,[.5,0],protocol)['passed_envs']==1
    rows[200:601,3] = -.5
    result['per_env'][0]['trace'] = rows.tolist()
    assert capability_gate(result,[-.5,0],protocol)['passed_envs']==1
    assert capability_gate(result,[.5,0],protocol)['passed_envs']==0


def test_course_progression_starts_at_frozen_stage():
    progression = TaskProgression(dict(initial_stage=1,max_enabled_stage=8,
        consecutive_confirmations=1,standing_regression_confirmations=2))
    cases = [{'command':[0,0],'gate':{'accepted':True}},
             {'command':[1,0],'gate':{'accepted':True}},
             {'command':[-1,0],'gate':{'accepted':True}}]
    event = progression.confirm(250,cases,episode_length_s=31)
    assert event['stage']==1 and event['next_stage']==2 and event['promoted']
