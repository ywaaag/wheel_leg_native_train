"""Offline same-case A/B results; complete windows and truncated common prefix separate."""
import json
from pathlib import Path
import numpy as np
from .data import sha

def evaluation(path):
 d=json.loads(Path(path).read_text());trace=Path(path).parent/d['trace']['path']
 if sha(trace)!=d['trace']['sha256']:raise ValueError('comparison trace SHA differs')
 a=np.load(trace);rows=[]
 for i,r in enumerate(d['per_env']):
  student=(a['controller'][:,i].reshape(-1)==3)&a['first_episode_valid'][:,i]
  ids=np.flatnonzero(student);ids=ids[:200]
  c=a['control'][ids,i];state=a['state'][ids,i];p=a['posture'][ids,i]
  w=c[:,[20,23]]*100.;rms=np.sqrt(np.mean(np.diff(w,axis=0)**2,axis=0)).tolist() if len(ids)>1 else [None,None]
  rows.append({**r,'common_first_2s':{'observed_student_intervals':len(ids),'complete':len(ids)==200,'wheel_delta_rms':rms,'limit_fraction':float(state[:,17].mean()) if len(ids) else None,'pitch_roll_peak_rad':np.max(abs(p[:,:2]),axis=0).tolist() if len(ids) else None,'mean_abs_vx':float(abs(state[:,7]).mean()) if len(ids) else None,'dual_contact_fraction':float((state[:,10:12]>2).all(-1).mean()) if len(ids) else None}})
 return {'case':d['case'],'per_env':rows,'evaluation_sha256':sha(path),'trace_sha256':sha(trace)}

def aggregate(rows):
 completed=[r for r in rows if r.get('hold_complete')]
 return {'environments':len(rows),'accepted':sum(r['accepted'] for r in rows),'entry':sum(r.get('entry_index') is not None for r in rows),'complete_windows':len(completed),'wheel_rms':float(np.mean([r['wheel_delta_rms'] for r in completed])) if completed else None,'limit_fraction':float(np.mean([r['limit_fraction'] for r in completed])) if completed else None,'other_checks_passed':sum(bool(r.get('checks')) and all(v for k,v in r['checks'].items() if k not in ('saturation','early_failure')) for r in rows),'paired_first2_complete':sum(r['common_first_2s']['complete'] for r in rows)}

def review(results):
 report={'version':'student_temporal_ab_comparison_v1','arms':{},'PPO_in_review':0,'no_automatic_long_training':True}
 for arm,item in results.items():
  root=Path(item['chain']);all_results={}
  for phase in ('source_eval','formal'):
   registry=json.loads((root/phase/'candidate_registry.json').read_text())
   candidates=registry if phase=='formal' else [registry[0]]
   for candidate in candidates:
    if phase=='formal' and candidate['update']==0:continue
    key=str(candidate['update']);groups={};details=[]
    for row in candidate.get('evaluations',[]):
     e=evaluation(root/phase/row['path']);case=e['case'];details.append(e)
     group='suffix' if case['case_id'].startswith('current_') else 'normal' if case['family']=='motion_native_normal' and case['kind']=='student' else 'Swing' if case['case_id']=='unassisted_Swing' else 'teacher'
     groups.setdefault(group,[]).extend(e['per_env'])
    # formal registry[0] carries source paths, source entry above already reports them.
    all_results[key]={'checkpoint':candidate['checkpoint'],'sha256':candidate['sha256'],'groups':{g:aggregate(rs) for g,rs in groups.items()},'details':details}
  report['arms'][arm]=all_results
 for update in ('50','100'):
  if all(update in report['arms'].get(a,{}) for a in ('A','B')):
   for group in ('suffix','normal'):
    b=report['arms']['B'][update]['groups'][group];source=report['arms']['B']['0']['groups'][group]
    improved=source['wheel_rms'] is not None and b['wheel_rms'] is not None and source['limit_fraction'] is not None and b['limit_fraction'] is not None and b['complete_windows']>=source['complete_windows'] and b['wheel_rms']<=source['wheel_rms']*.5 and b['limit_fraction']<=source['limit_fraction']*.7 and b['other_checks_passed']>=source['other_checks_passed']
    report.setdefault('threshold_checks',{})[update+'_'+group]={'improvement_candidate':bool(improved),'requires_per_env_pose_speed_contact_review':True}
 return report
