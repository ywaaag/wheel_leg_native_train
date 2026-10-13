FROZEN_TEST_SCOPE='PORTABLE'
import copy,torch,pytest
from native_stand.students.temporal import pairs,Regularizer,declaration
from native_stand.students.model import Student

def test_adjacent_pairs_reject_resets_ownership_terminal_and_gaps():
 x=torch.arange(5*2*31).float().reshape(5,2,31);student=torch.ones(5,2,dtype=torch.bool);entered=student.clone();episode=torch.zeros(5,2);time=torch.arange(5).double()[:,None].expand(-1,2)*.01;done=torch.zeros_like(student)
 student[0,0]=False;entered[1,1]=False;episode[3:,0]=1;done[2,1]=True
 left,right=pairs(x,student,entered,episode,time,done)
 assert len(left)==3
 torch.testing.assert_close(left,torch.stack([x[1,0],x[3,0],x[3,1]]));torch.testing.assert_close(right,torch.stack([x[2,0],x[4,0],x[4,1]]))
 time=time.clone();time[4,0]+=.01
 assert len(pairs(x,student,entered,episode,time,done)[0])==2

def test_regularizer_preserves_distribution_cache_rng_and_both_side_gradients():
 torch.manual_seed(11);actor=Student(version='multiskill_mcu_v2');actor.log_std.requires_grad_(False)
 x=torch.randn(7,31);y=torch.randn(7,31);actor(x,stochastic_output=True)
 cache=actor._current_distribution;raw=cache.sample();logp=actor.get_output_log_prob(raw).clone();rng=torch.get_rng_state().clone()
 reg=Regularizer(declaration('B'),'cpu');reg.set_pairs(x,y);value,n=reg.loss(actor)
 assert n==7 and value.requires_grad and actor._current_distribution is cache
 assert torch.equal(rng,torch.get_rng_state()) and torch.equal(logp,actor.get_output_log_prob(raw))
 expected=((100*actor.mean(y)[:,[2,5]]-100*actor.mean(x)[:,[2,5]])/10).square().mean()
 torch.testing.assert_close(value,expected)
 g=torch.autograd.grad(value,tuple(actor.mlp.parameters()),retain_graph=True)
 h=torch.autograd.grad(expected,tuple(actor.mlp.parameters()))
 for a,b in zip(g,h):torch.testing.assert_close(a,b)
 reg=Regularizer(declaration('A'),'cpu');reg.set_pairs(x,y);before=reg.generator.get_state().clone()
 z,n=reg.loss(actor);assert z==0 and n==0 and torch.equal(before,reg.generator.get_state())
 reg=Regularizer(declaration('B'),'cpu');reg.set_pairs(x[:0],y[:0]);assert reg.loss(actor)[1]==0

def test_regularizer_pair_limit_and_parameter_update():
 actor=Student(version='multiskill_mcu_v2');actor.log_std.requires_grad_(False);reg=Regularizer(declaration('B'),'cpu');reg.set_pairs(torch.randn(1000,31),torch.randn(1000,31))
 value,n=reg.loss(actor);assert n==256
 before=copy.deepcopy(actor.state_dict());opt=torch.optim.Adam(actor.parameters(),lr=3e-5);opt.zero_grad(set_to_none=True);(.01*value).backward();opt.step()
 assert not torch.equal(before['mlp.0.weight'],actor.state_dict()['mlp.0.weight'])
 assert torch.equal(before['log_std'],actor.log_std)

def test_lifecycle_source_formal_only_accepts_verified_course_evidence(tmp_path):
 from native_stand.command_v6.tools.run_state import transition,record
 with pytest.raises(ValueError,match='invalid RunState'):transition('SOURCE_EVAL','FORMAL')
 with pytest.raises(ValueError,match='evidence'):transition('SOURCE_EVAL','FORMAL',continuation={'verified':True})
 proof={'version':'verified_course_continuation_v1','verified':True,'checkpoint_sha256':'f'*64}
 record(tmp_path,'SUBMITTED');record(tmp_path,'SOURCE_EVAL');record(tmp_path,'FORMAL',continuation=proof)
 assert transition('SOURCE_EVAL','FORMAL',continuation=proof)=='FORMAL'

def test_real_controlled_ppo_auxiliary_preserves_policy_rng_and_empty_mask():
 from tensordict import TensorDict
 from rsl_rl.storage import RolloutStorage
 from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
 def build():
  obs=TensorDict({'student_actor':torch.randn(4,31),'student_critic':torch.randn(4,40),KEY:torch.ones(4,1,dtype=torch.bool)},batch_size=[4])
  actor=Student(version='multiskill_mcu_v2');actor.log_std.requires_grad_(False);critic=Student(False,version='multiskill_mcu_v2')
  storage=RolloutStorage('rl',4,3,obs,[6],'cpu')
  p=ControlledPPO(actor,critic,storage,num_learning_epochs=2,num_mini_batches=2,learning_rate=3e-5,schedule='fixed',entropy_coef=.001,use_clipped_value_loss=False)
  p.critic_control_only=True;p.record_gradient_norms=True
  for _ in range(3):p.act(obs);p.process_env_step(obs,torch.randn(4),torch.zeros(4,dtype=torch.bool),{})
  p.compute_returns(obs);return p
 torch.manual_seed(19);base=build();a=build();b=build()
 for p in (a,b):
  p.actor.load_state_dict(base.actor.state_dict());p.critic.load_state_dict(base.critic.state_dict());p.storage=copy.deepcopy(base.storage)
 x=torch.randn(12,31);y=torch.randn(12,31)
 for p,arm in ((a,'A'),(b,'B')):p.temporal_regularizer=Regularizer(declaration(arm),'cpu');p.temporal_regularizer.set_pairs(x,y)
 rng=torch.get_rng_state().clone();base.update();after=torch.get_rng_state().clone()
 torch.set_rng_state(rng);a.update();assert torch.equal(after,torch.get_rng_state())
 for u,v in zip(base.actor.parameters(),a.actor.parameters()):torch.testing.assert_close(u,v,rtol=0,atol=0)
 torch.set_rng_state(rng);b.update();assert torch.equal(after,torch.get_rng_state())
 assert b.mask_summary['temporal_pairs_sampled']>0 and b.mask_summary['temporal_weighted_gradient_norm_mean']>0
 invalid=build();invalid.temporal_regularizer=Regularizer(declaration('B'),'cpu');invalid.temporal_regularizer.set_pairs(x,y)
 invalid.storage.observations[KEY][:]=False
 original=copy.deepcopy(invalid.actor.state_dict());critic=copy.deepcopy(invalid.critic.state_dict());invalid.update()
 assert all(torch.equal(v,invalid.actor.state_dict()[k]) for k,v in original.items())
 assert all(torch.equal(v,invalid.critic.state_dict()[k]) for k,v in critic.items())
 assert invalid.mask_summary['actor_optimizer_steps']==invalid.mask_summary['critic_optimizer_steps']==0
