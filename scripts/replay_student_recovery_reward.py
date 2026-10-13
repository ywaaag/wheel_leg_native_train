"""Offline reward unit/event replay on existing complete first-episode data."""
import argparse,json
from pathlib import Path
import numpy as np,torch
from native_stand.students.data import sha
from native_stand.students.recovery_task import Certificate,reward,FIELDS,configuration
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,VERSION
ROOT=Path(__file__).resolve().parents[1]
def replay(output):
 torch.set_num_threads(4);output=Path(output)
 if output.exists():raise FileExistsError(output)
 rows=[];sources={}
 for run,case,label in [('2026_10_10-22_24__receiver_window_ppo0',3,'teacher_success'),('2026_10_11-11_36__mcu_v2_student_independent_ppo0',0,'student_failure')]:
  run=ROOT/'runs'/run;p=run/f'evaluation_{case:02d}.json';ev=json.loads(p.read_text());trace=run/ev['trace']['path'];assert sha(trace)==ev['trace']['sha256'];assert ev['field_schema']['state']==VERSION;sources[str(p)]=sha(p);sources[str(trace)]=sha(trace)
  with np.load(trace) as z:a={k:z[k] for k in z.files}
  for e in range(8):
   ix=np.flatnonzero(a['first_episode_valid'][:,e]&(a['controller'][:,e,0]>0));clock=Certificate(1,'cpu');h0=torch.tensor([a['root_pre'][ix[0],e,2]]);totals=torch.zeros(6);events=torch.zeros(3);episode_return=0.
   series=[]
   for i in ix:
    s=torch.tensor(a['state'][i,e])[None];p=torch.tensor(a['posture'][i,e])[None];previous=torch.tensor(a['previous_targets'][i,e])[None] if 'previous_targets' in a else torch.tensor(a['target_pre'][i,e])[None]
    prev=torch.zeros(1,6);prev[:,[0,1,3,4]]=previous[:,:4];prev[:,[2,5]]=previous[:,4:]
    ctl=torch.tensor(a['control'][i,e])[None];target=torch.zeros(1,6);target[:,[0,1,3,4]]=ctl[:,CONTROL['leg_target_after_limit']];target[:,[2,5]]=ctl[:,CONTROL['clipped_action']][:,[2,5]]*100
    root=torch.tensor(a['root_post'][i,e])[None] if 'root_post' in a else torch.tensor(a['root_state_post'][i,e])[None]
    xyz=-root[:,3:6];w=root[:,6:7];v=root[:,10:13];angular=v+2*torch.cross(xyz,torch.cross(xyz,v,dim=-1)+w*v,dim=-1)
    clock.set_velocity(s[:,7:10]);clock.observe(s[:,6],p[:,:2],s[:,15],s[:,10:12],s[:,13],s[:,12],s[:,17],active=torch.ones(1,dtype=torch.bool),valid=s[:,29].bool(),safety_failed=s[:,3].bool(),fault=s[:,4].bool())
    r=reward(s[:,6],h0,p[:,:2],s[:,10:12],s[:,13],ctl[:,CONTROL['applied_torque']],prev,target,angular,s[:,7:10],s[:,9],clock.entry>=0,torch.ones(1,dtype=torch.bool),s[:,4].bool(),clock.entry_confirmed,clock.certificate_passed,clock.task_failure)
    totals+=r['continuous_dt'][0];events+=r['events'][0];episode_return+=float(r['total']);series.append(torch.cat((r['raw'][0],r['weighted_density'][0],r['continuous_dt'][0],r['events'][0])))
   rows.append({'source':label,'env':e,'controlled_samples':len(ix),'continuous_reward_sum_by_term':dict(zip(FIELDS,totals.tolist())),'events_sum':events.tolist(),'undiscounted_return':episode_return,'certificate_passed':bool(clock.certificate_passed.item()),'entry_s':float(clock.entry.item())})
 output.mkdir();report={'reward':configuration(),'sources_sha256':sources,'episodes':rows,'optimizer_steps':0,'simulation':0,'interpretation':'offline reward signs/events/units only, not learning proof; no extra BC'}
 (output/'reward_replay.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(replay(a.output),indent=2))
