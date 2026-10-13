"""Explicit on-policy full-rollout auxiliary batch via public optimizer hook."""
import torch
from native_stand.recovery.proposal_costs import wheel_mean_excess

VERSION='swing_wheel_mean_excess_rollout_v1'

def declaration(version=VERSION):
    if version not in (VERSION,'swing_wheel_mean_excess_rollout_v2'):raise ValueError('Unknown auxiliary version')
    return {'version':version,'coefficient':.001 if version==VERSION else .03,'margin':.9,'channels':[2,5],
        'family':'swing_candidate_from_historical_r1','phase':'pre_entry',
        'batch':'all_eligible_current_rollout','denominator':'all_controlled_rollout_transitions',
        'application':'every_optimizer_step','gradient_order':'PPO_clipped_then_aux_then_actor_reclip',
        'apply_phases':['smoke','formal']}

def validate(spec):
    cfg=spec.get('recovery',{}).get('wheel_mean_auxiliary')
    if cfg is None:return
    if cfg!=declaration(cfg.get('version')) or spec.get('task')!='recovery' or spec.get('initialization')!='warmstart':
        raise ValueError('Unknown wheel mean auxiliary contract')
    if (spec.get('evaluation_only') or spec.get('wheel_envelope_conversion') or
        spec.get('retention',{}).get('enabled') or
        spec['recovery'].get('standing_task',{}).get('retention',{}).get('enabled') or
        spec['recovery'].get('exploration_initialization') or
        spec['recovery'].get('active_family')!=cfg['family']):
        raise ValueError('Mean auxiliary cannot mix initialization/retention/evaluation interventions')

class MeanAuxiliary:
    def __init__(self,actor,config,*,max_grad_norm):
        self.actor=actor;self.config=config;self.max_grad_norm=max_grad_norm
        self.begin_rollout()

    def begin_rollout(self):
        self.inputs=[];self.masks=[];self.control_masks=[];self.batch=None
        self.denominator=0;self.eligible_count=0;self.events=[];self.calls=0
        self.policy_sums=None;self.policy_count=None

    def capture(self,observation,eligible,controlled):
        # Preserve actual pre-action samples; selection does not draw RNG.
        self.inputs.append(torch.cat((observation['policy'],observation['history']),-1).detach().clone())
        self.masks.append(eligible.detach().clone());self.control_masks.append(controlled.detach().clone())

    def finalize(self):
        if not self.inputs:return
        x=torch.cat(self.inputs);mask=torch.cat(self.masks);controlled=torch.cat(self.control_masks)
        if bool((mask&~controlled).any()):raise ValueError('Auxiliary eligibility outside controlled samples')
        self.denominator=int(controlled.sum());self.eligible_count=int(mask.sum())
        # Clone outside rollout inference_mode so autograd can save the input.
        self.batch=x[mask].detach().clone();self.inputs=[];self.masks=[];self.control_masks=[]

    def observe_policy(self,mean,std,sampled,eligible):
        if self.policy_sums is None:
            self.policy_sums=torch.zeros((3,6),device=mean.device)
            self.policy_count=torch.zeros((),device=mean.device)
        mask=eligible[:,None]
        self.policy_sums.add_(torch.stack(((mean.abs()>1).float()*mask,
            (sampled.abs()>1).float()*mask,std.detach()*mask)).sum(1))
        self.policy_count.add_(eligible.sum())

    def before_step(self,optimizer,args,kwargs):
        self.calls+=1
        if self.batch is None or not self.eligible_count:return
        from tensordict import TensorDict
        named=[(n,p) for n,p in self.actor.named_parameters() if p.requires_grad]
        params=[p for _,p in named]
        with torch.inference_mode(False),torch.enable_grad():
            obs=TensorDict({'policy':self.batch[:,:25],'history':self.batch[:,25:]},batch_size=[len(self.batch)])
            mean=self.actor(obs,stochastic_output=False)
            raw=self.raw_terms(mean)
            loss=raw.sum()/self.denominator*self.config['coefficient']
            grads=torch.autograd.grad(loss,params,allow_unused=True)
        incoming=torch.sqrt(sum((p.grad.detach().square().sum() for p in params if p.grad is not None),loss.new_zeros(())))
        auxnorm=torch.sqrt(sum((g.detach().square().sum() for g in grads if g is not None),loss.new_zeros(())))
        for p,g in zip(params,grads):
            if g is not None:
                if not torch.isfinite(g).all():raise ValueError('Nonfinite auxiliary gradient')
                if p.grad is None:p.grad=g.detach().clone()
                else:p.grad.add_(g.detach())
        combined=torch.nn.utils.clip_grad_norm_(params,self.max_grad_norm,error_if_nonfinite=True)
        post=torch.sqrt(sum((p.grad.detach().square().sum() for p in params if p.grad is not None),loss.new_zeros(())))
        values=torch.stack((loss.detach(),raw.detach().mean(),incoming,auxnorm,combined,post)).cpu().tolist()
        self.events.append(dict(zip(('weighted_loss','raw_eligible_mean','incoming_PPO_entropy_actor_norm_after_clip',
            'weighted_aux_actor_norm','combined_actor_norm_before_reclip','combined_actor_norm_after_reclip'),values)))

    def raw_terms(self,mean):
        return wheel_mean_excess(mean,torch.ones(len(mean),dtype=torch.bool,device=mean.device),margin=self.config['margin'])

    def summary(self):
        policy=None
        if self.policy_sums is not None:
            count=int(self.policy_count)
            policy={'eligible_samples':count,'mean_outside_fraction':None,'sampled_clip_fraction':None,'normalized_std_mean':None}
            if count:
                values=(self.policy_sums/count).cpu().tolist()
                policy.update(mean_outside_fraction=values[0],sampled_clip_fraction=values[1],normalized_std_mean=values[2])
        return {'version':self.config['version'],'eligible_count':self.eligible_count,'controlled_denominator':self.denominator,
            'actual_pre_action_policy_sampling':policy,
            'optimizer_step_calls':self.calls,'nonempty_applications':len(self.events),'first_step':self.events[0] if self.events else None,
            'mean_weighted_loss':sum(e['weighted_loss'] for e in self.events)/len(self.events) if self.events else None,
            'scope':'fixed current on-policy rollout auxiliary batch reused per optimizer step; NOT current PPO minibatch',
            'configuration':self.config}
