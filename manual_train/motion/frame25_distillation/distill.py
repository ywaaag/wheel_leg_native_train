"""Bounded CPU teacher-query BC. No simulation, hardware, PPO or history in student."""
from pathlib import Path
import json,hashlib,time,copy
import numpy as np
import torch
from tensordict import TensorDict
ROOT=Path('/home/kellen/wheel_leg_native_train')
TEACHER=ROOT/'runs/2026_10_13-05_39__motion_standing034_pm2_block0003/formal/model_update_300.pt'
SHA='4750ee5661ade1e9089e7d81f7f6c294490e8f8c078a766c9a9c78f1a80ccafb'
VERSION='motion_frame25_distilled_v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def actor():
 return torch.nn.Sequential(torch.nn.Linear(25,128),torch.nn.ELU(),torch.nn.Linear(128,64),torch.nn.ELU(),torch.nn.Linear(64,32),torch.nn.ELU(),torch.nn.Linear(32,6))

def physical_error(pred,label):
 diff=(pred-label)*pred.new_tensor([.5,.5,100,.5,.5,100]);return diff

def loss(pred,label):
 e=physical_error(pred,label);return (e[:,[0,1,3,4]]/.1).square().mean()+(e[:,[2,5]]/10).square().mean()

def build(out):
 from native_stand.command_v6.tools.model_factory import model
 torch.set_num_threads(4);assert sha(TEACHER)==SHA
 spec=json.loads((TEACHER.parent/'source_snapshot/spec.json').read_text());obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);teacher=model(obs,actor=True,spec=spec);cp=torch.load(TEACHER,map_location='cpu',weights_only=False);teacher.load_state_dict(cp['actor']);teacher.eval();teacher.requires_grad_(False)
 manifest={'interface_version':VERSION,'teacher':{'checkpoint':str(TEACHER),'sha256':SHA,'height_command_m':.34},'target_method':'offline teacher deterministic query at .34 command, clipped to teacher existing action envelope; not physically executed at these counterfactual states','state_coverage':'successful normal zero-command .40m source episodes, close repeats, not .34 closed-loop evidence','network':[25,128,64,32,6],'activation':'ELU alpha1, linear mean','actions':{'left_first':['left_hip','left_active','left_wheel','right_hip','right_active','right_wheel'],'leg_scale_rad':.5,'wheel_scale_rad_s':100,'reference_rad':[0]*6},'files':{},'episodes':[]};packs={k:[] for k in ['x','y','episode','split','stage']};ep=0;alignment_max=0.;clipped_counts=np.zeros(6,dtype=int)
 for ri,runname in enumerate(['2026_10_10-16_44__recovery_motion_b250_handoff_ppo0','2026_10_10-22_24__receiver_window_ppo0']):
  run=ROOT/'runs'/runname;terminal=json.loads((run/'terminal_report.json').read_text());rb=json.loads((run/'runtime_readback.json').read_text());ids=rb['active_indices'];assert np.array(rb['reference']).max()==0
  condition=next(c for c in terminal['conditions'] if c['condition']['kind']=='normal_motion_baseline');p=run/condition['result'];saved=json.loads(p.read_text());assert saved['motion_sha256']=='5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e';arc=run/saved['trace']['path'];assert sha(arc)==saved['trace']['sha256'];manifest['files'][str(p)]=sha(p);manifest['files'][str(arc)]=sha(arc);a=np.load(arc,allow_pickle=False)
  for env,r in enumerate(saved['per_env']):
   if not r['accepted']:continue
   valid=a['first_episode_valid'][:,env] & (a['controller'][:,env,0]==2);indices=np.flatnonzero(valid);assert len(indices)>=1000
   frame=a['motion_frame'][indices,env].astype('f').copy();hist=a['motion_history'][indices,env].astype('f').copy()
   q=a['joint_q_pre'][indices,env][:,ids];dq=a['joint_dq_pre'][indices,env][:,ids];prev=a['motion_previous_input'][indices,env]
   alignment_max=max(alignment_max,float(np.abs(frame[:,9:13]-q[:,[0,1,3,4]]*2).max()),float(np.abs(frame[:,13:19]-dq*.05).max()),float(np.abs(frame[:,19:25]-prev).max()));assert np.allclose(frame[:,6:8],0) and np.allclose(frame[:,8],2.)
   frame[:,8]=1.7;hist.reshape(-1,5,25)[:,:,8]=1.7
   with torch.no_grad():
    td=TensorDict({'policy':torch.from_numpy(frame),'history':torch.from_numpy(hist)},batch_size=[len(frame)]);raw=teacher(td,stochastic_output=False).numpy();clipped_counts+=(np.abs(raw)>1).sum(0);label=np.clip(raw,-1,1)
   split=0 if ri==0 and env<6 else 1 if ri==0 else 2;stage=(np.arange(len(indices))>=20).astype('int64')
   packs['x'].append(torch.from_numpy(frame));packs['y'].append(torch.from_numpy(label));packs['episode'].append(torch.full((len(frame),),ep));packs['split'].append(torch.full((len(frame),),split));packs['stage'].append(torch.from_numpy(stage));manifest['episodes'].append({'id':ep,'run':runname,'env':env,'split':['train','validation','test'][split],'samples':len(frame),'reset_early_samples':20,'state_original_height_command_m':.40,'student_and_query_height_command_m':.34});ep+=1
 assert alignment_max<1e-5
 data={k:torch.cat(v) for k,v in packs.items()};torch.save(data,out/'dataset.pt');manifest.update(dataset_sha256=sha(out/'dataset.pt'),input_preaction_alignment_max=alignment_max,teacher_label_clipping_counts=clipped_counts.tolist(),episode_split_counts={n:sum(e['split']==n for e in manifest['episodes']) for n in ['train','validation','test']},samples_by_split={n:int((data['split']==i).sum()) for i,n in enumerate(['train','validation','test'])},teacher_history_used_only_to_query_labels=True,student_history=False);(out/'manifest.json').write_text(json.dumps(manifest,indent=2));return data,manifest

def metrics(net,data,split):
 out={}
 with torch.no_grad():
  for st,name in [(0,'reset_early'),(1,'hold')]:
   ids=torch.where((data['split']==split)&(data['stage']==st))[0];pred=torch.cat([net(data['x'][b]) for b in ids.split(2048)]);e=physical_error(pred,data['y'][ids]).abs();out[name]={'samples':len(ids),'per_channel_MAE':e.mean(0).tolist(),'per_channel_P95':torch.quantile(e,.95,dim=0).tolist(),'per_channel_max':e.amax(0).tolist(),'leg_MAE_rad':e[:,[0,1,3,4]].mean().item(),'wheel_MAE_rad_s':e[:,[2,5]].mean().item(),'loss':loss(pred,data['y'][ids]).item(),'output_clip_fraction':(pred.abs()>1).float().mean(0).tolist()}
 return out

def execute(output):
 out=Path(output);assert not out.exists();out.mkdir(parents=True);data,manifest=build(out);torch.manual_seed(20261013);net=actor();opt=torch.optim.Adam(net.parameters(),lr=.001);start=time.monotonic();history=[];best=float('inf');bad=0;draws=torch.zeros(len(data['x']),dtype=torch.long);gen=torch.Generator().manual_seed(20261014)
 def cp(step):return {'interface_version':VERSION,'role':'MotionFrame25ZeroStudent','actor':copy.deepcopy(net.state_dict()),'network':[25,128,64,32,6],'activation':'ELU alpha1 linear mean','offline_optimizer_steps':step,'online_PPO_updates':0,'teacher_sha256':SHA,'dataset_sha256':manifest['dataset_sha256'],'manifest_sha256':sha(out/'manifest.json'),'command_height_m':.34,'action_scales':[.5,100],'seed':20261013,'bc_optimizer':opt.state_dict(),'closed_loop':'NOT_RUN'}
 torch.save(cp(0),out/'random_initialization.pt');groups={st:[torch.where((data['split']==0)&(data['stage']==st)&(data['episode']==ep))[0] for ep in data['episode'][data['split']==0].unique().tolist()] for st in [0,1]};reason='step_limit';actual=0
 for step in range(1,5001):
  if time.monotonic()-start>=1200:reason='wall_limit';break
  selected=[]
  for st in [0,1]:
   for epidx in torch.randint(len(groups[st]),(256,),generator=gen).tolist():
    ids=groups[st][epidx];selected.append(int(ids[torch.randint(len(ids),(1,),generator=gen)]))
  ids=torch.tensor(selected);draws.index_add_(0,ids,torch.ones_like(ids));opt.zero_grad(set_to_none=True);value=loss(net(data['x'][ids]),data['y'][ids]);value.backward();opt.step();actual=step
  if step%200==0:
   m=metrics(net,data,1);score=sum(v['loss'] for v in m.values())/2;history.append({'step':step,'validation':m,'score':score})
   if score<best-1e-6:best=score;bad=0;torch.save(cp(step),out/'best_validation.pt')
   else:bad+=1
   if bad>=5:reason='five_validations_without_improvement';break
 torch.save(cp(actual),out/'latest.pt');bestcp=torch.load(out/'best_validation.pt',weights_only=False);net.load_state_dict(bestcp['actor']);torch.save(net.state_dict(),out/'actor_state_dict.pt');script=torch.jit.trace(net.eval(),torch.zeros(1,25));script.save(str(out/'actor_torchscript.pt'))
 with torch.no_grad():x=data['x'][data['split']==2][:64];err=(script(x)-net(x)).abs().max().item()
 result={'interface_version':VERSION,'role':'MotionFrame25ZeroStudent','offline_optimizer_steps':actual,'online_PPO_updates':0,'wall_s':time.monotonic()-start,'stop_reason':reason,'best_step':bestcp['offline_optimizer_steps'],'cpu_threads':4,'batch_size':512,'lr':.001,'seed':20261013,'actor_parameters':sum(p.numel() for p in net.parameters()),'actor_fp32_bytes':sum(p.numel()*4 for p in net.parameters()),'MAC_per_inference':13632,'metrics':{n:metrics(net,data,i) for i,n in enumerate(['train','validation','test'])},'sampling':{name:{'draws':int(draws[data['stage']==st].sum()),'unique_drawn':int((draws[data['stage']==st]>0).sum()),'unique_available_train':int(((data['split']==0)&(data['stage']==st)).sum())} for st,name in [(0,'reset_early'),(1,'hold')]},'validation_history':history,'teacher_unchanged':sha(TEACHER)==SHA,'TorchScript_max_abs_error':err,'checkpoints_sha256':{p.name:sha(p) for p in out.glob('*.pt')},'limitations':manifest['state_coverage'],'physics_evaluation':'NOT_RUN','locomotion_nonzero':'NOT_TAUGHT','GPU_training':False};assert result['teacher_unchanged'];(out/'training_result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['validation_history','metrics']},indent=2));print(json.dumps(result['metrics']['test'],indent=2))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);execute(p.parse_args().output)
