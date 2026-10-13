FROZEN_TEST_SCOPE='PORTABLE'
import copy,torch,pytest
from tensordict import TensorDict
from native_stand.students.model import Student
from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
from rsl_rl.storage import RolloutStorage

def make():
 actor=Student(version='multiskill_mcu_v2');actor.log_std.requires_grad_(False);critic=Student(False,version='multiskill_mcu_v2')
 obs=TensorDict({'student_actor':torch.randn(4,31),'student_critic':torch.randn(4,40),KEY:torch.ones(4,1,dtype=torch.bool)},batch_size=[4])
 storage=RolloutStorage('rl',4,8,obs,[6],device='cpu')
 ppo=ControlledPPO(actor,critic,storage,learning_rate=3e-5,schedule='fixed',num_learning_epochs=4,num_mini_batches=4,entropy_coef=.001,value_loss_coef=.5,use_clipped_value_loss=False);ppo.record_gradient_norms=True
 return ppo,obs
def fill(p,obs,valid=True):
 with torch.inference_mode():
  for i in range(8):
   obs=obs.clone();obs[KEY][:]=valid;a=p.act(obs)
   torch.testing.assert_close(p.transition.actions_log_prob,p.actor.log_prob(obs['student_actor'],a))
   p.process_env_step(obs,torch.ones(4)*.02,torch.tensor([i==7,False,False,False]),{})
  p.compute_returns(obs)
def clone_state(p):return {k:v.clone() for k,v in p.actor.state_dict().items()}
def test_real_cpu_optimizer_warmup_empty_mask_std_and_BC_disabled():
 torch.manual_seed(4);p,obs=make();before=clone_state(p);c=copy.deepcopy(p.critic.state_dict());rng=torch.get_rng_state().clone()
 fill(p,obs);p.actor_update_enabled=False;p.update()
 assert all(torch.equal(v,p.actor.state_dict()[k]) for k,v in before.items())
 assert any(not torch.equal(v,p.critic.state_dict()[k]) for k,v in c.items())
 assert not any(param in p.optimizer.state for param in p.actor.parameters())
 assert p.mask_summary['actor_optimizer_steps']==0 and p.mask_summary['BC_updates']==0 and p.mask_summary['BC_gradient_norm'] is None
 fill(p,obs);p.actor_update_enabled=True;p.update()
 assert any(not torch.equal(v,p.actor.state_dict()[k]) for k,v in before.items())
 assert torch.equal(before['log_std'],p.actor.log_std)
 assert p.mask_summary['actor_gradient_norm_mean']>0 and p.mask_summary['valid_actor_samples']==32
 actor=clone_state(p);state={id(k):{n:v.clone() if torch.is_tensor(v) else v for n,v in value.items()} for k,value in p.optimizer.state.items() if id(k) in set(map(id,p.actor.parameters()))}
 fill(p,obs,False);p.update()
 assert all(torch.equal(v,p.actor.state_dict()[k]) for k,v in actor.items())
 for param in p.actor.parameters():
  if id(param) in state:
   for k,v in state[id(param)].items():
    if torch.is_tensor(v):assert torch.equal(v,p.optimizer.state[param][k])
 assert p.mask_summary['actor_optimizer_steps']==0

def test_bootstrap_boundary_preserves_real_time_and_diagnostic_rng():
 torch.manual_seed(7);p,obs=make();q,_=make();q.actor.load_state_dict(p.actor.state_dict());q.critic.load_state_dict(p.critic.state_dict())
 q.record_gradient_norms=False
 rng=torch.get_rng_state().clone();fill(p,obs);returns=p.storage.returns.clone();torch.set_rng_state(rng);fill(q,obs)
 torch.testing.assert_close(returns,q.storage.returns)
 # Real terminal stops GAE, rollout endpoint is bootstrapped; initial mask not removed.
 assert p.storage.observations[KEY].shape==(8,4,1)
 rng=torch.get_rng_state().clone();p.update();after=torch.get_rng_state().clone();torch.set_rng_state(rng);q.update()
 assert torch.equal(after,torch.get_rng_state())
 assert all(torch.equal(v,q.actor.state_dict()[k]) for k,v in p.actor.state_dict().items())
