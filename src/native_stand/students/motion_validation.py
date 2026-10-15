"""Explicit migrated31D Motion PPO0 request and independent scoring."""
import torch
VERSION='student_motion31_validation_v1'
def protocol():
 return {'version':VERSION,'controlled_seconds':30.,'evaluation_seconds':31.52,'tracking_window_controlled_s':[5.,30.],
  'quality_window_controlled_s':[20.,30.],'command_schedule':'fixed throughout controlled episode; no parking certification',
  'commands_mps':[0.,.5,-.5,1.,-1.],'height_m':.34,'MAE_max_mps':.3,'direction_min':.9,'speed_ratio_range':[.8,1.2],
  'zero_horizontal_p95_max_mps':.3,'physical_quality':'v14 posture/contact/height/closure/saturation/geometry checks unchanged',
  'scored_envs':8,'training_allowed':False}

def validate(spec):
 if spec.get('student_motion_validation')!=protocol() or spec.get('student_training') or not spec.get('evaluation_only'):raise ValueError('explicit Motion PPO0 protocol required')
 if spec.get('interface_version')!='multiskill_mcu_v2':raise ValueError('Motion31 interface required')
 from .standing_survival_reward import configuration
 if spec['reward']!=configuration():raise ValueError('diagnostic episode clock recipe differs')
 rows=spec['student_evaluation']['cases']
 if [r.get('command') for r in rows]!=[[v,0.,.34] for v in protocol()['commands_mps']]:raise ValueError('Motion command matrix differs')
 if any(r['role']!='MotionZeroStudent' or r['kind']!='student' or r['family']!='motion_native_normal' or r['seconds']!=31.52 for r in rows):raise ValueError('Motion case scope differs')

def command_tensor(command,current,role):
 if role not in ('MotionZeroStudent','MotionStudent'):raise ValueError('explicit Motion role required')
 t=current.new_tensor(command)
 if t.shape!=(3,) or not torch.isfinite(t).all() or abs(float(t[0]))>4 or abs(float(t[1]))>4 or not .30<=float(t[2])<=.42:raise ValueError('invalid Motion command')
 return t.expand(current.shape[0],-1)

def score(state,posture,geometry,controlled,world_velocity,command):
 from .standing_survival_task import score as base_score
 r=base_score(state,posture,geometry,controlled=controlled,valid=torch.ones(len(state),dtype=torch.bool),world_velocity=world_velocity)
 mask=controlled.bool()&state[:,29].bool();s=state[mask][:3000];checks=dict(r['checks']);target=command[0]
 tracking={'samples':0,'mean_vx_mps':None,'MAE_mps':None,'direction_fraction':None,'speed_ratio':None}
 if len(s)==3000:
  vx=s[500:3000,7];tracking.update(samples=len(vx),mean_vx_mps=float(vx.mean()),MAE_mps=float((vx-target).abs().mean()))
  if target:
   direction=float((vx*target>0).float().mean());ratio=float(vx.mean()/target);tracking.update(direction_fraction=direction,speed_ratio=ratio)
   checks.pop('horizontal_speed',None);checks.update(tracking_MAE=tracking['MAE_mps']<=.3,direction=direction>=.9,speed_gain=.8<=ratio<=1.2)
 r.update(version=VERSION,checks=checks,tracking=tracking,command=command,accepted=all(checks.values()),
  failed_checks=[k for k,v in checks.items() if not v],capability_scope='single evaluation seed, fixed command30s Motion diagnostic; no parking or high-speed certification')
 return r

def finalize(run,spec,status):
 """Monitor-owned compact report after exact ledger reconciliation."""
 from pathlib import Path
 import json
 from native_stand.command_v6.completion import write,read,sha,identity
 run=Path(run);terminal=read(run/'terminal_report.json',{});rows=[]
 for c in terminal.get('conditions',[]):
  if c.get('result'):
   p=run/c['result'];d=read(p,{})
   rows.append({'case':c['condition'],'status':c['status'],'result':str(p),'sha256':sha(p),'passed_envs':d.get('passed_envs'),'per_env':d.get('per_env',[])})
 report={'event_id':identity({'attempt':terminal.get('attempt_id'),'run':str(run)})[:24],'status':status,'online_PPO':0,
  'accepted':status=='COMPLETED' and len(rows)==len(spec['student_evaluation']['cases']) and all(r['passed_envs']==8 for r in rows),'conditions':rows,'failure':terminal.get('failure')}
 candidate={'checkpoint':spec['source_checkpoint'],'sha256':spec['source_sha256'],'PPO':0,'capability_scope':'single seed fixed-command validation only'}
 write(run/'candidate_selection.json',{'source_baseline':candidate,'best_observed_candidate':candidate,
  'best_new_evaluated_candidate':None,'accepted_candidate':candidate if report['accepted'] else None})
 write(run/'analysis.json',report)
 text=['# Motion31 PPO0 validation',f'Status: {status}; accepted: {report["accepted"]}; PPO0',f'Failure: {report["failure"]}']
 for r in rows:text.append(f"{r['case']['case_id']}: {r['passed_envs']}/8; raw evidence: {r['result']}")
 (run/'completion_report.md').write_text('\n\n'.join(text)+'\n')
 write(run/'report_ready.json',{'event_id':report['event_id'],'status':'report_ready','report_sha256':sha(run/'completion_report.md')})
