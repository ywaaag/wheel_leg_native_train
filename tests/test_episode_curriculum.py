import torch
from native_stand.command_v6.domain.episode_curriculum import EpisodeWindows,EpisodeTracker
from native_stand.command_v6.config import schedule
from native_stand.command_v6.config import validate
import json
from pathlib import Path


CONFIG={'lengths_s':[6,10,20,30],'episodes_per_window':128,'consecutive_windows':2,
    'gates':{'normal_timeout_min':.95,'metric_episode_pass_min':.95,'vx_abs_max_mps':.03,
        'yaw_abs_max_rad_s':.03,'excursion_max_m':.2,'tilt_max_rad':.2,'dual_contact_min':.8,
        'height_m':[.34,.38],'saturation_max':.1,'closure_max_m':.005}}


def good(level=0):
    return [level,1,0,CONFIG['lengths_s'][level],.01,.01,.05,.05,.95,.363,0,.001]


def test_exact_nonoverlapping_windows_and_two_passes():
    manager=EpisodeWindows(CONFIG)
    assert manager.consume([good() for _ in range(127)])==[]
    assert manager.consume([good()])[0]['passed']
    assert manager.level==0
    events=manager.consume([good() for _ in range(128)])
    assert events[0]['promoted'] and manager.level==1
    assert manager.state()['pending_episodes']['0']==0


def test_failed_window_breaks_streak_and_survival_is_not_enough():
    manager=EpisodeWindows(CONFIG)
    manager.consume([good() for _ in range(128)])
    bad=good();bad[4]=.1
    assert not manager.consume([bad for _ in range(128)])[0]['passed']
    manager.consume([good() for _ in range(128)])
    assert manager.level==0


def test_timeout_fraction_exact_boundary_and_level_isolation():
    manager=EpisodeWindows(CONFIG)
    bad=good();bad[1:3]=[0,1]
    assert manager.consume([bad]*6+[good()]*122)[0]['passed']
    assert not manager.consume([bad]*7+[good()]*121)[0]['passed']
    manager.consume([good(1)]*256)
    assert manager.level==0


def test_reset_adopts_new_deadline_current_episode_unchanged():
    tracker=EpisodeTracker(2,'cpu',CONFIG,.01)
    ids=torch.arange(2)
    tracker.reset(ids,torch.zeros(2,2),0)
    assert tracker.deadline_steps.tolist()==[600,600]
    tracker.reset(torch.tensor([0]),torch.zeros(2,2),1)
    assert tracker.deadline_steps.tolist()==[1000,600]
    assert tracker.assigned_level.tolist()==[1,0]
    assert not bool((torch.tensor([999,599])>=tracker.deadline_steps).any())
    assert bool((torch.tensor([1000,600])>=tracker.deadline_steps).all())


def test_statistics_survive_rollout_and_reset_only_own_environment():
    tracker=EpisodeTracker(2,'cpu',CONFIG,.01)
    tracker.reset(torch.arange(2),torch.zeros(2,2),0)
    def observe(done):
        tracker.observe(torch.zeros(2,2),torch.full((2,),.363),torch.zeros(2),torch.zeros(2),
            torch.ones(2,2,dtype=torch.bool),torch.zeros(2),torch.zeros(2),
            torch.zeros(2,dtype=torch.bool),torch.zeros(2,dtype=torch.bool),done)
    observe(torch.tensor([False,False]))
    assert tracker.collect()==[]
    observe(torch.tensor([True,False]))
    records=tracker.collect()
    assert len(records)==1 and records[0][3]==.02
    tracker.reset(torch.tensor([0]),torch.zeros(2,2),1)
    assert tracker.count.tolist()==[0,2]


def test_no_light_eval_or_every_ten_evaluation():
    evaluation={'checkpoint_every_updates':100,'light_every_updates':0,'full_every_updates':500}
    assert not schedule(10,'formal',evaluation)['full']
    assert not schedule(100,'formal',evaluation)['light']
    assert schedule(500,'formal',evaluation)['full']


def test_installed_ppo_bootstraps_only_timeout():
    from rsl_rl.algorithms import PPO
    from types import SimpleNamespace
    class Model:
        def update_normalization(self,obs):
            pass
        def reset(self,dones):
            pass
    class Transition:
        values=torch.tensor([[2.],[3.]])
        def clear(self):
            pass
    stored=[]
    instance=SimpleNamespace(actor=Model(),critic=Model(),rnd=None,transition=Transition(),
        gamma=.99,device='cpu',storage=SimpleNamespace(add_transition=lambda transition:stored.append(transition.rewards.clone())))
    PPO.process_env_step(instance,None,torch.tensor([1.,1.]),torch.tensor([1,1]),
        {'time_outs':torch.tensor([True,False])})
    assert torch.allclose(stored[0],torch.tensor([2.98,1.]))


def test_long_spec_schema_and_explicit_gate_identity():
    spec=json.loads((Path(__file__).resolve().parents[1]/'configs/experiments/stand_long_20261001/spec.json').read_text())
    assert validate(spec)==[]
    assert spec['curriculum']['episode_curriculum']['gates']==CONFIG['gates']
    assert spec['budget']['formal_updates']*spec['ppo']['envs']*spec['ppo']['steps_per_env']==24576000


def test_inference_observe_then_normal_reset_preserves_buffer_identity():
    tracker=EpisodeTracker(2,'cpu',CONFIG,.01)
    peaks=tracker.peaks
    with torch.inference_mode():
        tracker.observe(torch.tensor([[.1,0.],[.2,0.]]),torch.full((2,),.363),
            torch.zeros(2),torch.zeros(2),torch.ones(2,2,dtype=torch.bool),
            torch.zeros(2),torch.zeros(2),torch.zeros(2,dtype=torch.bool),
            torch.zeros(2,dtype=torch.bool),torch.zeros(2,dtype=torch.bool))
    assert tracker.peaks is peaks and not tracker.peaks.is_inference()
    tracker.reset(torch.tensor([0]),torch.zeros(2,2),0)
    assert tracker.peaks[0].tolist()==[0.,0.,0.]
    assert abs(float(tracker.peaks[1,0])-.2)<1e-6


def test_application_shutdown_receives_terminal_exit_code():
    from native_stand.command_v6.train import close_app
    class FakeApp:
        def close(self, *, exit_code):
            self.exit_code=exit_code
    app=FakeApp()
    close_app(app,True)
    assert app.exit_code==1
    close_app(app,False)
    assert app.exit_code==0


def test_fast_shutdown_process_exit_matches_failure():
    import os
    import subprocess
    import sys
    environment={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
    code='''import os,sys
from native_stand.command_v6.train import close_app
class FastApp:
    def close(self, *, exit_code):
        os._exit(exit_code)
close_app(FastApp(),sys.argv[1]=="failed")
'''
    for state,expected in [('failed',1),('completed',0)]:
        child=subprocess.run([sys.executable,'-c',code,state],env=environment,timeout=20)
        assert child.returncode==expected
