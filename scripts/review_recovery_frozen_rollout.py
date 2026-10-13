"""Offline actual random-action/reward/value/GAE review; no simulator or optimizer."""
import argparse,json
from pathlib import Path
import numpy as np
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def describe(a):
    a=np.asarray(a)
    return {'n':a.size,'mean':float(a.mean()),'std':float(a.std()),'min':float(a.min()),'max':float(a.max())} if a.size else {'n':0,'mean':None}


def review(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';inputs=dict([checked_input(sp)])
    spec=json.loads(sp.read_text());p=run/'terminal_report.json';inputs.update([checked_input(p)]);terminal=json.loads(p.read_text())
    if terminal['status']!='COMPLETED':raise ValueError('Diagnostic not complete')
    p=run/terminal['completed'][0]['path'];inputs.update([checked_input(p)]);meta=json.loads(p.read_text())
    if meta['checkpoint_sha256']!=spec['source_sha256'] or not meta['frozen_state_unchanged']:raise ValueError('Frozen model identity/state not proved')
    p=run/meta['capture']['path'];inputs.update([checked_input(p,meta['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    md=a['pre_metadata'];names=meta['capture']['family_names'];idx=meta['capture']['reward_names'].index('support_record_progress')
    bonus=a['weighted_reward'][...,idx];record=a['record_transition'];eligible=record[...,5].astype(bool)
    value=a['value'][...,0];returns=a['returns'][...,0];adv=a['advantage_raw'][...,0];norm=a['advantage_normalized'][...,0]
    groups=[]
    for code,family in enumerate(names):
        mask=(md[...,0]==code)&md[...,2].astype(bool);n=mask.sum()
        samples=a['sample'][mask];clipped=a['post_control'][mask][...,18:24];means=a['mean'][mask]
        b=bonus[mask];v=value[mask];ad=adv[mask]
        groups.append({'family':family,'controlled_count':int(n),'fraction_all':float(n/md[...,0].size),
            'mean_abs_wheel':np.mean(abs(means[:,[2,5]]),axis=0).tolist() if n else None,
            'sample_wheel_clip_fraction':np.mean(abs(samples[:,[2,5]])>1,axis=0).tolist() if n else None,
            'physical_clipped_action_std':np.std(clipped,axis=0).tolist() if n else None,
            'record_bonus':describe(b),'value':describe(v),'returns':describe(returns[mask]),'advantage_raw':describe(ad),
            'advantage_normalized':describe(norm[mask]),'normalized_positive_fraction':float(np.mean(norm[mask]>0)) if n else None,
            'positive_bonus_advantage':describe(ad[b>0]),'zero_bonus_advantage':describe(ad[b==0]),
            'positive_bonus_normalized_positive_fraction':float(np.mean(norm[mask][b>0]>0)) if (b>0).any() else None,
            'episode_ids':np.unique(md[...,1][mask]).tolist()})
    original=a['reward']-bonus
    # New bonus contribution to GAE,linear before normalization and before policy/value changes.
    gamma=spec['ppo']['gamma'];lam=spec['ppo']['lam'];dones=a['done'].astype(bool);delta=np.zeros_like(bonus)
    for rollout in range(2):
        tail=np.zeros(64)
        for step in reversed(range(128)):
            tail=bonus[rollout,step]+gamma*lam*(~dones[rollout,step])*tail;delta[rollout,step]=tail
    normalized_checks=[]
    for roll in range(2):
        expected=(adv[roll]-adv[roll].mean())/(adv[roll].std(ddof=1)+1e-8)
        normalized_checks.append(float(np.max(abs(expected-norm[roll]))))
    checks={'reward_formula_max_error':float(np.max(abs(bonus-.3*np.maximum(record[...,2]-record[...,1],0)*record[...,5]*(1-record[...,6])))),
        'raw_advantage_matches_return_minus_value':float(np.max(abs(adv-(returns-value)))),
        'global_normalization_max_error':max(normalized_checks),'oldgroups_bonus_zero':bool((bonus[~eligible]==0).all()),
        'states_unchanged':meta['frozen_state_unchanged']}
    summary={'eligible_count':int(eligible.sum()),'positive_reward_count':int((bonus>0).sum()),
        'record_bonus_GAE_contribution':describe(delta[eligible]),'raw_GAE':describe(adv[eligible]),
        'bonus_counterfactual_changes_raw_sign_count':int(((adv>0)!=((adv-delta)>0))[eligible].sum()),
        'original_reward_controlled':describe(original[md[...,2].astype(bool)]),
        'phase_coverage_limited':'2.56sec total per env includes initialization; not full10sec hold coverage',
        'limitations':['bonus subtraction is fixed-trajectory/frozen-value counterfactual,not retraining or critic causal proof',
            'No optimizer/PPOgradient vectors; two batches cannot establish convergence or unique rootcause',
            'record not observed150D; value differences alone cannot diagnose critic state alias']}
    result={'inputs_sha256':inputs,'checks':checks,'groups':groups,'summary':summary,'simulation':0,'optimizer_updates':0}
    publish(output,{'review.json':result},inputs);print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();review(a.run,a.output_dir)
