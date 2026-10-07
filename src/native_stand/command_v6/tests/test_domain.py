import math
from pathlib import Path
import sys

import pytest
import torch
from tensordict import TensorDict
from rsl_rl.models import MLPModel

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from native_stand.command_v6.domain.contract import frame,history,targets,effort
from native_stand.command_v6.domain.command_schedule import effective,sample
from native_stand.command_v6.domain.reward import compute
from native_stand.command_v6.domain.protocol import EpisodeBuffer,score,select_best_standing
from native_stand.command_v6.domain.warmstart import expand_state,expand_adam,clear_first_moment
from native_stand.command_v6.domain.metrics import RolloutMetrics

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path("/home/kellen/wheel_leg_migration_audit/native_stand/stable_stand_v2/runs/chain_20260930_224452/B_formal/model_adapt_200.pt")
REWARD={"upright":2.,"height":1.,"velocity_tracking":1.,"two_wheel_contact":.5,
        "effort":-.02,"action_delta":-.01,"joint_margin":-.05}


def test_frame_history_and_local_reset():
    q=torch.zeros(2,6)
    c=torch.tensor([[.05,0.,.363],[-.05,0.,.363]])
    f=frame(torch.zeros(2,3),torch.tensor([[0.,-1.,0.]]).repeat(2,1),c,q,q,q,q)
    assert f.shape==(2,25)
    torch.testing.assert_close(f[:,6:9],c*torch.tensor([2.,.25,5.]))
    h=history(torch.zeros(2,125),f,torch.ones(2,dtype=torch.bool))
    torch.testing.assert_close(h.reshape(2,5,25),f[:,None,:].expand(-1,5,-1))
    later=f.clone();later[0,6]=.2;later[1,6]=-.2
    updated=history(h,later,torch.tensor([False,True]))
    assert updated[0,6]==f[0,6] and updated[0,-19]==later[0,6]
    torch.testing.assert_close(updated[1].reshape(5,25),later[1].repeat(5,1))


def test_schedule_sampling_and_counts():
    time=torch.tensor([0.,.5,.75,1.,4.,4.25,4.5,5.])
    target=torch.tensor([[.1,0.]]).repeat(8,1)
    command=effective(target,time)
    torch.testing.assert_close(command[:,0],torch.tensor([0.,0.,.05,.1,.1,.05,0.,0.]))
    commands=[[0,0],[.05,0],[-.05,0]]
    values,counts=sample(commands,[.4,.3,.3],10000,device="cpu",generator=torch.Generator().manual_seed(3))
    assert values.shape==(10000,2) and int(counts.sum())==10000
    assert counts[0]/10000>.38 and counts[1]/10000>.28 and counts[2]/10000>.28


def test_wide_leg_contract_disables_pair_projection_without_changing_wheels():
    reference=torch.zeros(1,6)
    action=torch.tensor([[1.,-1.,.25,-1.,1.,-.5]])
    clipped, legs, wheels=targets(action, reference, leg_scale=.5,
                                  combined_radius=0., wheel_scale=6.)
    torch.testing.assert_close(legs[0], torch.tensor([.5,-.5,-.5,.5]))
    torch.testing.assert_close(wheels[0], torch.tensor([1.5,-3.]))
    torch.testing.assert_close(clipped, action)


def test_reward_signed_tracking_and_rollout_summary():
    q=torch.zeros(2,6)
    c=torch.tensor([[.1,0.,.363],[-.1,0.,.363]])
    total,raw,weighted=compute(torch.full((2,),.363),torch.ones(2),
        torch.tensor([.1,-.1]),torch.zeros(2),torch.zeros(2),c,
        torch.ones(2,2,dtype=torch.bool),q,q,q,torch.zeros(2,4),
        torch.zeros(2,dtype=torch.bool),weights=REWARD,height_width=.06,
        linear_denominator=.01,yaw_denominator=.09,terminal_penalty=-1.)
    torch.testing.assert_close(raw["velocity_tracking"],torch.ones(2))
    assert total[0]==total[1]
    stats=RolloutMetrics(raw.keys(),("nonfinite","closure"),2,"cpu")
    stats.add(raw,weighted,{"nonfinite":torch.zeros(2,dtype=torch.bool),
        "closure":torch.zeros(2,dtype=torch.bool)},torch.ones(2,2,dtype=torch.bool),
        torch.zeros(2,4),q,(40,40,5.5,40,40,5.5))
    summary=stats.summary()
    assert summary["samples"]==2 and summary["raw_mean"]["velocity_tracking"]==1.


def test_terminal_snapshot_replaces_reset_and_missing_is_error():
    buffer=EpisodeBuffer(4,1,"cpu",dt=.01)
    row=torch.tensor([[0.,0.,.36,.1,0.,0.,0.,0.,100.,100.]+[0.]*6+[0.,.02]])
    for _ in range(3):
        buffer.append(row,torch.tensor([False]),[None])
    snapshot={"root_pos_w":[.4,0.,.36],"vx_mps":.1,"vy_mps":0.,
        "yaw_rad_s":0.,"wheel_contact_n":[100.,100.],"effort_nm":[0.]*6,
        "closure_each_m":[0.]*4,"up_cos":math.cos(.02),
        "causes":{name:False for name in ("nonfinite","closure","height","tilt","body_contact","joint_safety")},
        "time_out":True}
    reset=row.clone();reset[0,:3]=torch.tensor([0.,0.,.4])
    buffer.append(reset,torch.tensor([True]),[snapshot])
    result=score(*buffer.packed(),dt=.01,full_trace=False)["per_env"][0]
    assert result["outcome"]=="completed" and result["continuous_s"]==.04
    assert result["net_drift_m"]==pytest.approx(.4)
    assert result["max_excursion_m"]==pytest.approx(.4)
    assert result["dual_contact_fraction"]==1.
    assert result["mean_abs_vx_mps"] is None
    assert "trace" not in result
    with pytest.raises(ValueError,match="snapshot"):
        EpisodeBuffer(1,1,"cpu").append(reset,torch.tensor([True]),[None])


def test_two_second_window_completes_without_env_timeout():
    buffer=EpisodeBuffer(200,1,"cpu",dt=.01)
    row=torch.tensor([[0.,0.,.363,0.,0.,0.,0.,0.,100.,100.]+[0.]*6+[0.,0.]])
    for _ in range(200):
        buffer.append(row,torch.tensor([False]),[None])
    result=score(*buffer.packed(),dt=.01,target_window=(.5,2.),requested_steps=200)["per_env"][0]
    assert result["outcome"]=="completed"
    assert result["termination_reason"]=="evaluation_window"
    assert result["continuous_s"]==2.


def test_early_environment_time_limit_does_not_complete_longer_requested_window():
    buffer=EpisodeBuffer(10,1,"cpu",dt=.01)
    row=torch.tensor([[0.,0.,.363,0.,0.,0.,0.,0.,100.,100.]+[0.]*6+[0.,0.]])
    for _ in range(4):
        buffer.append(row,torch.tensor([False]),[None])
    snapshot={"root_pos_w":[0.,0.,.363],"vx_mps":0.,"vy_mps":0.,
        "yaw_rad_s":0.,"wheel_contact_n":[100.,100.],"effort_nm":[0.]*6,
        "closure_each_m":[0.]*4,"up_cos":1.,
        "causes":{name:False for name in ("nonfinite","closure","height","tilt","body_contact","joint_safety")},
        "time_out":True}
    buffer.append(row,torch.tensor([True]),[snapshot])
    result=score(*buffer.packed(),dt=.01,requested_steps=10)["per_env"][0]
    assert result["outcome"]=="UNKNOWN"
    assert result["termination_reason"]=="early_time_limit"


def test_best_standing_candidate_prefers_full_gate_and_tracks_latest_separately():
    observed={"accepted":False,"passed_envs":7,"mean_net_drift_m":.01}
    accepted={"accepted":True,"passed_envs":8,"mean_net_drift_m":.1}
    assert select_best_standing(observed,accepted)==accepted
    assert select_best_standing(accepted,observed)==accepted
    assert select_best_standing(None,observed)==observed


def test_tilt_and_mean_absolute_do_not_cancel():
    buffer=EpisodeBuffer(4,1,"cpu",dt=1.)
    for i,v in enumerate((.1,-.1,.1,-.1)):
        row=torch.tensor([[i*.1,0.,.36,v,0.,0.,0.,0.,100.,100.]+[0.]*6+[0.,.02]])
        if i<3:
            buffer.append(row,torch.tensor([False]),[None])
        else:
            snap={"root_pos_w":[.4,0.,.36],"vx_mps":-.1,"vy_mps":0.,"yaw_rad_s":0.,
                "wheel_contact_n":[100.,100.],"effort_nm":[0.]*6,"closure_each_m":[0.]*4,
                "up_cos":math.cos(.3),"causes":{n:n=="tilt" for n in
                ("nonfinite","closure","height","tilt","body_contact","joint_safety")},"time_out":False}
            buffer.append(row,torch.tensor([True]),[snap])
    values=buffer.packed()
    brief=score(*values,dt=1.)["per_env"][0]
    detailed=score(*values,dt=1.,full_trace=True)["per_env"][0]
    assert brief["outcome"]=="task_failure" and brief["peak_tilt_rad"]==pytest.approx(.3)
    assert brief["mean_abs_vx_mps"]==pytest.approx(.1)
    assert brief["abs_mean_vx_mps"]==pytest.approx(0.)
    assert {k:v for k,v in detailed.items() if k!="trace"}==brief


def test_b200_actor_and_critic_warmstart_exact():
    source=torch.load(SOURCE,map_location="cpu",weights_only=False)
    old=TensorDict({"policy":torch.randn(4,22),"history":torch.randn(4,110)},batch_size=[4])
    cmd=torch.tensor([[0.,0.,.363],[.05,0.,.363],[-.05,0.,.363],[0.,.1,.363]])
    def insert(value):
        frames=value.reshape(4,-1,22)
        return torch.cat((frames[:,:,:6],cmd[:,None,:].expand(-1,frames.shape[1],-1),
                          frames[:,:,6:]),-1).reshape(4,-1)
    new=TensorDict({"policy":insert(old["policy"]),"history":insert(old["history"])},batch_size=[4])
    for name,output in (("actor",6),("critic",1)):
        def model(obs):
            settings=dict(hidden_dims=(256,128,64),activation="elu",obs_normalization=False)
            if name=="actor":
                settings["distribution_cfg"]={"class_name":"rsl_rl.modules.distribution:GaussianDistribution",
                                              "init_std":.2,"std_type":"scalar"}
            return MLPModel(obs,{name:["policy","history"]},name,output,**settings)
        before,after=model(old),model(new)
        before.load_state_dict(source[name],strict=True)
        after.load_state_dict(expand_state(source[name],after.state_dict()),strict=True)
        torch.testing.assert_close(before(old,stochastic_output=False),
                                   after(new,stochastic_output=False),atol=2e-5,rtol=1e-6)


def test_b200_adam_moments_expand_by_verified_names():
    from rsl_rl.algorithms import PPO
    from rsl_rl.storage import RolloutStorage
    source=torch.load(SOURCE,map_location="cpu",weights_only=False)
    obs=TensorDict({"policy":torch.zeros(2,25),"history":torch.zeros(2,125)},batch_size=[2])
    def model(name,out):
        settings=dict(hidden_dims=(256,128,64),activation="elu",obs_normalization=False)
        if name=="actor":
            settings["distribution_cfg"]={"class_name":"rsl_rl.modules.distribution:GaussianDistribution",
                                          "init_std":.2,"std_type":"scalar"}
        return MLPModel(obs,{name:["policy","history"]},name,out,**settings)
    actor=model("actor",6);critic=model("critic",1)
    actor.load_state_dict(expand_state(source["actor"],actor.state_dict()))
    critic.load_state_dict(expand_state(source["critic"],critic.state_dict()))
    storage=RolloutStorage("rl",2,2,obs,[6],"cpu")
    ppo=PPO(actor,critic,storage,num_learning_epochs=1,num_mini_batches=1,
        clip_param=.2,gamma=.99,lam=.95,value_loss_coef=.5,entropy_coef=.001,
        learning_rate=3e-5,max_grad_norm=1.,use_clipped_value_loss=False,
        schedule="fixed",desired_kl=.01,device="cpu")
    old=[("actor."+n,p) for n,p in source["actor"].items()]+[
        ("critic."+n,p) for n,p in source["critic"].items()]
    new=[("actor."+n,p) for n,p in actor.named_parameters()]+[
        ("critic."+n,p) for n,p in critic.named_parameters()]
    expand_adam(source["optimizer"],ppo.optimizer,old,new,learning_rate=3e-5)
    assert len(ppo.optimizer.state)==17
    assert source["optimizer"]["param_groups"][0]["lr"]==1e-4
    assert ppo.optimizer.param_groups[0]["lr"]==3e-5
    first=ppo.optimizer.state[actor.mlp[0].weight]["exp_avg"]
    for offset in range(0,150,25):
        assert torch.all(first[:,offset+6:offset+9]==0.)


def test_clear_first_moment_preserves_variance():
    parameter=torch.nn.Parameter(torch.ones(2))
    optimizer=torch.optim.Adam([parameter],lr=1e-3)
    parameter.square().sum().backward(); optimizer.step()
    second=optimizer.state[parameter]['exp_avg_sq'].clone()
    assert clear_first_moment(optimizer)==1
    assert torch.count_nonzero(optimizer.state[parameter]['exp_avg'])==0
    torch.testing.assert_close(optimizer.state[parameter]['exp_avg_sq'],second)
