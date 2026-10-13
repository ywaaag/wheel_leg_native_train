"""Recovery-only PPO actor mask; original critic/GAE timeline remains intact."""
import torch
from rsl_rl.algorithms import PPO

KEY='recovery_actor_valid'

def declaration():
    return {'version':'recovery_controlled_actor_v1','scope':'pre_action_policy_control','advantage_normalization':'valid_global_rollout','critic':'all_transitions','invalid_actor_grad':'None'}

def pre_action_valid(initializing,initialization_checked):
    if initializing.shape!=initialization_checked.shape:raise ValueError('Actor control mask shape mismatch')
    return (~initializing.bool())&initialization_checked.bool()

def normalize_valid(raw,valid):
    if raw.shape!=valid.shape or valid.dtype!=torch.bool:raise ValueError('Actor mask missing/misaligned')
    out=torch.zeros_like(raw)
    if valid.any():
        v=raw[valid];out[valid]=(v-v.mean())/(v.std() +1e-8) if v.numel()>1 else 0.
    return out

class ControlledPPO(PPO):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.actor.is_recurrent or self.critic.is_recurrent or self.rnd or self.symmetry or self.is_multi_gpu or self.schedule!='fixed':raise ValueError('Controlled Recovery PPO supports fixed feedforward only')
        if set(map(id,self.actor.parameters()))&set(map(id,self.critic.parameters())):raise ValueError('Actor/critic shared parameters unsupported')
        self.storage.observations[KEY]=torch.zeros_like(self.storage.observations[KEY],dtype=torch.bool)
        self.mask_summary={};self.actor_update_enabled=True;self.record_gradient_norms=False
        self.critic_control_only=False
        self.temporal_regularizer=None

    def act(self,obs):
        if KEY not in obs or obs[KEY].dtype!=torch.bool or obs[KEY].shape!=(obs.batch_size[0],1):raise ValueError('Pre-action valid metadata required')
        return super().act(obs)

    def compute_returns(self,obs):
        super().compute_returns(obs) # exact original time recursion and targets
        if KEY not in self.storage.observations:raise ValueError('Storage actor mask missing')
        valid=self.storage.observations[KEY]
        self.storage.advantages=normalize_valid(self.storage.returns-self.storage.values,valid)

    def update(self):
        st=self.storage;valid=st.observations.get(KEY)
        if valid is None or valid.shape!=st.advantages.shape:raise ValueError('Storage mask missing/misaligned')
        totals={'value':0.,'surrogate':0.,'entropy':0.};count=0;actor_steps=0;critic_steps=0;empty=0;kl_sum=0.;clip_sum=0.;actor_grad=[];critic_grad=[];temporal_sum=0.;temporal_pairs=0;temporal_grads=[]
        for b in st.mini_batch_generator(self.num_mini_batches,self.num_learning_epochs):
            m=b.observations[KEY].squeeze(-1)
            self.actor(b.observations,stochastic_output=True) # same sampling RNG as ordinary PPO
            logp=self.actor.get_output_log_prob(b.actions);entropy=self.actor.output_entropy
            values=self.critic(b.observations)
            if self.critic_control_only and not m.any():
                self.optimizer.zero_grad(set_to_none=True);empty+=1
                continue # Neither Adam parameter nor momentum state advances.
            vloss=(b.returns-values).square().mean() if not self.use_clipped_value_loss else torch.maximum((b.returns-values).square(),(b.returns-(b.values+(values-b.values).clamp(-self.clip_param,self.clip_param))).square()).mean()
            if self.critic_control_only:
                if self.use_clipped_value_loss:raise ValueError('controlled critic requires declared unclipped value loss')
                vloss=(b.returns[m]-values[m]).square().mean()
            loss=self.value_loss_coef*vloss;sur=values.new_zeros(());ent=values.new_zeros(())
            if m.any() and self.actor_update_enabled:
                ratio=torch.exp(logp[m]-b.old_actions_log_prob.squeeze(-1)[m]);adv=b.advantages.squeeze(-1)[m]
                sur=torch.maximum(-adv*ratio,-adv*ratio.clamp(1-self.clip_param,1+self.clip_param)).mean();ent=entropy[m].mean()
                loss=loss+sur-self.entropy_coef*ent
                if self.temporal_regularizer is not None:
                    term,npairs=self.temporal_regularizer.loss(self.actor)
                    if self.record_gradient_norms and npairs:
                        pars=[p for p in self.actor.parameters() if p.requires_grad]
                        gs=torch.autograd.grad(self.temporal_regularizer.cfg['coefficient']*term,pars,retain_graph=True,allow_unused=True)
                        temporal_grads.append(float(torch.sqrt(sum((g.square().sum() for g in gs if g is not None),values.new_zeros(())))))
                    loss=loss+self.temporal_regularizer.cfg['coefficient']*term
                    temporal_sum+=float(term.detach());temporal_pairs+=npairs
                with torch.no_grad():
                    kl=self.actor.get_kl_divergence(tuple(p[m] for p in b.old_distribution_params),tuple(p[m] for p in self.actor.output_distribution_params)).mean()
                    kl_sum+=float(kl);clip_sum+=float((abs(ratio-1)>self.clip_param).float().mean())
                actor_steps+=1
            else:empty+=1
            self.optimizer.zero_grad(set_to_none=True);loss.backward()
            if not m.any() or not self.actor_update_enabled:
                for p in self.actor.parameters():p.grad=None
            if self.record_gradient_norms:
                actor_grad.append(float(torch.sqrt(sum((p.grad.square().sum() for p in self.actor.parameters() if p.grad is not None),values.new_zeros(())))))
                critic_grad.append(float(torch.sqrt(sum((p.grad.square().sum() for p in self.critic.parameters() if p.grad is not None),values.new_zeros(())))))
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(),self.max_grad_norm)
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(),self.max_grad_norm)
            self.optimizer.step()
            critic_steps+=1
            totals['value']+=float(vloss.detach());totals['surrogate']+=float(sur.detach());totals['entropy']+=float(ent.detach());count+=1
        self.mask_summary={'total_transitions':valid.numel(),'valid_actor_samples':int(valid.sum()),'invalid_actor_samples':int((~valid).sum()),'actor_optimizer_steps':actor_steps,'actor_skipped_minibatches':empty,'kl_valid_mean':kl_sum/max(actor_steps,1),'clip_fraction_valid_mean':clip_sum/max(actor_steps,1),'version':declaration()['version']}
        self.mask_summary.update(effective_actor_update_samples=int(valid.sum()) if self.actor_update_enabled else 0,
            actor_gradient_norm_mean=sum(actor_grad)/len(actor_grad) if actor_grad else None,critic_gradient_norm_mean=sum(critic_grad)/len(critic_grad) if critic_grad else None,
            BC_loss=0.,BC_gradient_norm=None,BC_updates=0,critic_warmup=not self.actor_update_enabled)
        self.mask_summary.update(critic_optimizer_steps=critic_steps,critic_control_only=self.critic_control_only)
        if self.temporal_regularizer is not None:self.mask_summary.update(temporal_loss_mean=temporal_sum/max(actor_steps,1),temporal_pairs_sampled=temporal_pairs,temporal_coefficient=self.temporal_regularizer.cfg['coefficient'],temporal_weighted_gradient_norm_mean=sum(temporal_grads)/len(temporal_grads) if temporal_grads else None)
        st.clear()
        return {k:v/max(count,1) for k,v in totals.items()}
