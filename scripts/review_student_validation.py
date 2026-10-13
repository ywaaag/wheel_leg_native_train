"""Read-only student first-episode rescore and earliest teacher deviation."""
import argparse,json
from pathlib import Path
import numpy as np
import torch
from native_stand.students.data import sha
from native_stand.students.interface import History,frame,task,LEGS
from native_stand.students.model import load
from native_stand.students.protocol import score
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,VERSION as TRACE
from native_stand.recovery.motion_handoff import score as teacher_score

def review(run,output):
 torch.set_num_threads(4);run=Path(run);output=Path(output)
 if output.exists():raise FileExistsError(output)
 mcu=False
 terminal=json.loads((run/'terminal_report.json').read_text());spec=json.loads((run/'source_snapshot/spec.json').read_text());settlement=json.loads((run/'monitor_exit.json').read_text());cases=[];hashes={};mcu=spec.get('interface_version')=='multiskill_mcu_v2'
 for c in terminal['conditions']:
  if c['status']!='COMPLETED':
   cases.append({'case_id':c['condition']['case_id'],'status':c['status'],'accepted':0,'entry':0,'hold':0,'per_env':[]});continue
  path=run/c['result'];saved=json.loads(path.read_text());trace=run/saved['trace']['path'];assert sha(trace)==saved['trace']['sha256'];hashes[str(path)]=sha(path);hashes[str(trace)]=sha(trace)
  with np.load(trace) as compressed:a={k:compressed[k] for k in compressed.files}
  assert saved['field_schema']['state']==TRACE and saved['field_schema']['control']==TRACE
  row=c['condition'];is_student=row['kind']=='student';per=[]
  for eid,original in enumerate(saved['per_env']):
   m=a['first_episode_valid'][:,eid];s=torch.tensor(a['state'][m,eid]);p=torch.tensor(a['posture'][m,eid]);controller=torch.tensor(a['controller'][m,eid,0]);times=torch.tensor(a['policy_time_s'][m],dtype=s.dtype)
   result=score(s,p,controller==3,policy_time_s=times) if is_student else teacher_score(s,p,controller==2,policy_time_s=times)
   for field in ('accepted','entry_index','hold_complete','failed_checks'):assert result[field]==original[field]
   ids=np.flatnonzero(m);controlled=np.flatnonzero(a['controller'][m,eid,0]>0);start=int(controlled[0])
   entry=result['entry_index'];windows={'preparation_or_rise':ids[start:entry+1 if entry is not None else len(ids)],'holding':ids[entry+1:] if entry is not None else ids[:0]};stats={}
   for stage,ix in windows.items():
    if not len(ix):continue
    delta=a['root_post'][ix,eid,:3]-a['root_pre'][ix,eid,:3];st=a['state'][ix,eid];po=a['posture'][ix,eid]
    stats[stage]={'duration_s':len(ix)*.01,'height_peak_m':float(st[:,6].max()),'height_min_m':float(st[:,6].min()),'native_vx_abs_mean_mps':float(np.abs(st[:,7]).mean()),'native_vx_peak_mps':float(np.abs(st[:,7]).max()),'pitch_roll_abs_peak_rad':np.abs(po[:,:2]).max(0).tolist(),'angular_speed_world_peak_rad_s':float(np.linalg.norm(a['root_post'][ix,eid,10:13],axis=-1).max()),'world_displacement_m':delta.sum(0).tolist(),'planar_path_m':float(np.linalg.norm(delta[:,:2],axis=1).sum()),'dual_contact_fraction':float((st[:,10:12]>2).all(-1).mean()),'policy_saturation_fraction':float(st[:,17].mean()),'raw_action_clip_per_channel':(np.abs(a['raw_action'][ix,eid])>1).mean(0).tolist(),'applied_limit_per_channel':(np.abs(a['control'][ix,eid,44:50])>=np.array([40,40,5.5,40,40,5.5])-1e-4).mean(0).tolist()}
   short=(p[:,2:4]<=.34).all(-1).numpy();best_run=current=0
   for hit in short:current=current+1 if hit else 0;best_run=max(best_run,current)
   independent_input_error=None;previous_cache_error=None
   if mcu and is_student:
    from native_stand.students.mcu_interface import encode
    root=torch.tensor(a['root_pre'][ids,eid]);qxyzw=root[:,3:7];xyz=-qxyzw[:,:3];w=qxyzw[:,3:4]
    def inverse(v):return v+2*torch.cross(xyz,torch.cross(xyz,v,dim=-1)+w*v,dim=-1)
    angular=inverse(root[:,10:13]);gravity=inverse(torch.tensor([0.,0.,-1.]).expand(len(ids),-1))
    q=torch.tensor(a['joint_q_pre'][ids,eid][:,saved['field_schema']['active_indices']]);dq=torch.tensor(a['joint_dq_pre'][ids,eid][:,saved['field_schema']['active_indices']]);prev=torch.tensor(a['previous_targets'][ids,eid]);ref=torch.zeros_like(q)
    reconstructed=encode(angular,gravity,q,dq,prev[:,:4],prev[:,4:],ref,'Recovery' if row['role']=='RecoveryStudent' else 'Motion',torch.tensor([[0.,0.,.4]]).expand(len(ids),-1))
    independent_input_error=float((reconstructed-torch.tensor(a['actor_input'][ids,eid])).abs().max())
    # Pre-target must be previous actual after-limit legs and clipped wheel target in same first episode.
    if len(ids)>1:
     previous_control=torch.tensor(a['control'][ids[:-1],eid]);expected=torch.cat((previous_control[:,CONTROL['leg_target_after_limit']],previous_control[:,CONTROL['clipped_action']][:,[2,5]]*100),-1)
     previous_cache_error=float((prev[1:]-expected).abs().max())
   result.update(simultaneous_short_minimum_m=p[:,2:4].min(0).values.tolist(),simultaneous_short_max_run_s=best_run*.01,simultaneous_short_50ms=best_run>=5,independent_31D_reconstruction_max_abs_error=independent_input_error,previous_actual_cache_max_abs_error=previous_cache_error,env=eid,initial_valid=original['initial_valid'],tilt_terminated=bool(original['termination_causes'][3]),controlled_duration_s=len(controlled)*.01,windows=stats)
   per.append(result)
  cases.append({'case_id':row['case_id'],'row':row,'per_env':per,'accepted':sum(x['accepted'] for x in per),'entry':sum(x['entry_index'] is not None for x in per),'hold':sum(x['hold_complete'] for x in per),'initial_valid':sum(x['initial_valid'] for x in per),'finite':all(np.isfinite(v).all() for v in a.values()),'model_unchanged':saved['model_unchanged']})
 pairs=[]
 for i,j in [(0,1),(2,3),(4,5),(6,7),(8,9)]:
  if max(i,j)>=len(terminal['conditions']):continue
  if terminal['conditions'][i]['condition']['kind']!='student':continue
  if terminal['conditions'][j]['condition']['kind']!='teacher_combination':continue
  if terminal['conditions'][i]['status']!='COMPLETED' or terminal['conditions'][j]['status']!='COMPLETED':continue
  sd=json.loads((run/terminal['conditions'][i]['result']).read_text());td=json.loads((run/terminal['conditions'][j]['result']).read_text())
  with np.load(run/sd['trace']['path']) as z:student={k:z[k] for k in z.files}
  with np.load(run/td['trace']['path']) as z:teacher={k:z[k] for k in z.files}
  row=terminal['conditions'][i]['condition'];actor,_=load(row['checkpoint'],row['role']);actor.eval();per=[]
  # Reconstruct NEW inputs from teacher's pre-action physical data, same encoder.
  histories=History(8);ref=torch.zeros(8,6);encoded=[]
  for t in range(len(teacher['state'])):
   legacy=torch.tensor(teacher['actor_input'][t,:,:25]);q=torch.tensor(teacher['joint_q_pre'][t][:,td['field_schema']['active_indices']]);dq=torch.tensor(teacher['joint_dq_pre'][t][:,td['field_schema']['active_indices']]);prev=torch.tensor(teacher['previous_targets'][t]);initial=torch.tensor(teacher['controller'][t,:,0]==0)
   if not mcu:prev[initial]=0
   f=frame(legacy[:,:3]/.25,legacy[:,3:6],q,dq,prev[:,:4],prev[:,4:],ref);histories.append(f,t*.01)
   if mcu:
    from native_stand.students.mcu_interface import actor_input,task as mcu_task
    encoded.append(actor_input(f,mcu_task('Recovery' if row['role']=='RecoveryStudent' else 'Motion',torch.tensor([[0.,0.,.40]]).repeat(8,1))).clone())
   else:
    cmd=task('Recovery' if row['role']=='RecoveryStudent' else 'Motion',torch.tensor([[0,0,.36 if row['role']=='RecoveryStudent' else .40,0,0]]).repeat(8,1));encoded.append(histories.encode(cmd).clone())
  teacher_x=torch.stack(encoded)
  with torch.no_grad():pred=actor(teacher_x.flatten(0,1)).reshape(-1,8,6)
  target=torch.tensor(teacher['control'][:,:,CONTROL['leg_target_after_limit']]);leg_error=(pred[:,:,LEGS]*1.5-target).abs().mean(-1).numpy()
  for eid in range(8):
   start_s=int(np.flatnonzero(student['controller'][:,eid,0]>0)[0]);start_t=int(np.flatnonzero(teacher['controller'][:,eid,0]>0)[0]);count=min(int(student['first_episode_valid'][start_s:,eid].sum()),int(teacher['first_episode_valid'][start_t:,eid].sum()))
   ix=np.arange(count);ss=student['state'][start_s+ix,eid];ts=teacher['state'][start_t+ix,eid];sp=student['posture'][start_s+ix,eid];tp=teacher['posture'][start_t+ix,eid]
   def first(mask):
    hit=np.flatnonzero(mask);return float((hit[0]+1)*.01) if len(hit) else None
   input_diff=np.abs(student['actor_input'][start_s,eid]-teacher_x[start_t,eid].numpy())
   per.append({'env':eid,'first_control_input_abs_max_difference':float(input_diff.max()),'first_control_current_frame_abs_max_difference':float(input_diff[:22].max()) if mcu else float(input_diff[50*23:51*23].max()),'first_height_difference_over_1cm_s':first(np.abs(ss[:,6]-ts[:,6])>.01),'first_pitch_roll_difference_over_p05rad_s':first(np.max(np.abs(sp[:,:2]-tp[:,:2]),axis=1)>.05),'first_actual_leg_target_difference_over_p1rad_s':first(np.max(np.abs(student['control'][start_s+ix,eid,CONTROL['leg_target_after_limit']]-teacher['control'][start_t+ix,eid,CONTROL['leg_target_after_limit']]),axis=1)>.1),'teacher_path_first_half_s_leg_mean_error_rad':float(leg_error[start_t:start_t+50,eid].mean())})
  pairs.append({'student_case':row['case_id'],'teacher_case':terminal['conditions'][j]['condition']['case_id'],'per_env':per})
 output.mkdir(parents=True);report={'terminal':terminal['status'],'settlement':settlement,'cases':cases,'pairs':pairs,'inputs_sha256':hashes,'rescore_matches':all(c.get('status','COMPLETED')=='COMPLETED' for c in cases),'output_bytes':sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),'interface_version':spec['interface_version'],'online_PPO':0,'offline_optimizer':0,'interpretation':'earliest mismatch is evidence, not sole causal proof; teacher labels only on actual validated teacher trajectories'}
 (output/'review.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=review(a.run,a.output);print(json.dumps({'rescore_matches':r['rescore_matches'],'output_bytes':r['output_bytes'],'cases':[(c['case_id'],c['accepted']) for c in r['cases']],'pairs':r['pairs']},indent=2))
