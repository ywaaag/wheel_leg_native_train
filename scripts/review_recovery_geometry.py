"""Offline event/window and single-variable reward audit of frozen full traces."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from native_stand.recovery.rising import score_rise
from native_stand.recovery.standing import longitudinal_geometry


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(run, output):
    if output.exists(): raise FileExistsError(output)
    paths=[run/'source_snapshot/spec.json',run/'source_snapshot/recovery_rising.py',
           run/'source_snapshot/recovery_standing.py',run/'evaluation_00.json',run/'terminal_report.json']
    inputs={str(p):sha(p) for p in paths}
    spec=json.loads(paths[0].read_text());data=json.loads(paths[3].read_text())
    dt=spec['control']['policy_dt_s'];protocol=data['effective_protocol'];rows=[]
    for e in data['per_env']:
        s=np.asarray(e['compact_trace_100hz']);p=np.asarray(e['posture_trace_100hz']);g=np.asarray(e['wheel_geometry_trace_100hz'])
        if s.shape!=(2300,39) or p.shape!=(2300,10) or g.shape!=(2300,13):raise ValueError('Incomplete aligned23s trace')
        if not all(np.isfinite(x).all() for x in (s,p,g)):raise ValueError('Nonfinite trace')
        offsets=longitudinal_geometry(torch.tensor(g[:,:6].reshape(-1,2,3)),torch.tensor(g[:,6:9])).abs().numpy()
        eligible=((s[:,6]>=.34)&(s[:,6]<=.38)&(s[:,15]<=.18)&(np.abs(p[:,:2])<=.1).all(1)&(s[:,10:12]>2).all(1)&s[:,29].astype(bool))
        start=int(np.flatnonzero(eligible)[0]);finish=start+round(10/dt)
        if e['post_rise_window_s']!=[start*dt,finish*dt]:raise ValueError('Saved index window differs')
        if abs(e['recovery_s']-s[start,0])>1e-6:raise ValueError('Saved recovery clock differs')
        replay=score_rise(torch.tensor(s),torch.tensor(p),dt=dt,
            protocol={**protocol,'initial_xy':s[0,19:21].tolist()},runtime_fault=e['runtime_fault'],
            initial_valid=e['initial_valid'],terminated=e['episode_result']['terminated'])
        if replay['failed_checks']!=e['standing_failed_checks']:raise ValueError('Scorer/gate differs')
        for key in ('height_in_range_fraction','dual_contact_fraction','height_steady_mean_m'):
            if abs(replay['metrics'][key]-e['post_rise_metrics'][key])>1e-6:raise ValueError('Score metric differs: '+key)
        def event(i):
            from native_stand.command_v6.domain.time_axis import event as aligned_event
            return None if i is None else {**aligned_event(int(i),dt=dt,recovery_seconds=float(s[i,0])),
                'offset_m':float(offsets[i]),'height_m':float(s[i,6])}
        def first(mask,lo=start):
            indices=np.flatnonzero(mask[lo:finish]);return int(indices[0]+lo) if len(indices) else None
        contact=(s[:,10:12]>2).all(1);loss=first(~contact)
        thresholds={str(v):event(first(offsets>=v)) for v in (.1,.2,.4,.5)}
        # A sustained threshold is100ms of recorded samples, not a causal certificate.
        sustained={}
        for v in (.2,.4):
            hit=np.convolve((offsets[start:finish]>=v).astype(int),np.ones(10,dtype=int),'valid')==10
            ix=np.flatnonzero(hit);sustained[str(v)]=event(int(start+ix[0]) if len(ix) else None)
        gate=np.clip((s[:,6]-.32)/.04,0,1)
        cost=-.1*gate*(np.maximum(offsets-.04,0)/.2)**2
        controlled=(s[:,29]>0)&(s[:,32]!=7)
        h=s[:,6];w=spec['reward'];levelgate=np.clip((h-.3)/.06,0,1)
        lift=w['lift']*np.clip((h-s[0,6])/max(.36-s[0,6],.05),-1,1)
        height=3*np.exp(-((h-.36)/.04)**2)
        pitch=w['pitch_level']*levelgate*(p[:,0]/.12)**2
        phases=[]
        for label,mask in [('below_gate',controlled&(h<.32)),('gate_ramp',controlled&(h>=.32)&(h<.36)),('full_gate',controlled&(h>=.36)),('hold',np.arange(len(s))>=start)]:
            if label=='hold':mask &= np.arange(len(s))<finish
            if not mask.any():continue
            phases.append({'name':label,'samples':int(mask.sum()),'cost_mean_per_s':float(cost[mask].mean()),
                'cost_peak_abs_per_s':float(np.abs(cost[mask]).max()),'cost_integral':float(cost[mask].sum()*dt),
                'lift_mean_per_s':float(lift[mask].mean()),'height_mean_per_s':float(height[mask].mean()),
                'pitch_mean_per_s':float(pitch[mask].mean())})
        rows.append({'env_id':e['env_id'],'entry':event(start),'window_index_half_open':[start,finish],
            'window_scored_samples':finish-start,'window_recovery_clock_s':[float(s[start,0]),float(s[finish-1,0])],
            'first_loss':event(loss),'first_height_exit':event(first((h<.34)|(h>.38))),
            'offset_threshold_first':thresholds,'offset_threshold_100ms':sustained,
            'mean_hold_offset_m':float(offsets[start:finish].mean()),'peak_hold_offset_m':float(offsets[start:finish].max()),
            'mean_hold_leg_difference_m':float(np.abs(p[start:finish,2]-p[start:finish,3]).mean()),
            'scorer_replay_matches':True,'failed_checks':e['standing_failed_checks'],'reward_scale_replay':phases})
    for path,digest in inputs.items():
        if sha(Path(path))!=digest:raise ValueError('Input changed')
    result={'inputs_sha256':inputs,'per_env':rows,'proposed_cost':{'weight':-.1,'deadband_m':.04,'scale_m':.2,'height_start_m':.32,'height_full_m':.36},
        'clock_semantics':'window bounds=start_index*dt, slices[start:start+1000]; recovery_s=series[start,0], excluding passive initialization. Do not compare these clocks directly.',
        'scope':'100Hz pre-reset main-wheel center horizontal projection, not contact patches or every-PD evidence; offline reward formula, not PPO gradients',
        'simulation':0,'PPO':0,'causality':'UNKNOWN; temporal precedence alone is not intervention evidence'}
    output.mkdir(parents=True)
    (output/'review.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(output),'per_env':[{'env':r['env_id'],'entry':r['entry'],'first_loss':r['first_loss'],'first_20cm_100ms':r['offset_threshold_100ms']['0.2'],'phases':r['reward_scale_replay']} for r in rows]},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();review(args.run.resolve(),args.output_dir.resolve())
