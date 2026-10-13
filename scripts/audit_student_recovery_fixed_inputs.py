"""Fixed source, no optimizer: per-channel physical errors and boundary ±5 rows."""
import json,argparse
from pathlib import Path
import torch
from native_stand.students.data import sha,STAGES
from native_stand.students.model import load
from native_stand.students.mcu_interface import ORDER,LEGS,WHEELS
def audit(output):
 torch.set_num_threads(4);root=Path(__file__).resolve().parents[1];data_path=root/'isolated/student_mcu_v2_teachers_20261011/RecoveryStudent.pt';checkpoint=root/'isolated/recovery_mcu_v2_bc_20261011/best_validation.pt'
 actor,source=load(checkpoint);d=torch.load(data_path,weights_only=False,map_location='cpu');assert sha(data_path)==source['dataset_sha256']
 with torch.inference_mode():p=torch.cat([actor(x) for x in d['x'].split(1024)])
 scale=torch.tensor([1.5,1.5,100,1.5,1.5,100]);error=(p-d['y']).abs()*scale
 report={'source':str(checkpoint),'source_sha256':sha(checkpoint),'dataset':str(data_path),'dataset_sha256':sha(data_path),'optimizer_steps':0,'stages':{},'teacher_boundary_rows':[]}
 for st,name in enumerate(STAGES):
  e=error[d['stage']==st];report['stages'][name]={channel:{'unit':'rad/s' if i in WHEELS else 'rad','MAE':float(e[:,i].mean()),'P95':float(torch.quantile(e[:,i],.95)),'max':float(e[:,i].max())} for i,channel in enumerate(ORDER)}
 for ep in d['episode'].unique():
  ids=torch.where(d['episode']==ep)[0];first=int(ids[d['stage'][ids]==1][0]);selected=torch.arange(first-5,first+5)
  assert (d['episode'][selected]==ep).all()
  report['teacher_boundary_rows'].append({'episode':int(ep),'split':int(d['split'][first]),'rows':[{'offset':int(k-first),'pre_action_31D':d['x'][k].tolist(),'teacher_target_leftfirst_rad_or_rad_s':(d['y'][k]*scale).tolist(),'student_target_leftfirst_rad_or_rad_s':(p[k]*scale).tolist(),'abs_error_per_channel':error[k].tolist()} for k in selected]})
 report['interpretation']='Input is close, not identical; teacher switch discontinuity and early preparation tail errors are risks, not impossibility proof. No BC refitting, no teacher state rescue, PPO start unchanged.'
 output=Path(output)
 if output.exists():raise FileExistsError(output)
 output.mkdir();(output/'fixed_input_audit.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();r=audit(a.output);print(json.dumps(r['stages'],indent=2))
