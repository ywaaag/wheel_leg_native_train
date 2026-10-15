"""Frozen stages, schedule, scoring and block initialization; pure explicit data."""
import torch
VERSION='student_motion31_training_v1'
SOURCE='a7a1c6f4323116507ad44efc746f4713e134d11cd581d193e5fd276bb5af1266'
STAGES=(('L1',1.),('L2',2.),('L3',3.),('L4',4.),('Y1',1.),('Y2',2.),('Y4',4.))
SMOKE5_PROFILE='motion31_quality_short_wiring5_v1'
def short_wiring():
 return {'version':SMOKE5_PROFILE,'updates':5,'critic_warmup_updates':4,'scope':'short wiring only, not full episode or survival acceptance',
  'episode_reset_required':False,'normal_timeout_required':False,'formal_warmup_updates':5,
  'mandatory':['actual_actor_update','actual_critic_update','nonzero_reward','all_cohort_hold_samples','checkpoint_roundtrip','independent_evaluation_no_runtime_fault']}

def phase_warmup(recipe,phase):
 return recipe['smoke_wiring']['critic_warmup_updates'] if phase=='smoke' and recipe.get('smoke_wiring') else recipe['warmup_updates_per_phase']
def commands(stage):
 if type(stage) is not int or not 0<=stage<len(STAGES):raise ValueError('invalid Motion stage')
 speeds=[.5,1.]+[float(v) for v in (2,3,4) if stage>=v-1]
 result=[[0.,0.]]+[[sign*v,0.] for v in speeds for sign in (1,-1)]
 if stage>=4:result += [[0.,sign*v] for v in (1.,2.,4.)[:stage-3] for sign in (1,-1)]
 return result
def stage_config(stage,envs=64):
 if envs not in (64,512):raise ValueError('Motion envs must be explicit64 or512')
 values=commands(stage);counts=[16]+[0]*(len(values)-1)
 current=[[sign*STAGES[stage][1],0.] if stage<4 else [0.,sign*STAGES[stage][1]] for sign in (1,-1)]
 old=[i for i,v in enumerate(values) if i and v not in current]
 for i,v in enumerate(values):
  if v in current:counts[i]=12
 #24 old slots, paired allocation, deterministic remainder by lower endpoints.
 for pair in range(12):
  j=(pair%(len(old)//2))*2;counts[old[j]]+=1;counts[old[j+1]]+=1
 counts=[n*(envs//64) for n in counts]
 slots=[i for i,n in enumerate(counts) for _ in range(n)]
 return {'id':stage,'name':STAGES[stage][0],'commands':values,'weights':[n/envs for n in counts],
  'sampling_mode':'fixed_slots','sampling_slots':slots,'enforce_whitelist':True,'slot_counts':counts}
PREVIEW_VERSION='motion31_manual_preview_v1'
def preview_stage_config(stage):
 """One-environment manual preview stage; never reuses training slots or the whitelist."""
 if type(stage) is not int or not 0<=stage<len(STAGES):raise ValueError('invalid Motion stage')
 values=commands(stage);counts=[1]+[0]*(len(values)-1)
 return {'id':stage,'name':STAGES[stage][0],'commands':values,'weights':counts,
  'sampling_mode':'fixed_slots','sampling_slots':[0],'enforce_whitelist':False,'slot_counts':counts,
  'preview':True}
def preview_command(vx,yaw,height,*,device=None):
 """Single preview command source; same [vx,yaw,height] triple the Actor columns scale."""
 values=(float(vx),float(yaw),float(height))
 if not all(isinstance(v,float) for v in values):raise ValueError('finite preview command required')
 return torch.tensor([list(values)],device=device)
def preview_declaration(stage,max_speed,max_yaw_speed):
 """Explicit manual-preview scope; no quota, ledger or capability claim."""
 if not 0<max_speed<=4 or not 0<=max_yaw_speed<=4:raise ValueError('preview caps must fit (0,4]')
 return {'version':PREVIEW_VERSION,'stage':stage,'envs':1,'max_speed_mps':float(max_speed),
  'max_yaw_rad_s':float(max_yaw_speed),
  'scope':'manual keyboard/panel input on the shared CommandEnv; physics, PD, action scale, height command,'
  ' reward configuration and scoring stay unchanged; preview is not capability certification'}
def declaration(source_sha=SOURCE,stage=0,*,reward_version=None):
 from .motion_tracking_reward import configuration
 from .motion_privileged import VERSION as PRIV
 result={'version':VERSION,'source_actor_sha256':source_sha,'critic_privileged_version':PRIV,'stage':stage,
 'reward':configuration() if reward_version is None else configuration(reward_version),'training_family':'motion_native_normal','training_yaw_rad':.01,'target_height_m':.34,
 'train_schedule_s':[.5,1.,25.5,1.],'parking_s':2.,'environment_seconds':31.52,
 'milestones':[100,200,300],'selected_rollouts_smoke':[],'selected_rollouts_formal':[],
 'final_seeds':[20261014,20261015,20261016],'storage_max_bytes':2*2**30,'warmup_updates_per_phase':5,
 'BC_coefficient':0.,'fixed_log_std':True,'physical_std_leg_rad':.05,'physical_std_wheel_rad_s':2.,
 'critic':'fresh49D_on_first_block_full_resume_later','optimizer':'fresh_Adam_on_first_block_full_resume_later',
 'selection_scope':'Motion tracking plus parking/physical/source posture guard; not stable standing certification'}
 from .motion_tracking_reward import SUCCESSOR_VERSION
 if reward_version==SUCCESSOR_VERSION:
  result.update(train_schedule_s=[.5,1.,28.5,0.],parking_s=0.,
   selection_scope='sustained tracking plus zero retention/physical/posture; parking diagnostic only; not standing certification')
 return result
def protocol(quality=False,successor=False):
 result={'version':'motion31_training_assessment_v1','controlled_seconds':30.,'seconds':31.52,
 'schedule_s':[2.,8.,8.,8.],'holding_window_s':[10.,18.],'parking_window_s':[26.,30.],
 'tracking_MAE_max':.3,'direction_min':.95,'gain_range':[.8,1.2],'zero_horizontal_p95_max':.3,
 'hold_fraction_above_70pct_min':.8,'final_endpoint_mean_range':[3.6,4.4],
 'final_endpoint_sustained_threshold':3.8,'final_endpoint_sustained_seconds':3.,
 'parking_horizontal_mean_max':.3,'parking_yaw_mean_max':.3,'height_mean_band_m':[.30,.38],
 'contact_min':.95,'saturation_max':.05,'closure_max_m':.005,'tilt_peak_max_rad':.50,
 'posture_relative_tolerance_rad':0.,'posture_note':'same-command/env source hold pitch and roll; no worsening; not standing quality',
 'fixed_scored_envs':8,'confirmations_required':2}
 if quality:
  result['version']='motion31_quality_assessment_v2'
  result['posture_quality']={'roll_hold_abs_mean_max_rad':.10,'roll_hold_abs_p95_max_rad':.20,'leg_difference_hold_mae_max_m':.02,
   'wheel_offset_hold_mae_max_m':.04,'joint_mirror_hold_mae_max_rad':.10,'terminated_quality_is_task_failure':True,
   'pitch_note':'retain physical tilt and source-relative guard; allow acceleration lean, not zero roll/leg symmetry relaxation'}
 if successor:
  if not quality:raise ValueError('successor requires posture-quality protocol')
  result.update(version='motion31_hold_level_assessment_v3',parking_required=False,parking_scope='diagnostic only; identical original full evaluation schedule')
 return result
def effective(target,age,training=False,config=None):
 from native_stand.command_v6.domain.command_schedule import effective as schedule
 times=(config or declaration())['train_schedule_s'] if training else protocol()['schedule_s']
 if training and times[3]==0:
  # No exit division by zero; command remains at target until normal timeout.
  gain=((age-times[0])/times[1]).clamp(0.,1.)
  return torch.cat((target*gain[:,None],torch.full_like(target[:,:1],.34)),-1)
 return schedule(target,age,height=.34,entry=times[0],ramp=times[1],hold=times[2],exit=times[3])
def score(state,posture,geometry,controlled,world_velocity,target):
 from .survival_probe import score as base
 from native_stand.recovery.standing import longitudinal_geometry
 r=base(state,posture,geometry,controlled=controlled,valid=torch.ones(len(state),dtype=torch.bool));mask=controlled.bool()&state[:,29].bool();s=state[mask][:3000];p=posture[mask][:3000];g=geometry[mask][:3000];w=world_velocity[mask][:3000];cfg=protocol()
 checks={'survival30':r['survival_passed']};tracking={}
 if len(s)==3000:
  h=s[1000:1800];ph=p[1000:1800];park=s[2600:3000];wp=w[2600:3000];axis=9 if target[1] else 7;T=target[1] if target[1] else target[0];speed=h[:,axis]
  tracking={'mean_signed_speed':float(speed.mean()),'MAE':float((speed-T).abs().mean()),'direction':float((speed*T>0).float().mean()) if T else None,
   'gain':float(speed.mean()/T) if T else None,'parking_horizontal_mean_mps':float(wp[:,:2].norm(dim=-1).mean()),'parking_yaw_abs_mean_rad_s':float(park[:,9].abs().mean()),
   'pitch_hold_abs_mean_rad':float(ph[:,0].abs().mean()),'roll_hold_abs_mean_rad':float(ph[:,1].abs().mean()),
   'wheel_offset_hold_mae_m':float(longitudinal_geometry(g[1000:1800,:6].reshape(-1,2,3),g[1000:1800,6:9]).abs().mean())}
  checks.update(height=cfg['height_mean_band_m'][0]<=float(h[:,6].mean())<=cfg['height_mean_band_m'][1],contact=float((h[:,10:12]>2).all(-1).float().mean())>=.95,
   saturation=float(h[:,17].mean())<=.05,closure=float(s[:,12].max())<=.005,clearance=float(s[:,13].min())>0,
   tilt=float(s[:,15].max())<=.50,
   parking=tracking['parking_horizontal_mean_mps']<=.3 and tracking['parking_yaw_abs_mean_rad_s']<=.3)
  if T:
   signed=speed*(1 if T>0 else -1);tracking['fraction_above_70pct']=float((signed>=abs(T)*.7).float().mean())
   checks.update(tracking=tracking['MAE']<=.3,direction=tracking['direction']>=.95,gain=.8<=tracking['gain']<=1.2,sustained_fraction=tracking['fraction_above_70pct']>=.8)
   if abs(T)==4:
    average=signed.unfold(0,100,1).mean(-1);above=average>=3.8;run=maximum=0
    for flag in above.tolist():
     run=run+1 if flag else 0;maximum=max(maximum,run)
    tracking['sustained_sliding_mean_seconds']=maximum*.01
    checks.update(final_mean=3.6<=float(signed.mean())<=4.4,final_sustained=maximum>=300)
  else:checks.update(zero_horizontal=float(torch.quantile(w[2000:3000,:2].norm(dim=-1),.95))<=.3,zero_yaw=float(s[2000:3000,9].abs().mean())<=.3)
  if target[1]:checks['in_place_translation']=float(w[1000:1800,:2].norm(dim=-1).mean())<=.3
 r.update(version=cfg['version'],accepted=all(checks.values()),checks=checks,failed_checks=[k for k,v in checks.items() if not v],tracking=tracking,
  capability_scope='slow-ramp Motion acceptance; not stationary posture certification',standing_quality_certified=False)
 return r
def compare_source(candidate,source):
 """Exact same command/env comparison; unavailable baseline is UNKNOWN, not pass."""
 if len(candidate['per_env'])!=len(source['per_env']):raise ValueError('source/candidate scored count differs')
 for row,baseline in zip(candidate['per_env'],source['per_env']):
  if row.get('env_id',row.get('env'))!=baseline.get('env_id',baseline.get('env')):raise ValueError('source/candidate environment order differs')
  checks=row['checks'];delta={}
  for axis in ('pitch','roll'):
   field=axis+'_hold_abs_mean_rad';x=row.get('tracking',{}).get(field);y=baseline.get('tracking',{}).get(field)
   delta[axis]=None if x is None or y is None else x-y
   checks[axis+'_source_guard']=delta[axis] is not None and delta[axis]<=protocol()['posture_relative_tolerance_rad']
  row['source_posture_delta_rad']=delta;row['accepted']=all(checks.values());row['failed_checks']=[k for k,v in checks.items() if not v]
 return candidate
def choose(candidates):
 def rank(c):
  es=c['per_env'];return (sum(e['accepted'] for e in es),sum(e['survival_passed'] for e in es),-max((e.get('tracking',{}).get('MAE',99.) for e in es),default=99.))
 new=[c for c in candidates if c['update']>0];passing=[c for c in new if c.get('complete_matrix') and all(e['accepted'] for e in c['per_env'])]
 streak=[]
 for c in new:
  if c in passing:streak.append(c)
  else:streak=[]
 confirmed=len(streak)>=2 and streak[-1]['update']-streak[-2]['update']>=100
 best=max(candidates,key=rank);accepted=max(streak,key=rank) if confirmed else None
 best_new=max(new,key=rank) if new else None
 return {'source':candidates[0],'latest':candidates[-1],'best_new':best_new,'best_overall':best,'best_observed_candidate':best,'accepted_candidate':accepted,'standing_quality_certified':False,
  'source_baseline':candidates[0],'latest_checkpoint':candidates[-1],'best_new_evaluated_candidate':best_new,
  'accepted_by_stage':{str(accepted.get('stage',0)):accepted} if accepted else {},'fallback_checkpoint':candidates[0],
  'final_multi_seed_certified':False}
