"""Read-only PPO event/reward review; no simulator or optimizer."""
import argparse,json
from pathlib import Path
import numpy as np,torch
from native_stand.students.data import sha
from native_stand.students.recovery_task import Certificate,reward,FIELDS,configuration
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,POSTURE,VERSION
ROOT=Path(__file__).resolve().parents[1]

def targets(control):
 out=np.zeros((*control.shape[:-1],6),dtype=np.float32)
 out[..., [0,1,3,4]]=control[...,CONTROL['leg_target_after_limit']]
 out[..., [2,5]]=control[...,CONTROL['clipped_action']][...,[2,5]]*100
 return out

def previous(value):
 out=np.empty_like(value);out[..., [0,1,3,4]]=value[...,:4];out[..., [2,5]]=value[...,4:];return out

def angular(root):
 xyz=-root[...,3:6];w=root[...,6:7];v=root[...,10:13]
 return v+2*np.cross(xyz,np.cross(xyz,v)+w*v)

def replay(a,e,ids,reward_configuration=None):
 clock=Certificate(1,'cpu');h0=torch.tensor([a['root_pre'][ids[0],e,2]]);series=[];raw=[];extra=[]
 for i in ids:
  s=torch.tensor(a['state'][i,e])[None];p=torch.tensor(a['posture'][i,e])[None];c=torch.tensor(a['control'][i,e])[None]
  clock.set_velocity(s[:,7:10]);clock.observe(s[:,6],p[:,:2],s[:,15],s[:,10:12],s[:,13],s[:,12],s[:,17],active=torch.ones(1,dtype=torch.bool),valid=s[:,29].bool(),safety_failed=s[:,3].bool(),fault=s[:,4].bool())
  r=reward(s[:,6],h0,p[:,:2],s[:,10:12],s[:,13],c[:,CONTROL['applied_torque']],torch.tensor(previous(a['previous_targets'][i,e]))[None],torch.tensor(targets(a['control'][i,e]))[None],torch.tensor(angular(a['root_post'][i,e]))[None],s[:,7:10],s[:,9],clock.entry>=0,torch.ones(1,dtype=torch.bool),s[:,4].bool(),clock.entry_confirmed,clock.certificate_passed,clock.task_failure,reward_configuration=reward_configuration)
  series.append(np.r_[r['continuous_dt'][0].numpy(),r['events'][0].numpy()]);raw.append(r['raw'][0].numpy());extra.append(float(r['pre_entry_angular_dt'][0]))
 values=np.asarray(series);extra=np.asarray(extra);powers=.99**np.arange(len(ids));return {'continuous_sum':dict(zip(FIELDS,values[:,:6].sum(0).tolist())),'event_sum':values[:,6:].sum(0).tolist(),'pre_entry_angular_sum':float(extra.sum()),'pre_entry_angular_gamma_sum':float((extra*powers).sum()),'return_undiscounted':float(values.sum()+extra.sum()),'return_gamma099':float(((values.sum(1)+extra)*powers).sum()),'discounted_failure_component':float((values[:,8]*powers).sum()),'return_gamma099_without_failure_event':float(((values[:,:8].sum(1)+extra)*powers).sum()),'height_progress_mean':float(np.mean(raw,axis=0)[0]),'support_quality_mean':float(np.mean(raw,axis=0)[1])}

def review(run,output):
 torch.set_num_threads(4);run=Path(run).resolve();output=Path(output).resolve()
 if output.exists():raise FileExistsError(output)
 frozen=run/'source_snapshot/spec.json';spec=json.loads(frozen.read_text())
 if spec['reward']!=configuration(spec['reward'].get('version')):raise ValueError('review reward declaration differs')
 if sha(spec['asset_path'])!=spec['asset_sha256']:raise ValueError('asset identity differs')
 sources={str(frozen):sha(frozen),spec['asset_path']:spec['asset_sha256']};traces={};rows=[]
 for name,phase,start in [('BC','source_eval',0),('teacher','source_eval',4),('update25','formal',0),('update50','formal',4),('update100','formal',8)]:
  groups=1 if name=='teacher' else 4
  for j in range(groups):
   f=run/phase/f'evaluation_{start+j:02}.json';d=json.loads(f.read_text());p=f.parent/d['trace']['path']
   assert d['field_schema']['state']==VERSION and sha(p)==d['trace']['sha256']
   assert d['asset_sha256']==spec['asset_sha256']
   assert sha(d['case']['checkpoint'])==d['case']['sha256']
   sources[str(f)]=sha(f);sources[str(p)]=sha(p);sources[d['case']['checkpoint']]=d['case']['sha256']
   with np.load(p) as z:a={k:z[k] for k in z.files}
   assert np.allclose(np.diff(a['policy_time_s']),.01,atol=1e-7)
   if name!='teacher':
    from native_stand.students.mcu_interface import encode
    mask=a['first_episode_valid']&a['actor_valid'][...,0]
    root=a['root_pre'][mask];rot=-root[:,3:6];w=root[:,6:7]
    def inv(v):return v+2*np.cross(rot,np.cross(rot,v)+w*v)
    gravity=np.zeros_like(root[:,10:13]);gravity[:,2]=-1
    previous_targets=a['previous_targets'][mask]
    q=torch.tensor(a['joint_q_pre'][mask][:,d['field_schema']['active_indices']]);dq=torch.tensor(a['joint_dq_pre'][mask][:,d['field_schema']['active_indices']])
    encoded=encode(torch.tensor(inv(root[:,10:13])),torch.tensor(inv(gravity)),q,dq,torch.tensor(previous_targets[:,:4]),torch.tensor(previous_targets[:,4:]),torch.zeros_like(q),'Recovery',torch.tensor([0.,0.,.4]).expand(len(q),3))
    input_error=float((encoded-torch.tensor(a['actor_input'][mask])).abs().max())
    if input_error>1e-5:raise ValueError('31D input/cache reconstruction differs')
   else:input_error=None
   traces[(name,j)]=a
   for e in range(8):
    ids=np.flatnonzero(a['first_episode_valid'][:,e]&a['actor_valid'][:,e,0]);s=a['state'][ids,e];pstate=a['posture'][ids,e];t=targets(a['control'][ids,e]);ages=np.arange(1,len(ids)+1)*.01
    assert len(ids) and np.all(np.diff(ids)==1) and len(np.unique(s[:,STATE['episode_id']]))==1
    q=a['control'][ids,e,CONTROL['joint_q']];v=angular(a['root_post'][ids,e]);height=s[:,STATE['height_m']];length=pstate[:,2:4]
    def first(mask):return float(ages[np.flatnonzero(mask)[0]]) if mask.any() else None
    windows={}
    for lo,hi in [(0,.25),(.25,.5),(.5,.75),(.75,1.),(1.,2.5)]:
     m=(ages>lo)&(ages<=hi)
     if m.any():windows[f'{lo:g}-{hi:g}']={'height_mean':float(height[m].mean()),'height_peak':float(height[m].max()),'pitch_roll_mean':pstate[m,:2].mean(0).tolist(),'angular_abs_mean':np.abs(v[m]).mean(0).tolist(),'vx_mean':float(s[m,7].mean()),'dual_contact_fraction':float((s[m,10:12]>2).all(1).mean()),'leg_length_mean':length[m].mean(0).tolist(),'target_mean':t[m].mean(0).tolist()}
    row={'model':name,'case_id':d['case']['case_id'],'env':e,'controlled_s':len(ids)*.01,'h0':float(a['root_pre'][ids[0],e,2]),'height_peak_m':float(height.max()),'height_final_m':float(height[-1]),'first_bilateral_short_s':first((length<=.34).all(1)),'first_height030_s':first(height>=.30),'first_tilt060_s':first(s[:,15]>=.60),'last_tilt_rad':float(s[-1,15]),'vx_final':float(s[-1,7]),'displacement_world_xyz':(a['root_post'][ids[-1],e,:3]-a['root_pre'][ids[0],e,:3]).tolist(),'target_jump_mean':np.abs(np.diff(t,axis=0)).mean(0).tolist(),'wheel_torque_limit_fraction':(np.abs(a['control'][ids,e,CONTROL['applied_torque']][:,[2,5]])>=5.5-1e-4).mean(0).tolist(),'terminal':d['per_env'][e]['termination_causes'],'entry':d['per_env'][e]['entry_index'],'accepted':d['per_env'][e]['accepted'],'windows':windows,'reward_replay':replay(a,e,ids,spec['reward'])}
    row['input_reconstruction_max_error']=input_error
    rows.append(row)
 summary={}
 for name in ['BC','teacher','update25','update50','update100']:
  group=[r for r in rows if r['model']==name];summary[name]={k:float(np.mean([r[k] for r in group])) for k in ['controlled_s','height_peak_m','height_final_m','last_tilt_rad','vx_final']};summary[name]['episodes']=len(group);summary[name]['bilateral_short_episodes']=sum(r['first_bilateral_short_s'] is not None for r in group);summary[name]['height030_episodes']=sum(r['first_height030_s'] is not None for r in group);summary[name]['entry']=sum(r['entry'] is not None for r in group);summary[name]['reward']={k:float(np.mean([r['reward_replay'][k] for r in group])) for k in ['return_undiscounted','return_gamma099','discounted_failure_component','return_gamma099_without_failure_event','height_progress_mean','support_quality_mean']}
 alignment=[]
 for candidate in ['update25','update50','update100','teacher']:
  for e in range(8):
   b=traces[('BC',0)];c=traces[(candidate,0)]
   bi=np.flatnonzero(b['first_episode_valid'][:,e]&b['actor_valid'][:,e,0]);ci=np.flatnonzero(c['first_episode_valid'][:,e]&c['actor_valid'][:,e,0]);n=min(len(bi),len(ci));bi=bi[:n];ci=ci[:n]
   delta=np.abs(targets(c['control'][ci,e])-targets(b['control'][bi,e]));state_delta=np.abs(c['posture'][ci,e,:2]-b['posture'][bi,e,:2]);hd=np.abs(c['state'][ci,e,6]-b['state'][bi,e,6])
   def earliest(mask):return (int(np.flatnonzero(mask)[0])+1)*.01 if mask.any() else None
   alignment.append({'candidate':candidate,'env':e,'aligned_controlled_s':n*.01,'first_leg_target_difference_gt010rad_s':earliest((delta[:,[0,1,3,4]]>.10).any(1)),'first_wheel_target_difference_gt10rad_s':earliest((delta[:,[2,5]]>10).any(1)),'first_pitchroll_difference_gt005rad_s':earliest((state_delta>.05).any(1)),'first_height_difference_gt001m_s':earliest(hd>.01),'target_delta_mean_first025s':delta[:25].mean(0).tolist()})
 metrics_path=run/'formal/metrics.jsonl';sources[str(metrics_path)]=sha(metrics_path);m=[json.loads(x) for x in metrics_path.read_text().splitlines()];blocks={}
 for lo,hi in [(1,5),(6,10),(11,25),(26,50),(51,100)]:
  g=m[lo-1:hi];blocks[f'{lo}-{hi}']={'controlled_samples':sum(r['controlled_samples'] for r in g),'effective_actor_samples':sum(r['actor_update_scope']['effective_actor_update_samples'] for r in g),'episode_length_mean_s':float(np.mean([r['episode_duration_mean_s'] for r in g if r['episode_duration_mean_s'] is not None])),'entry_events':sum(r['entry_events'] for r in g),'raw_reward_mean':np.mean([r['reward_raw_mean'] for r in g],0).tolist(),'weighted_density_mean':np.mean([r['reward_weighted_density_mean'] for r in g],0).tolist(),'failure_events':sum(r['reward_events_sum'][2] for r in g),'actor_gradient_norm_mean_pre_clip':float(np.mean([r['actor_update_scope']['actor_gradient_norm_mean'] for r in g])),'return_mean':float(np.mean([r['distributions']['returns']['mean'] for r in g]))}
 report={'version':'student_task_ppo_review_v1','source_run':str(run),'source_SHA':sources,'summary':summary,'per_episode':rows,'aligned_to_BC':alignment,'update_blocks':blocks,'online_PPO':0,'offline_optimizer':0,'clock':'first pre-action controlled sample; post state at t=.01; first episode only','comparison_limits':'Teacher is one native group; four student groups include small yaw. Direct timing alignment describes differences, not causal matched-state interventions. Reward replay hypothetical independent student control includes teacher preparation.'}
 output.mkdir(parents=True);(output/'review.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=review(a.run,a.output);print(json.dumps({'summary':r['summary'],'update_blocks':r['update_blocks']},indent=2))
