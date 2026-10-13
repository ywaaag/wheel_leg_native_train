"""Read-only terminal A/B review using each run's named frozen schema; CPU only."""
import argparse,collections,hashlib,json,runpy
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def schema(chain):
 p=chain/'source_snapshot/native_stand/command_v6/domain/trace_schema.py';s=runpy.run_path(str(p))
 if s['VERSION']!='recovery_policy_trace_v1':raise ValueError('unsupported named trace version')
 return s,p

def window(a,ids,env,s):
 if not len(ids):return None
 state=a['state'][ids,env];post=a['posture'][ids,env];control=a['control'][ids,env];S,C,P=s['STATE'],s['CONTROL'],s['POSTURE']
 wheel=control[:,C['clipped_action']][:,[2,5]]*100.
 applied=control[:,C['applied_torque']][:,[2,5]]
 return dict(intervals=len(ids),wheel_delta_rms_rad_s=np.sqrt(np.mean(np.diff(wheel,axis=0)**2,axis=0)).tolist() if len(ids)>1 else None,
  wheel_applied_torque_rms_nm=np.sqrt(np.mean(applied**2,axis=0)).tolist(),wheel_torque_sign_changes=(np.diff(np.sign(applied),axis=0)!=0).sum(0).tolist(),
  policy_limit_fraction=float(state[:,S['saturated']].mean()),mean_abs_vx_mps=float(abs(state[:,S['vx_mps']]).mean()),
  pitch_roll_peak_rad=np.max(abs(post[:,[P['pitch_rad'],P['roll_rad']]]),axis=0).tolist(),
  dual_contact_fraction=float((state[:,[S['left_contact_n'],S['right_contact_n']]]>2).all(-1).mean()),
  height_range_m=[float(state[:,S['height_m']].min()),float(state[:,S['height_m']].max())])

def evaluate(path,s):
 d=read(path);trace=path.parent/d['trace']['path']
 if sha(trace)!=d['trace']['sha256']:raise ValueError('trace SHA differs '+str(trace))
 if d['field_schema']['state']!=s['VERSION']:raise ValueError('state schema differs')
 with np.load(trace) as packed:
  a={k:packed[k] for k in ('state','posture','control','controller','first_episode_valid','termination_causes','policy_time_s')}
 if not np.isfinite(a['policy_time_s']).all() or not np.allclose(np.diff(a['policy_time_s']),.01,rtol=0,atol=2e-6):raise ValueError('policy time discontinuity')
 S,P=s['STATE'],s['POSTURE'];rows=[]
 for env,r in enumerate(d['per_env']):
  mask=(a['controller'][:,env,0]==d['field_schema']['controller']['student'])&a['first_episode_valid'][:,env]
  ids=np.flatnonzero(mask);entry=r.get('entry_index');hold=ids[ids>entry] if entry is not None else np.array([],dtype=int)
  if len(ids) and (np.diff(ids)!=1).any():raise ValueError('student interval discontinuity')
  if len(ids) and len(np.unique(a['state'][ids,env,S['episode_id']]))!=1:raise ValueError('first episode concatenation')
  first_violation=None
  for k in hold[:1000]:
   st=a['state'][k,env];pt=a['posture'][k,env]
   checks={'height':st[S['height_m']]>=.30,'level_peak':np.max(abs(pt[[P['pitch_rad'],P['roll_rad']]]))<=.15,'tilt':st[S['tilt_rad']]<=.18,'contact':min(st[S['left_contact_n']],st[S['right_contact_n']])>2,'clearance':st[S['clearance_m']]>0,'closure':st[S['closure_m']]<=.005}
   bad=[name for name,v in checks.items() if not v]
   if bad:
    def sample(index):
     state=a['state'][index,env];post=a['posture'][index,env];control=a['control'][index,env];q=control[s['CONTROL']['joint_q']][[0,1,3,4]]
     return {'pitch_roll_rad':post[[P['pitch_rad'],P['roll_rad']]].tolist(),'contact_resultant_n':state[[S['left_contact_n'],S['right_contact_n']]].tolist(),'vx_mps':float(state[S['vx_mps']]),'height_m':float(state[S['height_m']]),'leg_q_rad':q.tolist(),'leg_targets_rad':control[s['CONTROL']['leg_target_after_limit']].tolist(),'mirror_error_rad':[float(q[0]+q[2]),float(q[1]-q[3])]}
    first_violation={'after_entry_s':float((k-entry)*.01),'checks':bad,'at_event':sample(k),'100ms_before':sample(max(entry+1,k-10))};break
  causes=collections.Counter()
  for k in ids:
   for index,name in enumerate(('nonfinite','closure_or_penetration_or_joint','height','tilt','restricted_contact','joint_safety')):
    if a['termination_causes'][k,env,index]:causes[name]+=1
  rows.append(dict(env=r.get('env',env),accepted=r['accepted'],entry_index=entry,hold_complete=r.get('hold_complete',False),valid_hold_prefix_s=r.get('valid_hold_prefix_s',0.),failed_checks=r.get('failed_checks',[]),student_intervals=len(ids),
   first200=window(a,ids[:200],env,s),entry_first200=window(a,hold[:200],env,s),full_hold=window(a,hold[:1000],env,s) if r.get('hold_complete') and len(hold)>=1000 else None,
   first_instantaneous_hold_violation=first_violation,observed_termination_causes=dict(causes)))
 return {'case':d['case'],'evaluation_path':str(path.resolve()),'evaluation_sha256':sha(path),'trace_path':str(trace.resolve()),'trace_sha256':sha(trace),'rows':rows}

def aggregate(evals):
 rows=[r for e in evals for r in e['rows']]
 result=dict(n=len(rows),accepted=sum(r['accepted'] for r in rows),entry=sum(r['entry_index'] is not None for r in rows),complete_windows=sum(r['hold_complete'] for r in rows),median_valid_hold_prefix_s=float(np.median([r['valid_hold_prefix_s'] for r in rows])),failures=dict(collections.Counter(c for r in rows for c in r['failed_checks'])),terminations=dict(collections.Counter(c for r in rows for c in r['observed_termination_causes'])))
 for name in ('first200','entry_first200','full_hold'):
  windows=[r[name] for r in rows if r[name] is not None];complete=[w for w in windows if w['intervals']==(1000 if name=='full_hold' else 200)]
  result[name]={'complete_n':len(complete),'incomplete_n':len(windows)-len(complete)}
  if complete:
   for key in ('wheel_delta_rms_rad_s','wheel_applied_torque_rms_nm','wheel_torque_sign_changes','policy_limit_fraction','mean_abs_vx_mps','pitch_roll_peak_rad','dual_contact_fraction'):
    result[name][key]=np.mean([w[key] for w in complete],axis=0).tolist()
 return result

def normal_joint_margins(chain):
 phase=chain/'formal';spec=read(phase/'source_snapshot/spec.json');library=Path(spec['recovery']['pose_library']);limits=read(library)['joint_limits_rad'];readback=phase/'runtime_readback.json';names=read(readback)['control']['joint_names'];rows=[];inputs={str(library.resolve()):sha(library),str(readback.resolve()):sha(readback)}
 for p in sorted(phase.glob('evaluation_[0-9][0-9].json')):
  d=read(p)
  if d['case']['family']!='motion_native_normal':continue
  trace=phase/d['trace']['path']
  if sha(trace)!=d['trace']['sha256']:raise ValueError('joint margin trace SHA differs')
  inputs[str(trace.resolve())]=sha(trace)
  with np.load(trace) as a:
   mask=a['first_episode_valid']&(a['controller'][...,0]==d['field_schema']['controller']['student']);q=a['joint_q_pre'][mask]
  if q.shape[-1]!=len(names):raise ValueError('named full-joint q mapping differs')
  for j,name in enumerate(names):
   if name not in limits:continue
   lo,hi=limits[name];margin=np.minimum(q[:,j]-lo,hi-q[:,j])
   rows.append({'case':d['case']['case_id'],'joint':name,'min_margin_rad':float(margin.min()),'outside_1mrad':int((margin<-.001).sum())})
 return {'scope':'B50 existing deterministic normal, student-controlled pre-action first episode only; not env53 fault state','rows':sorted(rows,key=lambda r:r['min_margin_rad']),'inputs':inputs}

def review(root):
 out={'version':'recovery_temporal_terminal_offline_v1','simulation':0,'online_PPO_updates':0,'optimizer_steps':0,'arms':{},'inputs':{},'limitations':['100Hz held-torque only; not full PD/physics frequency','instantaneous first breach excludes running-mean speed/angle gates','no causal attribution from temporal ordering alone']}
 for arm in ('A','B'):
  chain=root/'runs'/('2026_10_12-20_49__recovery_wheel_temporal_'+arm.lower()+'_from100');s,sp=schema(chain);out['inputs'][str(sp.resolve())]=sha(sp)
  out['arms'][arm]={}
  for phase in ('source_eval','formal'):
   registry=read(chain/phase/'candidate_registry.json')
   for c in registry:
    if phase=='formal' and c['update']==0:continue
    cp=Path(c['checkpoint']);assert sha(cp)==c['sha256']
    details=[evaluate(chain/phase/r['path'],s) for r in c['evaluations']];groups={}
    for e in details:
     case=e['case'];g='suffix' if case['case_id'].startswith('current_') else 'normal' if case['family']=='motion_native_normal' and case['kind']=='student' else 'Swing' if case['case_id']=='unassisted_Swing' else 'teacher'
     groups.setdefault(g,[]).append(e)
    out['arms'][arm][str(c['update'])]={'checkpoint':str(cp),'checkpoint_sha256':sha(cp),'groups':{g:aggregate(es) for g,es in groups.items()},'details':details}
  f=chain/'formal/fault_all_environments.json'
  if f.exists():
   j=read(f);a=np.load(f.with_name(j['evidence']));out['fault']={'event':j,'values':{k:a[k].tolist() for k in a.files if k!='state'},'metadata_sha256':sha(f),'npz_sha256':sha(f.with_name(j['evidence'])),'joint_identification':'NOT_AVAILABLE: full q/dq/names/limits not saved in this fault bundle'}
 out['B50_normal_joint_margins']=normal_joint_margins(root/'runs/2026_10_12-20_49__recovery_wheel_temporal_b_from100')
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('/home/kellen/wheel_leg_native_train'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 a.output.write_text(json.dumps(review(a.root),indent=2,ensure_ascii=False)+'\n')
 print(a.output)
