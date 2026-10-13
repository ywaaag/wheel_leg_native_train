"""Pure normal-stance symmetry task; no file/env/runtime access."""
import math
import numpy as np
VERSION='recovery_standing_symmetry_task_v1'
RECIPE='student_recovery_ppo_standing_mirror_huber_v11'
SOURCE_SHA='2a587c31bbf81f2db669561965431cc97598c9e13b87043553582b8a09237a9a'

def plan():
 return dict(version=VERSION,total_update_limit=None,formal_block_updates=300,block_wall_s=14400,storage_max_bytes=2*2**30,smoke_new_recipe=12,initial_family='motion_native_normal',training_envs=64,teacher_control=False,automatic_dynamic_promotion=False,BC=0.,stagnant_blocks=3,rollback_limit=1,min_formal_before_plateau_stop=5000,target_height_m=.34,height_mean_error_max_m=.02,height_peak_error_max_m=.04,symmetry_mae_rad=.05,symmetry_p95_rad=.10,independent_normal_certification_envs=32,stop_on_fault=True)

def validate_task(task,spec):
 errors=[];c=spec['recovery_course'];state=c['state']
 if task['standing_training']!=plan():errors.append('standing task authorized plan differs')
 if state['stage']!='A' or state['prefix'] or state['previous_prefix'] or state['stage_A_updates']!=0:errors.append('standing task cannot train dynamic prefixes')
 if c['early_end_allowed']:errors.append('standing task requires block decision and symmetry certificate')
 if spec.get('student_temporal_regularization'):errors.append('standing task temporal auxiliary forbidden')
 if c['first_recipe_block'] and spec['source_sha256']!=SOURCE_SHA:errors.append('standing initial Actor source differs')
 if spec['student_training']['version']!=RECIPE:errors.append('standing task recipe differs')
 cases=spec['student_evaluation']['cases']
 if len([r for r in cases if r['case_id']=='normal_certification_yaw12' and r['family']=='motion_native_normal' and r['kind']=='student'])!=1:errors.append('standing32 certification case missing')
 return errors

def annotate(result,control,first_episode_valid):
 """Only the first fixed 1000-interval hold; main physical score is unchanged."""
 from native_stand.command_v6.domain.trace_schema import CONTROL
 window=result.get('hold_index_half_open');out=dict(standing_symmetry_pass=False,standing_joint_pass=False,standing_symmetry_mae_rad=None,standing_symmetry_p95_rad=None)
 if result.get('hold_complete') and window:
  lo,hi=window;q=control[lo:hi,CONTROL['joint_q']][:,[0,1,3,4]]
  if hi-lo!=1000 or len(q)!=1000 or not first_episode_valid[lo:hi].all() or not np.isfinite(q).all():raise ValueError('standing symmetry requires full valid fixed hold window')
  e=np.abs(np.stack((q[:,0]+q[:,2],q[:,1]-q[:,3]),-1));mae=e.mean(0);p95=np.percentile(e,95,axis=0)
  out.update(standing_symmetry_mae_rad=mae.tolist(),standing_symmetry_p95_rad=p95.tolist(),standing_symmetry_pass=bool((mae<=.05).all() and (p95<=.10).all()))
 out['standing_joint_pass']=bool(result['accepted'] and out['standing_symmetry_pass'])
 return out

def training_phase_metrics(rows,phase):
 if phase not in ('smoke','formal'):raise ValueError('unsupported standing training phase')
 return metrics(rows) if phase=='formal' else None

def metrics(rows):
 if len(rows)!=24:raise ValueError('standing primary assessment requires24 first episodes')
 def stable(r):return bool(r.get('hold_complete')) and all(v for k,v in r.get('checks',{}).items() if k not in ('saturation','early_failure','leg_symmetry')) and bool(r.get('checks'))
 complete=[r for r in rows if r.get('hold_complete')]
 finite_errors=[r['standing_symmetry_mae_rad'] for r in complete if r.get('standing_symmetry_mae_rad') is not None]
 return dict(joint_passed=sum(bool(r.get('standing_joint_pass')) for r in rows),physical_passed=sum(bool(r.get('standing_physical_pass',r['accepted'])) for r in rows),stable_except_limit=sum(stable(r) for r in rows),complete_windows=len(complete),entry=sum(r.get('entry_index') is not None for r in rows),hold_prefix_median_s=float(np.median([r.get('valid_hold_prefix_s',0.) for r in rows])),mirror_mae_rad=float(np.mean(finite_errors)) if len(finite_errors)==24 else None,limit_fraction=float(np.mean([r.get('limit_fraction',1.) for r in complete])) if len(complete)==24 else None)

def rank(m):
 return (m['joint_passed'],m['physical_passed'],m['stable_except_limit'],m['complete_windows'],m['hold_prefix_median_s'],-(m['mirror_mae_rad'] if m['mirror_mae_rad'] is not None else float('inf')),-(m['limit_fraction'] if m['limit_fraction'] is not None else float('inf')))

def improved(old,new):
 if old is None:return True
 if new['joint_passed']>=old['joint_passed']+2 or new['physical_passed']>=old['physical_passed']+2 or new['hold_prefix_median_s']>=old['hold_prefix_median_s']+.5:return True
 if new['stable_except_limit']<old['stable_except_limit']:return False
 return any(old[k] is not None and new[k] is not None and old[k]>0 and new[k]<=.8*old[k] for k in ('mirror_mae_rad','limit_fraction'))

def decide(book,candidates):
 """Block cadence is not authorization ceiling. One plateau rollback, then stop."""
 best=max(candidates,key=lambda c:rank(c['standing_metrics']));m=best['standing_metrics']
 confirmation=book.get('standing_confirmations',0)
 for c in sorted(candidates,key=lambda c:c['update']):
  if c['standing_metrics']['joint_passed']==24:confirmation+=1
  else:confirmation=0
 book['standing_confirmations']=confirmation
 finals=[c for c in candidates if c.get('standing_certification32_pass') and c['standing_metrics']['joint_passed']==24]
 if confirmation>=2 and finals:return {'action':'ACCEPT_STANDING','candidate':max(finals,key=lambda c:rank(c['standing_metrics']))}
 if improved(book.get('standing_best_metrics'),m):book['standing_stagnant_blocks']=0;book['standing_best_metrics']=m
 else:book['standing_stagnant_blocks']=book.get('standing_stagnant_blocks',0)+1
 if book.get('standing_best_trained') is None or rank(m)>rank(book['standing_best_trained']['standing_metrics']):book['standing_best_trained']=best
 if book['standing_stagnant_blocks']>=3 and sum(r['formal_updates'] for r in book.get('blocks',[]))>=5000:
  if book.get('standing_rollbacks',0):return {'action':'STOP','reason':'standing/symmetry plateau after one full-state rollback; new design variable required'}
  book['standing_rollbacks']=1;book['standing_stagnant_blocks']=0
  return {'action':'ROLLBACK','resume':book['standing_best_trained']}
 return {'action':'CONTINUE','resume':max(candidates,key=lambda c:c['update'])}
