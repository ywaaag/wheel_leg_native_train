"""CPU phase-matched reward/advantage associations and frozen-return sensitivity."""
import argparse,json
from pathlib import Path
import numpy as np
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def gae_bonus(bonus,done,gamma,lam):
    result=np.zeros_like(bonus,dtype=np.float64)
    for r in range(bonus.shape[0]):
        tail=np.zeros(bonus.shape[2])
        for t in reversed(range(bonus.shape[1])):
            tail=bonus[r,t]+gamma*lam*(~done[r,t])*tail;result[r,t]=tail
    return result


def matching(x,y,tick):
    centered_x=[];centered_y=[];buckets=[]
    for t in np.unique(tick):
        ids=tick==t;a=x[ids];b=y[ids]
        if len(a)<2:continue
        centered_x.extend(a-a.mean());centered_y.extend(b-b.mean())
        hi=a>a.mean();lo=~hi
        buckets.append({'clock_step':int(t),'n':len(a),'progress_std':float(a.std()),
            'raw_advantage_mean':float(b.mean()),'above_mean_progress_advantage_delta':float(b[hi].mean()-b[lo].mean()) if hi.any() and lo.any() else None})
    a=np.asarray(centered_x);b=np.asarray(centered_y)
    corr=float(np.corrcoef(a,b)[0,1]) if len(a)>1 and a.std()>1e-10 and b.std()>1e-10 else None
    return {'matched_samples':len(a),'within_clock_correlation':corr,'buckets':buckets,
        'meaning':'same observed postcontrol clock,across env/episodes; association only,not action-matched causal pair'}


def audit(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text());inputs=dict([checked_input(sp)])
    ep=run/'evaluation_00.json';d=json.loads(ep.read_text());inputs.update([checked_input(ep)])
    if d['checkpoint_sha256']!=s['source_sha256'] or not d['frozen_state_unchanged']:raise ValueError('Identity/state conflict')
    raw=run/d['capture']['path'];inputs.update([checked_input(raw,d['capture']['sha256'])])
    with np.load(raw) as z:a={k:z[k] for k in z.files}
    metadata=a['pre_metadata'];mask=(metadata[...,0]==d['capture']['family_names'].index('swing_candidate_from_historical_r1'))&metadata[...,2].astype(bool)
    record=a['record_transition'];bonus=a['weighted_reward'][...,d['capture']['reward_names'].index('support_record_progress')]
    advantage=a['advantage_raw'][...,0];done=a['done'].astype(bool);clock=np.rint(a['post_state'][...,0]*100).astype(int)
    g=a['post_geometry'];anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m']);length=np.linalg.norm(g[...,:6].reshape(*g.shape[:-1],2,3)-anchors,axis=-1)
    # Adjacent sameenv samples only within sameepisode; use postgeometry at previous step.
    previous=np.concatenate([length[0],length[1]],axis=0);episodes=metadata[...,1].reshape(256,64)
    delta=np.zeros_like(previous);delta[1:]=previous[:-1]-previous[1:];valid=np.zeros((256,64),bool);valid[1:]=episodes[1:]==episodes[:-1]
    contraction=delta.mean(-1).reshape(2,128,64);continuity=valid.reshape(2,128,64)&mask
    matched={'record_progress':matching(bonus[mask],advantage[mask],clock[mask]),
        'bilateral_mean_contraction':matching(contraction[continuity],advantage[continuity],clock[continuity])}
    contribution=gae_bonus(bonus,done,s['ppo']['gamma'],s['ppo']['lam']);base=advantage-contribution
    sensitivity=[]
    for beta in [0.,.3,1.,3.,10.]:
        cf=base+contribution*(beta/.3);normalized=np.empty_like(cf)
        for r in range(2):normalized[r]=(cf[r]-cf[r].mean())/(cf[r].std(ddof=1)+1e-8)
        positive=mask&(bonus>0)
        sensitivity.append({'beta':beta,'maximum_episode_bonus_from_Q0235':beta*(1-.235),
            'positive_bonus_raw_advantage_mean':float(cf[positive].mean()),
            'positive_bonus_normalized_positive_fraction':float((normalized[positive]>0).mean()),
            'Swing_raw_sign_changed_vs_actual':int(((cf>0)!=(advantage>0))[mask].sum()),
            'notes':'fixed actual trajectory/value/termination; no actor/critic training or physical reachability claim'})
    result={'inputs_sha256':inputs,'matching':matched,'sensitivity':sensitivity,
        'eligible_samples':int(mask.sum()),'review_optimizer_steps':0,'simulation':0,
        'limits':['time matching removes timing mean only; action,state,env and repeatedepisode correlations remain',
            'negative advantage on positivebonus cannot prove bad reward; eventualtilt failure remains',
            'large beta changes task objective and failure-path incentive,not justified by making advantage positive',
            'two frozen batches cannot decide convergence or fully diagnose hiddenrecord critic state']}
    publish(output,{'audit.json':result},inputs);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=audit(a.run,a.output_dir)
    print(json.dumps({'withinclock':{k:v['within_clock_correlation'] for k,v in r['matching'].items()},'sensitivity':r['sensitivity']},indent=2))
