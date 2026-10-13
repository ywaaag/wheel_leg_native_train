"""Offline frozen Level2 transition audit; no simulator, PPO, or historical writes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(run, output):
    if output.exists():raise FileExistsError(output)
    spec_path=run/'source_snapshot/spec.json'
    spec=json.loads(spec_path.read_text())
    # This replay is deliberately limited to the reviewed frozen recipe.
    if (spec['control']['policy_dt_s']!=.01 or
            spec['control']['height_command_m']!=.36 or
            spec['recovery']['curriculum'].get('automatic_upgrade') or
            spec['recovery']['standing_task']['reward']['weights']['standing_height']!=3. or
            spec['reward']['pitch_level_gate_mode']!='height' or
            spec['reward']['roll_level_gate_mode']!='height'):
        raise ValueError('audit replay does not support this recipe; no approximate report emitted')
    paths=[run/'source_eval/evaluation_source.json',
           *sorted((run/'formal').glob('evaluation_*.json'))]
    inputs={str(spec_path):sha(spec_path)};cases=[]
    for path in paths:
        inputs[str(path)]=sha(path)
        evaluation=json.loads(path.read_text());rows=[]
        for episode in evaluation['per_env']:
            s=np.asarray(episode.get('compact_trace_100hz',[]),dtype=float)
            p=np.asarray(episode.get('posture_trace_100hz',[]),dtype=float)
            if s.ndim!=2 or p.shape!=(len(s),10):
                rows.append({'env_id':episode['env_id'],'phases':[],
                    'evidence_status':'UNKNOWN: full aligned traces not recorded; failure tail is not full transition'})
                continue
            control=np.asarray(episode.get('control_diagnostics_100hz') or [],dtype=float)
            active=(s[:,29]>0)&(s[:,32]!=7)
            h=s[:,6];gate=np.clip((h-.3)/.06,0,1)
            # Formula replay of recorded inputs, NOT reward gradients or full returns.
            w=spec['reward'];target=spec['control']['height_command_m']
            accepted=np.flatnonzero(s[:,29]>0)
            initial_height=float(h[accepted[0]]) if len(accepted) else None
            if initial_height is None:raise ValueError('initialization reference missing')
            progress=np.clip((h-initial_height)/max(target-initial_height,.05),-1,1)
            terms={'lift':w['lift']*progress,'upright':w['upright']*np.clip(np.cos(s[:,15]),0,1),
                'standing_height':3*np.exp(-((h-target)/.04)**2),
                'height_overshoot':w['height_overshoot']*(np.maximum(h-target,0)/.04)**2,
                'pitch_level':w['pitch_level']*gate*(p[:,0]/.12)**2,
                'roll_level':w['roll_level']*gate*(p[:,1]/.12)**2,
                'vertical_motion':-.1*gate*(p[:,7]/.1)**2,
                'support':.5*(s[:,10:12]>2).all(axis=1)}
            item={'env_id':episode['env_id'],'initial_valid':episode['initial_valid'],
                'terminated':episode['episode_result']['terminated'],
                'runtime_fault':episode['runtime_fault'],'standing_entry_s':episode.get('recovery_s'),
                'post_rise_observed_s':episode.get('post_rise_observed_s'),
                'phases':[],'control_diagnostics_available':len(control)==len(s)}
            for label,mask in [('lift_below_034',active&(h<.34)),
                               ('height_band_034_038',active&(h>=.34)&(h<=.38)),
                               ('overshoot_above_038',active&(h>.38))]:
                n=int(mask.sum())
                row={'phase':label,'samples':n,'duration_s':n*.01}
                if n:
                    row.update(height_mean_m=float(h[mask].mean()),height_peak_m=float(h[mask].max()),
                        abs_pitch_mean_rad=float(np.abs(p[mask,0]).mean()),
                        dual_contact_fraction=float((s[mask,10:12]>2).all(axis=1).mean()),
                        saturation_any_channel_fraction=float(s[mask,17].mean()),
                        vertical_velocity_mean_mps=float(p[mask,7].mean()),
                        reward_replay_per_second={k:float(v[mask].mean()) for k,v in terms.items()},
                        reward_replay_integral={k:float(v[mask].sum()*.01) for k,v in terms.items()})
                    if len(control)==len(s):
                        row['per_channel_saturation_fraction']=(np.abs(control[mask,38:44])>=
                            np.array([40,40,5.5,40,40,5.5])-1e-4).mean(axis=0).tolist()
                item['phases'].append(row)
            rows.append(item)
        cases.append({'path':str(path),'accepted':evaluation['accepted'],'per_env':rows,
            'retained_results':[{k:x.get(k) for k in ['evaluation_family','accepted','passed_envs']}
                                for x in evaluation.get('retained_evaluations',[])]})
    payload={'inputs_sha256':inputs,'cases':cases,
        'scope':'Recorded first-episode 100Hz traces on frozen Level2 USD; phase samples may be noncontiguous.',
        'reward_replay_scope':'Selected continuous terms only; lift reference from first initialized pre-reset sample (no reverse curriculum). Per-second and dt-integral. No optimizer/GAE replay.',
        'unknown':['candidate per-channel torque/limit hits when control trace absent',
                   'passive knee angle history not stored in 6-channel control trace',
                   'causal reward gradients and complete return decomposition'],
        'simulation':0,'PPO_updates':0}
    for path,digest in inputs.items():
        if sha(Path(path))!=digest:raise ValueError('input changed during audit')
    output.mkdir(parents=True)
    with (output/'review.json').open('x') as f:json.dump(payload,f,indent=2,allow_nan=False)
    summary=['# Level2 recorded transition audit','Offline only; inputs and limitations in review.json.']
    for c in cases:
        summary.append('\n'+c['path'])
        for label in ['lift_below_034','height_band_034_038','overshoot_above_038']:
            rows=[p for e in c['per_env'] for p in e['phases'] if p['phase']==label]
            nonempty=[x for x in rows if x['samples']]
            if nonempty:
                mean=lambda k:sum(x[k] for x in nonempty)/len(nonempty)
                summary.append(f"{label}: mean duration={mean('duration_s'):.3f}s, pitch={mean('abs_pitch_mean_rad'):.3f}rad, any-channel saturation={mean('saturation_any_channel_fraction'):.3f}")
    with (output/'review.md').open('x') as f:f.write('\n'.join(summary)+'\n')
    print('\n'.join(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();review(args.run.resolve(),args.output_dir.resolve())
