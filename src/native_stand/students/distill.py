"""Bounded CPU BC, episode/phase-balanced; no teacher optimizer or simulation."""
import json,time,copy,os,subprocess
from pathlib import Path
import torch
from .model import Student
from .interface import VERSION,LEGS,WHEELS
from .data import STAGES,sha

def physical_errors(pred,label):
 e=(pred-label).abs();leg=e[:,LEGS]*1.5;wheel=e[:,WHEELS]*100.
 return {'leg_mae_rad':float(leg.mean()),'wheel_mae_rad_s':float(wheel.mean()),
         'leg_p95_rad':float(torch.quantile(leg.flatten(),.95)),'wheel_p95_rad_s':float(torch.quantile(wheel.flatten(),.95)),
         'leg_mae_per_channel_rad':leg.mean(0).tolist(),'leg_p95_per_channel_rad':torch.quantile(leg,.95,dim=0).tolist(),
         'wheel_mae_per_channel_rad_s':wheel.mean(0).tolist(),'wheel_p95_per_channel_rad_s':torch.quantile(wheel,.95,dim=0).tolist(),
         'mean_saturation_per_channel':(pred.abs()>=.99).float().mean(0).tolist(),
         'label_boundary_per_channel':(label.abs()>=.99).float().mean(0).tolist()}
def loss(pred,label):
 return (((pred[:,LEGS]-label[:,LEGS])*15)**2).mean()+(((pred[:,WHEELS]-label[:,WHEELS])*10)**2).mean()

def select_device(actor,x,y,requested='cpu'):
 """Compare bounded scratch gradient throughput; no source/Adam updates."""
 if requested not in ('cpu','cuda:0','auto'):raise ValueError('BC device must be cpu, cuda:0 or auto')
 if requested=='cpu':return 'cpu',{'selection':'explicit CPU','optimizer_steps':0}
 if os.environ.get('CUDA_VISIBLE_DEVICES')!='0':raise ValueError('GPU BC requires explicit physical GPU0 CUDA_VISIBLE_DEVICES=0')
 snapshot=subprocess.run(['nvidia-smi','--query-gpu=index,uuid,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
 gpu=next(row for row in snapshot.splitlines() if row.split(',')[0].strip()=='0');fields=[a.strip() for a in gpu.split(',')]
 if int(fields[2])-int(fields[3])<2048:raise ValueError('GPU0 shared memory reserve insufficient; do not preempt or switch device')
 if not torch.cuda.is_available():raise ValueError('CUDA unavailable for requested BC benchmark')
 if requested=='cuda:0':return 'cuda:0',{'selection':'explicit GPU0 shared','snapshot':gpu,'optimizer_steps':0}
 cpu_rng=torch.get_rng_state();cuda_rng=torch.cuda.get_rng_state_all();times={}
 try:
  for device in ('cpu','cuda:0'):
   scratch=copy.deepcopy(actor).to(device);bx=x[:512].to(device);by=y[:512].to(device)
   for _ in range(10):scratch.zero_grad(set_to_none=True);loss(scratch(bx),by).backward()
   if device.startswith('cuda'):torch.cuda.synchronize()
   start=time.perf_counter()
   for _ in range(100):scratch.zero_grad(set_to_none=True);loss(scratch(bx),by).backward()
   if device.startswith('cuda'):torch.cuda.synchronize()
   times[device]=(time.perf_counter()-start)/100
   del scratch,bx,by
 finally:
  torch.set_rng_state(cpu_rng);torch.cuda.set_rng_state_all(cuda_rng)
 return min(times,key=times.get),{'selection':'measured forward/backward throughput at batch512; optimizer and dataset sampling not benchmarked','seconds_per_gradient_batch':times,'snapshot':gpu,'scratch_gradient_batches_per_device':110,'optimizer_steps':0,'RNG_restored':True}
def metrics(model,data,split):
 result={};model.eval()
 with torch.no_grad():
  for st,name in enumerate(data.get('stage_names',STAGES)):
   ids=torch.where((data['split']==split)&(data['stage']==st))[0]
   if not len(ids):continue
   pred=torch.cat([model(data['x'][c]) for c in ids.split(1024)])
   m=physical_errors(pred,data['y'][ids]);m.update(samples=len(ids),loss=float(loss(pred,data['y'][ids])))
   m['fit_reference_pass']=m['leg_mae_rad']<=.05 and m['wheel_mae_rad_s']<=2 and m['leg_p95_rad']<=.1 and m['wheel_p95_rad_s']<=5
   result[name]=m
 model.train();return result

def train(dataset,output,role,*,steps=5000,wall_s=1200,seed=20261011,source_checkpoint=None,device='cpu'):
 if not 0<steps<=5000 or not 0<wall_s<=1200:raise ValueError('BC authorization ceiling exceeded')
 torch.set_num_threads(4);torch.manual_seed(seed);start=time.monotonic();output=Path(output)
 if output.exists():raise FileExistsError(output)
 output.mkdir(parents=True);dataset=Path(dataset);manifest_path=dataset.parent/'manifest.json';manifest=json.loads(manifest_path.read_text())
 assert sha(dataset)==manifest[role]['sha256'];data=torch.load(dataset,map_location='cpu',weights_only=False)
 teachers={v['path']:sha(v['path']) for v in manifest['teachers'].values()};version=manifest['interface_version'];actor=Student(version=version);critic=Student(False,version=version)
 source_sha=None
 if source_checkpoint:
  from .model import load
  source_checkpoint=Path(source_checkpoint).resolve();source_sha=sha(source_checkpoint);actor,source=load(source_checkpoint,role)
  if source['interface_version']!=version:raise ValueError('distillation source interface differs')
  if manifest.get('source_checkpoint')!={'path':str(source_checkpoint),'sha256':source_sha}:raise ValueError('standing distillation source binding differs')
 selected_device,device_review=select_device(actor,data['x'],data['y'],device)
 actor=actor.to(selected_device)
 data['x']=data['x'].to(selected_device);data['y']=data['y'].to(selected_device)
 init={'interface_version':version,'role':role,'actor':copy.deepcopy(actor.state_dict()),'critic':copy.deepcopy(critic.state_dict()),'seed':seed,'offline_bc_steps':0}
 initialization_path=output/('inherited_actor_initialization.pt' if source_checkpoint else 'random_initialization.pt')
 init.update(source_actor_sha256=source_sha,critic_origin='new_random',actor_origin='source_checkpoint' if source_checkpoint else 'new_random')
 torch.save(init,initialization_path);optimizer=torch.optim.Adam(actor.mlp.parameters(),lr=1e-3)
 # std deliberately excluded: deterministic means only.
 groups={}
 for st in sorted(data['stage'][data['split']==0].unique().tolist()):
  groups[st]=[torch.where((data['split']==0)&(data['stage']==st)&(data['episode']==ep))[0] for ep in sorted(data['episode'][(data['split']==0)&(data['stage']==st)].unique().tolist())]
 standing=manifest.get('sampling_version') in ('standing_priority_recovery_v1','standing_priority_reset_v2')
 reset_priority=manifest.get('sampling_version')=='standing_priority_reset_v2'
 if role=='RecoveryStudent' and set(groups)!=set(range(5 if standing else 4)):raise ValueError('declared teaching phases required')
 stage_names=data.get('stage_names',STAGES)
 draw_counts={st:(256 if st==4 else 64) if standing else 512//len(groups) for st in groups}
 generator=torch.Generator().manual_seed(seed+1);visits=torch.zeros(len(data['x']),dtype=torch.long);history=[];best=float('inf');bad=0;reason='step_limit';actual=0
 def checkpoint(step):return {'interface_version':version,'role':role,'actor':copy.deepcopy(actor.state_dict()),'critic':copy.deepcopy(critic.state_dict()),'offline_bc_steps':step,'seed':seed,'dataset_sha256':sha(dataset),'manifest_sha256':sha(manifest_path),'initialization_sha256':sha(initialization_path),'optimizer_origin':'new CPU BC Adam; not for PPO resume','bc_optimizer':optimizer.state_dict(),'teacher_sha256':teachers,'source_actor_sha256':source_sha,'distillation_method':manifest.get('sampling_version','four_phase_balanced_v1')}
 for step in range(1,steps+1):
  if time.monotonic()-start>=wall_s:reason='wall_limit';break
  selected=[]
  for st,episodes in groups.items():
   ep_indices=torch.randint(len(episodes),(draw_counts[st],),generator=generator)
   for draw,ep in enumerate(ep_indices.tolist()):
    ids=episodes[ep]
    if reset_priority and st==4:
     ids=ids[:1] if draw%4==0 else ids[1:20] if draw%4 in (1,2) else ids[20:]
     if not len(ids):raise ValueError('normal reset/early/hold bucket missing')
    selected.append(int(ids[torch.randint(len(ids),(1,),generator=generator)]))
  ids=torch.tensor(selected);visits.index_add_(0,ids,torch.ones_like(ids));optimizer.zero_grad(set_to_none=True);value=loss(actor(data['x'][ids]),data['y'][ids]);value.backward();optimizer.step();actual=step
  if step%200==0 or step==steps:
   validation=metrics(actor,data,1);score=sum(v['loss']*(draw_counts[st]/512) for st,v in enumerate(validation.values())) if standing else sum(v['loss'] for v in validation.values())/len(validation)
   history.append({'step':step,'wall_s':time.monotonic()-start,'validation':validation,'validation_score':score})
   if score<best-1e-6:best=score;bad=0;torch.save(checkpoint(step),output/'best_validation.pt')
   else:bad+=1
   if bad>=5:reason='five_validations_without_improvement';break
 torch.save(checkpoint(actual),output/'latest.pt')
 if not (output/'best_validation.pt').exists():torch.save(checkpoint(actual),output/'best_validation.pt')
 best_checkpoint=torch.load(output/'best_validation.pt',map_location='cpu',weights_only=False);actor.load_state_dict(best_checkpoint['actor'])
 report={'role':role,'interface_version':version,'seed':seed,'online_PPO_updates':0,'offline_optimizer_steps':actual,'wall_s':time.monotonic()-start,'stop_reason':reason,'threads':4,'batch_size':512,'learning_rate':.001,'validation_every_steps':200,'best_step':best_checkpoint['offline_bc_steps'],
  'metrics':{name:metrics(actor,data,si) for si,name in enumerate(('train','validation','test'))},'validation_history':history,
  'sampling':{name:{'unique_available':int(((data['split']==0)&(data['stage']==st)).sum()),'draws':int(visits[data['stage']==st].sum()),'unique_drawn':int((visits[data['stage']==st]>0).sum()),'repeat_draws':int(visits[data['stage']==st].sum()-(visits[data['stage']==st]>0).sum())} for st,name in enumerate(stage_names)},
  'manifest_sha256':sha(manifest_path),'checkpoints':{p.name:sha(p) for p in output.glob('*.pt')},'teachers_unchanged':all(sha(p)==s for p,s in teachers.items()),'capability':'action fitting only; closed-loop recovery/locomotion NOT_RUN'}
 report['source_actor_sha256']=source_sha;report['source_unchanged']=source_checkpoint is None or sha(source_checkpoint)==source_sha
 report['training_device']=selected_device;report['device_selection']=device_review
 assert report['teachers_unchanged'] and report['source_unchanged'];(output/'training_result.json').write_text(json.dumps(report,indent=2)+'\n');return report
