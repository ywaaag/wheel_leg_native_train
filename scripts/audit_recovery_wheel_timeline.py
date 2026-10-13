"""Read-only 100Hz wheel/control and geometry chronology; exclusive output."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def starts(mask):
    return np.flatnonzero(mask & ~np.r_[False,mask[:-1]])


def audit(run,output):
    if output.exists():raise FileExistsError(output)
    records=[];inputs={}
    for update in (50,100):
        path=run/f'evaluation_{update}_0_0.json';inputs[str(path)]=digest(path)
        d=json.loads(path.read_text());envs=[]
        for e in d['per_env']:
            c=np.asarray(e['control_diagnostics_100hz'],float)
            g=np.asarray(e['gate_diagnostics_100hz'],float)
            if c.shape!=(2300,54) or g.shape!=(2300,20):raise ValueError('unexpected alignment')
            t=(np.arange(len(c))+1)*.01
            dq=c[:,[8,11]];target=c[:,[20,23]]*100
            request=c[:,[34,37]];clipped=c[:,[40,43]];applied=c[:,[46,49]]
            sat=abs(clipped)>=5.5-1e-4
            mirror=(abs(c[:,0]+c[:,3])+abs(c[:,1]-c[:,4]))/2
            row={'env_id':e['env_id'],'wheel_order':['left','right'],'windows':[]}
            for label,mask in [('all_after_1s',t>=1),('last5s',t>18)]:
                a=clipped[mask];v=dq[mask];w=target[mask]
                row['windows'].append({'label':label,'samples':int(mask.sum()),
                    'wheel_actual_speed_mean_rad_s':v.mean(0).tolist(),
                    'wheel_target_mean_rad_s':w.mean(0).tolist(),
                    'wheel_speed_error_mean_abs_rad_s':abs(w-v).mean(0).tolist(),
                    'requested_torque_mean_abs_nm':abs(request[mask]).mean(0).tolist(),
                    'clipped_torque_mean_abs_nm':abs(a).mean(0).tolist(),
                    'clipped_torque_range_nm':[a.min(0).tolist(),a.max(0).tolist()],
                    'wheel_saturation_fraction':sat[mask].mean(0).tolist(),
                    'any_wheel_saturation_fraction':float(sat[mask].any(1).mean()),
                    'torque_sign_switch_count':(np.sign(a[1:])!=np.sign(a[:-1])).sum(0).tolist(),
                    'mirror_error_mean_rad':float(mirror[mask].mean()),
                    'dual_contact_gate_fraction':float(g[mask,6].mean()),
                    'applied_minus_clipped_max_abs_nm':float(abs(applied[mask]-a).max()),
                    'held_PD_vs_endstep_speed_residual_max_nm':float(abs(request[mask]-(w-v)).max())})
            onset=starts(sat.any(1)&(t>=1))
            row['saturation_events']=[{'time_s':float(t[i]),'target_rad_s':target[i].tolist(),
                'actual_speed_rad_s':dq[i].tolist(),'request_nm':request[i].tolist(),
                'clipped_nm':clipped[i].tolist()} for i in onset[:12]]
            loss=starts((g[:,6]<.5)&(t>=1))
            row['contact_loss_events']=[{'time_s':float(t[i]),
                'mirror_before_100ms_rad':float(mirror[max(0,i-10):i].mean()) if i else None,
                'mirror_at_loss_rad':float(mirror[i]),
                'mirror_after_100ms_rad':float(mirror[i:min(len(c),i+10)].mean())}
                for i in loss[:20]]
            tail=np.asarray(e.get('failure_window_100hz',[]),float)
            posture=np.asarray(e.get('failure_posture_window_100hz',[]),float)
            if len(tail) and len(posture)==len(tail):
                row['last1s_recorded_geometry']={'height_mean_m':float(tail[:,6].mean()),
                    'leg_length_difference_mean_m':float(abs(posture[:,2]-posture[:,3]).mean()),
                    'pitch_mean_abs_rad':float(abs(posture[:,0]).mean()),
                    'roll_mean_abs_rad':float(abs(posture[:,1]).mean())}
            row['missing_full_geometry']=not bool(e.get('compact_trace_100hz'))
            envs.append(row)
        records.append({'update':update,'per_env':envs})
    report={'inputs_sha256':inputs,'results':records,'simulation':0,'PPO':0,
        'scope':'100Hz pre-reset policy-end state and latest held5ms PD torque. Signed means can hide alternating saturation.',
        'limitations':['update50 has only final1s height/leg-length/posture traces; full contact flag and active-joint mirror traces exist',
            'contact force gate is sensor resultant >2N, not certified normal load',
            'held PD uses substep joint speed; residual versus policy-end speed is not alone a wiring fault',
            'event precedence does not establish causation; passive knee joint history not recorded']}
    for p,h in inputs.items():
        if digest(Path(p))!=h:raise ValueError('input changed')
    output.mkdir(parents=True)
    with (output/'audit.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
    print(json.dumps([{'update':r['update'],'env0_last5s':r['per_env'][0]['windows'][-1],
        'env0_contact_loss':r['per_env'][0]['contact_loss_events'][:6]} for r in records],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.run.resolve(),a.output_dir.resolve())
