"""Pure Recovery continuous-course contracts and deterministic decisions; no I/O."""
import copy,math
VERSION='recovery_continuous_swing_v1'
SMOOTH_RECIPE='student_recovery_ppo_hold_wheel_smooth_v8'
SUFFIX_RECIPE='student_recovery_ppo_dynamic_suffix_v9'
CONTACT_SUFFIX_RECIPE='student_recovery_ppo_dynamic_suffix_contact_v10'
SOURCE_SHA='2a587c31bbf81f2db669561965431cc97598c9e13b87043553582b8a09237a9a'
PREFIXES=[180,150,120,100,80,65,50,40,25,10,0]
SWING='swing_candidate_from_historical_r1'
NORMAL='motion_native_normal'

def recipe_for(state,task):
 if task.get('standing_training'):
  from .standing import RECIPE
  return RECIPE
 variant=task.get('dynamic_recipe',SUFFIX_RECIPE)
 if variant not in (SUFFIX_RECIPE,CONTACT_SUFFIX_RECIPE):raise ValueError('unknown authorized dynamic recipe')
 return SMOOTH_RECIPE if state['stage']=='A' else variant

def plan():
 return dict(version=VERSION,total_update_limit=None,total_wall_limit_s=None,formal_block_updates=300,block_wall_s=14400,block_storage_bytes=2*2**30,smoke_updates_new_recipe=12,stage_A_max_formal_updates=600,prefix_intervals=PREFIXES,group_counts=[32,16,8,8],consolidation_counts=[56,8],stagnant_blocks=3,max_insertions_per_interval=2,rollback_per_interval=1,physics_mutation=False,teacher_rescue=False,BC=0.,stop_on_fault=True,source_sha256=SOURCE_SHA)

def initial_state():
 return dict(version=VERSION,stage='A',prefix=0,previous_prefix=0,base_index=0,stage_A_updates=0,confirmation_streak=0,last_confirm_update=None,stagnant=0,best_metrics=None,best=None,latest=None,best_standing=None,best_suffix=None,best_unassisted=None,accepted_full_recovery=None,rollback_counts={},insertions={},pending_return=None,return_stack=[],interval_id=None,consecutive_failure_evaluations=0,certified=[],cumulative_updates=0,status='READY')

def validate_state(state):
 if state.get('version')!=VERSION or state.get('stage') not in ('A','B','CONSOLIDATE','DONE'):raise ValueError('unknown Recovery course state')
 for k in ('prefix','previous_prefix','stage_A_updates','stagnant','confirmation_streak','cumulative_updates'):
  if type(state.get(k)) is not int or state[k]<0:raise ValueError('course integer field '+k)
 if state['stage']=='A' and state['stage_A_updates']>600:raise ValueError('standing course bound exceeded')
 return state

def slot_groups(state,n=64):
 validate_state(state)
 if n!=64:raise ValueError('fixed course requires64 environments')
 if state['stage']=='A':return [{'group':'normal','family':NORMAL,'prefix':0} for _ in range(n)]
 if state['stage']=='CONSOLIDATE':return [{'group':'unassisted','family':SWING,'prefix':0} for _ in range(56)]+[{'group':'normal','family':NORMAL,'prefix':0} for _ in range(8)]
 return ([{'group':'current','family':SWING,'prefix':state['prefix']} for _ in range(32)]+[{'group':'previous','family':SWING,'prefix':state['previous_prefix']} for _ in range(16)]+[{'group':'normal','family':NORMAL,'prefix':0} for _ in range(8)]+[{'group':'unassisted','family':SWING,'prefix':0} for _ in range(8)])

def controlled_owners(initial,valid,elapsed,threshold):
 import torch
 active=(~initial.bool())&valid.bool();student=active&(elapsed>=threshold)
 return torch.where(~active,0,torch.where(student,3,torch.where(elapsed<50,1,2))),student

def summary(rows):
 if len(rows)!=24:raise ValueError('current assessment requires24 first episodes')
 import statistics
 passing_without_limit=lambda r:bool(r.get('hold_complete')) and all(v for k,v in r.get('checks',{}).items() if k not in ('saturation','early_failure')) and bool(r.get('checks'))
 return {'passed':sum(bool(r.get('accepted')) for r in rows),'entry':sum(r.get('entry_index') is not None for r in rows),'prefix_median_s':statistics.median(r.get('valid_hold_prefix_s',0.) for r in rows),'limit_fraction':sum(r.get('limit_fraction',1.) for r in rows)/24,'wheel_delta_rms':sum(sum(r.get('wheel_delta_rms',[0.,0.]))/2 for r in rows)/24 if all('wheel_delta_rms' in r for r in rows) else None,'all_other_passed':all(passing_without_limit(r) for r in rows)}

def standing_rank(m):
 return (m['all_other_passed'],m['passed'], -m['limit_fraction'] if m['all_other_passed'] else m['prefix_median_s'], -(m['wheel_delta_rms'] if m['wheel_delta_rms'] is not None else float('inf')))

def rank(m):return (m['passed'],m['entry'],m['prefix_median_s'],-m['limit_fraction'])

def improved(old,new):
 if old is None:return True
 return new['passed']>=old['passed']+2 or new['entry']>=old['entry']+2 or new['prefix_median_s']>=old['prefix_median_s']+.5 or (new['all_other_passed'] and old['all_other_passed'] and old['limit_fraction']>0 and new['limit_fraction']<=old['limit_fraction']*.8)

def observe_confirmation(state,m,cumulative_update):
 s=copy.deepcopy(state)
 if m['passed']==24 and cumulative_update!=s['last_confirm_update']:
  s['confirmation_streak']+=1;s['last_confirm_update']=cumulative_update;s['consecutive_failure_evaluations']=0
 elif m['passed']!=24:s['confirmation_streak']=0;s['last_confirm_update']=None;s['consecutive_failure_evaluations']+=1
 return s

def advance(state,metrics,*,formal_updates,cumulative_update,best,latest,source_metrics=None):
 """One completed block; ordinary failures never become engineering stops."""
 s=copy.deepcopy(validate_state(state));s['cumulative_updates']=cumulative_update;s['latest']=latest
 if s['stage']=='B':s['best_suffix']=best
 if s['stage']=='A':
  s['stage_A_updates']+=formal_updates
  if best:s['best_standing']=best
  continue_A=s['stage_A_updates']<600 and s['confirmation_streak']<2 and metrics['all_other_passed'] and source_metrics and metrics['limit_fraction']<=source_metrics['limit_fraction']*.8
  if continue_A:return s,{'action':'CONTINUE','resume':latest}
  s.update(stage='B',prefix=180,previous_prefix=180,base_index=0,stagnant=0,best_metrics=None,best=None,confirmation_streak=0,last_confirm_update=None)
  return s,{'action':'NEW_REWARD','resume':s['best_standing'] or best}
 if s['stage']=='CONSOLIDATE':
  s['stage']='DONE';return s,{'action':'FINAL_RECHECK','resume':best,'fallback':s['accepted_full_recovery']}
 if best and (s['best_metrics'] is None or rank(metrics)>rank(s['best_metrics'])):s['best']=best
 if s['confirmation_streak']>=2:
  s['certified'].append({'prefix':s['prefix'],'checkpoint':best,'update':cumulative_update})
  if s['prefix']==0:
   s['best_unassisted']=best;return s,{'action':'CERTIFY32','resume':best}
  previous=s['prefix']
  if s['return_stack']:following=s['return_stack'].pop()
  else:
   s['base_index']+=1;following=PREFIXES[s['base_index']];s['interval_id']=f'{previous}:{following}'
  s.update(prefix=following,previous_prefix=previous,stagnant=0,best_metrics=None,best=None,confirmation_streak=0,last_confirm_update=None)
  return s,{'action':'PROMOTE','resume':latest}
 if improved(s['best_metrics'],metrics):s['stagnant']=0;s['best_metrics']=metrics
 else:s['stagnant']+=1
 if s['stagnant']<3:return s,{'action':'CONTINUE','resume':latest}
 interval=s['interval_id'] or f"{s['previous_prefix']}:{s['prefix']}"
 s['interval_id']=interval
 count=s['insertions'].get(interval,0)
 if s['rollback_counts'].get(interval,0)>=1 and count>=2:
  s['status']='NEEDS_DESIGN';return s,{'action':'STOP','reason':'课程未取得进展，需要新的设计变量'}
 first_rollback=not s['rollback_counts'].get(interval,0)
 s['rollback_counts'][interval]=1;s['stagnant']=0
 if s['previous_prefix']!=s['prefix'] and count<2:
  midpoint=(s['prefix']+s['previous_prefix'])//2
  if midpoint in (s['prefix'],s['previous_prefix']):s['status']='NEEDS_DESIGN';return s,{'action':'STOP','reason':'课程未取得进展，需要新的设计变量'}
  s['insertions'][interval]=count+1;s['return_stack'].append(s['prefix']);s['prefix']=midpoint
 else:
  if s['rollback_counts'].get(interval,0) and count==2:s['status']='NEEDS_DESIGN';return s,{'action':'STOP','reason':'课程未取得进展，需要新的设计变量'}
  s['insertions'][interval]=2 # equal first level permits one rollback, no fictitious midpoint
 s.update(best_metrics=None,best=None,confirmation_streak=0,last_confirm_update=None)
 return s,{'action':'ROLLBACK' if first_rollback else 'SPLIT','resume':(best or state['best']) if first_rollback else latest}
