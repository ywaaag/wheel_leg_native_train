import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from tensordict import TensorDict
from native_stand.recovery.standing import (posture,standing_costs,score_standing,
                                           StandingRetention,StandingRegression,REWARD_FIELDS)
from native_stand.recovery.domain import RecoveryFSM,ReverseRecoveryCurriculum,process_reward
from native_stand.recovery.selection import classify_recovery
from native_stand.command_v6.config import validate,schedule,evaluation_seconds


ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/recovery_standing_balance_20261006/spec.json'


@pytest.fixture
def spec():
    value=json.loads(SPEC.read_text())
    value['budget'].update(formal_updates=500,formal_wall_s=7200,sample_limit=503*8192)
    return value


def fresh_book():
    return {'authorization':'UNAUTHORIZED','limits':{'source_eval':1,'smoke':3,'formal':500,'evaluate':2},
            'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0},'attempts':{},
            'source_eval_wall_used_s':0.,'sample_limit':503*8192}


def perfect_trace(n=1000):
    rows=torch.zeros(n,39)
    rows[:,0]=torch.arange(1,n+1)*.01
    rows[:,6]=.36;rows[:,10:12]=50.;rows[:,19:22]=torch.tensor([0.,0.,.36])
    d=torch.zeros(n,10);d[:,2:4]=.3
    return rows,d


def test_recipe_physics_source_and_schedule(spec):
    assert validate(spec)==[]
    assert spec['source_update']==1500 and spec['source_input_dim']==150
    assert spec['control']['height_command_m']==.36
    assert spec['action']['leg_scale_rad']==1.6 and spec['action']['wheel_scale_rad_s']==100.
    assert spec['ground']['collider']=='plane'
    assert spec['recovery']['curriculum']['max_enabled_stage']==0
    assert schedule(10,'formal',spec['evaluation'])==dict(checkpoint=False,light=False,full=False)
    assert schedule(250,'formal',spec['evaluation'])['full']
    assert schedule(100,'formal',spec['evaluation'])['light']
    assert evaluation_seconds(spec,full=False)==2. and evaluation_seconds(spec,full=True)==10.
    from native_stand.command_v6.completion import plan
    summary=plan(spec,'formal')
    assert (summary['checkpoints'],summary['light_evaluations'],summary['full_evaluations'])==(6,4,2)
    book=fresh_book()
    assert book['authorization']=='UNAUTHORIZED' and not book['attempts']
    assert sum(book['limits'][p] for p in ('smoke','formal'))*8192==book['sample_limit']


def test_new_source_plan_has_no_writes_or_isaac_import(tmp_path,spec):
    import sys
    from native_stand.command_v6.tools.preflight import check
    output=tmp_path/'not_created'
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    book=path.with_name('budget.json');book.write_text(json.dumps(fresh_book()))
    before=book.read_bytes()
    result=check(path,output,'source_eval')
    assert result['status']=='READY_NEEDS_AUTH' and result['cpu_valid']
    assert result['errors']==['new simulation/PPO budget has not been authorized']
    assert not output.exists() and before==book.read_bytes()
    assert not any(name=='isaaclab' or name.startswith('isaaclab.') for name in sys.modules)


def test_smoke_requires_same_identity_continuous_source_not_new_behavior_pass(spec,tmp_path):
    from native_stand.command_v6.tools.preflight import check,digest
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    book=fresh_book();book['authorization']='AUTHORIZED'
    baseline=tmp_path/'source';baseline.mkdir()
    book['used']['source_eval']=1
    book['attempts']['source_fixture']={'phase':'source_eval','status':'COMPLETED','output_dir':str(baseline)}
    path.with_name('budget.json').write_text(json.dumps(book))
    manifest={'spec_sha256':digest(path)}
    (baseline/'manifest.json').write_text(json.dumps(manifest))
    result={'checkpoint_sha256':spec['source_sha256'],'accepted':False,
        'success_protocol':{'standing_protocol':spec['recovery']['standing_task']['protocol'],
                            'continuous_seconds':10.},
        'per_env':[{'initial_valid':True,'continuous_window_completed':True,
                    'continuous_s':10.,'runtime_fault':False} for _ in range(8)]}
    evaluation=baseline/'evaluation_source.json';evaluation.write_text(json.dumps(result))
    assert check(path,tmp_path/'smoke','smoke')['status']=='PASS'
    result['per_env'][0]['continuous_s']=2.
    evaluation.write_text(json.dumps(result))
    assert 'standing source continuous10s baseline pending or invalid' in check(
        path,tmp_path/'smoke','smoke')['errors']


def test_pose_sampling_and_offline_closure(spec):
    poses=json.loads(Path(spec['recovery']['pose_library']).read_text())['poses']
    for family in ('R0','R0_perturbed'):
        for split in ('train','holdout'):
            rows=[p for p in poses if p['family']==family and p['split']==split]
            assert len(rows)==4 and sum(r['sample_weight'] for r in rows)==pytest.approx(1.)
            assert rows[0]['sample_weight']==.7
            assert all(r['offline_valid'] and r['runtime_valid'] is None and r['closure_max_m']<1e-4 for r in rows)
    assert not set(p['seed'] for p in poses if p['split']=='train') & set(
        p['seed'] for p in poses if p['split']=='holdout' and p['family'] in ('R0','R0_perturbed'))


@pytest.mark.parametrize('section,key,value',[
    ('reward','height_width_m',0.),('protocol','dual_contact_min',1.1),
    ('retention','coefficient',float('nan')),('retention','max_samples_per_rollout',2.5),
    ('root','hip_anchors_root_m',[[0,0],[0,0,0]])])
def test_standing_preflight_rejects_invalid_recipe(spec,section,key,value):
    cfg=spec['recovery']['standing_task']
    (cfg if section=='root' else cfg[section])[key]=value
    assert validate(spec)


def test_posture_mirror_and_canonical_tilt():
    q=torch.tensor([[.2,.4,0.,-.2,.4,0.]])
    gravity=torch.tensor([[0.,-1.,0.]])
    hip=torch.tensor([[[.17,0.,0.],[-.17,0.,0.]]]);wheel=hip.clone();wheel[:,:,2]=-.3
    d=posture(gravity,q,torch.zeros(1,2),hip,wheel,torch.zeros(1,3),torch.zeros(1,3))
    assert torch.allclose(d[:,2:4],torch.full((1,2),.3))
    assert not d[:,[0,1,4,5,6]].any()
    pitch=.1;gravity=torch.tensor([[0.,-torch.cos(torch.tensor(pitch)),torch.sin(torch.tensor(pitch))]])
    assert posture(gravity,q,torch.zeros(1,2),hip,wheel,torch.zeros(1,3),torch.zeros(1,3))[0,0]==pytest.approx(pitch)


def test_height_gate_deadband_and_reward_dt(spec):
    cfg=spec['recovery']['standing_task']['reward'];h=torch.tensor([.2,.36,.36])
    d=torch.zeros(3,10);d[:,4:6]=torch.tensor([[.5,.5],[.02,.02],[.10,-.10]])
    d[:,7]=.1
    raw=standing_costs(h,torch.full_like(h,.36),d,torch.ones(3,3)*.2,cfg)
    assert raw['mirror_posture'][0]==0 and raw['mirror_posture'][1]==0 and raw['mirror_posture'][2]>0
    assert raw['vertical_motion'][0]==0 and raw['vertical_motion'][1]>0
    z=torch.zeros(3)
    args=(h,torch.full_like(h,.168),torch.full_like(h,.36),torch.ones(3),torch.zeros(3,6),
          torch.zeros(3,6),z,z.bool(),z.bool())
    old,_,_=process_reward(*args,weights=spec['reward'],dt=.01,pitch=z,roll=z,
        contact=torch.full((3,2),3.),wheel_velocity=torch.zeros(3,2),support_balance=z)
    new,newraw,weighted=process_reward(*args,weights=spec['reward'],dt=.01,pitch=z,roll=z,
        contact=torch.full((3,2),3.),wheel_velocity=torch.zeros(3,2),support_balance=z,
        standing_config=cfg,standing_diagnostics=d,angular_velocity=torch.ones(3,3)*.2)
    for name in REWARD_FIELDS:
        torch.testing.assert_close(weighted[name],newraw[name]*cfg['weights'][name]*.01)
    torch.testing.assert_close(new-old,sum(weighted[n] for n in REWARD_FIELDS))


def score(rows,d,spec,**kwargs):
    return score_standing(rows,d,dt=.01,requested_s=10.,
        protocol={**spec['recovery']['standing_task']['protocol'],'initial_xy':[0.,0.]},
        runtime_fault=False,initial_valid=True,terminated=False,**kwargs)


def test_continuous_standing_metrics_and_no_cancel(spec):
    rows,d=perfect_trace();assert score(rows,d,spec)['accepted']
    rows[:,7]=torch.where(torch.arange(1000)%2==0,.05,-.05)
    r=score(rows,d,spec)
    assert not r['accepted'] and 'vx' in r['failed_checks']
    assert r['metrics']['mean_abs_vx_mps']>.049 and r['metrics']['abs_mean_vx_mps']<.001


def test_missing_window_early_death_and_symmetry_fail(spec):
    rows,d=perfect_trace(100)
    assert 'continuous' in score(rows,d,spec)['failed_checks']
    assert 'steady_window_missing' in score(rows,d,spec)['failed_checks']
    rows,d=perfect_trace();d[:,4]=.3
    assert 'mirror' in score(rows,d,spec)['failed_checks']
    rows[-1,19]=.4
    assert 'excursion' in score(rows,d,spec)['failed_checks']


def test_success_pulse_does_not_end_continuous_evaluation(spec):
    f=RecoveryFSM(1,'cpu',spec['recovery']['fsm']);yes=torch.tensor([True]);no=~yes
    pulses=0
    for _ in range(1000):
        p,failed,fault=f.step(yes,yes,no,no,dt=.01,finish_on_success=False)
        pulses+=int(p.sum())
        assert not failed.any() and not fault.any() and f.mode[0]==2
    assert pulses==1
    f.step(yes,yes,yes,no,dt=.01,finish_on_success=False)
    assert f.mode[0]==6


def test_curriculum_two_windows_and_two_full_confirmations():
    c=ReverseRecoveryCurriculum(['R0','R1'],episodes_per_window=128,
        full_confirmations_required=2,max_enabled_stage=1)
    c.record_episodes([(0,True,False)]*256)
    assert c.stage==0
    c.confirm_evaluation(stage=0,accepted=True,continuous_s=2.)
    assert c.full_passed==0
    c.confirm_evaluation(stage=0,accepted=True,continuous_s=10.)
    assert c.stage==0
    c.confirm_evaluation(stage=0,accepted=True,continuous_s=10.)
    assert c.stage==1
    capped=ReverseRecoveryCurriculum(['R0','R1'],episodes_per_window=128,max_enabled_stage=0)
    capped.record_episodes([(0,True,False)]*1024)
    assert capped.stage==0
    restored=ReverseRecoveryCurriculum(['R0','R1'],episodes_per_window=128,max_enabled_stage=0)
    restored.restore_checkpoint_state(capped.checkpoint_state())
    assert restored.stage==0
    assert all(window['episodes']==128 for window in capped.windows)
    assert c.state()['consecutive_full_confirmations']==0
    with pytest.raises(ValueError):
        restored.restore_checkpoint_state({**capped.checkpoint_state(),'stage':1})


class Actor(torch.nn.Module):
    def __init__(self):
        super().__init__();self.layer=torch.nn.Linear(150,6)
    def forward(self,obs,stochastic_output=False):
        return self.layer(torch.cat((obs['policy'],obs['history']),-1))


def test_retention_real_inference_inputs_public_hook_and_frozen_teacher():
    student=Actor();teacher=copy.deepcopy(student)
    hook=StandingRetention(student,teacher,coefficient=.02,max_samples=4,max_grad_norm=1.)
    opt=torch.optim.Adam(student.parameters(),lr=3e-5)
    original_step=opt.step
    handle=opt.register_step_pre_hook(hook.before_step)
    with torch.inference_mode():
        obs=TensorDict({'policy':torch.randn(8,25),'history':torch.randn(8,125)},batch_size=[8])
        hook.capture(obs,torch.tensor([True,False,True,False,True,False,True,False]))
    with torch.no_grad():student.layer.bias.add_(.1)
    before=teacher.layer.bias.detach().clone()
    opt.zero_grad();opt.step()
    assert opt.step==original_step
    assert not any(p.requires_grad or p.grad is not None for p in teacher.parameters())
    torch.testing.assert_close(teacher.layer.bias,before)
    assert hook.summary()['raw']>0 and hook.summary()['retained_samples']==4
    handle.remove()


def test_actual_source1500_strict_actor_critic_adam_and_learning_rate(spec):
    from native_stand.command_v6.learning import model
    from native_stand.command_v6.domain.warmstart import initialize_state,initialize_adam
    source=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
    obs=TensorDict({'policy':torch.randn(8,25),'history':torch.randn(8,125)},batch_size=[8])
    actor=model(obs,actor=True,spec=spec)
    critic=model(obs,actor=False,spec=spec)
    for name,network in (('actor',actor),('critic',critic)):
        network.load_state_dict(initialize_state(source[name],network.state_dict(),input_dim=150),strict=True)
        for key,value in network.state_dict().items():
            torch.testing.assert_close(value,source[name][key],rtol=0,atol=0)
    old_named=[('actor.'+n,p) for n,p in source['actor'].items()]+[
               ('critic.'+n,p) for n,p in source['critic'].items()]
    named=[('actor.'+n,p) for n,p in actor.named_parameters()]+[
           ('critic.'+n,p) for n,p in critic.named_parameters()]
    opt=torch.optim.Adam([p for _,p in named],lr=1e-4)
    initialize_adam(source['optimizer'],opt,old_named,named,input_dim=150,learning_rate=3e-5)
    assert opt.param_groups[0]['lr']==3e-5 and len(opt.state)==17
    for (_,parameter),pid in zip(named,source['optimizer']['param_groups'][0]['params']):
        for field in ('step','exp_avg','exp_avg_sq'):
            torch.testing.assert_close(opt.state[parameter][field],source['optimizer']['state'][pid][field],rtol=0,atol=0)


def test_new_protocol_cannot_accept_two_second_certificate(spec):
    rows,d=perfect_trace();metrics=score(rows,d,spec)['metrics']
    row={'continuous_s':2.,'verify_s':2.,'height_min_m':.36,'height_final_m':.36,
         'dual_contact_fraction':1.,'closure_max_m':0.,'tilt_peak_rad':0.,
         'saturation_fraction_policy':0.,'success':True,'recovery_s':None,'outcome':'success',
         'standing_metrics':metrics,'standing_failed_checks':[],'continuous_window_completed':True}
    result={'per_env':[row],'recovery_gate':{'accepted':True,'passed_envs':1},
        'success_protocol':{'mode':'autonomous_hold','required_stable_s':2.,'teacher_control':False,
                           'standing_protocol':spec['recovery']['standing_task']['protocol'],
                           'continuous_seconds':2.}}
    identity={'scored_envs':1}
    entry={'identity':identity,'kind':'full','result':result}
    assert not classify_recovery(entry,identity)['accepted']
    result['success_protocol']['continuous_seconds']=10.
    assert 'invalid_standing_certificate' in classify_recovery(entry,identity)['exclusion_reasons']


def test_standing_regression_does_not_stop_unlearned_task_or_light_screens():
    gate=StandingRegression()
    for _ in range(5):assert not gate.observe(accepted=False,full=True,continuous_s=10.)
    assert not gate.observe(accepted=True,full=True,continuous_s=10.)
    for _ in range(5):assert not gate.observe(accepted=False,full=False,continuous_s=2.)
    assert not gate.observe(accepted=False,full=True,continuous_s=10.)
    assert gate.observe(accepted=False,full=True,continuous_s=10.)
    assert not gate.observe(accepted=True,full=True,continuous_s=10.)


def test_missing_or_nonfinite_diagnostics_cannot_pass(spec):
    rows,d=perfect_trace()
    result=score(rows,d[:0],spec)
    assert not result['accepted'] and result['checks']['missing_metrics'] is False
    d[0,0]=float('nan')
    result=score(rows,d,spec)
    assert not result['accepted'] and 'finite' in result['failed_checks']
    assert result['metrics']=={}


class FakeStandingEnv:
    """Reset deliberately corrupts live state; pre-reset snapshots remain intact."""
    def __init__(self,spec,*,fall_step=None,drift=False):
        self.recovery_config=copy.deepcopy(spec['recovery'])
        self.family='R0';self.split='train';self.curriculum_training=True
        self.continuous_evaluation=False;self.fsm=SimpleNamespace(config=copy.deepcopy(spec['recovery']['fsm']))
        self.num_envs=8;self.device='cpu';self.step_dt=.01
        self.pose_library={'poses':[{'family':'R0','seed':123,'pose_id':'fixture'}]}
        self.episode_origin=torch.zeros(8,2)
        self.recovery_snapshot=torch.zeros(8,39)
        self.standing_snapshot=torch.zeros(8,10);self.standing_snapshot[:,2:4]=.3
        self.recovery_control_snapshot=torch.zeros(8,54)
        self.recovery_cause_snapshot=torch.zeros(8,6,dtype=torch.bool)
        self.terminal_causes={k:torch.zeros(8,dtype=torch.bool) for k in
                              ('nonfinite','closure','tilt','height','body_contact','limits')}
        self.gate_diagnostic_names=[]
        self.recovery_config['gate_diagnostics']=False
        self.fall_step=fall_step;self.drift=drift;self.live_height=0.;self.resets=0

    def select_initial_family(self,family,split):self.family,self.split=family,split
    def reset(self):
        self.index=0;self.resets+=1;self.live_height=0.
        return torch.zeros(8,150),{}
    def initialization_summary(self):return {'valid':8,'rejected':0}
    def step(self,action):
        self.index+=1
        self.recovery_snapshot.zero_()
        self.recovery_snapshot[:,0]=self.index*.01
        self.recovery_snapshot[:,1]=min(self.index*.01,2.)
        self.recovery_snapshot[:,6]=.36
        self.recovery_snapshot[:,10:12]=50.
        self.recovery_snapshot[:,19]=.4*(self.index/1000) if self.drift else 0.
        self.recovery_snapshot[:,21]=.36
        self.recovery_snapshot[:,29]=1.
        self.recovery_snapshot[:,31]=7.
        self.recovery_snapshot[:,32]=2.
        done=torch.full((8,),self.index==self.fall_step)
        if bool(done.any()):
            self.recovery_cause_snapshot[:,2]=True
            self.live_height=0.  # The live reset state must never replace the snapshot.
        else:self.live_height=.36
        return torch.zeros(8,150),torch.zeros(8),done,torch.zeros(8,dtype=torch.bool),{}


def test_actual_evaluator_continues_success_and_restores_training_rng(spec):
    from native_stand.recovery.recipe import evaluate_actor
    env=FakeStandingEnv(spec);state=torch.get_rng_state().clone()
    result=evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=10.,seed=321)
    assert result['accepted'] and result['passed_envs']==8
    assert all('failure_window_100hz' not in row for row in result['per_env'])
    assert all(row['continuous_s']==pytest.approx(10.) and row['continuous_window_completed']
               for row in result['per_env'])
    assert env.curriculum_training and not env.continuous_evaluation and env.split=='train'
    torch.testing.assert_close(state,torch.get_rng_state())
    identity={'scored_envs':8}
    entry={'identity':identity,'kind':'full','result':result}
    assert classify_recovery(entry,identity)['accepted']


def test_actual_evaluator_early_fall_uses_pre_reset_state(spec):
    from native_stand.recovery.recipe import evaluate_actor
    env=FakeStandingEnv(spec,fall_step=300,drift=True)
    result=evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=10.,seed=321)
    assert not result['accepted']
    for row in result['per_env']:
        assert row['height_final_m']==pytest.approx(.36)
        assert row['continuous_s']==pytest.approx(3.)
        assert row['termination_reason']==['tilt']
        assert row['standing_metrics']['net_drift_m']==pytest.approx(.12)
        assert 'continuous' in row['standing_failed_checks']
        assert row['terminal_pre_reset'][6]==pytest.approx(.36)
    assert env.live_height==0.


def test_actual_evaluator_window_completion_is_not_zero_drift_reset(spec):
    from native_stand.recovery.recipe import evaluate_actor
    env=FakeStandingEnv(spec,drift=True)
    result=evaluate_actor(lambda obs:torch.zeros(8,6),None,env,seconds=10.,seed=321)
    assert not result['accepted']
    for row in result['per_env']:
        assert row['continuous_window_completed']
        assert row['termination_reason']==['evaluation_window']
        assert row['standing_metrics']['net_drift_m']==pytest.approx(.4)
        assert row['standing_metrics']['max_excursion_m']==pytest.approx(.4)
        assert row['standing_failed_checks']==['excursion']
