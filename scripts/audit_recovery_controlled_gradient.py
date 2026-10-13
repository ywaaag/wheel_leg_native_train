"""Frozen pre-update score gradients, no entropy/critic/Adam or simulator."""
import json,argparse
from pathlib import Path
import torch,numpy as np
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def audit(run,output):
    run=Path(run);inputs={}
    def read(p):
        k,h=checked_input(p);inputs[k]=h;return json.loads(Path(k).read_text())
    spec=read(run/'source_snapshot/spec.json');d=read(run/'evaluation_00.json');k,h=checked_input(run/d['capture']['path'],d['capture']['sha256']);inputs[k]=h
    cp,sha=checked_input(spec['source_checkpoint'],spec['source_sha256']);inputs[cp]=sha
    with np.load(k) as z:a={n:z[n] for n in z.files}
    rng=torch.get_rng_state().clone();threads=torch.get_num_threads();torch.set_num_threads(1)
    try:
        obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);actor=model(obs,actor=True,spec=spec);actor.load_state_dict(torch.load(cp,map_location='cpu',weights_only=False)['actor']);actor.eval();params=list(actor.parameters());rows=[]
        for roll in range(2):
            x=torch.tensor(a['pre_obs150'][roll].reshape(-1,150));act=torch.tensor(a['sample'][roll].reshape(-1,6));adv=torch.tensor(a['advantage_normalized'][roll].reshape(-1));md=a['pre_metadata'][roll].reshape(-1,4);valid=torch.tensor(md[:,d['capture']['pre_metadata_columns'].index('controlled')].astype(bool))
            mean=actor(TensorDict({'policy':x[:,:25],'history':x[:,25:]},batch_size=[len(x)]),stochastic_output=False);normal=torch.distributions.Normal(mean,actor.distribution.std_param.expand_as(mean));logp=normal.log_prob(act).sum(-1)
            old=torch.distributions.Normal(torch.tensor(a['mean'][roll].reshape(-1,6)),torch.tensor(a['std'][roll].reshape(-1,6))).log_prob(act).sum(-1);ratio=torch.exp(logp-old)
            norms=[]
            for mask in (valid,~valid):
                loss=-(adv*ratio*mask).sum()/len(x);grad=torch.autograd.grad(loss,params,retain_graph=True,allow_unused=True);norms.append(float(torch.sqrt(sum(g.square().sum() for g in grad if g is not None))))
            rows.append({'rollout':roll,'controlled_gradient_norm':norms[0],'uncontrolled_gradient_norm':norms[1],'uncontrolled_over_controlled':norms[1]/norms[0],'ratio_max_error':float(abs(ratio-1).max().detach())})
        counts={f:{'total':int((a['pre_metadata'][...,0]==i).sum()),'controlled':int(((a['pre_metadata'][...,0]==i)&a['pre_metadata'][...,2].astype(bool)).sum())} for i,f in enumerate(d['capture']['family_names'])}
        result={'counts':counts,'score_gradients':rows,'simulation':0,'optimizer_steps':0,'scope':'Fullbatch actual sample weight, score surrogate only at ratio approx1; not entropy/critic/Adam or causality'}
        publish(output,{'audit.json':result},inputs,completion_marker=True);print(json.dumps(result,indent=2))
    finally:torch.set_rng_state(rng);torch.set_num_threads(threads)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.run,a.output_dir)
