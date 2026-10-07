import copy
import hashlib
import json
import signal
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from scipy.spatial.transform import Rotation

from native_stand.command_v6.domain.contract import projection_fraction,targets,history,frame
from native_stand.recovery.domain import RecoveryFSM,Mode,blend_targets,process_reward,summarize_episodes
from native_stand.recovery.preflight import check
from native_stand.recovery.selection import classify_recovery

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/recovery_r1_20261002/spec.json'


@pytest.mark.parametrize('radius,expected',[(0.,0.),(.12,1.)])
def test_projection_disabled_or_enabled(radius,expected):
    action=torch.ones(3,6)
    assert torch.equal(projection_fraction(action,leg_scale=.5,combined_radius=radius),torch.full((3,),expected))


def test_sigterm_after_fake_app_handler_is_replaced():
    code="""import signal,os
from native_stand.command_v6 import train
signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(RuntimeError('app closed too soon')))
train.install_stop_handlers()
os.kill(os.getpid(),signal.SIGTERM)
assert train.STOP
print('SAFE_STOP_HANDLER')
"""
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,
        env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert 'SAFE_STOP_HANDLER' in result.stdout


def test_stopped_attempt_settles_before_app_shutdown(tmp_path):
    from native_stand.command_v6 import train
    from native_stand.command_v6.ledger import Ledger
    budget=tmp_path/'budget.json';output=tmp_path/'run';output.mkdir()
    budget.write_text(json.dumps({'authorization':'AUTHORIZED','limits':{'formal':5},
        'used':{'formal':1},'attempts':{'exact':{'phase':'formal','output_dir':str(output.resolve()),
            'status':'RUNNING','updates':1}}}))
    report={'status':'STOPPED_BOUNDED','exit_code':0,'actual_updates':1,'samples':8192,
        'wall_s':1.,'failure':None,'stop_kind':'user_signal','early_stop_reason':'SIGTERM'}
    train.settle_attempt(output,{'actual_updates':1,'status':'STOPPED_BOUNDED'},report,Ledger(budget),'exact')
    class App:
        def close(self,exit_code):
            assert json.loads((output/'terminal_report.json').read_text())['stop_kind']=='user_signal'
            assert json.loads(budget.read_text())['attempts']['exact']['status']=='STOPPED_BOUNDED'
            assert exit_code==0
    train.close_app(App(),False)


def test_first_terminal_copy_survives_reset_and_later_episode():
    from native_stand.recovery.domain import capture_terminal
    state=torch.tensor([[.4,5.],[.17,0.]])
    terminal=torch.zeros_like(state);control=state.clone();dest=terminal.clone()
    causes=torch.zeros(2,1,dtype=torch.bool);out=causes.clone()
    active=torch.ones(2,dtype=torch.bool)
    new=capture_terminal(state,control,causes,active,torch.tensor([True,False]),terminal,dest,out)
    active &= ~new
    state[0]=torch.tensor([.17,0.])
    capture_terminal(state,control,causes,active,torch.tensor([True,False]),terminal,dest,out)
    assert torch.equal(terminal[0],torch.tensor([.4,5.]))


def fsm(n=2):
    return RecoveryFSM(n,'cpu',{'gate_dwell_s':.5,'blend_s':.3,'verify_s':5.,'timeout_s':15.})


def test_handover_is_not_success_and_five_seconds_required():
    state=fsm();yes=torch.ones(2,dtype=torch.bool);no=~yes
    for _ in range(50):
        success,_,_=state.step(yes,yes,no,no,dt=.01)
    assert not success.any() and (state.mode==int(Mode.HANDOVER)).all()
    count=0
    for _ in range(550):
        success,_,_=state.step(yes,yes,no,no,dt=.01)
        count+=int(success.sum())
    assert count==2 and (state.verify>=5.-1e-5).all()
    assert (state.mode==int(Mode.STAND)).all()


def test_final_partial_blend_step_does_not_count_as_frozen_stand():
    state=fsm();yes=torch.ones(2,dtype=torch.bool);no=~yes
    state.mode[:]=int(Mode.HANDOVER);state.dwell[:]=.29
    state.step(yes,yes,no,no,dt=.01)
    assert (state.mode==int(Mode.STAND_VERIFY)).all()
    assert torch.equal(state.verify,torch.zeros(2))
    for _ in range(499):
        pulse,_,_=state.step(yes,yes,no,no,dt=.01)
        assert not pulse.any()
    pulse,_,_=state.step(yes,yes,no,no,dt=.01)
    assert pulse.all()


def test_verify_failure_not_retried_and_runtime_distinct():
    state=fsm();state.mode[:]=int(Mode.STAND_VERIFY)
    success,failed,fault=state.step(torch.ones(2,dtype=torch.bool),torch.tensor([False,True]),
        torch.tensor([False,True]),torch.zeros(2,dtype=torch.bool),dt=.01)
    assert not success.any()
    assert state.mode.tolist()==[int(Mode.RECOVERY_FAILED),int(Mode.RUNTIME_FAULT)]


def test_local_reset_does_not_erase_other_episode():
    state=fsm();state.age[:]=torch.tensor([4.,7.]);state.verify[:]=3.
    state.reset(torch.tensor([0]))
    assert state.age.tolist()==[0.,7.] and state.verify.tolist()==[0.,3.]


def test_recovery_timeout_is_failure_not_stand_timeout():
    state=fsm();state.age[:]=15.
    _,failed,_=state.step(*[torch.zeros(2,dtype=torch.bool) for _ in range(4)],dt=.01)
    assert failed.all() and (state.mode==int(Mode.RECOVERY_FAILED)).all()


def test_target_blend_physical_units_not_raw_action():
    legs=torch.ones(2,4)*1.6;wheels=torch.ones(2,2)*100
    l,w=blend_targets(legs,wheels,torch.zeros_like(legs),torch.zeros_like(wheels),torch.tensor([0.,.5]))
    assert torch.allclose(l[1],torch.full((4,),.8))
    assert torch.allclose(w[1],torch.full((2,),50.))


def test_lift_reward_not_upright_plateau_and_success_once():
    weights={'lift':3.,'upright':.5,'effort':-.02,'action_delta':-.01,'joint_margin':-.05,'success_once':10.,'failure_once':-1.}
    h=torch.tensor([.17,.25,.35,.4]);zeros=torch.zeros(4,6)
    reward,raw,_=process_reward(h,torch.full_like(h,.17),torch.full_like(h,.4),torch.ones(4),zeros,zeros,
        torch.zeros(4),torch.zeros(4,dtype=torch.bool),torch.zeros(4,dtype=torch.bool),weights=weights,dt=.01)
    assert bool((reward[1:]>reward[:-1]).all()) and raw['lift'][0]==0


def test_history_real_commands_local_reset():
    current=torch.zeros(2,25);current[:,6:9]=torch.tensor([0.,0.,2.])
    old=torch.arange(250,dtype=torch.float).reshape(2,125)
    result=history(old,current,torch.tensor([True,False]))
    assert torch.equal(result[0],current[0].repeat(5))
    assert torch.equal(result[1,:100],old[1,25:])


def test_pose_closure_against_independent_authored_rest_transform():
    from pxr import UsdGeom
    from native_stand.recovery.asset_poses import AssetPoses
    spec=json.loads(SPEC.read_text());asset=AssetPoses(spec['asset_path'])
    cache=UsdGeom.XformCache();root=np.asarray(cache.GetLocalToWorldTransform(asset.bodies['robot'])).T
    actual=asset.forward({})
    for name,prim in asset.bodies.items():
        expected=np.linalg.inv(root)@np.asarray(cache.GetLocalToWorldTransform(prim)).T
        assert np.max(np.abs(expected-actual[name]))<2e-6,name


def test_library_closed_limits_and_geometry_limitation_preserved():
    spec=json.loads(SPEC.read_text());library=json.loads(Path(spec['recovery']['pose_library']).read_text())
    assert library['attempted']==42 and library['offline_rejected']==0
    assert library['runtime_rejection_rate'] is None
    for row in library['poses']:
        assert max(row['closure_each_m'])<1e-4
        assert min(row['ideal_collider_gaps_m'].values())>=.0019
        if row['family']=='R1':
            assert .09<row['chassis_bottom_clearance_m']<.11
            assert .16<row['root_height_m']<.18
    assert not spec['recovery']['geometry_definition_confirmed']


def test_frozen_stand_checkpoint_and_forward_cpu_unchanged():
    from native_stand.command_v6.learning import model
    from tensordict import TensorDict
    spec=json.loads(SPEC.read_text());c=spec['recovery'];path=Path(c['stand_checkpoint'])
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    assert before==c['stand_sha256']
    saved=torch.load(path,map_location='cpu',weights_only=False)
    obs=TensorDict({'policy':torch.randn(8,25),'history':torch.randn(8,125)},batch_size=[8])
    policy=model(obs,actor=True,spec=json.loads(Path(c['stand_spec']).read_text()))
    policy.load_state_dict(saved['actor'],strict=True);policy.eval()
    for p in policy.parameters():p.requires_grad_(False)
    actual=policy(obs)
    value=torch.cat((obs['policy'],obs['history']),-1)
    for number in (0,2,4,6):
        value=torch.nn.functional.linear(value,saved['actor'][f'mlp.{number}.weight'],saved['actor'][f'mlp.{number}.bias'])
        if number!=6:value=torch.nn.functional.elu(value)
    assert torch.allclose(actual,value,atol=1e-7,rtol=1e-6)
    assert all(not p.requires_grad for p in policy.parameters())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before


def test_preflight_no_writes_and_budget_not_authorized(tmp_path):
    output=tmp_path/'unused'
    spec=json.loads(SPEC.read_text())
    spec['colleague_config_sha256']=hashlib.sha256(Path(spec['colleague_config_path']).read_bytes()).hexdigest()
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    path.with_name('budget.json').write_bytes(SPEC.with_name('budget.json').read_bytes())
    result=check(path,output)
    assert result['cpu_valid'],result['errors']
    assert result['simulation']==result['ppo']==result['files_written']==0
    assert not output.exists()
    assert result['budget_authorization']=='UNAUTHORIZED'
    assert len(result['runtime_blockers'])==3


def test_rejections_not_deleted_and_zero_denominator_missing():
    rows=[{'family':'R1','seed':1,'initial_valid':False,'success':False},
          {'family':'R2','seed':2,'initial_valid':True,'success':True,'recovery_s':3.}]
    summary=summarize_episodes(rows)
    assert summary['R1:1']['success_rate_valid'] is None
    assert summary['R1:1']['rejection_rate']==1.


def test_recovery_candidate_requires_five_second_verification():
    row={'env_id':0,'continuous_s':4.,'verify_s':0.,'height_min_m':.17,'height_final_m':.4,
        'dual_contact_fraction':1.,'closure_max_m':0.,'tilt_peak_rad':0.,'saturation_fraction_policy':0.,
        'success':True,'recovery_s':4.,'outcome':'success'}
    identity={'scored_envs':1}
    entry={'identity':identity,'kind':'full','result':{'per_env':[row],
        'recovery_gate':{'accepted':True,'passed_envs':1}},'checkpoint_sha256':'fixture'}
    value=classify_recovery(entry,identity)
    assert not value['accepted'] and 'insufficient_stand_verification' in value['exclusion_reasons']
