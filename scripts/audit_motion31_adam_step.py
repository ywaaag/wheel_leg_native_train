"""Two CPU single-Adam-step counterfactuals on an exact frozen Motion31 batch.

A includes all cohorts. B zeros only the -1.5 cohort Actor surrogate contribution,
keeping the same batch denominator, normalized advantages and Critic objective.
No simulator, online PPO, RNG sampling, checkpoint export or historical replay.
"""
import argparse
import copy
import json
from pathlib import Path
import time
import numpy as np
import torch
from native_stand.students.data import sha



def source_equal(a,b):
    """Checkpoint metadata includes NumPy RNG arrays as well as Torch state."""
    if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(source_equal(v,b[k]) for k,v in a.items())
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(source_equal(x,y) for x,y in zip(a,b))
    return a==b


def flat(parameters):
    return torch.cat([p.detach().reshape(-1) for p in parameters])


def tensor_summary(v):
    v=v.detach().float().reshape(-1)
    if not v.numel():return None
    return {'mean':float(v.mean()),'std':float(v.std(unbiased=False)),
            'p05':float(torch.quantile(v,.05)),'p50':float(v.median()),'p95':float(torch.quantile(v,.95))}


def replay_arm(source,arrays,commands,config,*,exclude_index=None):
    from native_stand.students.model import Student
    from native_stand.command_v6.tools.frozen_rollout_probe import tree_equal
    with torch.random.fork_rng(devices=[]):
        actor=Student(True,version='multiskill_mcu_v2')
        critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1')
    actor.load_state_dict(source['actor'],strict=True);critic.load_state_dict(source['critic'],strict=True)
    actor.log_std.requires_grad_(False);actor.train();critic.train()
    parameters=list(actor.parameters())+list(critic.parameters())
    optimizer=torch.optim.Adam(parameters,lr=config['learning_rate'])
    optimizer.load_state_dict(copy.deepcopy(source['optimizer']))
    if [g['lr'] for g in optimizer.param_groups]!=[config['learning_rate']]:raise ValueError('Source Adam LR differs')
    if any(p.requires_grad and (p not in optimizer.state or optimizer.state[p]['exp_avg'].shape!=p.shape or optimizer.state[p]['exp_avg_sq'].shape!=p.shape) for p in parameters):
        raise ValueError('Source Adam state missing/misaligned')
    restored=tree_equal(optimizer.state_dict(),source['optimizer'])
    if not restored:raise ValueError('Adam exact restore differs')
    actor_parameters=[p for p in actor.parameters() if p.requires_grad]
    critic_parameters=list(critic.parameters())
    before_actor=flat(actor_parameters).clone();before_critic=flat(critic_parameters).clone();fixed_std=actor.log_std.detach().clone()
    valid=torch.from_numpy(arrays['actor_valid'].reshape(-1).astype(bool))
    index=torch.from_numpy(arrays['command_index'].reshape(-1))
    x=torch.from_numpy(arrays['actor_input'].reshape(-1,31));cx=torch.from_numpy(arrays['critic_input'].reshape(-1,49))
    actions=torch.from_numpy(arrays['action_raw'].reshape(-1,6))
    advantage=torch.from_numpy(arrays['advantage_normalized'].reshape(-1)).detach()
    returns=torch.from_numpy(arrays['returns'].reshape(-1)).detach()
    denominator=int(valid.sum())
    included=valid if exclude_index is None else valid&(index!=exclude_index)
    if not denominator or not included.any():raise ValueError('No valid counterfactual Actor samples')
    dist=actor.distribution(x);old_mean=dist.mean.detach().clone();old_logp=dist.log_prob(actions).sum(-1).detach()
    ratio=(dist.log_prob(actions).sum(-1)-old_logp).exp()
    actor_loss=(torch.maximum(-advantage*ratio,-advantage*ratio.clamp(1-config['clip'],1+config['clip']))*included).sum()/denominator
    value_loss=(critic(cx).squeeze(-1)-returns).square().mean()
    total=actor_loss+config['value_coef']*value_loss-config['entropy_coef']*dist.entropy().sum(-1)[valid].mean()
    optimizer.zero_grad(set_to_none=True);total.backward()
    gradient=torch.cat([p.grad.detach().reshape(-1) for p in actor_parameters]).clone()
    actor_grad_norm=float(torch.nn.utils.clip_grad_norm_(actor.parameters(),config['max_grad_norm']))
    critic_grad_norm=float(torch.nn.utils.clip_grad_norm_(critic.parameters(),config['max_grad_norm']))
    actor_states=[optimizer.state[p]['step'].item() for p in actor_parameters]
    optimizer.step() # exactly one CPU step per arm, never saved as a checkpoint
    if not torch.equal(fixed_std,actor.log_std):raise RuntimeError('Fixed std changed')
    actor_steps_after=[optimizer.state[p]['step'].item() for p in actor_parameters]
    if any(b!=a+1 for a,b in zip(actor_states,actor_steps_after)):raise RuntimeError('Adam step counter differs')
    delta=flat(actor_parameters)-before_actor;critic_delta=flat(critic_parameters)-before_critic
    if not torch.isfinite(delta).all() or not torch.isfinite(critic_delta).all():raise RuntimeError('Nonfinite offline step')
    with torch.no_grad():
        new_dist=actor.distribution(x);new_mean=new_dist.mean;logp_delta=new_dist.log_prob(actions).sum(-1)-old_logp
        new_ratio=logp_delta.exp();kl=torch.distributions.kl_divergence(torch.distributions.Normal(old_mean,actor.log_std.exp()),new_dist).sum(-1)
        clipped_gain=torch.minimum(advantage*new_ratio,advantage*new_ratio.clamp(1-config['clip'],1+config['clip']))-advantage
        groups=[]
        for i,command in enumerate(commands):
            mask=valid&(index==i)
            if not mask.any():groups.append({'command':command,'samples':0});continue
            dm=new_mean[mask]-old_mean[mask]
            pg=(advantage[mask]*logp_delta[mask])
            groups.append({'command':command,'samples':int(mask.sum()),'surrogate_contribution_included':i!=exclude_index,
                'log_prob_delta':tensor_summary(logp_delta[mask]),'ratio':tensor_summary(new_ratio[mask]),
                'KL_mean':float(kl[mask].mean()),'clip_fraction':float(((new_ratio[mask]-1).abs()>config['clip']).float().mean()),
                'advantage_weighted_log_prob_delta_mean':float(pg.mean()),
                'clipped_surrogate_gain_mean':float(clipped_gain[mask].mean()),
                'action_mean_before_per_channel':old_mean[mask].mean(0).tolist(),
                'action_mean_after_per_channel':new_mean[mask].mean(0).tolist(),
                'action_mean_delta_per_channel':dm.mean(0).tolist(),
                'action_mean_delta_rms_per_channel':dm.square().mean(0).sqrt().tolist(),
                'scaled_target_mean_delta_per_channel':(dm.mean(0)*dm.new_tensor([1.5,1.5,100.,1.5,1.5,100.])).tolist()})
        old_mask=valid&(index<5);new_mask=valid&(index>=5)
        result={'arm':'A_full_batch' if exclude_index is None else 'B_zero_minus1p5_actor_contribution',
            'offline_optimizer_steps':1,'exact_Adam_restore':restored,'denominator':denominator,
            'included_actor_samples':int(included.sum()),'critic_samples':len(returns),
            'initial_actor_surrogate':float(actor_loss.detach()),'initial_value_loss':float(value_loss.detach()),
            'initial_combined_loss':float(total.detach()),'actor_gradient_norm_before_clipping':actor_grad_norm,
            'critic_gradient_norm_before_clipping':critic_grad_norm,'actor_clip_scale':min(1.,config['max_grad_norm']/(actor_grad_norm+1e-6)),
            'actor_parameter_delta_norm':float(delta.norm()),'critic_parameter_delta_norm':float(critic_delta.norm()),
            'gradient_dot_Adam_delta':float(torch.dot(gradient,delta)),
            'old5_clipped_surrogate_gain_mean':float(clipped_gain[old_mask].mean()),
            'new2_clipped_surrogate_gain_mean':float(clipped_gain[new_mask].mean()),
            'full_clipped_surrogate_gain_mean':float(clipped_gain[valid].mean()),
            'old5_KL_mean':float(kl[old_mask].mean()),'new2_KL_mean':float(kl[new_mask].mean()),
            'std_unchanged':True,'groups':groups}
    return result,delta,critic_delta



def replay_full_arm(source,arrays,commands,config,*,exclude_index=None,shuffle_seed=20261015):
    """Run the installed production ControlledPPO.update, observe each real CPU step."""
    import hashlib
    from tensordict import TensorDict
    from rsl_rl.storage import RolloutStorage
    from native_stand.students.model import Student
    from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
    class AuditStorage(RolloutStorage):
        def mini_batch_generator(self,*args,**kwargs):
            for batch in super().mini_batch_generator(*args,**kwargs):
                self.current_batch=batch
                ids=batch.observations['probe_sample_id'].reshape(-1).long()
                self.batch_identity={'sha256':hashlib.sha256(ids.numpy().tobytes()).hexdigest(),
                    'samples':len(ids),'cohort_counts':torch.bincount(flat_index[ids],minlength=len(commands)).tolist()}
                yield batch
    with torch.random.fork_rng(devices=[]):
        actor=Student(True,version='multiskill_mcu_v2')
        critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1')
    actor.load_state_dict(source['actor']);critic.load_state_dict(source['critic']);actor.log_std.requires_grad_(False)
    actor.train();critic.train()
    t,n=arrays['actor_valid'].shape
    flat_index=torch.from_numpy(arrays['command_index'].reshape(-1))
    x=torch.from_numpy(arrays['actor_input'].reshape(-1,31));cx=torch.from_numpy(arrays['critic_input'].reshape(-1,49))
    actions=torch.from_numpy(arrays['action_raw'].reshape(-1,6));valid=torch.from_numpy(arrays['actor_valid'].reshape(-1).astype(bool))
    advantage=torch.from_numpy(arrays['advantage_normalized'].reshape(-1)).detach()
    obs=TensorDict({'student_actor':x[:n], 'student_critic':cx[:n],KEY:valid[:n,None],
                   'probe_sample_id':torch.arange(n)[:,None]},batch_size=[n])
    storage=AuditStorage('rl',n,t,obs,[6],device='cpu')
    storage.observations['student_actor'].copy_(x.reshape(t,n,31));storage.observations['student_critic'].copy_(cx.reshape(t,n,49))
    storage.observations[KEY].copy_(valid.reshape(t,n,1))
    storage.observations['probe_sample_id'].copy_(torch.arange(t*n).reshape(t,n,1))
    storage.actions.copy_(actions.reshape(t,n,6));storage.values.copy_(torch.from_numpy(arrays['value']))
    storage.returns.copy_(torch.from_numpy(arrays['returns']))
    storage.advantages.copy_(advantage.reshape(t,n,1))
    if exclude_index is not None:storage.advantages[flat_index.reshape(t,n)==exclude_index]=0
    with torch.no_grad():
        baseline=actor.distribution(x);old_mean=baseline.mean.clone();old_std=baseline.stddev.clone()
        old_logp=baseline.log_prob(actions).sum(-1).clone()
    storage.actions_log_prob.copy_(old_logp.reshape(t,n,1))
    storage.distribution_params=(old_mean.reshape(t,n,6),old_std.reshape(t,n,6))
    storage.step=t
    ppo=ControlledPPO(actor,critic,storage,device='cpu',schedule='fixed',
        learning_rate=config['learning_rate'],num_learning_epochs=config['epochs'],num_mini_batches=config['minibatches'],
        clip_param=config['clip'],value_loss_coef=config['value_coef'],entropy_coef=config['entropy_coef'],
        gamma=config['gamma'],lam=config['lam'],max_grad_norm=config['max_grad_norm'],use_clipped_value_loss=False)
    storage.observations[KEY].copy_(valid.reshape(t,n,1)) # ControlledPPO initializes its mask buffer
    ppo.optimizer.load_state_dict(copy.deepcopy(source['optimizer']))
    if not source_equal(ppo.optimizer.state_dict(),source['optimizer']):raise ValueError('Full update Adam restore differs')
    if [g['lr'] for g in ppo.optimizer.param_groups]!=[config['learning_rate']]:raise ValueError('Full update LR differs')
    actor_parameters=[p for p in actor.parameters() if p.requires_grad];critic_parameters=list(critic.parameters())
    before_actor=flat(actor_parameters).clone();before_critic=flat(critic_parameters).clone();fixed_std=actor.log_std.detach().clone()
    actor_step_before=[int(ppo.optimizer.state[p]['step']) for p in actor_parameters]
    scalar=lambda v:float(v.detach())
    @torch.no_grad()
    def measure():
        dist=actor.distribution(x);lp=dist.log_prob(actions).sum(-1)-old_logp;ratio=lp.exp()
        kl=torch.distributions.kl_divergence(torch.distributions.Normal(old_mean,old_std),dist).sum(-1)
        gain=torch.minimum(advantage*ratio,advantage*ratio.clamp(1-config['clip'],1+config['clip']))-advantage
        groups=[]
        for i,command in enumerate(commands):
            mask=valid&(flat_index==i)
            if not mask.any():groups.append({'command':command,'samples':0});continue
            dm=dist.mean[mask]-old_mean[mask]
            groups.append({'command':command,'samples':int(mask.sum()),
                'clipped_surrogate_gain_mean':scalar(gain[mask].mean()),'KL_mean':scalar(kl[mask].mean()),
                'clip_fraction':scalar(((ratio[mask]-1).abs()>config['clip']).float().mean()),
                'log_prob_delta_mean':scalar(lp[mask].mean()),'ratio_mean':scalar(ratio[mask].mean()),
                'advantage_weighted_log_prob_delta_mean':scalar((advantage[mask]*lp[mask]).mean()),
                'action_mean_delta_per_channel':dm.mean(0).tolist(),
                'action_mean_delta_rms_per_channel':dm.square().mean(0).sqrt().tolist()})
        old=valid&(flat_index<5)
        return {'groups':groups,'old5_clipped_surrogate_gain_mean':scalar(gain[old].mean()),
            'full_clipped_surrogate_gain_mean':scalar(gain[valid].mean()),'old5_KL_mean':scalar(kl[old].mean()),
            'full_KL_mean':scalar(kl[valid].mean()),'full_clip_fraction':scalar(((ratio[valid]-1).abs()>config['clip']).float().mean()),
            'actor_parameter_delta_norm':scalar((flat(actor_parameters)-before_actor).norm()),
            'critic_value_loss':scalar((critic(cx).squeeze(-1)-torch.from_numpy(arrays['returns'].reshape(-1))).square().mean())}
    trajectory=[];gradient_squares={'actor':[],'critic':[]};pending={};handles=[]
    for name,parameters in (('actor',actor_parameters),('critic',critic_parameters)):
        for p in parameters:
            def observe(g,name=name):gradient_squares[name].append(g.detach().float().square().sum())
            handles.append(p.register_hook(observe))
    def before_step(optimizer,args,kwargs):
        nonlocal pending
        pending={'actor_gradient_norm_before_clipping':scalar(torch.stack(gradient_squares['actor']).sum().sqrt()),
                 'critic_gradient_norm_before_clipping':scalar(torch.stack(gradient_squares['critic']).sum().sqrt()),
                 'actor_gradient_norm_after_clipping':scalar(torch.stack([p.grad.square().sum() for p in actor_parameters]).sum().sqrt()),
                 'minibatch':copy.deepcopy(storage.batch_identity)}
    def after_step(optimizer,args,kwargs):
        result=measure();result.update(pending,optimizer_step=len(trajectory)+1,
            epoch=len(trajectory)//config['minibatches']+1,minibatch_in_epoch=len(trajectory)%config['minibatches']+1)
        trajectory.append(result)
        gradient_squares['actor'].clear();gradient_squares['critic'].clear()
    handles.extend([ppo.optimizer.register_step_pre_hook(before_step),ppo.optimizer.register_step_post_hook(after_step)])
    initial=measure()
    try:
        # Actual generator draws one permutation and reuses it across epochs in this installed RSL-RL.
        # Actor sampling inside update consumes RNG as production; both arms start the same CPU seed.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(shuffle_seed);loss=ppo.update()
    finally:
        for h in handles:h.remove()
    expected=config['epochs']*config['minibatches']
    if len(trajectory)!=expected or not torch.equal(fixed_std,actor.log_std):raise RuntimeError('Full update step/std differs')
    if any(int(ppo.optimizer.state[p]['step'])!=s+expected for p,s in zip(actor_parameters,actor_step_before)):
        raise RuntimeError('Full update Adam counters differ')
    result={'arm':'A_full_batch' if exclude_index is None else 'B_zero_minus1p5_actor_contribution',
        'offline_optimizer_steps':len(trajectory),'initial':initial,'per_step':trajectory,'final':trajectory[-1],
        'production_update_loss':loss,'production_mask_summary':ppo.mask_summary,'shuffle_seed':shuffle_seed,
        'std_unchanged':True,'exact_Adam_restore':True,'critic_parameter_delta_norm':scalar((flat(critic_parameters)-before_critic).norm())}
    return result,flat(actor_parameters)-before_actor,flat(critic_parameters)-before_critic


def audit(run,output,*,full_update=False):
    started=time.perf_counter();run=Path(run).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    meta=json.loads((run/'probe_result.json').read_text());terminal=json.loads((run/'terminal_report.json').read_text())
    specpath=run/'source_snapshot/spec.json';spec=json.loads(specpath.read_text());capture=run/meta['capture']['path']
    if terminal['status']!='COMPLETED' or terminal.get('failure') or not meta['frozen_state_unchanged'] or meta['optimizer_updates']!=0:
        raise ValueError('Complete unchanged frozen source rollout required')
    if sha(specpath)!=meta['spec_sha256'] or sha(capture)!=meta['capture']['sha256'] or sha(spec['source_checkpoint'])!=meta['source_sha256']:
        raise ValueError('Input identity differs')
    with np.load(capture,allow_pickle=False) as archive:arrays={k:archive[k] for k in archive.files}
    commands=spec['curriculum']['stages'][0]['commands']
    if commands!=[[0.,0.],[.5,0.],[-.5,0.],[1.,0.],[-1.,0.],[1.5,0.],[-1.5,0.]]:raise ValueError('Exact seven-cohort matrix required')
    from native_stand.students.model import load
    _,source=load(spec['source_checkpoint'],'MotionZeroStudent')
    if source.get('critic_privileged_version')!='motion_privileged49_v1':raise ValueError('Wrong Critic semantics')
    # Validate sampled data/GAE first by the existing independent audit implementation.
    from review_motion31_advantage_probe import analyze
    checks=analyze(arrays,meta,spec)
    if not checks['checks_passed']:raise ValueError('Independent rollout audit failed')
    snapshot=copy.deepcopy(source)
    replay=replay_full_arm if full_update else replay_arm
    arm_a,delta_a,critic_a=replay(source,arrays,commands,spec['ppo'])
    arm_b,delta_b,critic_b=replay(source,arrays,commands,spec['ppo'],exclude_index=6)
    if full_update and [r['minibatch'] for r in arm_a['per_step']] != [r['minibatch'] for r in arm_b['per_step']]:
        raise RuntimeError('A/B minibatch identities differ')
    from native_stand.command_v6.tools.frozen_rollout_probe import tree_equal
    if not source_equal(snapshot,source):raise RuntimeError('Source checkpoint state mutated in memory')
    if not torch.equal(critic_a,critic_b):raise RuntimeError('Critic ablation leaked')
    result={'version':'motion31_offline_full_update_ablation_v1' if full_update else 'motion31_offline_adam_ablation_v1','online_optimizer_updates':0,'offline_optimizer_steps':arm_a['offline_optimizer_steps']+arm_b['offline_optimizer_steps'],
        'simulation':0,'checkpoint_exports':0,'source_unchanged':True,'critic_updates_identical':True,
        'common_batch':'same65536 transitions, returns, normalized advantages, Adam/std and global denominator; only minus1.5 Actor surrogate contribution masked in B',
        'old_log_prob_reference':'CPU source re-forward on exact captured states/actions; exact ratio1 at start, not historical GPU logprob bitwise replay',
        'arms':[arm_a,arm_b],
        'actor_delta_cosine_A_B':float(torch.dot(delta_a,delta_b)/(delta_a.norm()*delta_b.norm()).clamp_min(1e-20)),
        'actor_delta_difference_norm':float((delta_a-delta_b).norm()),
        'inputs':{str(p):sha(p) for p in [specpath,capture,run/'probe_result.json',run/'terminal_report.json',Path(spec['source_checkpoint'])]},
        'limitations':['CPU production ControlledPPO.update,16 steps per arm, same new CPU shuffle; not historical GPU replay' if full_update else 'one CPU full-batch Adam step per arm; actual PPO uses16 shuffled optimizer steps per update',
            'no original5 critic warmup; this is the source initial counterfactual',
            'fixed recorded inputs cannot predict actual speed/pitch/contact after physical rollout',
            'ablation is not a proposed online sampler: no refill, re-normalization or changed denominator',
            'no critic/Adam initialization A/B and no historical training trajectory replay'],
        'wall_s':time.perf_counter()-started}
    output.mkdir(parents=True,exist_ok=False)
    if full_update:
        result['implementation_sha256']={'ControlledPPO.update':sha(__import__('native_stand.recovery.controlled_ppo',fromlist=['__file__']).__file__),
            'RolloutStorage':sha(__import__('inspect').getfile(__import__('rsl_rl.storage',fromlist=['RolloutStorage']).RolloutStorage))}
        with (output/'audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
        lines=['# Motion31 CPU完整PPO update对照','',
            '同一冻结batch，生产ControlledPPO.update，每臂16次CPU optimizer step；不是在线训练或历史GPU重放。','',
            '|step|A旧五组surrogate gain|B旧五组surrogate gain|A旧五组KL|B旧五组KL|','|---|---:|---:|---:|---:|']
        for a,b in zip(arm_a['per_step'],arm_b['per_step']):
            lines.append(f"|{a['optimizer_step']}|{a['old5_clipped_surrogate_gain_mean']:.8g}|{b['old5_clipped_surrogate_gain_mean']:.8g}|{a['old5_KL_mean']:.8g}|{b['old5_KL_mean']:.8g}|")
        lines+=['','## 最终逐命令','', '|命令|A surrogate gain|B surrogate gain|A KL|B KL|','|---|---:|---:|---:|---:|']
        for a,b in zip(arm_a['final']['groups'],arm_b['final']['groups']):
            lines.append(f"|{a['command'][0]}|{a['clipped_surrogate_gain_mean']:.8g}|{b['clipped_surrogate_gain_mean']:.8g}|{a['KL_mean']:.8g}|{b['KL_mean']:.8g}|")
        lines+=['','固定样本surrogate、KL与动作变化不代表机器人实际速度或姿态变化；未复现五次Critic适应。']
        with (output/'audit.md').open('x') as f:f.write('\n'.join(lines)+'\n')
        return result
    with (output/'audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    lines=['# Motion31 固定batch离线Adam单步对照','',
        '每臂仅一次CPU Adam step。来源不变、不导出checkpoint；不是在线PPO或历史更新复现。','',
        '|指标|A完整batch|B消融−1.5 Actor贡献|','|---|---:|---:|']
    for key in ['actor_gradient_norm_before_clipping','actor_clip_scale','actor_parameter_delta_norm','old5_clipped_surrogate_gain_mean','old5_KL_mean','full_clipped_surrogate_gain_mean']:
        lines.append(f'|{key}|{arm_a[key]:.8g}|{arm_b[key]:.8g}|')
    lines+=['','## 逐命令（正surrogate gain只表示固定样本目标改善，不代表物理速度改善）','',
        '|命令|A surrogate gain|B surrogate gain|A KL|B KL|','|---|---:|---:|---:|---:|']
    for a,b in zip(arm_a['groups'],arm_b['groups']):
        lines.append(f"|{a['command'][0]}|{a['clipped_surrogate_gain_mean']:.8g}|{b['clipped_surrogate_gain_mean']:.8g}|{a['KL_mean']:.8g}|{b['KL_mean']:.8g}|")
    lines+=['','完整六通道变化、输入SHA、限制见audit.json。A/B差异不能单独证明后续几百次更新的行为因果；不凭动作均值方向推断行驶方向。']
    with (output/'audit.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--cpu-threads',type=int,default=2)
    parser.add_argument('--full-update',action='store_true',help='production4epochs x4minibatches per arm;32 offline steps, no simulation')
    a=parser.parse_args()
    if a.cpu_threads<1:parser.error('positive CPU threads required')
    torch.set_num_threads(a.cpu_threads)
    result=audit(a.run,a.output_dir,full_update=a.full_update)
    print(json.dumps({k:v for k,v in result.items() if k not in ('arms','inputs')},indent=2))
    print((a.output_dir/'audit.md').read_text())
