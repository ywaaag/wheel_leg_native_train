"""CPU continuous reward replay, old/new physical target units; no simulation."""
import json,hashlib
from pathlib import Path
import numpy as np,torch
from native_stand.students.recovery_task import reward,configuration,SYMMETRY_VERSION,SLIDING_VERSION
from native_stand.command_v6.domain.trace_schema import CONTROL,STATE,VERSION
ROOT=Path('/home/kellen/wheel_leg_native_train')
def replay(output):
 output=Path(output)
 if output.exists():raise FileExistsError(output)
 rows=[];inputs={};torch.set_num_threads(4)
 groups=[('student_v7',ROOT/'runs/2026_10_12-00_12__recovery_standing_velocity_huber_from200/formal',i) for i in (16,17,18)]
 groups+=[('teacher_B250',ROOT/'runs/2026_10_12-20_49__recovery_wheel_temporal_a_from100/source_eval',7)]
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 for label,folder,index in groups:
  p=folder/f'evaluation_{index:02}.json'
  if not p.exists() and label=='teacher_B250':
   p=next(p for p in folder.glob('evaluation_[0-9][0-9].json') if json.load(open(p))['case']['kind']=='teacher_normal')
  d=json.load(open(p));trace=folder/d['trace']['path'];assert sha(trace)==d['trace']['sha256'] and d['field_schema']['state']==VERSION
  inputs[str(p)]=sha(p);inputs[str(trace)]=sha(trace)
  with np.load(trace) as a:z={k:a[k] for k in ('state','posture','control','root_post','previous_targets','first_episode_valid')}
  for env,r in enumerate(d['per_env']):
   lo,hi=r['hold_index_half_open'];s=torch.tensor(z['state'][lo:hi,env]);post=torch.tensor(z['posture'][lo:hi,env]);ctl=torch.tensor(z['control'][lo:hi,env]);root=torch.tensor(z['root_post'][lo:hi,env]);previous=torch.tensor(z['previous_targets'][lo:hi,env]);n=len(s)
   target=torch.zeros(n,6);target[:,[0,1,3,4]]=ctl[:,CONTROL['leg_target_after_limit']];target[:,[2,5]]=ctl[:,CONTROL['clipped_action']][:,[2,5]]*100
   prev=torch.zeros_like(target);prev[:,[0,1,3,4]]=previous[:,:4];prev[:,[2,5]]=previous[:,4:]
   xyz=-root[:,3:6];w=root[:,6:7];v=root[:,10:13];angular=v+2*torch.cross(xyz,torch.cross(xyz,v,dim=-1)+w*v,dim=-1)
   eligible=torch.ones(n,dtype=torch.bool);no=~eligible
   values=dict(height=s[:,6],h0=torch.full((n,),.4),angles=post[:,:2],contacts=s[:,10:12],clearance=s[:,13],torque=ctl[:,CONTROL['applied_torque']],previous_targets=prev,executed_targets=target,angular_body=angular,velocity_native=s[:,7:10],yaw=s[:,9],entered=eligible,controlled=eligible,fault=no,entry_event=no,success_event=no,failure_event=no,active_leg_q=ctl[:,CONTROL['joint_q']][:,[0,1,3,4]])
   old=reward(**values,reward_configuration=configuration(SLIDING_VERSION));new=reward(**values,reward_configuration=configuration(SYMMETRY_VERSION))
   assert torch.isfinite(new['total']).all();torch.testing.assert_close(old['continuous_dt'][:,1:],new['continuous_dt'][:,1:])
   rows.append(dict(source=label,env=env,case=d['case']['case_id'],mean_height_m=float(s[:,6].mean()),old_density_per_s=float(old['total'].mean()/.01),new_density_per_s=float(new['total'].mean()/.01),old_mirror_density=float(old['motion_mirror_weighted_density'][:,1].mean()),new_mirror_density=float(new['motion_mirror_weighted_density'][:,1].mean()),new_height_density=float(new['weighted_density'][:,0].mean()),mirror_mae_rad=new['mirror_error_rad'].abs().mean(0).tolist()))
 output.write_text(json.dumps(dict(recipe=configuration(SYMMETRY_VERSION),inputs_sha256=inputs,episodes=rows,simulation=0,optimizer_steps=0,interpretation='continuous units/signs/reward preference replay; B250 original0.40m is not a0.34m expert or certificate'),indent=2)+'\n')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();replay(a.output)
