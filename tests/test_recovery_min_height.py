"""Independent boundary fixtures for the versioned finite rise/hold task."""
import pytest
import torch
from native_stand.recovery.min_height import RiseHold,protocol,height_terms,score


def trace(n=1220,entry=200,h=.42):
    s=torch.zeros(n,39,dtype=torch.float64);a=torch.zeros(n,10,dtype=torch.float64)
    s[:,0]=torch.arange(1,n+1)*.01;s[:,6]=.168;s[entry:,6]=h
    s[:,10:12]=3.;s[:,13]=.01;s[:,29]=1
    return s,a


def review(s,a,**kw):
    return score(s,a,dt=.01,p=protocol(),initial_valid=True,**kw)


@pytest.mark.parametrize('height',[.30,.36,.42])
def test_new_height_and_positive_clearance(height):
    s,a=trace(h=height);assert review(s,a)['accepted']
    s[400,6]=.2999;assert not review(s,a)['accepted']
    s[400,6]=height;s[400,13]=0.;assert not review(s,a)['accepted']


def test_height_platform_no_upper_preference():
    t=height_terms(torch.tensor([.168,.2999,.30,.34,.36,.42]))
    total=2*t['lift']+3*t['standing_height']
    assert torch.isfinite(total).all() and total[0]==0 and total[-1]==total[-2]==5


def test_first_confirmed_entry_exact_next1000_and_terminal():
    s,a=trace();r=review(s,a,terminated=True,terminal_success=True)
    assert r['accepted'] and r['entry_confirmation_index']==219 and r['post_rise_observed_s']==10.
    assert not review(s[:-1],a[:-1],terminated=True,terminal_success=True)['accepted']
    assert not review(s,a,terminated=True,terminal_success=False)['accepted']
    assert r['diagnostic_hold_prefix_s']==10.


def test_short_crossing_first_latch_and_mean_not_entry_peak():
    s,a=trace();s[10:29,6]=.42
    assert review(s,a)['entry_confirmation_index']==219
    a[300,0]=.11;assert review(s,a)['accepted']
    a[300,0]=.151;assert not review(s,a)['accepted']
    a[300,0]=0.;s[300,6]=.29
    assert review(s,a)['entry_confirmation_index']==219 and not review(s,a)['accepted']


def online():
    return RiseHold(1,'cpu',dt=.01,p=protocol())


def step(f,*,h=.42,angle=0.,clearance=.01,active=True,fault=False):
    return f.observe(torch.tensor([h]),torch.tensor([[angle,0.]]),torch.tensor([0.]),
        torch.tensor([[3.,3.]]),torch.tensor([clearance]),torch.tensor([0.]),torch.tensor([False]),
        active=torch.tensor([active]),valid=torch.tensor([True]),safety_failed=torch.tensor([False]),fault=torch.tensor([fault]))


@pytest.mark.parametrize('confirm',[780,1150])
def test_late_entry_deadline_rollout_and_once(confirm):
    f=online()
    for i in range(confirm):
        out=step(f,h=.42 if i>=confirm-20 else .168)
        assert not out[2].item()
    assert float(f.entry[0])==pytest.approx(confirm*.01)
    for i in range(1000):
        out=step(f)
        assert out[0].item()==(i==999)
        assert out[2].item()==(i==999)
    assert not step(f)[2].item()
    f.reset(torch.tensor([0]));assert f.entry[0]==-1 and f.count[0]==0


def test_initialization_excluded_noentry_and_safety_priority():
    f=online()
    for _ in range(200):step(f,active=False)
    assert f.age[0]==0
    for i in range(1150):out=step(f,h=.168)
    assert out[1].item() and not out[0].item()
    f=online();assert step(f,fault=True)[2].item()


def test_online_offline_same_first_window_and_peak_latch():
    s,a=trace();f=online()
    for i in range(len(s)):
        out=step(f,h=float(s[i,6]),angle=.11 if i==300 else 0.)
    a[300,0]=.11
    assert out[0].item()==review(s,a,terminated=True,terminal_success=True)['accepted']
    assert f.count[0]==1000


def test_prepared_v2_config_and_old_configs_unchanged():
    import json
    from pathlib import Path
    from native_stand.command_v6.config import validate
    root=Path(__file__).resolve().parents[1]
    old=json.loads((root/'configs/experiments/2026_10_7-20_55__recovery_level2_alignment_from50/spec.json').read_text())
    assert not validate(old)


def test_initialization_accept_sample_not_counted_offline():
    s,a=trace(entry=0,n=1040);s[:40,0]=0;s[:40,32]=7
    s[40:,0]=torch.arange(1,1001)*.01
    r=review(s,a)
    assert r['entry_confirmation_index']==59 and r['post_rise_observed_s']==9.8 and not r['accepted']


def test_phase_coverage_disjoint_pose_groups_and_units():
    from native_stand.recovery.min_height import PhaseCoverage
    c=PhaseCoverage(2,'cpu')
    c.observe(torch.tensor([0,1]),torch.tensor([0,3]),torch.tensor([True,True]),
        {'lift':torch.tensor([.5,1.])},{'lift':torch.tensor([.01,.02])},torch.zeros(2,6,dtype=torch.bool))
    rows=c.summary([{'pose_id':'a','family':'DrawBack'},{'pose_id':'b','family':'R0'}],.01)
    assert sum(r['transition_count'] for r in rows)==2
    assert rows[0]['continuous_reward']['lift']['weighted_dt_sum']==pytest.approx(.01)
    assert rows[7]['transition_count']==1 and rows[1]['transition_count']==0
    c.reset();assert c.count.sum()==0


def test_guard_consecutive_fail_pass_fail_resets():
    from native_stand.recovery.min_height import ProgressGuard
    cfg={'entry_count_drop':2,'confirmations':2,'delta_min_rad_s':10.,'alternation_fraction_min':.8,'limit_fraction_min':.5}
    def row(entered=True,osc=False):
        trace=torch.zeros(1200,54)
        if osc:
            trace[:,20]=torch.arange(1200)%2*.4-.2;trace[:,40]=5.5
        return {'recovery_s':.2 if entered else None,'entry_confirmation_index':19 if entered else None,'control_diagnostics_100hz':trace.tolist()}
    source={'per_env':[row() for _ in range(8)]};g=ProgressGuard(source,cfg)
    bad={'per_env':[row(i<6) for i in range(8)]}
    assert not g.observe(bad)['stop'];assert not g.observe(source)['stop']
    assert not g.observe(bad)['stop'];assert g.observe(bad)['stop']
    g=ProgressGuard(source,cfg);osc={'per_env':[row(osc=True) for _ in range(8)]}
    assert not g.observe(osc)['stop'];assert g.observe(osc)['stop']


def test_no_entry_retains_measured_diagnostics_and_failed_certificate():
    s,a=trace();s[:,6]=.168
    r=review(s,a);assert not r['accepted']
    assert r['metrics']['mean_abs_pitch_rad']==0 and r['metrics']['height_min_m']==.168
    assert r['standing_metrics_scope']=='pre_entry_diagnostic_only'


def test_new_spec_declaration_and_schedule_is_exact():
    import json
    from pathlib import Path
    from native_stand.command_v6.config import validate,schedule
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    s=json.loads((Path(__file__).resolve().parents[1]/'configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/spec.json').read_text())
    assert not validate(s) and s['authorization']['status'] in ('UNAUTHORIZED','AUTHORIZED')
    assert [u for u in range(1,101) if schedule(u,'formal',s['evaluation'])['full']]==[25,50,100]
    p=protocol_for_spec(s,23.)
    assert 'task_success terminal allowed' in p['termination_semantics'] and p['minimum_height_m']==.30
    s['recovery']['standing_task']['protocol']['height_m']=[.34,.38]
    assert validate(s)


def test_real_evaluator_finite_success_terminal_and_classifier(tmp_path):
    import importlib.util,json
    from pathlib import Path
    from native_stand.recovery.recipe import evaluate_actor
    from native_stand.recovery.selection import classify_recovery
    root=Path(__file__).resolve().parents[1]
    fixture=importlib.util.spec_from_file_location('standing_fixture',root/'tests/test_recovery_standing_balance.py')
    module=importlib.util.module_from_spec(fixture);fixture.loader.exec_module(module)
    spec=json.loads((root/'configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/spec.json').read_text())
    class Env(module.FakeStandingEnv):
        def step(self,action):
            obs,reward,_,timeout,extras=super().step(action)
            self.recovery_snapshot[:,13]=.01
            self.recovery_snapshot[:,1]=max(0,self.index-20)*.01
            done=torch.full((8,),self.index==1020)
            self.recovery_snapshot[:,2]=done.float()
            return obs,reward,done,timeout,extras
    env=Env(spec);env.reverse_curriculum=None;actor=torch.nn.Linear(150,6);actor.train();rng=torch.get_rng_state().clone()
    result=evaluate_actor(actor,None,env,seconds=23.,seed=104,full_trace=True)
    assert result['accepted'] and result['passed_envs']==8
    assert result['per_env'][0]['continuous_s']==pytest.approx(10.2)
    assert result['per_env'][0]['episode_result']['terminated'] and result['per_env'][0]['termination_reason']==['task_success']
    assert classify_recovery({'identity':{'scored_envs':8},'kind':'full','result':result},{'scored_envs':8})['accepted']
    assert actor.training and env.curriculum_training and not env.continuous_evaluation
    torch.testing.assert_close(rng,torch.get_rng_state())

    # Matching new-version source evidence may unlock smoke even before DrawBack ability passes.
    import hashlib
    from native_stand.command_v6.tools.preflight import check
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    baseline=tmp_path/'source';baseline.mkdir()
    result['checkpoint_sha256']=spec['source_sha256']
    (baseline/'evaluation_source.json').write_text(json.dumps(result))
    (baseline/'manifest.json').write_text(json.dumps({'spec_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
    book=json.loads((root/'configs/experiments/2026_10_7-22_10__recovery_min_height_p1_from_s50/budget.json').read_text())
    book['attempts']={'fixture':{'phase':'source_eval','status':'COMPLETED','output_dir':str(baseline)}}
    path.with_name('budget.json').write_text(json.dumps(book))
    planned=check(path,tmp_path/'NOT_CREATED','smoke')
    assert not any('baseline pending or invalid' in error for error in planned['errors'])
    assert not (tmp_path/'NOT_CREATED').exists()


def test_no_episode_stitching_or_missing_policy_intervals():
    s,a=trace();s[700:,31]=1
    assert 'same_episode' in review(s,a)['failed_checks']
    s[:,31]=0;s[700,0]+=.1
    assert 'policy_intervals' in review(s,a)['failed_checks']


def test_inference_evaluation_then_normal_reset_and_training_step():
    f=online()
    names=('age','dwell','entry','count','angle_sum','saturation',
           'hard_failed','sent','prefix','prefix_closed')
    storage={name:getattr(f,name).data_ptr() for name in names}
    for _ in range(2):  # DrawBack evaluation, then retained R0 evaluation.
        with torch.inference_mode():
            for _ in range(30):step(f)
        assert f.entry[0]>=0 and f.count[0]==10
        for name in names:
            assert not getattr(f,name).is_inference()
            assert getattr(f,name).data_ptr()==storage[name]
        f.reset(torch.tensor([0]))  # Real cleanup runs outside inference mode.
        assert f.entry[0]==-1 and f.count[0]==0 and f.dwell[0]==0
    step(f)  # Subsequent training remains writable.
    assert f.dwell[0]==1 and f.age[0]==pytest.approx(.01)


def test_phase_coverage_inference_rollouts_then_normal_reset():
    from native_stand.recovery.min_height import PhaseCoverage
    c=PhaseCoverage(1,'cpu')
    for _ in range(2):
        with torch.inference_mode():
            c.observe(torch.tensor([0]),torch.tensor([0]),torch.tensor([True]),
                {'lift':torch.ones(1)},{'lift':torch.ones(1)*.02},
                torch.zeros(1,6,dtype=torch.bool))
        assert not c.terms['lift'].is_inference()
        assert c.count.sum()==1
        c.reset()
        assert c.count.sum()==0 and not c.terms['lift'].any()
