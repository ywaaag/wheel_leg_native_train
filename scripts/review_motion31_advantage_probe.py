"""CPU audit of one identity-bound Motion31 frozen rollout; no optimizer/simulator."""
import argparse
import json
from pathlib import Path
import numpy as np
from native_stand.students.data import sha


def stats(v):
    v=np.asarray(v,dtype=np.float64).reshape(-1)
    return None if not len(v) else dict(count=len(v),mean=float(v.mean()),std=float(v.std()),
        median=float(np.median(v)),p05=float(np.quantile(v,.05)),p95=float(np.quantile(v,.95)),
        positive_fraction=float((v>0).mean()))


def analyze(a, metadata, spec):
    valid=a['actor_valid'].astype(bool); raw=a['advantage_raw'][...,0]; norm=a['advantage_normalized'][...,0]
    expected=np.zeros_like(raw);expected[valid]=(raw[valid]-raw[valid].mean())/(raw[valid].std(ddof=1)+1e-8)
    normalization_error=float(np.max(np.abs(expected-norm)))
    values=a['value'][...,0];returns=a['returns'][...,0];rewards=a['storage_reward'][...,0]
    done=a['terminated']|a['truncated'];gae=np.zeros_like(values[0]);computed=np.zeros_like(values)
    for t in range(len(values)-1,-1,-1):
        nv=a['bootstrap_last_value'][...,0] if t==len(values)-1 else values[t+1]
        live=1-done[t].astype(np.float32)
        gae=rewards[t]+spec['ppo']['gamma']*nv*live-values[t]+live*spec['ppo']['gamma']*spec['ppo']['lam']*gae
        computed[t]=gae+values[t]
    gae_error=float(np.max(np.abs(computed-returns)))
    command_error=float(np.max(np.abs(a['actor_input'][...,22:25]-a['command']/np.array([4,4,.5]))))
    direction=np.sign(a['target'][...,0]);velocity=a['state_pre_reset'][...,7]
    age=a['episode_age_s'];schedule=spec['student_training']['train_schedule_s'];hold=(age>=sum(schedule[:2]))&(age<sum(schedule[:3]))
    groups=[]
    for index,target in enumerate(spec['curriculum']['stages'][0]['commands']):
        mask=valid&(a['command_index']==index);m=mask&hold
        row={'target':target,'valid_samples':int(mask.sum()),'hold_samples':int(m.sum()),
            'episode_age_s':stats(age[mask]),'value':stats(values[mask]),'return':stats(returns[mask]),
            'raw_advantage':stats(raw[mask]),'normalized_advantage':stats(norm[mask]),
            'sign_flip_fraction':float(((raw[mask]>0)!=(norm[mask]>0)).mean()) if mask.any() else None,
            'raw_positive_to_normalized_negative_fraction':float(((raw[mask]>0)&(norm[mask]<0)).mean()) if mask.any() else None,
            'hold_velocity':stats(velocity[m]),
            'hold_tracking_MAE':float(np.abs(velocity[m]-a['command'][...,0][m]).mean()) if m.any() else None,
            'hold_direction_rate':float((velocity[m]*direction[m]>0).mean()) if m.any() and target[0] else None,
            'hold_pitch_abs':stats(np.abs(a['posture_pre_reset'][...,0][m])),
            'hold_roll_abs':stats(np.abs(a['posture_pre_reset'][...,1][m])),
            'hold_height':stats(a['state_pre_reset'][...,6][m]),
            'hold_both_wheel_contact':float((a['state_pre_reset'][...,10:12][m]>2).all(-1).mean()) if m.any() else None,
            'raw_action_clip_fraction':float((np.abs(a['action_raw'][mask])>1).mean()) if mask.any() else None,
            'reward_dt_mean':dict(zip(metadata['reward_names'],a['reward_dt'][mask].mean(0).tolist())) if mask.any() else None,
            'error_bins':[]}
        error=np.abs(velocity-a['command'][...,0])
        for lo,hi in [(0,.1),(.1,.3),(.3,.75),(.75,1.5),(1.5,float('inf'))]:
            chosen=mask&(error>=lo)&(error<hi)
            row['error_bins'].append({'abs_vx_error_range':[lo,None if np.isinf(hi) else hi],
                'samples':int(chosen.sum()),'raw_advantage':stats(raw[chosen]),'normalized_advantage':stats(norm[chosen])})
        groups.append(row)
    return {'normalization_max_abs_error':normalization_error,'GAE_return_max_abs_error':gae_error,
        'actor_command_readback_max_abs_error':command_error,
        'checks_passed':normalization_error<1e-4 and gae_error<1e-4 and command_error<1e-6,
        'raw_advantage_global':stats(raw[valid]),'normalized_advantage_global':stats(norm[valid]),
        'eligible_samples':int(valid.sum()),'ineligible_samples':int((~valid).sum()),
        'terminated':int(a['terminated'].sum()),'truncated':int(a['truncated'].sum()),'groups':groups,
        'interpretation':'Centering sign flips are expected, not proof of harmful updates. No optimizer step or capability certification.'}



def local_gradients(actor, arrays, commands):
    """Offline exact-unit-ratio surrogate; no optimizer, cache changes or RNG."""
    import torch
    valid=arrays['actor_valid'].reshape(-1).astype(bool)
    index=arrays['command_index'].reshape(-1)
    raw=arrays['advantage_raw'].reshape(-1);norm=arrays['advantage_normalized'].reshape(-1)
    center=raw[valid].mean();ss=((raw[valid]-center)**2).sum()
    before={k:v.detach().clone() for k,v in actor.state_dict().items()}
    actor.log_std.requires_grad_(False)
    parameters=[p for p in actor.parameters() if p.requires_grad]
    x=torch.from_numpy(arrays['actor_input'].reshape(-1,31))
    actions=torch.from_numpy(arrays['action_raw'].reshape(-1,6))
    gradients=[];groups=[]
    for i,command in enumerate(commands):
        mask=valid&(index==i)
        if not mask.any():
            gradients.append(torch.zeros(sum(p.numel() for p in parameters)))
            groups.append({'command':command,'sample_count':0});continue
        selected=torch.from_numpy(mask)
        lp=actor.distribution(x[selected]).log_prob(actions[selected]).sum(-1)
        loss=-(torch.from_numpy(norm[mask])*(lp-lp.detach()).exp()).sum()/int(valid.sum())
        gradient=torch.cat([g.reshape(-1) for g in torch.autograd.grad(loss,parameters)]).detach()
        gradients.append(gradient)
        groups.append({'command':command,'sample_count':int(mask.sum()),
            'global_centered_sum_squares_fraction':float(((raw[mask]-center)**2).sum()/ss) if ss else None,
            'normalized_advantage_positive_fraction':float((norm[mask]>0).mean()),
            'raw_positive_to_normalized_negative_fraction':float(((raw[mask]>0)&(norm[mask]<0)).mean()),
            'terminated':int(arrays['terminated'].reshape(-1)[mask].sum()),
            'raw_advantage_std':float(raw[mask].std()),'local_actor_gradient_norm_batch_weighted':float(gradient.norm())})
    total=sum(gradients);old=sum(gradients[:5]);new=sum(gradients[5:])
    cosine=lambda u,v:float(torch.dot(u,v)/(u.norm()*v.norm()).clamp_min(1e-20))
    for row,g in zip(groups,gradients):row['cosine_with_full_batch_gradient']=cosine(g,total)
    return {'provenance':'offline local surrogate gradient; exact unit ratio; no historical gradient claim',
        'groups':groups,'actor_gradient_total_norm':float(total.norm()),
        'old5_gradient_norm':float(old.norm()),'new2_gradient_norm':float(new.norm()),
        'old5_vs_new2_cosine':cosine(old,new),'minus1p5_vs_old5_cosine':cosine(gradients[-1],old),
        'without_minus1p5_vs_full_cosine':cosine(sum(gradients[:-1]),total),
        'command_gradient_cosines':[[cosine(a,b) for b in gradients] for a in gradients],
        'parameters_unchanged':all(torch.equal(v,actor.state_dict()[k]) for k,v in before.items()),
        'optimizer_updates':0,'limitations':'single source batch before new-task critic adaptation; not historical minibatch/Adam update or physical causality'}


def review(run,output):
    run=Path(run).resolve();output=Path(output).resolve()
    terminal=json.loads((run/'terminal_report.json').read_text());meta=json.loads((run/'probe_result.json').read_text())
    specpath=run/'source_snapshot/spec.json';spec=json.loads(specpath.read_text());capture=run/meta['capture']['path']
    if terminal['status']!='COMPLETED' or terminal.get('failure') or not meta['frozen_state_unchanged'] or meta['optimizer_updates']!=0:
        raise ValueError('Complete unchanged frozen diagnostic required')
    if sha(capture)!=meta['capture']['sha256'] or sha(specpath)!=meta['spec_sha256'] or sha(spec['source_checkpoint'])!=meta['source_sha256']:
        raise ValueError('Probe identity changed')
    with np.load(capture,allow_pickle=False) as archive:a={k:archive[k] for k in archive.files}
    result=analyze(a,meta,spec)
    # Repeated public forward; no sampling and no mutation of the distribution cache.
    import torch
    from native_stand.students.model import load
    actor,_=load(spec['source_checkpoint'],'MotionZeroStudent');actor.eval()
    with torch.no_grad():
        x=torch.from_numpy(a['actor_input']);actions=torch.from_numpy(a['action_raw'])
        mean=actor.mean(x);repeat=actor.mean(x)
        logp=actor.distribution(x).log_prob(actions).sum(-1).numpy()
    result['forward_audit']={'repeat_forward_max_abs_difference':float((mean-repeat).abs().max()),
        'CPU_vs_GPU_mean_max_abs_difference':float(np.max(np.abs(mean.numpy()-a['action_mean']))),
        'old_log_prob_max_abs_difference':float(np.max(np.abs(logp-a['old_log_prob'][...,0]))),
        'scope':'CPU re-forward on exact sampled states, numerical GPU/CPU differences allowed; not an optimizer replay'}
    result['local_gradient_summary']=local_gradients(actor,a,spec['curriculum']['stages'][0]['commands'])
    paths=[run/'terminal_report.json',run/'probe_result.json',specpath,capture,Path(spec['source_checkpoint'])]
    result['inputs']={str(p):sha(p) for p in paths}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    lines=['# Motion31冻结rollout advantage审计','',f"检查：{result['checks_passed']}；有效样本：{result['eligible_samples']}；optimizer更新：0。",'',
        '|目标vx|样本|保持vx|保持MAE|raw A均值|normalized A均值|符号翻转率|','|---|---:|---:|---:|---:|---:|---:|']
    for r in result['groups']:
        def val(x):return 'UNKNOWN' if x is None else f'{x:.6f}'
        lines.append('|'+ '|'.join([str(r['target'][0]),str(r['valid_samples']),val((r['hold_velocity'] or {}).get('mean')),val(r['hold_tracking_MAE']),val((r['raw_advantage'] or {}).get('mean')),val((r['normalized_advantage'] or {}).get('mean')),val(r['sign_flip_fraction'])])+'|')
    lines+=['','这是来源1600在新课程分布的单rollout，不是历史训练轨迹。中心化导致的符号翻转本身不证明错误或因果；不据此自动采用分组归一化。详细value/return、误差区间、奖励贡献及SHA见audit.json。']
    with (output/'audit.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    r=review(args.run,args.output_dir);print(json.dumps({k:v for k,v in r.items() if k not in ('groups','inputs')},indent=2))
