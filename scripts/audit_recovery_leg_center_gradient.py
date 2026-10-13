"""Two actual frozen-rollout batch actor gradients; no optimizer step or simulator."""
import argparse,json,copy
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.recovery.leg_center_proposal import eligible_mask,terms


def flat_grad(loss,params):
    values=torch.autograd.grad(loss,params,allow_unused=True)
    return torch.cat([torch.zeros_like(p).flatten() if g is None else g.flatten() for p,g in zip(params,values)]).detach()


def audit(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text());inputs=dict([checked_input(sp)])
    p=run/'evaluation_00.json';d=json.loads(p.read_text());inputs.update([checked_input(p),checked_input(s['source_checkpoint'],s['source_sha256'])])
    if d['checkpoint_sha256']!=s['source_sha256'] or not d['frozen_state_unchanged']:raise ValueError('Identity/state conflict')
    p=run/d['capture']['path'];inputs.update([checked_input(p,d['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    saved=torch.load(s['source_checkpoint'],map_location='cpu',weights_only=False)
    rng=torch.get_rng_state().clone();threads=torch.get_num_threads();torch.set_num_threads(1)
    rows=[]
    try:
        dummy=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);actor=model(dummy,actor=True,spec=s);actor.load_state_dict(saved['actor'],strict=True);actor.eval()
        before=copy.deepcopy(actor.state_dict());params=list(actor.parameters())
        def forward(x):
            td=TensorDict({'policy':x[:,:25],'history':x[:,25:]},batch_size=[len(x)])
            return actor(td)
        for roll in range(2):
            x=torch.tensor(a['pre_obs150'][roll].reshape(-1,150));sample=torch.tensor(a['sample'][roll].reshape(-1,6));oldmean=torch.tensor(a['mean'][roll].reshape(-1,6));std=torch.tensor(a['std'][roll].reshape(-1,6))
            advantage=torch.tensor(a['advantage_normalized'][roll].reshape(-1));md=torch.tensor(a['pre_metadata'][roll].reshape(-1,4));state=torch.tensor(a['post_state'][roll].reshape(-1,39))
            controlled=md[:,2].bool();preclock=(state[:,0]-.01).clamp_min(0)
            mask=eligible_mask(md[:,0]==d['capture']['family_names'].index('swing_candidate_from_historical_r1'),controlled,preclock,md[:,3],state[:,3].bool()|state[:,4].bool())
            def surrogate():
                mean=forward(x);normal=torch.distributions.Normal(mean,actor.distribution.std_param.expand_as(mean))
                logp=normal.log_prob(sample).sum(-1);old=torch.distributions.Normal(oldmean,std).log_prob(sample).sum(-1)
                ratio=torch.exp(logp-old);entropy=normal.entropy().sum(-1).mean()
                return -(ratio*advantage).mean()-s['ppo']['entropy_coef']*entropy,mean,ratio
            base,mean,ratio=surrogate();replay=float(abs(mean-oldmean).max().detach());ratioerror=float(abs(ratio-1).max().detach());g=flat_grad(base,params)
            mu=forward(x);per=terms(mu,x,mask);aux=per.sum()/controlled.sum();h=flat_grad(aux,params)
            norm=g.norm().item();hnorm=h.norm().item();cos=torch.dot(g,h).item()/max(norm*hnorm,1e-30)
            clipped=g*min(1.,1/max(norm,1e-30));incoming=clipped.norm().item()
            error=1.6*mean.detach()[:,[0,1,3,4]]-x[:,9:13]/2
            lambdas=[]
            for coefficient in [.001,.003,.01,.03,.1]:
                combined=clipped+coefficient*h;post=combined*min(1.,1/max(combined.norm().item(),1e-30))
                lambdas.append({'lambda':coefficient,'aux_over_incoming_actor_norm':coefficient*hnorm/max(incoming,1e-30),
                    'combined_postclip_norm':post.norm().item(),'postclip_cosine_original':torch.dot(post,clipped).item()/max(post.norm().item()*incoming,1e-30)})
            rows.append({'rollout':roll,'eligible_count':int(mask.sum()),'controlled_denominator':int(controlled.sum()),
                'mean_replay_error':replay,'ratio_error':ratioerror,'raw_PPO_actor_gradient_norm':norm,'clipped_actor_gradient_norm':incoming,
                'unit_aux_gradient_norm':hnorm,'gradient_cosine':cos,'unweighted_aux_loss':aux.item(),
                'eligible_target_error_mean_rad':error[mask].mean(0).tolist(),'eligible_target_error_abs_mean_rad':abs(error[mask]).mean(0).tolist(),
                'masked_noneligible_loss_max':float(per[~mask].abs().max()),'candidates':lambdas})
        if not all(torch.equal(v,actor.state_dict()[k]) for k,v in before.items()):raise ValueError('Actor state changed')
    finally:torch.set_num_threads(threads);torch.set_rng_state(rng)
    acceptable=[c for c in [.001,.003,.01,.03,.1] if all(.03<=next(x['aux_over_incoming_actor_norm'] for x in r['candidates'] if x['lambda']==c)<=.2 for r in rows)]
    result={'inputs_sha256':inputs,'rollouts':rows,'gradient_only_candidate_lambda':acceptable[0] if acceptable else None,
        'actor_state_unchanged':True,'critic_Adam_not_loaded_for_mutation':True,'simulation':0,'optimizer_steps':0,'runtime_wired':False,
        'limits':['frozenfullbatch actor gradient at ratio≈1 plusentropy,not historicalminibatchupdate replay',
            'actorclip1 thenaux thenactorreclip assumedlike priorauxhook; criticgrad not included',
            'preclock inferred postclockminusdt; latestRuntimepreclock must verify beforeintegration',
            '3to20percent normrange is engineeringcandidate heuristic,not stability/skill guarantee',
            'no Adamstep executed; moments inheritance preserved but counterfactual parameter/oldtask outputs unknown',
            'auxmayrewardinactivity and suppressnecessaryswing; trueRL trial needed for acceptance']}
    publish(output,{'audit.json':result},inputs);print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.run,a.output_dir)
