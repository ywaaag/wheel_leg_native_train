import argparse,json,os
os.environ.setdefault('CUDA_VISIBLE_DEVICES','0')
from native_stand.students.distill import train
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--output',required=True);p.add_argument('--role',choices=['RecoveryStudent','MotionStudent','MotionZeroStudent'],required=True);p.add_argument('--steps',type=int,default=5000);p.add_argument('--wall-s',type=float,default=1200);p.add_argument('--source-checkpoint');p.add_argument('--device',choices=['auto','cpu','cuda:0'],default='auto');a=p.parse_args()
r=train(a.dataset,a.output,a.role,steps=a.steps,wall_s=a.wall_s,source_checkpoint=a.source_checkpoint,device=a.device);print(json.dumps({k:r[k] for k in ('role','offline_optimizer_steps','wall_s','stop_reason','best_step','metrics','training_device','device_selection')},indent=2))
