"""Explicit dual-policy coordinates and finite-time handoff scoring, CPU safe."""
import torch
from native_stand.command_v6.domain.contract import frame,history,targets,LEG_COLUMNS
from native_stand.recovery.min_height import protocol,entry_mask


def encode_executed(legs,wheels,reference,*,leg_scale,wheel_scale):
    if legs.shape[-1]!=4 or wheels.shape!=legs.shape[:-1]+(2,) or reference.shape!=legs.shape[:-1]+(6,):raise ValueError('Physical target coordinates differ')
    raw=torch.zeros_like(reference);raw[...,list(LEG_COLUMNS)]=(legs-reference[...,list(LEG_COLUMNS)])/leg_scale;raw[...,[2,5]]=wheels/wheel_scale
    clipped=raw.clamp(-1,1)
    return {'raw':raw,'clipped':clipped,'information_loss':raw-clipped,'outside':raw.abs()>1}


def motion_frame(angular,gravity,q,dq,executed_legs,executed_wheels,reference,motion_history,reset,command=None):
    previous=encode_executed(executed_legs,executed_wheels,reference,leg_scale=.5,wheel_scale=100.)
    command=q.new_tensor([0.,0.,.40]).expand(q.shape[0],-1) if command is None else command
    if command.shape!=(q.shape[0],3):raise ValueError('Motion command shape differs')
    current=frame(angular,gravity,command,q,dq,previous['clipped'],reference)
    updated=history(motion_history,current,reset)
    return {'policy':current,'history':updated,'previous_action_readback':previous}


def physical_targets(action,reference,*,controller):
    if controller not in ('Recovery','Motion'):raise ValueError('Unknown controller')
    clipped,legs,wheels=targets(action,reference,leg_scale=1.6 if controller=='Recovery' else .5,combined_radius=0.,wheel_scale=100.)
    return legs,wheels


def score(state,posture,motion_control,*,dt=.01,max_settle_s=2.,vx_max=.5,vy_max=.02,yaw_max=.03,policy_time_s=None,schema="recovery_policy_trace_v1",configuration=None,entry_extra=None):
    """One first-episode trace; Motion-on mask must be chronological, no stitching."""
    if state.ndim!=2 or state.shape[-1]!=39 or posture.shape!=(len(state),10) or motion_control.shape!=(len(state),):raise ValueError('Explicit handoff traces required')
    from .handoff_protocol import declaration,SCHEMA,validate_protocol
    cfg=validate_protocol(configuration) if configuration else declaration()
    if configuration is not None:max_settle_s=cfg['settle_s']
    result={'accepted':False,'version':cfg['version'],'entry_index':None,'hold_complete':False,'strict_vx_0p02_pass':False}
    if dt!=cfg['dt'] or max_settle_s!=cfg['settle_s'] or schema!=SCHEMA:return {**result,'failed_checks':['protocol_or_schema_conflict']}
    times=state[:,0] if policy_time_s is None else policy_time_s
    if times.shape!=(len(state),) or not torch.isfinite(times).all() or (len(times) and times[0]<=0) or (len(times)>1 and not torch.allclose(times[1:]-times[:-1],torch.full_like(times[1:],dt),atol=2e-6,rtol=0)):
        return {**result,'failed_checks':['invalid_time_axis']}
    if not len(state) or not torch.isfinite(state).all() or not torch.isfinite(posture).all():return {**result,'failed_checks':['missing_or_nonfinite']}
    if len(torch.unique(state[:,31]))!=1:return {**result,'failed_checks':['episode_stitched']}
    ids=torch.where(motion_control)[0]
    if not len(ids):return {**result,'failed_checks':['not_switched']}
    start=int(ids[0])
    if bool(state[:start,3:5].bool().any()):return {**result,'failed_checks':['failed_before_switch']}
    if not motion_control[start:].all():return {**result,'failed_checks':['controller_not_continuous']}
    p=protocol();elig=entry_mask(state[:,6],posture[:,:2],state[:,15],state[:,10:12],state[:,13],state[:,29].bool(),p)
    if entry_extra is not None:
        if entry_extra.shape!=elig.shape or entry_extra.dtype!=torch.bool:raise ValueError('explicit additional entry gate shape/type differs')
        elig=elig&entry_extra
    dwell=0;entry=None
    for i in range(start,min(len(state),start+round(max_settle_s/dt))):
        dwell=dwell+1 if bool(elig[i]) else 0
        if dwell>=round(.20/dt):entry=i;break
    if entry is None:return {**result,'failed_checks':['not_settled_within_2s']}
    stop=entry+1+round(cfg['hold_s']/dt);result['entry_index']=entry;result['settle_s']=float(times[entry]-times[start]+dt)
    if stop>len(state):return {**result,'failed_checks':['incomplete_hold']}
    s=state[entry+1:stop];a=posture[entry+1:stop];failed=[]
    checks={'height':bool((s[:,6]>=.30).all()),'level_peak':bool((a[:,:2].abs()<=.15).all()),'level_mean':bool((a[:,:2].abs().mean(0)<=.10).all()),'tilt':bool((s[:,15]<=.18).all()),'contact':bool((s[:,10:12]>2).all()),'clearance':bool((s[:,13]>0).all()),'closure':bool((s[:,12]<=.005).all()),'saturation':bool(s[:,17].mean()<=.05),'vx':bool(s[:,7].abs().mean()<=vx_max),'vy':bool(s[:,8].abs().mean()<=vy_max),'yaw':bool(s[:,9].abs().mean()<=yaw_max),'runtime':not bool(state[start:stop,4].bool().any()),'early_failure':not bool(state[start:stop,3].bool().any()),'all_samples_valid':bool(s[:,29].bool().all()) and bool((s[:,32]!=7).all())}
    failed=[k for k,v in checks.items() if not v]
    return {**result,'strict_vx_0p02_pass':bool(s[:,7].abs().mean()<=cfg['strict_vx']),'velocity_means':[float(s[:,j].abs().mean()) for j in (7,8,9)],'accepted':not failed,'hold_complete':True,'hold_index_half_open':[entry+1,stop],'checks':checks,'failed_checks':failed}


def scan_conditions(candidates):
    if len(candidates)!=4 or len(set(candidates))!=4:raise ValueError('Exactly four distinct Recovery identities required')
    return [{'kind':'normal_motion_baseline','recovery':None,'switch_s':0.}, {'kind':'direct_swing_motion','recovery':None,'switch_s':0.}]+[{'kind':'recovery_prefix_then_motion','recovery':c,'switch_s':t} for t in (.10,.25,.50,1.,2.) for c in candidates]
