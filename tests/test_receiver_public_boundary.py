FROZEN_TEST_SCOPE='PROJECT_DATA'
import ast,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import torch
from native_stand.command_v6.config import validate
from native_stand.command_v6.tools.evaluate_checkpoint import batch_plan,protocol_for_spec
ROOT=Path(__file__).resolve().parents[1]

def preparation(kind):
    spec=importlib.util.spec_from_file_location('receiver_prepare',ROOT/'scripts/prepare_receiver_stage1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.prepare(kind,'CPU_TEST',False)

def test_real_preparer16cases_no_write_and_training_contract():
    e=preparation('evaluation');s=e['spec'];assert validate(s)==[]
    assert len(s['motion_handoff']['cases'])==16 and len({r['case_id'] for r in s['motion_handoff']['cases']})==16
    assert s['budget']['chain_wall_s']==1800
    t=preparation('training')['spec'];assert validate(t)==[]
    assert t['budget']['sample_limit']==983040 and t['source_update']==250
    assert not t['restore_source_rng'] and not t['recovery'].get('support_record_reward')
    assert t['receiver_reward']['linear_cohort_width']['retained_denominator']==.04
    assert t['receiver_training']['critic_context']['phase_time']=='storage_metadata_not_network_input'
    assert protocol_for_spec(t,13.52)['protocol_identity']=='receiver_combination_v1'

def test_real_trainer_control_boundary_stores_requested_action():
    text=(ROOT/'src/native_stand/command_v6/train.py').read_text();ast.parse(text)
    assert 'env.actor_valid_pre() if spec.get(\'receiver_training\')' in text
    assert 'executed_action=env.compose_training_action(action)' in text
    assert 'actor_optimizer_steps' in (ROOT/'src/native_stand/command_v6/wiring.py').read_text()
    assert "ppo.process_env_step(obs,reward,dones,extras)" in text

def test_receiver_runtime_import_order_no_secondary_trainer():
    text=(ROOT/'src/native_stand/recovery/receiver_recipe.py').read_text();tree=ast.parse(text)
    assert not any(isinstance(n,ast.ImportFrom) and n.module and 'receiver_runtime' in n.module for n in tree.body)
    text=(ROOT/'src/native_stand/recovery/receiver_runtime.py').read_text()
    assert 'self.prefix_actor(observation[prefix],stochastic_output=False)' in text
    assert 'return reward*valid' in text
    assert 'physics' not in [n.name for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name.startswith('simulate')]

def test_actual_runtime_composition_never_replaces_ppo_requested_actions(monkeypatch):
    import sys,types
    from tensordict import TensorDict
    from native_stand.recovery.domain import Mode
    fake=types.ModuleType('native_stand.recovery.handoff_runtime')
    fake.HandoffEnv=type('Base',(),{})
    monkeypatch.setitem(sys.modules,'native_stand.recovery.handoff_runtime',fake)
    spec=importlib.util.spec_from_file_location('native_stand.recovery._receiver_cpu_test',ROOT/'src/native_stand/recovery/receiver_runtime.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    env=module.ReceiverEnv.__new__(module.ReceiverEnv)
    env.num_envs=4;env.device='cpu';env.fsm=types.SimpleNamespace(mode=torch.tensor([int(Mode.INITIALIZING),int(Mode.RECOVERY),int(Mode.RECOVERY),int(Mode.RECOVERY)]))
    env.initialization_checked=torch.tensor([False,True,True,True]);env.executed_prefix=torch.tensor([0,49,50,0])
    env.pose_direct_reset=torch.tensor([False,True]);env.initial_pose_index=torch.tensor([0,0,0,1])
    env.recovery_observation={'policy':torch.zeros(4,25),'history':torch.zeros(4,125)}
    class Prefix:
        def __call__(self,obs,stochastic_output):
            assert not stochastic_output and len(obs)==1
            return torch.full((1,6),.8)
    env.prefix_actor=Prefix();requested=torch.full((4,6),.2);before=requested.clone()
    executed=env.compose_training_action(requested)
    assert torch.equal(requested,before)
    assert torch.equal(executed[0],torch.zeros(6)) and torch.equal(executed[1],torch.full((6,),.8))
    assert torch.equal(executed[2:],requested[2:]) and env.actor_valid_pre().tolist()==[False,False,True,True]
    env.return_to_original=torch.tensor([True,False,True,False])
    assert env.actor_valid_pre().tolist()==[False,False,False,True]
    assert torch.equal(env.compose_training_action(requested)[2],requested[2])
    assert torch.equal(env.compose_training_action(requested)[0],torch.zeros(6))

def test_real_receiver_metadata_storage_and_optimizer_cpu():
    from tensordict import TensorDict
    from rsl_rl.storage import RolloutStorage
    from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
    from native_stand.command_v6.tools.model_factory import model
    obs=TensorDict({'policy':torch.zeros(4,25),'history':torch.zeros(4,125),KEY:torch.tensor([[False],[False],[True],[True]]),
        'receiver_phase':torch.tensor([[0],[1],[2],[2]]),'receiver_phase_time_s':torch.zeros(4,1),
        'receiver_executed_action':torch.zeros(4,6),'receiver_physical_target':torch.zeros(4,6)},batch_size=[4])
    s={'task':'recovery','ppo':{'hidden_dims':[8,4]}}
    actor=model(obs,actor=True,spec=s);critic=model(obs,actor=False,spec=s)
    storage=RolloutStorage('rl',4,2,obs,[6],'cpu')
    p=ControlledPPO(actor,critic,storage,num_learning_epochs=1,num_mini_batches=2,schedule='fixed',use_clipped_value_loss=False)
    torch.manual_seed(2)
    for i in range(2):
        requested=p.act(obs)
        p.transition.observations['receiver_executed_action']=torch.where(obs[KEY],requested,torch.zeros_like(requested))
        p.process_env_step(obs,torch.arange(4).float()+i,torch.zeros(4,dtype=torch.bool),{})
    p.compute_returns(obs)
    assert p.storage.observations['receiver_phase'][0,:,0].tolist()==[0,1,2,2]
    before={k:v.clone() for k,v in actor.state_dict().items()};p.update()
    assert p.mask_summary['valid_actor_samples']==4 and p.mask_summary['actor_optimizer_steps']>0
    assert any(not torch.equal(v,actor.state_dict()[k]) for k,v in before.items())

def test_receiver_zero_reward_matches_frozen_motion_formula_and_dt():
    from native_stand.command_v6.domain.reward import compute,fields
    p=ROOT/'runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/domain_reward.py'
    module_spec=importlib.util.spec_from_file_location('native_stand.command_v6.domain._frozen_motion_reward',p)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    c=preparation('training')['spec']['receiver_reward'];n=4
    args=(torch.tensor([.18,.3,.4,.42]),torch.tensor([.8,.95,1.,1.]),torch.tensor([1.2,.2,0.,0.]),
        torch.zeros(n),torch.zeros(n),torch.tensor([[0.,0.,.4]]).repeat(n,1),
        torch.ones(n,2,dtype=torch.bool),torch.ones(n,6),torch.full((n,6),.1),torch.zeros(n,6),
        torch.zeros(n,4),torch.tensor([False,False,False,True]))
    kw=dict(weights={k:c[k] for k in fields(c)},height_width=c['height_width_m'],linear_denominator=.04,
        yaw_denominator=.09,terminal_penalty=c['terminal_penalty'],dt=.01,
        action_delta_wheel_factor=c['action_delta_wheel_factor'])
    a=compute(*args,**kw);b=module.compute(*args,**kw)
    assert torch.equal(a[0],b[0]) and all(torch.equal(a[2][k],b[2][k]) for k in a[2])
