"""CPU exact Gaussian tail/localbox coverage and reference migration costs."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.special import ndtr,log_ndtr
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def coverage(mu,std,q,reference):
    mu,std,q,reference=[np.asarray(x,dtype=np.float64) for x in (mu,std,q,reference)]
    sign=np.array([1,1,-1,1]);threshold=(q-reference)/1.6
    # Source limits contain the ±.025-.15rad localtarget box and normalized bounds.
    z=sign*(threshold-mu)/std
    logp=log_ndtr(-z).sum(-1)
    low=np.minimum(q+sign*.025,q+sign*.15);high=np.maximum(q+sign*.025,q+sign*.15)
    a=(low-reference)/1.6;b=(high-reference)/1.6
    valid=((a>-1)&(b<1)).all(-1)
    za=(a-mu)/std;zb=(b-mu)/std
    # Positive tails use survival differences to avoid cancellation near CDF=1.
    marginal=np.where(za>0,ndtr(-za)-ndtr(-zb),ndtr(zb)-ndtr(za))
    prob=np.maximum(marginal,0).prod(-1)*valid
    return {'joint_sign_probability_mean':float(np.exp(logp).mean()),'joint_sign_log10_probability_mean':float(logp.mean()/np.log(10)),
        'local_box_probability_mean':float(prob.mean()),'local_box_prob_max':float(prob.max()),
        'per_channel_boundary_distance_std_mean':z.mean(0).tolist(),
        'leg_rawclip_probability_mean':(ndtr((-1-mu)/std)+ndtr((mu-1)/std)).mean(0).tolist()}


def audit(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text());inputs=dict([checked_input(sp)])
    ep=run/'evaluation_00.json';d=json.loads(ep.read_text());inputs.update([checked_input(ep)])
    if not d['frozen_state_unchanged'] or d['checkpoint_sha256']!=s['source_sha256']:raise ValueError('Identity differs')
    p=run/d['capture']['path'];inputs.update([checked_input(p,d['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    leg=[0,1,3,4];q=a['pre_joint_pos'][...,np.asarray(d['capture']['active_indices'])[leg]]
    reference=q-a['pre_obs150'][...,9:13]/2;mu=a['mean'][...,leg];std=a['std'][...,leg]
    md=a['pre_metadata'];clock=np.rint(a['post_state'][...,0]*100).astype(int);mask=(md[...,0]==d['capture']['family_names'].index('swing_candidate_from_historical_r1'))&md[...,2].astype(bool)&(clock<=4)
    rows=[]
    for scale in [1,2,4,8]:rows.append({'candidate':'std_multiplier','scale':scale,**coverage(mu[mask],std[mask]*scale,q[mask],reference[mask])})
    rows.append({'candidate':'all_leg_mean_tanh','scale':1,**coverage(np.tanh(mu[mask]),std[mask],q[mask],reference[mask])})
    # Coordinate redesign candidate: joint-current residual,global,without family mask.
    rows.append({'candidate':'current_q_residual_reference','scale':1,**coverage(mu[mask],std[mask],q[mask],q[mask])})
    changes=[]
    for code,family in enumerate(d['capture']['family_names']):
        m=(md[...,0]==code)&md[...,2].astype(bool)
        original=reference[m]+1.6*np.clip(mu[m],-1,1)
        for kind,target in [('leg_mean_tanh',reference[m]+1.6*np.tanh(mu[m])),('current_q_residual',q[m]+1.6*np.clip(mu[m],-1,1))]:
            delta=target-original;changes.append({'family':family,'candidate':kind,'target_shift_abs_mean_rad':abs(delta).mean(0).tolist(),'target_shift_abs_peak_rad':abs(delta).max(0).tolist()})
    r={'inputs_sha256':inputs,'early_samples':int(mask.sum()),'coverage':rows,'oldstate_target_shift':changes,'simulation':0,'optimizer_steps':0,
       'limits':['Fourdirection/localbox is one sufficient localgeometrycandidate,not all recoverableactions',
       'Assume independent Gaussian sameprestate; futurestate/forces/learning unknown',
       'Currentqresidual changes target reference/action interpretation and optimizer/oldpolicy behavior,not approvedruntime',
       'std multipliers affect all tasks and torque; no acceptablecoefficient implied by tailprobability']}
    publish(output,{'audit.json':r},inputs);print(json.dumps(r,indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.run,a.output_dir)
