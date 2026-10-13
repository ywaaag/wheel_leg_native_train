"""Reuse verified physical-unit teacher labels, relabel stance as Recovery."""
import argparse,copy,json
from pathlib import Path
import torch
from native_stand.students.data import sha,STAGES
from native_stand.students.mcu_interface import contract

def build(dataset_dir,source,output,*,reset_priority=False,mirror_targets=False):
 dataset_dir=Path(dataset_dir).resolve();source=Path(source).resolve();output=Path(output).resolve()
 if output.exists():raise FileExistsError(output)
 m=json.loads((dataset_dir/'manifest.json').read_text())
 if m['interface_version']!='multiskill_mcu_v2':raise ValueError('31D source dataset required')
 for path,digest in m['files'].items():
  if sha(path)!=digest:raise ValueError('teacher raw evidence SHA differs: '+path)
 packs=[]
 for role in ('RecoveryStudent','MotionZeroStudent'):
  path=dataset_dir/m[role]['file']
  if sha(path)!=m[role]['sha256']:raise ValueError('teacher dataset SHA differs')
  packs.append(torch.load(path,map_location='cpu',weights_only=False))
 recovery,standing=packs;standing=copy.deepcopy(standing)
 if not torch.isfinite(standing['x']).all() or standing['x'].shape[1]!=31:raise ValueError('standing input differs')
 if not (standing['x'][:,25:28]==torch.tensor([1.,0.,0.])).all():raise ValueError('standing original Motion identity differs')
 standing['x'][:,25:28]=torch.tensor([0.,1.,0.]);standing['stage'].fill_(4)
 if mirror_targets:
  if not reset_priority:raise ValueError('mirror target experiment requires explicit reset-priority sampling')
  from native_stand.students.standing_mirror import project,errors
  physical=standing['y'][:,[0,1,3,4]]*1.5
  original_y=standing['y'].clone();mirrored=project(physical)
  if not torch.isfinite(mirrored).all() or (mirrored.abs()>1.5).any():raise ValueError('projected targets outside student envelope')
  # Preserve original teacher previous target input: these are offline labels,
  # not a fabricated replay of new physical dynamics.
  standing['y'][:,[0,1,3,4]]=mirrored/1.5
 if set(recovery['episode'].tolist())&set(standing['episode'].tolist()):raise ValueError('episode identities overlap')
 data={k:torch.cat((recovery[k],standing[k])) for k in recovery};data['stage_names']=(*STAGES,'normal_standing')
 for split in range(3):
  if not ((standing['split']==split).any()):raise ValueError('missing episode split')
 output.mkdir(parents=True);torch.save(data,output/'RecoveryStudent.pt')
 result=copy.deepcopy(m);result.update(interface_contract=contract(),sampling_version='standing_priority_reset_v2' if reset_priority else 'standing_priority_recovery_v1',source_checkpoint={'path':str(source),'sha256':sha(source)},original_manifest={'path':str(dataset_dir/'manifest.json'),'sha256':sha(dataset_dir/'manifest.json')},task_reencoding='normal Motion teacher task -> Recovery, physical labels/pre-action state unchanged; command remains .40m',sampling_weights={'preparation':.125,'turn_lift':.125,'dynamic_settle':.125,'stable_hold':.125,'normal_standing':.5})
 if reset_priority:result['normal_sampling_buckets']={'first_action':.25,'next19_actions':.5,'remaining_hold':.25,'scope':'inside normal standing half; episode balance unchanged'}
 if mirror_targets:
  torch.save(original_y,output/'original_normal_teacher_labels.pt')
  result['normal_target_intervention']={'version':'mirrored_leg_target_projection_v1','physical_mapping':'hipL=-hipR; activeL=activeR','only_stage':'normal_standing','wheel_targets':'original teacher unchanged','runtime_projection':False,'teacher_previous_target_input':'original executed teacher cache, unchanged','modified_labels_are_not_teacher_verified_actions':True,'original_labels_sha256':sha(output/'original_normal_teacher_labels.pt'),'physical_change_mae_rad':float((mirrored-physical).abs().mean()),'mirror_error_max_rad':float(errors(mirrored).abs().max())}
 result['RecoveryStudent']={'file':'RecoveryStudent.pt','sha256':sha(output/'RecoveryStudent.pt'),'unique_samples':len(data['x']),'split_stage_counts':{name:{stage:int(((data['split']==si)&(data['stage']==st)).sum()) for st,stage in enumerate(data['stage_names'])} for si,name in enumerate(('train','validation','test'))}}
 result.pop('MotionZeroStudent',None)
 result['limitations']='original episode splits preserved; native normal stance data only, no perturbed or student-failure expert labels; fitting is not standing certification'
 (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset-dir',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--reset-priority',action='store_true');p.add_argument('--mirror-targets',action='store_true');a=p.parse_args();r=build(a.dataset_dir,a.source,a.output,reset_priority=a.reset_priority,mirror_targets=a.mirror_targets);print(json.dumps(r['RecoveryStudent'],indent=2))
