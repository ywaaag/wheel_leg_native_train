"""Public batch diagnostic implementation; AppLauncher before runtime imports."""
import json,hashlib,time,os,traceback
from pathlib import Path
import numpy as np
from .handoff_requests import validate
from .handoff_protocol import declaration,duration
from .motion_handoff import score


def plan(args,spec,preflight):
    validate(spec);c=spec['motion_handoff']
    for path,key in ((c['motion_checkpoint'],'motion_sha256'),(c['motion_spec'],'motion_spec_sha256')):
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=c[key]:raise ValueError('Motion identity drift')
    ms=json.loads(Path(c['motion_spec']).read_text())
    for k in ('physics_dt_s','pd_dt_s','policy_dt_s','leg_kp','leg_kd','wheel_kv','effort_limits_nm','closure_fault_m'):
        if ms['control'][k]!=spec['control'][k]:raise ValueError('Physical contract drift '+k)
    for row in c['cases']:
        if hashlib.sha256(Path(row['checkpoint']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Recovery identity drift')
    return {'preflight':preflight,'requested':spec,'effective_recipe':{'motion_handoff':c},'execution_identity':preflight['execution_identity'],'requests':c['cases'],'simulation':0,'online_PPO':0,'offline_optimizer_updates':0,'files_written':0}


def json_value(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,dict):return {k:json_value(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_value(v) for v in value]
    return value

def atomic_result(folder,index,payload,arrays,cap,*,artifact_cap_bytes=None):
    payload=json_value(payload)
    encoded=json.dumps(payload,allow_nan=False)
    folder=Path(folder);tmp=folder/f'.trace_{index:02d}.tmp.npz';dest=folder/f'trace_{index:02d}.npz';jsonpath=folder/f'evaluation_{index:02d}.json'
    if dest.exists() or jsonpath.exists():raise FileExistsError('No result overwrite')
    try:
        np.savez_compressed(tmp,**arrays)
        payload['trace']={'path':dest.name,'sha256':hashlib.sha256(tmp.read_bytes()).hexdigest(),'arrays':{k:list(v.shape) for k,v in arrays.items()},'axes':'policy_sample,scored_env,feature'}
        encoded=json.dumps(payload,indent=2,allow_nan=False)
        added=tmp.stat().st_size+len(encoded.encode())
        if artifact_cap_bytes is not None and added>artifact_cap_bytes:raise RuntimeError('Evaluation artifact storage cap exceeded')
        if sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())+len(encoded.encode())>cap:raise RuntimeError('Handoff cumulative storage cap exceeded')
        part=jsonpath.with_suffix('.tmp');part.write_text(encoded)
        tmp.rename(dest)
        try:part.rename(jsonpath)
        except BaseException:
            dest.unlink();raise
    finally:
        if tmp.exists():tmp.unlink()
        part=jsonpath.with_suffix('.tmp')
        if part.exists():part.unlink()
    return jsonpath


def execute(args,spec):
    from native_stand.command_v6.completion import write
    from native_stand.command_v6.ledger import Ledger
    from native_stand.command_v6.tools.evaluate_checkpoint import batch_plan
    from native_stand.command_v6.train import record_run_configuration
    import torch
    from tensordict import TensorDict
    p=batch_plan(args,spec)
    if not args.run:print(json.dumps(p,indent=2));return 0
    if p['preflight']['status']!='PASS' or not args.attempt_id or not args.wall_limit_s:raise ValueError('Public reservation/preflight required')
    book=json.loads(Ledger(args.spec.with_name('budget.json')).path.read_text());attempt=book['attempts'].get(args.attempt_id)
    if not attempt or attempt['status']!='RUNNING' or attempt['output_dir']!=str(args.output.resolve()):raise ValueError('Exact reservation differs')
    start=attempt['started_unix_s'];deadline=start+args.wall_limit_s;app=env=None;completed=[];status='FAILED';failure=None;allsteps=scoredsteps=0;rows=spec['motion_handoff']['cases'];states=[{'index':i,'status':'NOT_RUN','condition':row} for i,row in enumerate(rows)]
    args.output.mkdir(exist_ok=False,parents=True);snapshot=record_run_configuration(args.output,args.spec)
    rng=torch.get_rng_state().clone();cuda_rng=None;buffers={};valid=[];index=None
    write(args.output/'manifest.json',{'attempt_id':args.attempt_id,'phase':'evaluate','spec_sha256':hashlib.sha256(args.spec.read_bytes()).hexdigest(),'asset_sha256':spec['asset_sha256'],'source_sha256':spec['source_sha256'],'source_snapshot_sha256':snapshot,'PPO':0,'optimizer':0,'protocol':spec['motion_handoff']['protocol'],'simulated_envs':64,'scored_envs':8})
    try:
        import sys
        sys.path.insert(0,spec['asset_module_root'])
        from isaaclab.app import AppLauncher
        app=AppLauncher({'headless':True,'device':'cuda:0','multi_gpu':False}).app
        from native_stand.command_v6.runtime.env import CommandEnvCfg
        from native_stand.command_v6.runtime.configure import apply,verify_asset_import
        from native_stand.command_v6.runtime.control_readback import verify,verify_ground
        from native_stand.command_v6.tools.model_factory import model
        from native_stand.recovery.handoff_runtime import HandoffEnv
        from native_stand.recovery.domain import Mode
        cfg=apply(CommandEnvCfg(),spec,envs=64,mode='evaluation');library=json.loads(Path(spec['recovery']['pose_library']).read_text())
        ms=json.loads(Path(spec['motion_handoff']['motion_spec']).read_text());dummy=TensorDict({'policy':torch.zeros(64,25,device='cuda:0'),'history':torch.zeros(64,125,device='cuda:0')},batch_size=[64])
        motion=model(dummy,actor=True,spec=ms).to('cuda:0');motion.load_state_dict(torch.load(spec['motion_handoff']['motion_checkpoint'],map_location='cuda:0',weights_only=False)['actor']);motion.eval();motion.requires_grad_(False)
        # Frozen STAND dependency not used for control; existing environment contract needs an injected actor.
        env=HandoffEnv(cfg,recovery_config=spec['recovery'],pose_library=library,stand_policy=motion,stage=spec['curriculum']['stages'][0],command_height=.36,reward_config=spec['reward'],schedule_s=spec['curriculum']['schedule_s'])
        env.configure_protocol(spec['motion_handoff']['protocol'])
        if spec['motion_handoff'].get('initialization_randomization'):
            env.configure_randomization(spec['motion_handoff']['initialization_randomization'])
        from native_stand.command_v6.runtime.execution_mode import apply as mode
        mode(env,'evaluation',family=rows[0]['family'])
        write(args.output/'runtime_readback.json',{'asset':verify_asset_import(spec),'control':verify(env),'ground':verify_ground(env,spec),'reference':env.reference[:8].cpu().tolist(),'joint_names':env.robot.joint_names,'body_names':env.robot.body_names,'active_indices':env.ids,'velocity_semantics':'root_lin_vel_w Isaac articulation root-link COM velocity property; native vx/vy/yaw from shared _motion_state, root pose is link frame','torque_sampling':'100Hz held values, not all200Hz/1kHz'})
        cuda_rng=torch.cuda.get_rng_state_all();motion_before={k:v.clone() for k,v in motion.state_dict().items()}
        for index,row in enumerate(rows):
            if time.time()>=deadline-100:status='STOPPED_BOUNDED';break
            states[index]['status']='INCOMPLETE';torch.manual_seed(row['seed']);torch.cuda.manual_seed_all(row['seed']);env.configure_case(row);env.select_initial_family(row['family'],'holdout');obs,_=env.reset()
            recovery_spec=spec
            if row.get('recovery_spec'):
                if hashlib.sha256(Path(row['recovery_spec']).read_bytes()).hexdigest()!=row['recovery_spec_sha256']:raise ValueError('Case Recovery spec SHA differs')
                recovery_spec=json.loads(Path(row['recovery_spec']).read_text())
            recovery=model(dummy,actor=True,spec=recovery_spec).to('cuda:0');recovery.load_state_dict(torch.load(row['checkpoint'],map_location='cuda:0',weights_only=False)['actor']);recovery.eval();recovery.requires_grad_(False);write(args.output/f'initial_state_{index:02d}.json',{'condition':row,'root_state':env.robot.data.root_state_w.torch[:8].cpu().tolist(),'joint_q':env.robot.data.joint_pos.torch[:8].cpu().tolist(),'joint_dq':env.robot.data.joint_vel.torch[:8].cpu().tolist(),'reference':env.reference[:8].cpu().tolist(),'initialization':'native direct zero reset' if index==0 else 'declared passive settle'});rec_before={k:v.clone() for k,v in recovery.state_dict().items()}
            active=torch.ones(8,device='cuda:0',dtype=torch.bool);buffers={};valid=[];switch_records=[]
            def add(k,v):buffers.setdefault(k,[]).append(v[:8].detach().cpu().numpy().copy())
            with torch.inference_mode():
                for step in range(round(row['seconds']/.01)):
                    if time.time()>=deadline-90:raise TimeoutError('Handoff wall budget exhausted')
                    initializing=env.fsm.mode==int(Mode.INITIALIZING);mot=(~initializing)&(env.executed_prefix>=env.switch_steps);rec=(~initializing)&~mot
                    action=torch.zeros((64,6),device='cuda:0');td=TensorDict(obs,batch_size=[64]);mo=env.motion_obs
                    if rec.any():action[rec]=recovery(td[rec],stochastic_output=False)
                    if mot.any():action[mot]=motion(TensorDict({'policy':mo['policy'][mot],'history':mo['history'][mot]},batch_size=[int(mot.sum())]),stochastic_output=False)
                    add('recovery_frame',td['policy']);add('recovery_history',td['history']);add('motion_frame',mo['policy']);add('motion_history',mo['history']);add('motion_previous_raw',mo['previous_action_readback']['raw']);add('motion_previous_input',mo['previous_action_readback']['clipped']);add('motion_previous_loss',mo['previous_action_readback']['information_loss'])
                    add('recovery_previous_input',env.action);from .motion_handoff import encode_executed
                    recprev=encode_executed(env.executed_leg,env.executed_wheel,env.reference,leg_scale=1.6,wheel_scale=100.);add('recovery_previous_raw',recprev['raw']);add('recovery_previous_loss',recprev['information_loss'])
                    add('root_pre',env.robot.data.root_state_w.torch);add('joint_q_pre',env.robot.data.joint_pos.torch);add('joint_dq_pre',env.robot.data.joint_vel.torch);add('target_pre',torch.cat((env.executed_leg,env.executed_wheel),-1))
                    oldcontroller=env.controller.clone();obs,reward,terminated,truncated,extra=env.step(action);done=terminated|truncated;allsteps+=64;scoredsteps+=int(active.sum())
                    add('state',env.recovery_snapshot);add('posture',env.standing_snapshot);add('geometry',env.wheel_geometry_snapshot);add('control',env.recovery_control_snapshot);add('controller',env.handoff_controller[:,None]);add('actor_valid',(env.handoff_controller==2)[:,None]);add('scoring_phase',torch.where((env.handoff_controller==2)&(env.rise_hold.entry>=0),3,env.handoff_controller)[:,None]);add('switch_event',((env.handoff_controller==2)&(oldcontroller!=2))[:,None]);add('recovery_controlled_clock_s',(env.executed_prefix*.01)[:,None]);add('root_post',env.handoff_root_post);add('motion_clock_s',env.handoff_motion_age[:,None]);add('initialization_clock_s',env.handoff_initial_age[:,None]);add('joint_q_post',env.handoff_joint_q_post);add('joint_dq_post',env.handoff_joint_dq_post);add('termination_causes',env.recovery_cause_snapshot);add('episode_result',env.episode_result_snapshot)
                    valid.append(active.cpu().numpy().copy());active&=~done[:8]
                    if not active.any():break
            if not all(torch.equal(v,recovery.state_dict()[k]) for k,v in rec_before.items()) or not all(torch.equal(v,motion.state_dict()[k]) for k,v in motion_before.items()):raise RuntimeError('Frozen model changed')
            arrays={k:np.stack(v) for k,v in buffers.items()};arrays['first_episode_valid']=np.stack(valid);arrays['policy_time_s']=np.arange(1,len(valid)+1)*.01
            results=[]
            for eid in range(8):
                m=arrays['first_episode_valid'][:,eid];st=torch.tensor(arrays['state'][m,eid]);po=torch.tensor(arrays['posture'][m,eid]);ctrl=torch.tensor(arrays['controller'][m,eid,0]);times=torch.tensor(arrays['policy_time_s'][m],dtype=st.dtype)
                result=score(st,po,ctrl==2,policy_time_s=times,configuration=spec['motion_handoff']['protocol']);result.update(env_id=eid,initial_valid=bool((st[:,29]>0).any()),actually_switched=bool((ctrl==2).any()))
                result['switch_state']=None
                switches=np.flatnonzero(arrays['controller'][m,eid,0]==2)
                if len(switches):
                    ii=int(switches[0]);original=np.flatnonzero(m)[ii];pre=arrays['root_pre'][original,eid];result['switch_state']={'policy_index':original,'root_state_pre':pre.tolist(),'previous_physical_target':arrays['target_pre'][original,eid].tolist(),'first_physical_target':np.r_[arrays['control'][original,eid,28:32],arrays['control'][original,eid,[20,23]]*100].tolist(),'motion_previous_outside_fraction':float((abs(arrays['motion_previous_raw'][original,eid])>1).mean()),'root_position_jump_at_switch':'no writes at switch; full pre/post state retained'}
                result['failure_stage']='passed' if result['accepted'] else 'initialization' if not result['initial_valid'] else 'prefix' if not result['actually_switched'] else 'settle' if result['entry_index'] is None else 'hold'
                result['channel_limit_fraction']=(abs(arrays['control'][m,eid,44:50])>=np.array([40,40,5.5,40,40,5.5])-1e-4).mean(0).tolist()
                results.append(result)
            payload={'condition':row,'protocol':spec['motion_handoff']['protocol'],'spec_sha256':hashlib.sha256(args.spec.read_bytes()).hexdigest(),'motion_sha256':spec['motion_handoff']['motion_sha256'],'checkpoint_sha256':row['sha256'],'per_env':results,'passed_envs':sum(r['accepted'] for r in results),'scored_envs':8,'accepted':all(r['accepted'] for r in results),'field_schema':{'state':'recovery_policy_trace_v1','control':'recovery_policy_trace_v1','geometry':'recovery_policy_trace_v1','joint_names':env.robot.joint_names,'active_indices':env.ids,'root_state':'pos_w3,quat_xyzw4,linear_velocity_w3,angular_velocity_w3'},'model_state_unchanged':True,'case_id':row.get('case_id',f'legacy_{index:02d}'),'randomization':spec['motion_handoff'].get('initialization_randomization',{'version':'none'}),'controller_codes':{'initialization':0,'Recovery':1,'receiver':2}}
            resultpath=atomic_result(args.output,index,payload,arrays,spec['motion_handoff']['max_storage_bytes']);states[index].update(status='COMPLETED',result=resultpath.name,passed_envs=payload['passed_envs']);completed.append({'index':index,'path':resultpath.name,'accepted':payload['accepted']})
            write(args.output/'progress.json',{'status':'RUNNING','actual_updates':0,'completed':completed,'conditions':states})
            if bool(arrays['state'][...,4].astype(bool).any()):raise RuntimeError('Runtime fault recorded; do not expand scan')
            if index==0 and not payload['accepted']:status='COMPLETED';break
        else:status='COMPLETED'
    except TimeoutError as exc:status='STOPPED_BOUNDED';failure={'reason':str(exc)}
    except BaseException as exc:
        failure={'reason':repr(exc),'traceback':traceback.format_exc()}
        if buffers and index is not None:
            try:
                partial={k:np.stack(v) for k,v in buffers.items() if len(v)==len(valid)}
                partial['first_episode_valid']=np.stack(valid)
                atomic_result(args.output,100+index,{'condition':rows[index],'status':'INCOMPLETE','accepted':False,'failure':failure},partial,spec['motion_handoff']['max_storage_bytes'])
            except BaseException as storage_exc:failure['partial_storage_error']=repr(storage_exc)
    finally:
        torch.set_rng_state(rng)
        if cuda_rng is not None:torch.cuda.set_rng_state_all(cuda_rng)
        write(args.output/'terminal_report.json',{'status':status,'attempt_id':args.attempt_id,'actual_updates':0,'samples':0,'online_PPO':0,'offline_optimizer_updates':0,'completed':completed,'conditions':states,'missing_requests':rows[len(completed):],'failure':failure,'wall_s':time.time()-start,'all_simulated_env_steps':allsteps,'scored_env_steps':scoredsteps,'cleanup':'monitor owns final exact-ID settlement'})
        # Existing cleanup helper API is verified by caller; fallback isolated error reporting.
        errors=[]
        for obj in (env,app):
            if obj is not None:
                try:obj.close()
                except BaseException as exc:errors.append(repr(exc))
        if errors:write(args.output/'cleanup_errors.json',{'errors':errors,'primary_failure':failure})
    return 1 if status=='FAILED' else 0
