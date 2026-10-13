"""Event-centred support review, existing first episodes only; no simulation."""
import argparse,json
from pathlib import Path
import numpy as np,torch
from native_stand.students.data import sha
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,VERSION
from review_student_recovery_task_ppo import angular,targets

def review(run,output):
 run=Path(run).resolve();output=Path(output)
 if output.exists():raise FileExistsError(output)
 rows=[];sources={}
 for name,phase,index in [('teacher','source_eval',4),('student100','formal',8)]:
  for case in range(1 if name=='teacher' else 4):
   p=run/phase/f'evaluation_{index+case:02}.json';d=json.loads(p.read_text());zpath=p.parent/d['trace']['path'];assert sha(zpath)==d['trace']['sha256'] and d['field_schema']['state']==VERSION
   assert sha(d['case']['checkpoint'])==d['case']['sha256'];sources[str(p)]=sha(p);sources[str(zpath)]=sha(zpath);sources[d['case']['checkpoint']]=d['case']['sha256']
   z=np.load(zpath)
   for e in range(8):
    ids=np.flatnonzero(z['first_episode_valid'][:,e]&z['actor_valid'][:,e,0]);s=z['state'][ids,e];post=z['posture'][ids,e];w=angular(z['root_post'][ids,e]);t=targets(z['control'][ids,e]);g=z['geometry'][ids,e];times=np.arange(1,len(ids)+1)*.01
    # Peak defined within the rise/deadline interval, excluding long teacher hold.
    rise=times<=2.5;pk=int(np.argmax(np.where(rise,s[:,6],-np.inf)))
    crests=[k for k in range(1,len(s)-5) if rise[k] and s[k,6]>=.35 and s[k,6]>=s[k-1,6] and s[k,6]>=s[k+1,6] and s[k:k+6,6].min()<s[k,6]-.002]
    first_crest=crests[0] if crests else pk
    indices={'peak_height':pk,'first_lift_crest':first_crest}
    pk=first_crest  # Fall/target/contact events are relative to the first rise crest.
    for key,mask in [('height030',(s[:,6]>=.30)),('fall_below030_after_peak',(s[:,6]<.30)&(np.arange(len(s))>pk)),('positive_pitch010',(post[:,0]>.10)&(np.arange(len(s))>pk)),('wheel_both_positive_after_peak',(t[:,[2,5]]>0).all(1)&(np.arange(len(s))>pk)),('dual_contact_lost_after_peak',~(s[:,10:12]>2).all(1)&(np.arange(len(s))>pk))]:
     hits=np.flatnonzero(mask);indices[key]=int(hits[0]) if len(hits) else None
    events={}
    for key,i in indices.items():
     if i is None:events[key]=None;continue
     events[key]={'controlled_s':float(times[i]),'height_m':float(s[i,6]),'pitch_roll_rad':post[i,:2].tolist(),'angular_body_rad_s':w[i].tolist(),'vx_vy_yaw':s[i,7:10].tolist(),'wheel_contact_resultant_n':s[i,10:12].tolist(),'leg_lengths_m':post[i,2:4].tolist(),'physical_targets_leftfirst':t[i].tolist(),'active_q':z['control'][ids[i],e,CONTROL['joint_q']].tolist(),'wheel_geometry':g[i].tolist(),'requested_torque':z['control'][ids[i],e,CONTROL['requested_torque']].tolist(),'applied_torque':z['control'][ids[i],e,CONTROL['applied_torque']].tolist()}
    rows.append({'model':name,'case_id':d['case']['case_id'],'env':e,'entry':d['per_env'][e]['entry_index'],'accepted':d['per_env'][e]['accepted'],'controlled_s':len(ids)*.01,'terminal_causes':d['per_env'][e]['termination_causes'],'events':events})
 result={'version':'student_support_loss_review_v1','run':str(run),'source_SHA':sources,'per_episode':rows,'crest_definition':'first local maximum >=.35m followed by >.002m drop within50ms, else maximum in first2.5s','geometry_semantics':'two wheel centres relative to root, body XYZ6; gravity body3; active leg q4. Authored frozen constructor below.','physical_scope':'100Hz applied torque sample, not full PD trace; contacts >2N resultant, not normal load','clock':'controlled first post-state=.01s, first episode only','optimizer_updates':0,'simulation':0}
 frozen=run/'source_snapshot/native_stand/recovery/runtime.py';text=frozen.read_text();a=text.index('self.wheel_geometry_snapshot.copy_');result['frozen_geometry_constructor_excerpt']=text[a:a+1150];sources[str(frozen)]=sha(frozen)
 output.mkdir(parents=True);(output/'support_loss.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=review(a.run,a.output);print(json.dumps({'episodes':len(r['per_episode']),'output':a.output}))
