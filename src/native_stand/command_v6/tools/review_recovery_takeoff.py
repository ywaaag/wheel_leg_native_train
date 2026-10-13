"""Offline first-episode takeoff/landing alignment; no simulator or optimizer."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from native_stand.command_v6.domain.time_axis import event,sustained_events
from native_stand.command_v6.domain.trace_schema import WIDTHS,VERSION,validate_rows,STATE,POSTURE,CONTROL,PHASE_CODES
from native_stand.command_v6.tools.evaluation_loader import load
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.recovery.standing import longitudinal_geometry


def review(run,output,updates=None):
    run=Path(run).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    spec_path=run/'source_snapshot/spec.json';spec=json.loads(spec_path.read_text());inputs=dict([checked_input(spec_path),checked_input(run/'manifest.json')])
    registry=json.loads((run/'candidate_registry.json').read_text());inputs.update([checked_input(run/'candidate_registry.json')])
    if updates is None:
        updates=sorted({e['update'] for e in registry if e.get('role')!='source'})
    from native_stand.command_v6.domain.recovery_events import analyze
    dt=spec["control"]["policy_dt_s"];hold_samples=round(spec["recovery"]["rising_task"]["post_rise_hold_s"]/dt)
    wheel_scale=spec["action"]["wheel_scale_rad_s"]
    cases=[];plot_data=[]
    for update in updates:
        checkpoint=run/f'model_update_{update}.pt';model_sha=checked_input(checkpoint)[1];inputs.update([checked_input(checkpoint)])
        entry=next(e for e in registry if e['update']==update and e['checkpoint_sha256']==model_sha)
        data,evidence=load(run,entry,spec_sha256=inputs[str(spec_path)],checkpoint_sha256=model_sha,
            asset_sha256=spec['asset_sha256'],required_fields=('compact_trace_100hz','posture_trace_100hz','wheel_geometry_trace_100hz','control_diagnostics_100hz'))
        inputs[evidence['path']]=evidence['sha256'];groups=[]
        for group in (data,*data.get('retained_evaluations',[])):
            rows=[]
            for e in group['per_env']:
                events=analyze(e,dt=dt,hold_s=hold_samples*dt,wheel_scale=wheel_scale)
                if events.get('task_window_category')!='COMPLETE_HOLD_WINDOW' or e.get('wheel_geometry_trace_100hz') is None:
                    rows.append({'env_id':e['env_id'],'event_analysis':events,'geometry_analysis':'MISSING_FULL_HOLD_OR_GEOMETRY'});continue
                s=np.asarray(e['compact_trace_100hz']);p=np.asarray(e['posture_trace_100hz']);g=np.asarray(e['wheel_geometry_trace_100hz']);c=np.asarray(e['control_diagnostics_100hz']);n=len(s)
                if s.shape!=(n,WIDTHS['state']) or p.shape!=(n,WIDTHS['posture']) or g.shape!=(n,WIDTHS['geometry']) or c.shape!=(n,WIDTHS['control']) or not all(np.isfinite(x).all() for x in (s,p,g,c)):raise ValueError('Incomplete/nonfinite aligned traces')
                if len(np.unique(s[:,STATE['episode_id']]))!=1:raise ValueError('Episode stitched')
                t=s[:,STATE['recovery_clock_s']];active=(t>0)&(s[:,STATE['previous_mode']]!=PHASE_CODES['initializing'])&s[:,STATE['initial_valid']].astype(bool);entry_index=e['entry_confirmation_index'];hold_start=entry_index+1;hold_stop=hold_start+hold_samples
                if hold_stop>n:raise ValueError('Missing full hold')
                offset=longitudinal_geometry(torch.as_tensor(g[:,:6].reshape(-1,2,3)),torch.as_tensor(g[:,6:9])).numpy()
                centers=g[:,:6].reshape(-1,2,3);up=-g[:,6:9]/np.maximum(np.linalg.norm(g[:,6:9],axis=1,keepdims=True),1e-12)
                vertical=(centers*up[:,None,:]).sum(-1);vz=np.full(n,np.nan);vz[1:]=np.diff(s[:,STATE['height_m']])/dt
                both_low=(s[:,[STATE['left_contact_n'],STATE['right_contact_n']]]<=2).all(1);left_low=s[:,STATE['left_contact_n']]<=2;right_low=s[:,STATE['right_contact_n']]<=2
                def first(mask):
                    ids=np.flatnonzero(mask&active);return int(ids[0]) if len(ids) else None
                def at(i):
                    if i is None:return None
                    return {**event(i,dt=dt,recovery_seconds=float(t[i])), 'height_m':float(s[i,STATE['height_m']]),'roll_rad':float(p[i,POSTURE['roll_rad']]),
                        'offset_signed_m':float(offset[i]),'wheel_height_difference_m':float(vertical[i,0]-vertical[i,1]),
                        'wheel_force_n':s[i,[STATE['left_contact_n'],STATE['right_contact_n']]].tolist(),'leg_q_rad':c[i,[0,1,3,4]].tolist(),
                        'leg_target_rad':c[i,CONTROL['leg_target_after_limit']].tolist(),'wheel_target_rad_s':(c[i,[20,23]]*wheel_scale).tolist(),
                        'wheel_actual_rad_s':c[i,[8,11]].tolist(),'leg_applied_nm':c[i,[44,45,47,48]].tolist(),
                        'wheel_requested_nm':c[i,[34,37]].tolist(),'wheel_clipped_nm':c[i,[40,43]].tolist(),
                        'wheel_applied_nm':c[i,[46,49]].tolist()}
                early=active&(t<=2);peak=int(np.argmax(np.where(early,s[:,STATE['height_m']],-np.inf)))
                lift=first(s[:,STATE['height_m']]>=.30)
                # Find both-low episodes after the .30m crossing, excluding unraised initialization.
                air_mask=both_low&active&(np.arange(n)>=(lift if lift is not None else n))&(np.arange(n)<=entry_index)
                air_events=sustained_events(air_mask.tolist(),dt=dt);landings=[]
                for a in air_events:
                    start,stop=a['index_half_open'];end=entry_index+1
                    l=np.flatnonzero(s[stop:end,STATE['left_contact_n']]>2);rr=np.flatnonzero(s[stop:end,STATE['right_contact_n']]>2)
                    li=int(stop+l[0]) if len(l) else None;ri=int(stop+rr[0]) if len(rr) else None
                    landings.append({'both_low_start':at(start),'both_low_last':at(stop-1),'duration_s':a['duration_s'],
                        'left_force_reappearance':at(li),'right_force_reappearance':at(ri),
                        'landing_order':('simultaneous_at100Hz' if li==ri else 'left_first' if li is not None and (ri is None or li<ri) else 'right_first'),
                        'left_minus_right_landing_s':(li-ri)*dt if li is not None and ri is not None else None})
                def phase(a,b):
                    x=c[a:b];state=s[a:b];post=p[a:b];delta=x[:,[20,23]]*wheel_scale
                    return {'samples':b-a,'contact_fraction':float((state[:,[STATE['left_contact_n'],STATE['right_contact_n']]]>2).all(1).mean()),
                        'height_min_m':float(state[:,STATE['height_m']].min()),'height_max_m':float(state[:,STATE['height_m']].max()),
                        'roll_peak_rad':float(np.abs(post[:,POSTURE['roll_rad']]).max()),'offset_abs_mean_m':float(np.abs(offset[a:b]).mean()),
                        'wheel_vertical_difference_peak_m':float(np.abs(vertical[a:b,0]-vertical[a:b,1]).max()),
                        'mean_wheel_target_common_rad_s':float(delta.mean(1).mean()),
                        'mean_abs_wheel_target_differential_rad_s':float(np.abs((delta[:,0]-delta[:,1])/2).mean()),
                        'mean_abs_wheel_actual_differential_rad_s':float(np.abs((x[:,8]-x[:,11])/2).mean()),
                        'leg_applied_rms_nm':np.sqrt((x[:,[44,45,47,48]]**2).mean(0)).tolist()}
                loss_mask=(left_low|right_low)&(np.arange(n)>=hold_start)&(np.arange(n)<hold_stop)
                losses=[{'start':at(x['index_half_open'][0]),'end':at(x['index_half_open'][1]-1),'duration_s':x['duration_s'],
                    'left_low_samples':int(left_low[slice(*x['index_half_open'])].sum()),'right_low_samples':int(right_low[slice(*x['index_half_open'])].sum())}
                    for x in sustained_events(loss_mask.tolist(),dt=dt)]
                earliest=next((x['both_low_start']['trace_index'] for x in landings),None)
                threshold_events={name:at(first(mask)) for name,mask in [('offset_abs_4cm',np.abs(offset)>=.04),('roll_abs_0p03',np.abs(p[:,POSTURE['roll_rad']])>=.03),('wheel_vertical_diff_5mm',np.abs(vertical[:,0]-vertical[:,1])>=.005)]}
                rows.append({'event_analysis':events,'env_id':e['env_id'],'pose_id':e['pose_id'],'episode_id':e['episode_id'],'first_height_0p30':at(lift),'height_peak_first2':at(peak),'entry_confirmation':at(entry_index),'takeoff_force_events':landings,
                    'early_asymmetry_threshold_events':threshold_events,'hold_contact_loss_events':losses,
                    'pre_entry':phase(int(np.flatnonzero(active)[0]),entry_index+1),'hold':phase(hold_start,hold_stop),
                    'first2s_peak_vz_finite_difference_mps':float(np.nanmax(vz[early]))})
                if e['env_id']==0 and group['evaluation_family']=='drawback_manual0001':plot_data.append((update,t,s,p,offset,c))
            groups.append({'family':group['evaluation_family'],'rows':rows})
        cases.append({'update':update,'checkpoint':str(checkpoint),'checkpoint_sha256':model_sha,'groups':groups})
    report={'trace_schema_version':VERSION,'policy_dt_s':dt,'hold_samples':hold_samples,'scope':'Offline measured100Hz first episodes; contact resultants <=2N do not independently certify flight; held applied torque not each PD/physics step',
        'inputs_sha256':inputs,'models':cases,'geometry_definition':'root-frame wheel centers projected onto horizontal native forward -root Z using measured gravity; vertical onto -gravity,NOT gravity-as-forward',
        'actor_mean_history':'UNKNOWN: complete150D actor inputs and pre-action history not saved; control raw_action is executed action,not full actor replay',
        'interpretation':'Temporal thresholds are diagnostic choices,not acceptance changes or causal proof','simulation':0,'PPO':0}
    publish(output,{'review.json':report},inputs)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(5,max(1,len(plot_data)),figsize=(max(7,6*len(plot_data)),12),sharex=True,squeeze=False)
    for j,(u,t,s,p,offset,c) in enumerate(plot_data):
        axes[0,j].plot(t,s[:,STATE['height_m']]);axes[0,j].set_title(f'update{u}, env0, full recorded first episode')
        axes[1,j].plot(t,s[:,STATE['left_contact_n']],label='left');axes[1,j].plot(t,s[:,STATE['right_contact_n']],label='right');axes[1,j].axhline(2,color='gray',ls='--');axes[1,j].legend()
        axes[2,j].plot(t,p[:,POSTURE['roll_rad']]);axes[3,j].plot(t,offset)
        axes[4,j].plot(t,c[:,20]*wheel_scale,label='left target');axes[4,j].plot(t,c[:,23]*wheel_scale,label='right target');axes[4,j].legend();axes[4,j].set_xlabel('Measured recovery clock (s)')
    for i,label in enumerate(('Root height (m)','Contact resultant (N)','Roll (rad)','Signed fore-aft offset (m)','Wheel target (rad/s)')):
        for a in axes[i]:a.set_ylabel(label);a.grid(alpha=.2)
    fig.tight_layout();fig.savefig(output/'comparison.png',dpi=140);plt.close(fig)
    print(json.dumps({'output':str(output),'models':[{ 'update':x['update'],'env0':x['groups'][0]['rows'][0].get('height_peak_first2')} for x in cases]},indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--update',type=int,action='append',help='explicit registry updates; default all saved non-source entries');a=p.parse_args();review(a.run,a.output_dir,a.update)

if __name__=='__main__':main()
