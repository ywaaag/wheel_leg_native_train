"""Versioned minimum-height rise/hold task; pure explicit-input Torch domain."""
import math
import torch

VERSION='autonomous_rise_min_height_v2'

def protocol():
    from native_stand.recovery.task_protocol import resolve
    seconds=resolve({'rising_task':{'version':VERSION,'recovery_deadline_s':11.5,'post_rise_hold_s':10.}})['evaluation_seconds']
    return dict(version=VERSION,protocol_identity=VERSION,objective='survival_level',
        minimum_height_m=.30,entry_dwell_s=.20,recovery_deadline_s=11.5,post_rise_hold_s=10.,
        level_mean_max_rad=.10,level_peak_max_rad=.15,peak_tilt_max_rad=.18,
        dual_contact_min_n=2.,chassis_clearance_min_m=0.,saturation_max=.05,closure_max_m=.005,
        seconds=seconds,steady_window_s=[0.,seconds],window_alignment='first_confirmed_entry_then_next1000_samples')

def entry_mask(height,angles,tilt,contact,clearance,valid,p):
    return (valid&(height>=p['minimum_height_m'])&(angles.abs()<=p['level_mean_max_rad']).all(-1)&
        (tilt<=p['peak_tilt_max_rad'])&(contact>p['dual_contact_min_n']).all(-1)&(clearance>0))

def hold_metrics(height,angles,tilt,contact,clearance,closure,saturation,p):
    hard=((height>=p['minimum_height_m'])&(contact>p['dual_contact_min_n']).all(-1)&(clearance>0)&
        (angles.abs()<=p['level_peak_max_rad']).all(-1)&(tilt<=p['peak_tilt_max_rad'])&
        (closure<=p['closure_max_m']))
    return hard

def height_terms(height):
    return {'lift':((height-.168)/(.30-.168)).clamp(0,1),
            'standing_height':((height-.30)/(.34-.30)).clamp(0,1)}

class RiseHold:
    """First entry latches once; hold starts on NEXT interval, exactly1000 samples."""
    def __init__(self,n,device,*,dt,p):
        self.p=p;self.dt=dt;self.required=round(p['post_rise_hold_s']/dt);self.entry_required=round(p['entry_dwell_s']/dt)
        with torch.inference_mode(False):
            self.age=torch.zeros(n,device=device,dtype=torch.float64);self.dwell=torch.zeros(n,device=device,dtype=torch.long)
            self.entry=torch.full_like(self.age,-1.);self.count=torch.zeros_like(self.dwell)
            self.angle_sum=torch.zeros((n,2),device=device);self.saturation=torch.zeros_like(self.age)
            self.hard_failed=torch.zeros(n,device=device,dtype=torch.bool);self.sent=torch.zeros_like(self.hard_failed)
            self.prefix=torch.zeros_like(self.dwell);self.prefix_closed=torch.zeros_like(self.hard_failed)
    def reset(self,ids):
        for x in (self.age,self.dwell,self.count,self.angle_sum,self.saturation,self.hard_failed,self.sent,self.prefix,self.prefix_closed):x[ids]=0
        self.entry[ids]=-1
    def observe(self,h,a,t,c,g,cl,sat,*,active,valid,safety_failed,fault):
        self.age+=active*self.dt
        holding=active&(self.entry>=0)&~self.sent
        hard=hold_metrics(h,a,t,c,g,cl,sat,self.p)&valid
        self.hard_failed|=holding&~hard
        self.prefix_closed|=holding&~hard
        self.prefix+=holding&~self.prefix_closed
        self.count+=holding
        self.angle_sum+=a.abs()*holding[:,None]
        self.saturation+=sat*holding
        searching=active&(self.entry<0)&~self.sent
        eligible=entry_mask(h,a,t,c,g,valid,self.p)
        # Preserve normal persistent storage across inference evaluation and reset.
        self.dwell.copy_(torch.where(searching&eligible,self.dwell+1,torch.zeros_like(self.dwell)))
        confirmed=searching&(self.dwell>=self.entry_required)&(self.age<=self.p['recovery_deadline_s']+1e-5)
        self.entry[confirmed]=self.age[confirmed]
        expired=searching&~confirmed&(self.age>=self.p['recovery_deadline_s']-1e-5)
        complete=holding&(self.count>=self.required)
        passed=(complete&~self.hard_failed&
            (self.angle_sum/self.count.clamp_min(1)[:,None]<=self.p['level_mean_max_rad']).all(-1)&
            (self.saturation/self.count.clamp_min(1)<=self.p['saturation_max']))
        end=(expired|complete|safety_failed|fault)&~self.sent
        success=end&passed&~safety_failed&~fault
        failure=end&~success&~fault
        self.sent|=end
        return success,failure,end,fault

def score(series,posture,*,dt,p,initial_valid,terminated=False,terminal_success=False,runtime_fault=False):
    """Offline first episode scoring, also accepts exact task-success terminal."""
    if not math.isfinite(dt) or abs(dt-.01)>1e-10:raise ValueError('Minimum-height v2 requires100Hz policy samples')
    if series.ndim!=2 or series.shape[1]!=39 or posture.shape!=(len(series),10) or not len(series):
        return {'accepted':False,'evidence_status':'MISSING_EVIDENCE','failed_checks':['missing_full_trace']}
    if not torch.isfinite(series).all() or not torch.isfinite(posture).all():
        return {'accepted':False,'evidence_status':'INVALID','failed_checks':['nonfinite_trace']}
    eligible=entry_mask(series[:,6],posture[:,:2],series[:,15],series[:,10:12],series[:,13],series[:,29].bool()&(series[:,0]>0)&(series[:,32]!=7),p)
    run=0;confirm=None
    for i in range(len(series)):
        run=run+1 if bool(eligible[i]) else 0
        if run>=round(p['entry_dwell_s']/dt) and float(series[i,0])<=p['recovery_deadline_s']+1e-5:
            confirm=i;break
    base={'accepted':False,'evidence_status':'COMPLETE_TRACE','entry_confirmation_index':confirm,
        'recovery_s':float(series[confirm,0]) if confirm is not None else None,
        'post_rise_window_s':None,'post_rise_observed_s':0.,'post_rise_metrics':None,
        'standing_metrics_scope':'pre_entry_diagnostic_only','post_rise_evidence_status':'NOT_ENTERED',
        'diagnostic_hold_prefix_s':0.,'height_peak_m':float(series[:,6].max()),'height_gain_m':float(series[:,6].max()-series[0,6])}
    if confirm is None:return {**base,'checks':{'standing_entry':False},'failed_checks':['standing_entry'],'metrics':measure(series,posture,p)}
    start=confirm+1;finish=start+round(p['post_rise_hold_s']/dt);s=series[start:finish];a=posture[start:finish,:2]
    from native_stand.command_v6.domain.time_axis import interval,event
    base['entry_time_axis']=event(confirm,dt=dt,recovery_seconds=float(series[confirm,0]))
    base['observed_hold_time_axis']=interval(start,min(finish,len(series)),dt=dt,total_samples=len(series))
    base['requested_hold_index_half_open']=[start,finish]
    base.update(post_rise_window_s=[start*dt,finish*dt],post_rise_observed_s=len(s)*dt,
        standing_metrics_scope='first_confirmed_entry_hold_window',post_rise_evidence_status='COMPLETE' if finish<=len(series) else 'INCOMPLETE')
    if not len(s):return {**base,'checks':{'continuous':False},'failed_checks':['continuous'],'metrics':{}}
    hard=hold_metrics(s[:,6],a,s[:,15],s[:,10:12],s[:,13],s[:,12],s[:,17],p)
    bad=torch.nonzero(~hard).flatten();base['diagnostic_hold_prefix_s']=(int(bad[0]) if len(bad) else len(s))*dt
    metrics=measure(s,posture[start:finish],p)
    checks={'same_episode':bool((series[:,31]==series[0,31]).all()),
        'valid_hold_samples':bool(s[:,29].bool().all()),
        'policy_intervals':bool(((s[1:,0]-s[:-1,0]-.01).abs()<=2e-4).all()),
        'continuous':finish<=len(series),
        'terminal_consistent':not terminated or (finish==len(series)),
        'initial_valid':initial_valid,'runtime_fault':not runtime_fault,'finite':True,
        'terminal_certificate':not (terminated and finish==len(series)) or terminal_success,
        'recovery_deadline':base['recovery_s']<=p['recovery_deadline_s']+1e-5,
        'continuous_height':bool((s[:,6]>=p['minimum_height_m']).all()),
        'continuous_contact':bool((s[:,10:12]>2).all()),'positive_clearance':bool((s[:,13]>0).all()),
        'pitch':metrics['mean_abs_pitch_rad']<=p['level_mean_max_rad'] and metrics['peak_abs_pitch_rad']<=p['level_peak_max_rad'],
        'roll':metrics['mean_abs_roll_rad']<=p['level_mean_max_rad'] and metrics['peak_abs_roll_rad']<=p['level_peak_max_rad'],
        'tilt':metrics['peak_tilt_rad']<=p['peak_tilt_max_rad'],'saturation':metrics['saturation_fraction_policy']<=p['saturation_max'],
        'closure':bool((series[:,12]<=p['closure_max_m']).all())}
    return {**base,'accepted':all(checks.values()),'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],
        'metrics':metrics,'post_rise_metrics':metrics}

class PhaseCoverage:
    """Per-pose and mutually exclusive phase transition/reward totals, no IO/RNG."""
    PHASES=('pre_entry','hold_0_2','hold_2_5','hold_5_10')
    def __init__(self,poses,device):
        with torch.inference_mode(False):
            self.count=torch.zeros((poses*4,),device=device,dtype=torch.long)
            self.terms={};self.limits=torch.zeros((poses*4,6),device=device)
    def reset(self):
        self.count.zero_();self.limits.zero_()
        for record in self.terms.values():record.zero_()
    def observe(self,pose,phase,active,raw,weighted,saturated):
        ids=pose*4+phase
        self.count.index_add_(0,ids,active.long())
        self.limits.index_add_(0,ids,saturated.float()*active[:,None])
        for key,value in raw.items():
            if key not in self.terms:
                # Rollout collection uses inference mode; reset does not.
                with torch.inference_mode(False):
                    self.terms[key]=torch.zeros((len(self.count),3),device=self.count.device)
            self.terms[key].index_add_(0,ids,torch.stack((value,weighted[key],(value!=0).float()),-1)*active[:,None])
    def summary(self,poses,dt):
        counts=self.count.cpu().tolist();limits=self.limits.cpu().tolist();terms={k:v.cpu().tolist() for k,v in self.terms.items()}
        return [{'pose_id':pose['pose_id'],'family':pose['family'],'phase':name,
            'transition_count':counts[i*4+j],
            'sampled_limit_channel_counts':limits[i*4+j],
            'continuous_reward':{k:{'raw_sum':v[i*4+j][0],'weighted_dt_sum':v[i*4+j][1],
                'weighted_per_second_sum':v[i*4+j][1]/dt,'nonzero_raw_count':v[i*4+j][2],
                'status':'MEASURED' if counts[i*4+j] else 'NO_TRANSITIONS'} for k,v in terms.items()},
            'nonzero_raw_is_not_general_gate_activation':True}
            for i,pose in enumerate(poses) for j,name in enumerate(self.PHASES)]


def oscillation(rows,config):
    """Fixed first-entry+1..2s deterministic target/held-torque window."""
    values=[]
    for row in rows:
        index=row.get('entry_confirmation_index');data=row.get('control_diagnostics_100hz')
        if index is None:values.append(None);continue
        if data is None:raise ValueError('Declared wheel oscillation control trace missing')
        start=index+1+100;window=torch.as_tensor(data[start:start+100])
        if window.shape!=(100,54):values.append(None);continue
        targets=window[:,[20,23]]*100.;effort=window[:,[40,43]]
        delta=targets[1:]-targets[:-1]
        alternating=((delta[1:]*delta[:-1]<0)&(delta[1:].abs()>=config['delta_min_rad_s'])&
                     (delta[:-1].abs()>=config['delta_min_rad_s'])).float().mean(0)
        saturation=(effort.abs()>=5.5-1e-4).float().mean(0)
        values.append(bool(((alternating>=config['alternation_fraction_min'])&
                            (saturation>=config['limit_fraction_min'])).any()))
    return values

class ProgressGuard:
    def __init__(self,source,config):
        self.config=config;self.source_entries=sum(r.get('recovery_s') is not None for r in source['per_env'])
        self.source_oscillation=oscillation(source['per_env'],config)
        self.failures={'entry_loss':0,'new_oscillation':0}
    def observe(self,result):
        entries=sum(r.get('recovery_s') is not None for r in result['per_env'])
        values=oscillation(result['per_env'],self.config)
        bad={'entry_loss':entries<=self.source_entries-self.config['entry_count_drop'],
             'new_oscillation':any(v is True and s is False for v,s in zip(values,self.source_oscillation))}
        for key in bad:self.failures[key]=self.failures[key]+1 if bad[key] else 0
        return {'entries':entries,'source_entries':self.source_entries,'oscillation_per_env':values,
                'consecutive_failures':dict(self.failures),'stop':any(v>=self.config['confirmations'] for v in self.failures.values()),
                'scope':'Declared deterministic 100Hz fixed window; held torque,not all PD samples'}


def measure(s,posture,p):
    a=posture[:,:2]
    return {'height_min_m':float(s[:,6].min()),'height_steady_mean_m':float(s[:,6].mean()),
        'height_in_range_fraction':float((s[:,6]>=p['minimum_height_m']).float().mean()),
        'dual_contact_fraction':float((s[:,10:12]>2).all(-1).float().mean()),
        'mean_abs_pitch_rad':float(a[:,0].abs().mean()),'mean_abs_roll_rad':float(a[:,1].abs().mean()),
        'peak_abs_pitch_rad':float(a[:,0].abs().max()),'peak_abs_roll_rad':float(a[:,1].abs().max()),
        'peak_tilt_rad':float(s[:,15].max()),'saturation_fraction_policy':float(s[:,17].mean()),
        'closure_max_m':float(s[:,12].max()),'chassis_clearance_min_m':float(s[:,13].min()),
        'mean_abs_vx_mps':float(s[:,7].abs().mean()),'mean_abs_vy_mps':float(s[:,8].abs().mean()),
        'mean_abs_yaw_rad_s':float(s[:,9].abs().mean()),'mean_mirror_error_rad':float(posture[:,4:6].abs().mean()),
        'mean_leg_length_difference_m':float((posture[:,2]-posture[:,3]).abs().mean()),
        'mean_support_difference':float(((s[:,10]-s[:,11]).abs()/s[:,10:12].sum(-1).clamp_min(1)).mean()),
        'net_drift_m':float((s[-1,19:21]-s[0,19:21]).norm()),'max_excursion_m':float((s[:,19:21]-s[0,19:21]).norm(dim=-1).max())}
