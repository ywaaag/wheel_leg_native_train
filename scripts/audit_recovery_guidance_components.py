"""CPU persisted geometry decomposition; no runtime or optimizer."""
import argparse,json
from pathlib import Path
import torch
from native_stand.recovery.drawback_guidance_proposal import quality
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.command_v6.tools.evaluation_storage import read


def audit(run,output):
    run=Path(run);inputs={};cases=[]
    for u in (0,10,25,50):
        folder=run/('source_eval' if u==0 else 'formal');p=folder/('evaluation_source.json' if u==0 else f'evaluation_{u}_0_0.json');key,h=checked_input(p);inputs[key]=h;d=read(p)
        sp=folder/'source_snapshot/spec.json';key,h=checked_input(sp);inputs[key]=h;spec=json.loads(sp.read_text())
        if d['spec_sha256']!=h:raise ValueError('Evaluation spec conflict')
        cfg=spec['recovery']['drawback_guidance'];rows=[]
        for e in d['per_env']:
            s=torch.tensor(e['compact_trace_100hz']);g=torch.tensor(e['wheel_geometry_trace_100hz']);m=(s[:,0]>0)&(s[:,0]<=.30+1e-6)&(s[:,32]!=7)&s[:,29].bool()
            q=quality(g[m,:6].reshape(-1,2,3),g[m,9:13],g.new_tensor(cfg['target_root_m']))
            p=q['position_quality'];sym=q['mirror_quality'];rows.append({'env_id':e['env_id'],'position_mean':float(p.mean()),'symmetry_mean':float(sym.mean()),'product_mean':float((p*sym).mean()),'position_signal_retained_fraction':float((p*sym).sum()/p.sum()),'target_distance_mean_m':float(q['wheel_distance_m'].mean()),'local_position_slope_abs_per_m':float((2*q['wheel_distance_m']/.25**2*p[:,None]*sym[:,None]).mean())})
        cases.append({'update':u,'rows':rows})
    result={'cases':cases,'simulation':0,'optimizer_steps':0,'scope':'same first300ms measured states; slope proxy not actor policy gradient or causal evidence','conclusion':'Symmetry multiplication suppresses position signal; improved symmetry does not imply wheel placement. Do not change reward while testing stopping policy.'}
    publish(output,{'audit.json':result},inputs,completion_marker=True);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=audit(a.run,a.output_dir);print(json.dumps(r,indent=2))
