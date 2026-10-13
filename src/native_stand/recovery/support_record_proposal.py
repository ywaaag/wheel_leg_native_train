"""CPU-only smooth geometry record reward; changes objective, NOT PBRS."""
import torch

VERSION='swing_support_record_reward_v1'

def declaration():
    return {'version':VERSION,'beta':.3,'short_m':.15,'width_m':.225,
        'family':'swing_candidate_from_historical_r1','scope':'controlled_pre_entry',
        'baseline':'exact_pre_first_control','terminal_reward':'zero_on_failure',
        'bilateral':'mean','actor_observes_record':False}

def validate(spec):
    c=spec.get('recovery',{}).get('support_record_reward')
    if c is None:return
    if (c!=declaration() or spec.get('task')!='recovery' or
            spec['recovery'].get('wheel_mean_auxiliary') or spec['recovery'].get('exploration_initialization') or
            spec['recovery'].get('rising_task',{}).get('version')!='autonomous_rise_min_height_v2'):
        raise ValueError('Unknown/conflicting support record reward declaration')

def quality(length,cos_down,*,short_m=.15,width_m=.225):
    if length.shape[-1]!=2 or length.shape!=cos_down.shape or width_m<=0:
        raise ValueError('Invalid bilateral geometry')
    if not torch.isfinite(length).all() or not torch.isfinite(cos_down).all() or (length<=0).any():
        raise ValueError('Invalid physical geometry')
    # Nonzero slope at the measured0.375m start; no hard saturation at long_m.
    length_quality=torch.exp(-((length-short_m)/width_m).square())
    direction_quality=(1+cos_down.clamp(-1,1))/2
    side=length_quality*direction_quality
    return {'side':side,'quality':side.mean(-1),'length_quality':length_quality}

def record_step(current,previous_best,*,eligible,failed,beta=.3):
    if (current.shape!=previous_best.shape or eligible.shape!=current.shape or failed.shape!=current.shape or beta<0):
        raise ValueError('Record transition shape differs')
    if not torch.isfinite(current).all() or not torch.isfinite(previous_best).all():
        raise ValueError('Nonfinite geometry record')
    if ((current<0)|(current>1)|(previous_best<0)|(previous_best>1)).any():raise ValueError('Quality outside bounds')
    # Terminal improvements update the record but are not rewarded. No terminal
    # potential release or height-gate bonus. No extra dt: budget is perepisode.
    next_best=torch.where(eligible,torch.maximum(previous_best,current),previous_best)
    reward=beta*(next_best-previous_best)*eligible*(~failed)
    return reward,next_best

class RecordState:
    """Explicit episode reward state,never changes action/observation/control."""
    def __init__(self,num_envs,device):
        with torch.inference_mode(False):
            self.audit_counts=torch.zeros(5,device=device,dtype=torch.long)
            self.episode_paid=torch.zeros(num_envs,device=device)
            self.best=torch.zeros(num_envs,device=device)
            self.initialized=torch.zeros(num_envs,dtype=torch.bool,device=device)
            self.pre_eligible=torch.zeros_like(self.initialized)
            self.snapshot=torch.zeros((num_envs,7),device=device)

    def reset(self,ids):
        self.audit_counts[0]+=len(ids);self.episode_paid[ids]=0.
        self.best[ids]=0.;self.initialized[ids]=False;self.pre_eligible[ids]=False
        # Snapshot survives local reset,like existing pre-reset reward/state evidence.

    def before(self,current,eligible):
        new=eligible&~self.initialized
        self.audit_counts[1]+=new.long().sum()
        self.best[new]=current[new];self.initialized[new]=True
        self.pre_eligible.copy_(eligible&self.initialized)
        self.snapshot[:,0].copy_(current);self.snapshot[:,1].copy_(self.best)

    def after(self,current,failed,*,beta):
        reward,next_best=record_step(current,self.best,eligible=self.pre_eligible,failed=failed,beta=beta)
        self.episode_paid.add_(reward)
        self.audit_counts[2]+=(failed&(reward>0)).long().sum()
        self.audit_counts[3]+=((~self.pre_eligible)&(reward>0)).long().sum()
        self.audit_counts[4]+=(self.episode_paid>beta+1e-6).long().sum()
        self.best.copy_(next_best)
        self.snapshot[:,2].copy_(current);self.snapshot[:,3].copy_(next_best)
        self.snapshot[:,4].copy_(reward);self.snapshot[:,5].copy_(self.pre_eligible)
        self.snapshot[:,6].copy_(failed)
        return reward

    def audit_summary(self):
        return dict(zip(('reset_count','baseline_established_count','failed_step_reward_violations','ineligible_reward_violations','episode_budget_violations'),self.audit_counts.cpu().tolist()))

class PolicyReadback:
    """Observe existing PPO distribution/sample only; no extra actor call or RNG."""
    def __init__(self,device):
        self.sums=torch.zeros(9,device=device,dtype=torch.float64)

    def add(self,mean,std,sample,eligible):
        mean=mean[:,[2,5]];std=std[:,[2,5]];sample=sample[:,[2,5]]
        values=torch.cat((mean.abs(),std,((sample<-1)|(sample>1)).to(mean.dtype),
                          ((mean<-1)|(mean>1)).to(mean.dtype)),dim=-1)
        self.sums[0]+=eligible.sum()
        self.sums[1:]+=(values.double()*eligible[:,None]).sum(0)

    def summary(self):
        v=self.sums.cpu().tolist();n=v[0]
        return {'eligible_count':int(n),'wheel_channels':[2,5],
            'abs_mean_normalized':[x/n for x in v[1:3]] if n else None,
            'std_normalized':[x/n for x in v[3:5]] if n else None,
            'sample_clip_fraction':[x/n for x in v[5:7]] if n else None,
            'mean_clip_fraction':[x/n for x in v[7:9]] if n else None,
            'scope':'actual existing ppo.act,controlled Swing pre-entry only'}
