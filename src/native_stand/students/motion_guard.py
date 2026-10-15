"""Explicit-data Motion assessment and tolerant per-command retention policy."""
import copy,math
VERSION='motion31_absolute_posture_retention_v1'
ASSESSMENT='motion31_absolute_posture_assessment_v4'
def configuration():
 return {'version':VERSION,'adaptation_updates':300,'evaluation_every_updates':250,'consecutive_failures':3,
  'pitch_hold_abs_max_rad':.1,'roll_hold_abs_max_rad':.05,'tracking_MAE_stop_mps':.5,'tracking_MAE_increase_stop_mps':.2,
  'direction_stop_below':.8,'zero_horizontal_p95_stop_mps':.5,'survival_stop_below_envs':6,'expected_envs':8,
  'relative_posture':'diagnostic only','unknown':'blocks promotion; does not count as behavior regression',
  'runtime_fault':'stop immediately; individual ordinary episode failures remain learning samples'}
def protocol():
 from .motion_training import protocol as base
 p=base(quality=True);p.update(version=ASSESSMENT,absolute_posture=configuration(),posture_note='absolute hold maxima pitch<=.1 roll<=.05; relative deltas diagnostic only')
 return p

def assess(result,posture,state,controlled,world_velocity):
 """Same full30s / hold10..18s / zero20..30s, no shortened failure window."""
 p=protocol();r=copy.deepcopy(result);mask=controlled.bool()&state[:,29].bool();q=posture[mask];w=world_velocity[mask]
 r['legacy_checks']=dict(r['checks']);r['legacy_accepted']=r['accepted'];r['version']=ASSESSMENT
 for key in ('pitch_source_guard','roll_source_guard'):r['checks'].pop(key,None)
 complete=len(q)>=3000
 r['checks']['absolute_posture_complete_window']=complete
 if complete:
  q=q[1000:1800];pitch=float(q[:,0].abs().max());roll=float(q[:,1].abs().max())
  r['tracking'].update(pitch_hold_abs_max_rad=pitch,roll_hold_abs_max_rad=roll)
  r['tracking']['horizontal_steady_p95_mps']=float(__import__('torch').quantile(w[2000:3000,:2].norm(dim=-1),.95))
  r['checks'].update(pitch_absolute_quality=pitch<=.1,roll_absolute_quality=roll<=.05)
 else:r['checks'].update(pitch_absolute_quality=False,roll_absolute_quality=False)
 r.update(accepted=all(r['checks'].values()),failed_checks=[k for k,v in r['checks'].items() if not v],relative_posture_scope='diagnostic only')
 return r

def advance(state,records,source_records,update,policy=None):
 """Never mutate evidence; missing evidence cannot pass or mimic regression."""
 c=configuration() if policy is None else policy
 if c!=configuration():raise ValueError('unknown retention policy')
 if type(update) is not int or update<0 or len(records)!=len(source_records):raise ValueError('guard update/matrix differs')
 if state and update<=state.get('last_update',-1):raise ValueError('guard update must advance')
 if state and set(state)-{'last_update','commands','version'}:raise ValueError('guard state fields differ')
 out={'version':VERSION,'last_update':update,'commands':{}};decisions=[];stop=False
 for candidate,source in zip(records,source_records):
  command=candidate.get('case',{}).get('command');original=source.get('case',{}).get('command')
  if not command or command!=original:raise ValueError('retention command identity differs')
  key=','.join(map(str,command));rows=candidate.get('per_env',[]);baseline=source.get('per_env',[]);reasons=[];known=len(rows)==len(baseline)==8
  if known:
   ids=[r.get('env',r.get('env_id')) for r in rows];bids=[r.get('env',r.get('env_id')) for r in baseline]
   known=ids==bids and len(set(ids))==8
  if known and (any(type(r.get('survival_passed')) is not bool or type(r.get('accepted')) is not bool for r in rows+baseline)):known=False
  if known and any(r.get('checks',{}).get('runtime_fault') is True or r.get('runtime_fault') is True for r in rows):
   stop=True;reasons.append('runtime_fault')
  retained=known and all(r.get('accepted') is True for r in baseline)
  if known and retained:
   if sum(r.get('survival_passed') is True for r in rows)<6:reasons.append('survival')
   for r,b in zip(rows,baseline):
    t=r.get('tracking',{});bt=b.get('tracking',{})
    fields=['MAE','direction'] if command[0] or command[1] else ['horizontal_steady_p95_mps']
    for f in fields:
     value=t.get(f);old=bt.get(f)
     if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in (value,old)):known=False;continue
     if f=='MAE' and value>.5 and value-old>=.2:reasons.append('tracking')
     if f=='direction' and value<.8:reasons.append('direction')
     if f=='horizontal_steady_p95_mps' and value>.5:reasons.append('zero_drift')
    for f,limit in (('pitch_hold_abs_max_rad',.1),('roll_hold_abs_max_rad',.05)):
     v=t.get(f)
     if not isinstance(v,(int,float)) or not math.isfinite(v):known=False
     elif v>limit:reasons.append(f)
  # Only fixed scheduled checks after adaptation may accumulate failures.
  eligible=update>=c['adaptation_updates'] and update%c['evaluation_every_updates']==0
  old=(state or {}).get('commands',{}).get(key,0)
  if eligible and state and state['last_update']!=update-c['evaluation_every_updates']:old=0
  count=old
  if eligible:count=old+1 if known and retained and reasons else 0
  out['commands'][key]=count
  stop|=bool(eligible and count>=3)
  decisions.append({'command':command,'evidence':'KNOWN' if known else 'UNKNOWN','retained_source':retained,'adaptation':update<300,'scheduled_check':eligible,'reasons':sorted(set(reasons)),'consecutive':count,'promotion_allowed':known and all(r.get('accepted') is True for r in rows)})
 return out,{'stop':stop,'decisions':decisions,'policy':c}
