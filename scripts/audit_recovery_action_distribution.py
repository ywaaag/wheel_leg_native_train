"""CPU action-coordinate candidates; deterministic quadrature,no runtime wiring."""
import argparse,json
from pathlib import Path
import numpy as np
from numpy.polynomial.hermite import hermgauss
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def moments(mean,std,kind):
    nodes,weights=hermgauss(64);weights=weights/np.sqrt(np.pi)
    x=mean[...,None]+np.sqrt(2)*std[...,None]*nodes
    if kind=='clipped_gaussian':y=np.clip(x,-1,1)
    elif kind=='tanh_gaussian':y=np.tanh(x)
    elif kind=='clipped_mean_gaussian':y=np.clip(np.clip(mean,-1,1)[...,None]+np.sqrt(2)*std[...,None]*nodes,-1,1)
    elif kind=='bounded_mean_gaussian':y=np.clip(np.tanh(mean)[...,None]+np.sqrt(2)*std[...,None]*nodes,-1,1)
    else:raise ValueError('Unknown candidate')
    first=y@weights;variance=np.maximum((y*y)@weights-first*first,0)
    return first,np.sqrt(variance)


def candidate_mean(mean,kind):
    if kind in ('tanh_gaussian','bounded_mean_gaussian'):return np.tanh(mean)
    return np.clip(mean,-1,1)


def audit(run,output):
    run=Path(run).resolve();p=run/'source_snapshot/spec.json';s=json.loads(p.read_text());inputs=dict([checked_input(p)])
    p=run/'evaluation_00.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
    if d['checkpoint_sha256']!=s['source_sha256'] or not d['frozen_state_unchanged']:raise ValueError('Source/readback conflict')
    p=run/d['capture']['path'];inputs.update([checked_input(p,d['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    md=a['pre_metadata'];rows=[]
    for code,family in enumerate(d['capture']['family_names']):
        mask=(md[...,0]==code)&md[...,2].astype(bool);mu=a['mean'][mask];sd=a['std'][mask]
        base=np.clip(mu,-1,1)
        for kind,channels in [('clipped_gaussian',[2,5]),('tanh_gaussian',[2,5]),('tanh_gaussian',[0,1,2,3,4,5]),('clipped_mean_gaussian',[2,5]),('bounded_mean_gaussian',[2,5])]:
            changed=base.copy();changed[:,channels]=candidate_mean(mu[:,channels],kind)
            expectation,physical_std=moments(mu[:,[2,5]],sd[:,[2,5]],kind)
            delta=changed-base;wheel_delta=delta[:,[2,5]]*100;leg_delta=delta[:,[0,1,3,4]]*1.6
            rows.append({'family':family,'kind':kind,'channels':channels,'n':len(mu),
                'wheel_expected_target_mean_rad_s':expectation.mean(0).__mul__(100).tolist(),
                'wheel_within_state_sample_std_mean_rad_s':physical_std.mean(0).__mul__(100).tolist(),
                'wheel_deterministic_target_delta_abs_mean_rad_s':abs(wheel_delta).mean(0).tolist(),
                'wheel_deterministic_target_delta_abs_peak_rad_s':abs(wheel_delta).max(0).tolist(),
                'leg_deterministic_target_delta_abs_mean_rad':abs(leg_delta).mean(0).tolist(),
                'leg_deterministic_target_delta_abs_peak_rad':abs(leg_delta).max(0).tolist()})
    # First controlled sample from each observed family episode; no postreset q confusion.
    first=[]
    for env in range(64):
        seen=set()
        for flat in range(256):
            roll,step=divmod(flat,128);m=md[roll,step,env]
            if not m[2] or (int(m[0]),int(m[1])) in seen:continue
            seen.add((int(m[0]),int(m[1])))
            obs=a['pre_obs150'][roll,step,env];mu=a['mean'][roll,step,env]
            # Current frame contract q is recoverable only from explicit frame scale/ref.
            control=a['post_control'][roll,step,env]
            first.append({'env_id':env,'family':d['capture']['family_names'][int(m[0])],'episode_id':int(m[1]),
                'first_raw_mean':mu.tolist(),'first_target_after_limit_rad':control[28:32].tolist(),
                'first_actual_post_leg_q_rad':control[:6][[0,1,3,4]].tolist(),
                'target_minus_post_actual_rad':(control[28:32]-control[:6][[0,1,3,4]]).tolist(),
                'scope':'same first controlled posttransition snapshot; not exact precontrol q'})
    result={'inputs_sha256':inputs,'candidates':rows,'first_control':first,'simulation':0,'optimizer_steps':0,
        'runtime_wired':False,'quadrature':'64point GaussHermite,normalized independent sourceGaussian; no RNG',
        'limits':['Saved source observations only; candidate changes future states,unknown retention.',
            'Tanh maps latentGaussian to bounded physical action; proper transformed log_prob needs Jacobian and latent/physical cache contract.',
            'ClippedmeanGaussian retains deterministic clipped targets but changes stochastic means; clamp derivative zero for outofrange mean,may freeze mean learning.',
            'BoundedmeanGaussian transforms neural mean only; samples remain Gaussian in sameaction coordinates,no Jacobian in sampledaction log_prob,and remaining hardclip remains explicit.',
            'Bounded output does not prove PD torque unsaturated or recovery possible.',
            'Allchannel tanh changes old leg targets and cannot be called strictbehaviorpreserving warmstart.']}
    publish(output,{'audit.json':result},inputs);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=audit(a.run,a.output_dir)
    print(json.dumps(r['candidates'],indent=2))
