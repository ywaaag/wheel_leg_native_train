"""Explicit student preview via shared environment; never launches by default."""
import json,time,os,sys
from pathlib import Path
from .data import sha
from .requests import validate

def execute(args,spec):
 errors=validate(spec)
 if errors:raise ValueError(errors)
 family=getattr(args,'preview_family',None) or spec['recovery']['active_family']
 independent=[r for r in spec['student_evaluation']['cases'] if r['kind']=='student' and r['family']==family]
 diagnostic=getattr(args,'diagnostic_initialization',False)
 if diagnostic:
  if not getattr(args,'preview_family',None):raise ValueError('diagnostic initialization requires explicit preview-family')
  library_path=spec['recovery']['pose_library']
  if sha(library_path)!=spec['recovery']['pose_library_sha256']:raise ValueError('preview pose library SHA differs')
  library=json.loads(Path(library_path).read_text())
  from .requests import evaluation_recovery
  evaluation_recovery(spec['recovery'],library['poses'],family)
  if not independent:
   baseline=next((r for r in spec['student_evaluation']['cases'] if r['kind']=='student'),None)
   if baseline is None:raise ValueError('student diagnostic baseline absent')
   independent=[{**baseline,'family':family}]
 row=next((r for r in independent if r['checkpoint']==str(args.checkpoint.resolve())),None)
 if row is None:
  from .model import load
  _,candidate=load(args.checkpoint,'RecoveryStudent')
  if candidate.get('spec_sha256')!=sha(args.spec) or candidate.get('asset_sha256')!=spec['asset_sha256'] or candidate.get('recipe_version')!=spec.get('student_training',{}).get('version') or candidate.get('interface_version')!=spec['interface_version']:
   raise ValueError('Student preview candidate spec/asset/recipe/interface identity differs')
  row=next(iter(independent),None)
  if row is None:raise ValueError('Student preview family not declared')
  row={**row,'checkpoint':str(args.checkpoint.resolve()),'sha256':sha(args.checkpoint)}
 if sha(args.checkpoint)!=row['sha256']:raise ValueError('Student preview checkpoint SHA differs')
 if not args.preview or args.handoff_condition is not None or args.keyboard:raise ValueError('Student preview must be independent, without teacher/keyboard override')
 result={'interface_version':spec['interface_version'],'checkpoint':str(args.checkpoint),'checkpoint_sha256':sha(args.checkpoint),'initial_family':row['family'],'teacher_control':False,'teacher_prefix_intervals':0,'simulation':0,'online_PPO':0}
 result.update(diagnostic_initialization=diagnostic,capability_certification=False,
  assessment_family_declared=any(r['family']==family for r in spec['student_evaluation']['cases']),
  target_height_m=spec.get('student_training',{}).get('target_height_m'))
 from native_stand.command_v6.tools.experiment_preparation import verify_publication
 # Registration legitimately replaces spec/ledger against its exact receipt.
 # Perform the same strict identity check in CPU preview and GUI execution.
 result['publication']=verify_publication(args.spec,authorized=True)
 if not args.run:print(json.dumps(result,indent=2));return
 if args.physical_gpu not in (0,1):raise ValueError('Explicit physical GPU0 or GPU1 required')
 if spec.get('device',{}).get('physical_index')!=args.physical_gpu:raise ValueError('preview physical GPU differs from declared spec')
 os.environ['CUDA_VISIBLE_DEVICES']=str(args.physical_gpu);sys.path.insert(0,spec['asset_module_root'])
 from isaaclab.app import AppLauncher
 app=AppLauncher({'headless':False,'device':'cuda:0','visualizer':['kit'],'visualizer_explicit':True}).app;env=None
 try:
  from .evaluator import environment
  from .model import load
  import torch
  env=environment(spec,row['role'],envs=1,initial_family=row.get('family'),autonomous_preview=True);env.student_yaw_amplitude=row['yaw_rad'];env.select_initial_family(row['family'],'holdout')
  actor,_=load(row['checkpoint'],row['role']);actor=actor.to(env.device).eval();obs,_=env.reset();count=0;start=time.monotonic()
  from native_stand.command_v6.tools.ground_visual import setup,camera_view
  try:
   import omni.usd
   result.update(setup(omni.usd.get_context().get_stage(),env.sim,style=args.ground_style,
     extent_m=args.ground_extent_m,grid_spacing_m=args.ground_grid_spacing_m))
  except Exception as error:
   print(f'[Visual Notice] Visual setup skipped: {error}',flush=True)
  camera_view(env.sim)
  print('GUI running: independent Recovery student; close window or Ctrl-C.',flush=True)
  with torch.inference_mode():
   while app.is_running() and (not args.max_policy_steps or count<args.max_policy_steps) and time.monotonic()-start<args.max_wall_seconds:
    obs,*_=env.step(actor(obs));count+=1
    if count%200==0:
     root=env.robot.data.root_pos_w.torch[0].cpu().tolist()
     camera_view(env.sim,root[:2])
 finally:
  original=sys.exception()
  for obj in (env,app):
   if obj:
    try:obj.close()
    except BaseException:
     if original is None:raise
