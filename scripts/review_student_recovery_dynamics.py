"""CPU-only loss-of-support alignment and episode-isolated short-history probe."""
import argparse,json
from pathlib import Path
import numpy as np,torch
from native_stand.students.data import sha,STAGES
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,VERSION
from review_student_recovery_task_ppo import targets,angular

from native_stand.students.history_diagnostic import history_rows

def history_probe(path):
 d=torch.load(path,map_location='cpu',weights_only=False);h,valid=history_rows(d)
 # Equal counts per stage/episode, chronological stride; no adjacent-frame split.
 selected=[]
 for ep in d['episode'].unique():
  for stage in range(4):
   ids=torch.where((d['episode']==ep)&(d['stage']==stage)&valid)[0]
   if len(ids):selected.extend(ids[torch.linspace(0,len(ids)-1,min(24,len(ids))).long()].tolist())
 selected=torch.tensor(selected);train=selected[d['split'][selected]==0];out={}
 for si,label in [(1,'validation'),(2,'test_descriptive_not_selection')]:
  query=selected[d['split'][selected]==si]
  assert not set(d['episode'][train].tolist())&set(d['episode'][query].tolist())
  strategies={}
  for name,x in [('current',d['x'][:,:22]),('current_plus_four',h.flatten(1)/5**.5)]:
   distances=torch.cdist(x[query],x[train]);near=distances.argmin(1);error=(d['y'][query]-d['y'][train[near]]).abs()*torch.tensor([1.5,1.5,100,1.5,1.5,100])
   strategies[name]={STAGES[st]:{'query_samples':int((d['stage'][query]==st).sum()),'MAE_per_channel':error[d['stage'][query]==st].mean(0).tolist(),'P95_per_channel':torch.quantile(error[d['stage'][query]==st],.95,dim=0).tolist(),'median_input_L2':float(distances[d['stage'][query]==st].min(1).values.median())} for st in range(4)}
  out[label]=strategies
 # Direct adjacent boundary conflict samples: no equal-observation claim.
 boundaries=[]
 for ep in d['episode'].unique():
  ids=torch.where(d['episode']==ep)[0];turn=ids[d['stage'][ids]==1]
  if len(turn):
   b=int(turn[0]);a=b-1
   if d['episode'][a]==ep:
    boundaries.append({'episode':int(ep),'split':int(d['split'][b]),'current_input_L2':float(torch.linalg.vector_norm(d['x'][b]-d['x'][a])),'history_L2':float(torch.linalg.vector_norm(h[b]-h[a])),'physical_target_jump':((d['y'][b]-d['y'][a])*torch.tensor([1.5,1.5,100,1.5,1.5,100])).tolist()})
 return {'dataset':str(path),'SHA':sha(path),'complete_history_eligible_samples':int(valid.sum()),'sampled_train':len(train),'episode_disjoint':True,'nearest_neighbor':out,'boundary_pairs':boundaries,'limitations':'Diagnostic nearest-neighbor labels, no new optimizer, no causal/closed-loop proof. Only 40ms history; same local initial conditions. Boundary is teacher direct switch, not autonomous optimal action evidence.','candidate_resource_if_implemented':{'input_dim':124,'layout':'5*(22 body + 1 validity)+9 current task','Actor_parameters':26534,'weights_FP32_bytes':106136,'MAC':26304,'hardware_verified':False}}

def dynamics(run):
 result=[];sources={}
 for label,phase,index in [('teacher','source_eval',4),('new25','formal',0),('new50','formal',4),('new100','formal',8)]:
  groups=1 if label=='teacher' else 4
  for j in range(groups):
   f=run/phase/f'evaluation_{index+j:02}.json';ev=json.loads(f.read_text());p=f.parent/ev['trace']['path'];assert sha(p)==ev['trace']['sha256'];assert ev['field_schema']['state']==VERSION
   sources[str(f)]=sha(f);sources[str(p)]=sha(p)
   with np.load(p) as z:a={k:z[k] for k in z.files}
   for e in range(8):
    ids=np.flatnonzero(a['first_episode_valid'][:,e]&a['actor_valid'][:,e,0]);s=a['state'][ids,e];post=a['posture'][ids,e];ang=angular(a['root_post'][ids,e]);tar=targets(a['control'][ids,e]);clock=np.arange(1,len(ids)+1)*.01
    def first(mask):return float(clock[np.flatnonzero(mask)[0]]) if mask.any() else None
    anchors={}
    for threshold in [.20,.25,.30,.35]:
     hits=np.flatnonzero(s[:,STATE['height_m']]>=threshold)
     if len(hits):
      k=int(hits[0]);anchors[str(threshold)]={'time_s':float(clock[k]),'height':float(s[k,6]),'pitch_roll':post[k,:2].tolist(),'angular_body':ang[k].tolist(),'contacts':s[k,10:12].tolist(),'leg_lengths':post[k,2:4].tolist(),'targets':tar[k].tolist(),'vx_vy_yaw':s[k,7:10].tolist()}
    near=np.flatnonzero(s[:,15]>=.6)
    k=int(near[0]) if len(near) else len(s)-1
    l=max(k-5,0);u=min(k+6,len(s));rows=[{'controlled_s':float(clock[v]),'height':float(s[v,6]),'pitch_roll':post[v,:2].tolist(),'angular':ang[v].tolist(),'legs':post[v,2:4].tolist(),'contact':s[v,10:12].tolist(),'targets':tar[v].tolist(),'requested_torque':a['control'][ids[v],e,CONTROL['requested_torque']].tolist(),'applied_torque':a['control'][ids[v],e,CONTROL['applied_torque']].tolist()} for v in range(l,u)]
    result.append({'model':label,'case':ev['case']['case_id'],'env':e,'first_tilt030_s':first(s[:,15]>=.3),'first_tilt060_s':first(s[:,15]>=.6),'first_high_horizontal_angular_gt3_s':first(np.linalg.norm(ang[:,[0,2]],axis=1)>3),'first_dual_contact_lost_s':first(~(s[:,10:12]>2).all(1)),'height_peak':float(s[:,6].max()),'anchors':anchors,'tilt060_plusminus5_intervals':rows})
 return {'source_SHA':sources,'per_episode':result,'notes':'Event order describes observations; no causal force attribution. Angle thresholds .3/.6 are diagnostics, not new gates; contact resultant >2N, not normal load.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--dataset',required=True);p.add_argument('--output',required=True);a=p.parse_args();torch.set_num_threads(4);output=Path(a.output)
 if output.exists():raise FileExistsError(output)
 d={'dynamics':dynamics(Path(a.run).resolve()),'short_history_probe':history_probe(Path(a.dataset).resolve()),'online_updates':0,'offline_optimizer_steps':0,'simulation':0}
 output.mkdir(parents=True);(output/'dynamics_history_review.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['short_history_probe']['nearest_neighbor'],indent=2))
