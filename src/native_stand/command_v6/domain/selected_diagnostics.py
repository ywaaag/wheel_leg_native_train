"""Opt-in selected-update tensor summaries; never invent historical gradients."""
import torch


def configuration(spec):
    value=spec.get('diagnostics',{})
    if not isinstance(value,dict):raise ValueError('diagnostics must be an object')
    updates=value.get('record_updates',[])
    if not isinstance(updates,list) or any(type(i) is not int or i<1 for i in updates):
        raise ValueError('diagnostics record_updates must contain positive integer updates')
    for name in ('enabled','record_reward_components','record_ppo_summary','record_retention_summary'):
        if name in value and type(value[name]) is not bool:
            raise ValueError('diagnostics '+name+' must be boolean')
    return {'enabled':value.get('enabled',False) is True,'record_updates':updates,
            **{name:value.get(name,False) is True for name in
               ('record_reward_components','record_ppo_summary','record_retention_summary')}}


def selected(spec,update):
    config=configuration(spec)
    return config['enabled'] and update in config['record_updates']


def summarize_tensor(value):
    values=value.detach().float().reshape(-1)
    if not values.numel():return {'sample_count':0,'values':None}
    summary=torch.stack((values.mean(),values.std(unbiased=False),values.min(),values.max(),
                         *torch.quantile(values,values.new_tensor([.05,.5,.95]))))
    result=dict(zip(('mean','std','min','max','p05','p50','p95'),summary.cpu().tolist()))
    return {'sample_count':values.numel(),**result}


def storage_summary(storage):
    result={'provenance':'online pre-update storage; actual gradients not collected',
            'gradient_summary':None,'missing_reason':'no optimizer-step gradient capture'}
    for name in ('values','returns','advantages','actions_log_prob'):
        value=getattr(storage,name,None)
        result[name]=summarize_tensor(value) if isinstance(value,torch.Tensor) else None
    result['raw_advantages']=summarize_tensor(storage.returns-storage.values)
    result['advantages_scope']='stored PPO advantages after configured normalization'
    return result


def retention_coverage(metadata, *, eligible, total, rollout_steps, poses=None):
    """Selected on-policy sample coverage; diagnostics only, not a balancing rule."""
    selected = 0 if metadata is None else len(metadata)
    result = {'eligible_count':eligible, 'selected_count':selected,
              'discarded':{'ineligible_mask':None if eligible is None else total-eligible,
                           'sample_limit_or_selection':None if eligible is None else eligible-selected},
              'discard_reason_scope':'mask false; individual eligibility predicates not recorded',
              'per_episode':None,'per_pose':None,'per_family':None,'rollout_position_histogram':None}
    if metadata is None or metadata.shape[1] < 7:
        result['missing_reason']='episode/pose/rollout-position metadata not captured'
        return result
    pairs, counts = torch.unique(metadata[:,3:5].long(),dim=0,return_counts=True)
    result['per_episode']=[{'env_id':key[0],'reset_count':key[1],'sample_count':count}
                          for key,count in zip(pairs.cpu().tolist(),counts.cpu().tolist())]
    ids, counts = torch.unique(metadata[:,5].long(),return_counts=True)
    families={}
    result['per_pose']=[]
    for index,count in zip(ids.cpu().tolist(),counts.cpu().tolist()):
        pose=(poses or [])[index] if poses is not None and 0<=index<len(poses) else {}
        result['per_pose'].append({'pose_index':index,'pose_id':pose.get('pose_id'),'sample_count':count})
        if 'family' in pose:families[pose['family']]=families.get(pose['family'],0)+count
    result['per_family']=families or None
    bins=(metadata[:,6]*10/max(1,rollout_steps)).long().clamp(0,9)
    result['rollout_position_histogram']={'bins':10,'sample_counts':torch.bincount(bins,minlength=10).cpu().tolist(),
        'scope':'pre-action rollout step index divided by frozen rollout length'}
    return result


def command_phase_summary(storage, targets, ages, schedule, normalization):
    """Recorded transition counts, not reset command assignment counts."""
    targets=torch.stack(targets).detach()
    ages=torch.stack(ages).detach()
    entry,ramp,hold,exit=schedule
    phase=torch.bucketize(ages,ages.new_tensor([entry,entry+ramp,entry+ramp+hold,entry+ramp+hold+exit]),right=True)
    names=('prepare','ramp_up','hold','ramp_down','parking')
    groups=[]
    for command in torch.unique(targets.reshape(-1,2),dim=0):
        matched=(targets==command).all(-1)
        for i,name in enumerate(names):
            mask=matched & (phase==i)
            count=int(mask.sum().cpu())
            if not count:continue
            group={'command':command.cpu().tolist(),'phase':name,'transition_count':count,
                   'episode_age_s':summarize_tensor(ages[mask])}
            for key,value in (('value',storage.values),('return',storage.returns),
                    ('raw_advantage',storage.returns-storage.values),('normalized_advantage',storage.advantages)):
                group[key]=summarize_tensor(value[mask])
            groups.append(group)
    return {'normalization':normalization,'sample_count':targets.shape[0]*targets.shape[1],
            'scope':'online pre-update storage grouped by sampled endpoint and actual pre-action episode age',
            'groups':groups}


class PolicyUpdateSummary:
    """Deterministic full-rollout before/after probe, not a historical minibatch replay."""
    def __init__(self,actor,storage,clip_param):
        from tensordict import TensorDict
        self.obs=TensorDict({key:value.flatten(0,1).detach().clone() for key,value in storage.observations.items()},
                           batch_size=[storage.num_envs*storage.num_transitions_per_env])
        self.actions=storage.actions.flatten(0,1).detach().clone()
        self.old_log_prob=storage.actions_log_prob.flatten().detach().clone()
        self.old_params=tuple(value.flatten(0,1).detach().clone() for value in storage.distribution_params)
        self.clip_param=clip_param
        self.before=self.measure(actor)

    @torch.no_grad()
    def measure(self,actor):
        # Native MLP has no dropout/normalization state updates. Use public latent
        # and distribution APIs without sampling or touching the actor's cached distribution.
        import copy
        # Module shallow copy isolates the cached distribution while reading the
        # original parameters. Deepcopy can fail on the live non-leaf PPO cache.
        distribution=copy.copy(actor.distribution)
        distribution.update(actor.mlp(actor.get_latent(self.obs)))
        log_prob=distribution.log_prob(self.actions).reshape(-1)
        ratio=(log_prob-self.old_log_prob).exp()
        kl=distribution.kl_divergence(self.old_params,distribution.params)
        return {'ratio':summarize_tensor(ratio),'KL':summarize_tensor(kl),
            'clip_fraction':float(((ratio-1).abs()>self.clip_param).float().mean().cpu()),
            'entropy':summarize_tensor(distribution.entropy),
            'mean':summarize_tensor(distribution.mean),'std':summarize_tensor(distribution.std)}

    def summary(self,actor):
        return {'provenance':'online deterministic full rollout before/after actual PPO update; not minibatch KL or scheduler input',
                'before':self.before,'after':self.measure(actor)}


class GradientSummary:
    """Observe gradients actually supplied to the optimizer, without modifying them."""
    def __init__(self,actor,critic,optimizer):
        self.squares={name:[] for name in ('actor','critic','std')}
        self.handles=[]
        self.parameters=[]
        for prefix,model in (('actor',actor),('critic',critic)):
            for name,parameter in model.named_parameters():
                if not parameter.requires_grad:continue
                group='std' if prefix=='actor' and 'std' in name else prefix
                self.parameters.append((group,parameter))
        def record(optimizer,args,kwargs):
            for group,parameter in self.parameters:
                if parameter.grad is not None:
                    self.squares[group].append(parameter.grad.detach().float().square().sum())
        self.handles.append(optimizer.register_step_pre_hook(record))

    def close(self):
        for handle in self.handles:handle.remove()

    def summary(self):
        return {'provenance':'online optimizer pre-step; after existing clipping/retention hooks; aggregate across minibatches',
                **{name:float(torch.stack(values).sum().sqrt().cpu()) if values else None
                   for name,values in self.squares.items()}}
