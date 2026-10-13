"""Fixedstate CPU mixture coverage/oldtarget shift; no randomsamples or runtime."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.special import ndtr
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from audit_recovery_leg_exploration import coverage


def audit(run,output):
    run=Path(run).resolve();p=run/'source_snapshot/spec.json';s=json.loads(p.read_text());inputs=dict([checked_input(p)])
    p=run/'evaluation_00.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
    if d['checkpoint_sha256']!=s['source_sha256'] or not d['frozen_state_unchanged']:raise ValueError('Source identity conflict')
    p=run/d['capture']['path'];inputs.update([checked_input(p,d['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    leg=[0,1,3,4];q=a['pre_joint_pos'][...,np.asarray(d['capture']['active_indices'])[leg]];reference=q-a['pre_obs150'][...,9:13]/2
    mu=a['mean'][...,leg];std=a['std'][...,leg];center=(q-reference)/1.6;md=a['pre_metadata'];clock=np.rint(a['post_state'][...,0]*100).astype(int)
    mask=(md[...,0]==d['capture']['family_names'].index('swing_candidate_from_historical_r1'))&md[...,2].astype(bool)&(clock<=4)
    base=coverage(mu[mask],std[mask],q[mask],reference[mask]);rows=[];shifts=[]
    for sigma_m in [.025,.05,.1]:
        local=coverage(center[mask],np.ones_like(center[mask])*sigma_m/1.6,q[mask],reference[mask])
        for weight in [.01,.05,.1]:
            rows.append({'local_target_std_rad':sigma_m,'weight':weight,
                'joint_direction_probability':(1-weight)*base['joint_sign_probability_mean']+weight*local['joint_sign_probability_mean'],
                'local_box_probability':(1-weight)*base['local_box_probability_mean']+weight*local['local_box_probability_mean'],
                'local_component_clip_probability':local['leg_rawclip_probability_mean']})
    for code,f in enumerate(d['capture']['family_names']):
        m=(md[...,0]==code)&md[...,2].astype(bool)
        base_target=reference[m]+1.6*np.clip(mu[m],-1,1);local_target=q[m]
        delta=local_target-base_target
        shifts.append({'family':f,'local_component_target_shift_abs_mean_rad':abs(delta).mean(0).tolist(),
            'local_component_target_shift_abs_peak_rad':abs(delta).max(0).tolist(),
            'weighted_mean_shift_abs_mean_rad_at005':(.05*abs(delta)).mean(0).tolist(),
            'one_or_more_local_selection_probability_100steps_weight005':1-.95**100})
    r={'inputs_sha256':inputs,'coverage':rows,'retention_cost':shifts,'runtime_wired':False,'simulation':0,'optimizer_steps':0,
        'semantics':{'component_selection':'one per transition sharedfourlegs','center':'current_qencodedin150D,no family or signbias',
            'likelihood':'joint4D logsumexp,not product of4independent mixtures','wheels':'same baseGaussian in bothcomponents',
            'deterministic':'must explicitly choose basecomponent or mixturemean,not silently share legacyoutput',
            'entropy_KL':'no ordinaryGaussian closedform; needs new publicinterface/accurate approximation'},
        'limits':['single step localbox not fulltemporal coordinatedrecovery path','local_component qnearhold shifts oldpolicy actions,newstate unknown',
                  'constantweight small still frequently affects10secondhold','fixedlocalcomponent has no trainable targetcenter; local action advantage does not directly teach base mean when separated']}
    publish(output,{'audit.json':r},inputs);print(json.dumps(r,indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.run,a.output_dir)
