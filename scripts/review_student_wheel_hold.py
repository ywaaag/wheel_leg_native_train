"""Read-only named-schema wheel hold diagnostics and v8 smoothing reward replay."""
import argparse,json
from pathlib import Path
import numpy as np
from native_stand.students.data import sha
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,POSTURE

def review(paths):
 rows=[]
 for path in map(Path,paths):
  r=json.loads(path.read_text());t=path.parent/r['trace']['path']
  if r['field_schema']['control']!='recovery_policy_trace_v1' or sha(t)!=r['trace']['sha256']:raise ValueError('named schema or trace SHA differs')
  z=np.load(t)
  if not np.allclose(np.diff(z['policy_time_s']),.01,atol=2e-6,rtol=0):raise ValueError('trace time axis differs')
  for e,v in enumerate(r['per_env']):
   if not v.get('hold_complete'):continue
   lo,hi=v['hold_index_half_open'];c=z['control'][lo:hi,e];s=z['state'][lo:hi,e];w=c[:,CONTROL['clipped_action']][:,[2,5]]*100
   previous=z['previous_targets'][lo:hi,e,-2:]
   raw=((w-previous)/10.)**2
   torque=c[:,CONTROL['physical_clipped_torque']][:,[2,5]];sat=abs(torque)>=5.5-1e-4
   longest=[]
   for j in range(2):
    a=np.r_[False,sat[:,j],False].astype(int);start=np.where(np.diff(a)==1)[0];end=np.where(np.diff(a)==-1)[0];longest.append(float((end-start).max(initial=0))*.01)
   rows.append(dict(evaluation=str(path.resolve()),evaluation_sha256=sha(path),trace_sha256=sha(t),env=e,window=[lo,hi],wheel_target_delta_rms=np.sqrt(np.mean(np.diff(w,axis=0)**2,axis=0)).tolist(),sign_changes=np.sum(torque[1:]*torque[:-1]<0,axis=0).tolist(),limit_fraction=sat.mean(0).tolist(),longest_limit_s=longest,torque_rms={name:np.sqrt(np.mean(c[:,sl][:,[2,5]]**2,axis=0)).tolist() for name,sl in CONTROL.items() if name.endswith('torque')},new_wheel_cost_density_mean=float(-.2*raw.mean()),new_wheel_cost_dt_sum=float(-.2*raw.mean(-1).sum()*.01),pitch_roll_abs_mean=np.abs(z['posture'][lo:hi,e,:2]).mean(0).tolist(),vx_abs_mean=float(abs(s[:,STATE['vx_mps']]).mean()),accepted=v['accepted']))
 return {'sampling':'100Hz latest held PD torque, not full PD/physics frequency','per_env':rows,'episodes':len(rows)}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evaluation',type=Path,action='append',required=True);p.add_argument('--output',type=Path);a=p.parse_args();r=review(a.evaluation)
 text=json.dumps(r,indent=2)
 if a.output:
  with a.output.open('x') as f:f.write(text+'\n')
 else:print(text)
