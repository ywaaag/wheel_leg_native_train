"""Native physical-joint checkpoint diagnostic on read-only wheel_leg_sim2sim MJCF.

No virtual-leg mapping, equilibrium solver, compensation or model mutation.
Default is CPU identity/contract plan; --run creates a fresh bounded evidence run.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import mujoco
import numpy as np
import torch

JOINTS = ('left_hip_pitch', 'left_active_link_pitch', 'left_wheel_spin',
          'right_hip_pitch', 'right_active_link_pitch', 'right_wheel_spin')
ACTUATORS = ('left_hip_motor', 'left_active_hip_motor', 'left_wheel_motor',
             'right_hip_motor', 'right_active_hip_motor', 'right_wheel_motor')
LOOPS = (('left_node_site','left_upper_site'), ('left_parallel_site','left_lower_site'),
         ('right_node_site','right_upper_site'), ('right_parallel_site','right_lower_site'))
# CAD-to-upright frame is for geometry/roll reporting ONLY. Native actor uses CAD.
CAD_TO_UPRIGHT_REPORTING_ONLY = np.array([[0.,0.,-1.],[-1.,0.,0.],[0.,1.,0.]])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, payload):
    if path.exists():raise FileExistsError(path)
    from native_stand.command_v6.completion import write
    write(path,payload)


def obj(model, kind, name):
    index = mujoco.mj_name2id(model, kind, name)
    if index<0:raise ValueError('missing MJCF object '+name)
    return index


def binding(model):
    js=[obj(model,mujoco.mjtObj.mjOBJ_JOINT,n) for n in JOINTS]
    actuators=[obj(model,mujoco.mjtObj.mjOBJ_ACTUATOR,n) for n in ACTUATORS]
    if list(model.actuator_trnid[actuators,0])!=js:raise ValueError('actuator/joint mapping differs')
    gears=model.actuator_gear[actuators,0]
    if not np.isfinite(gears).all() or (np.abs(gears)<1e-12).any():raise ValueError('invalid signed transmission gear')
    return {'joints':js,'qpos':model.jnt_qposadr[js],'dofs':model.jnt_dofadr[js],
        'actuators':actuators,'gears':model.actuator_gear[actuators,0],
        'root':obj(model,mujoco.mjtObj.mjOBJ_BODY,'robot'),
        'ground':obj(model,mujoco.mjtObj.mjOBJ_GEOM,'ground'),
        'wheels':[obj(model,mujoco.mjtObj.mjOBJ_BODY,n) for n in ('left_wheel','right_wheel')],
        'loops':[(obj(model,mujoco.mjtObj.mjOBJ_SITE,a),obj(model,mujoco.mjtObj.mjOBJ_SITE,b)) for a,b in LOOPS]}


def state(model, data, refs):
    source_rotation=data.xmat[refs['root']].reshape(3,3)
    rotation=source_rotation@CAD_TO_UPRIGHT_REPORTING_ONLY.T
    velocity=np.zeros(6)
    mujoco.mj_objectVelocity(model,data,mujoco.mjtObj.mjOBJ_BODY,refs['root'],velocity,0)
    angular=source_rotation.T@velocity[:3]
    linear=source_rotation.T@velocity[3:]
    gravity=source_rotation.T@np.array([0.,0.,-1.])
    up=float(-gravity[1]);tilt=float(np.arccos(np.clip(up,-1,1)))
    roll=float(np.arctan2(rotation[2,1],rotation[2,2]))
    pitch=float(np.arcsin(np.clip(-rotation[2,0],-1,1)))
    offset=float((rotation.T@(data.xpos[refs['wheels'][0]]-data.xpos[refs['wheels'][1]]))[0])
    closure=max(np.linalg.norm(data.site_xpos[a]-data.site_xpos[b]) for a,b in refs['loops'])
    contact=np.zeros(2)
    for i in range(data.ncon):
        c=data.contact[i]
        if refs['ground'] not in (c.geom1,c.geom2):continue
        other=c.geom2 if c.geom1==refs['ground'] else c.geom1
        body=int(model.geom_bodyid[other])
        if body in refs['wheels']:
            force=np.zeros(6);mujoco.mj_contactForce(model,data,i,force)
            contact[refs['wheels'].index(body)]+=max(0.,force[0])
    from native_stand.command_v6.domain.posture_geometry import measure as geometry
    hips=data.xanchor[np.array(refs['joints'])[[0,3]]]
    shape=geometry(torch.from_numpy(hips)[None],torch.from_numpy(data.xpos[refs['wheels']])[None],
                   torch.from_numpy(source_rotation.copy())[None])
    measured={k:(bool(v[0]) if k=='valid' else float(v[0])) for k,v in shape.items()}
    return angular,gravity,{'vx':float(-linear[2]),'vy':float(-linear[0]),'yaw_rate':float(angular[1]),
        'height':float(data.xpos[refs['root'],2]),'up':up,'tilt':tilt,'roll':roll,'pitch':pitch,
        'wheel_offset_m':offset,'closure_m':float(closure),'contact_force_n':contact.tolist(),
        'root_xy':data.xpos[refs['root'],:2].tolist(),
        'measurement_point':'body_COM','root_position_w':data.xpos[refs['root']].tolist(),
        'root_quaternion_wxyz':data.xquat[refs['root']].tolist(),
        'COM_position_w':data.xipos[refs['root']].tolist(),
        'COM_linear_velocity_w':velocity[3:].tolist(),'angular_velocity_w':velocity[:3].tolist(),
        'posture_geometry':measured}


def plan(args):
    spec=json.loads(args.spec.read_text())
    from native_stand.command_v6.config import validate
    errors=validate(spec)
    if errors:raise ValueError(errors)
    if spec.get('task')=='recovery':raise ValueError('Motion checkpoint only')
    if not 0<args.wall_seconds<=1800:raise ValueError('wall bound must be 0..1800 seconds')
    commands=args.commands or [0,.5,-.5,1,-1,1.5,-1.5,2,-2,2.5,-2.5]
    if len(set(commands))!=len(commands) or any(not np.isfinite(c) or abs(c)>4 for c in commands):
        raise ValueError('commands must be distinct finite targets within +/-4')
    from native_stand.command_v6.tools.checkpoint_input import inspect
    info=inspect(args.checkpoint,spec,args.spec)
    if info['actor_input_dim']!=150:raise ValueError('MuJoCo diagnostic requires strict native150D actor')
    model=mujoco.MjModel.from_xml_path(str(args.xml));refs=binding(model)
    if model.nu!=6 or model.neq!=4 or not np.isclose(model.opt.timestep,.001):
        raise ValueError('MJCF topology/timestep differs')
    data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    _,gravity,initial=state(model,data,refs)
    if initial['closure_m']>1e-6 or not np.allclose(gravity,[0,-1,0],atol=1e-6):
        raise ValueError('initial CAD/native frame or closure invalid')
    native=np.array(spec['control']['effort_limits_nm'])
    ctrl=native/np.abs(refs['gears'])
    if np.any(ctrl>np.min(np.abs(model.actuator_ctrlrange[refs['actuators']]),axis=1)):
        raise ValueError('native torque request exceeds source actuator control range')
    inputs={str(p.resolve()):sha(p) for p in (args.spec,args.checkpoint,args.xml,Path(__file__))}
    import xml.etree.ElementTree as ET
    tree=ET.parse(args.xml)
    meshdir=tree.getroot().find('compiler').get('meshdir','')
    for mesh in tree.findall('./asset/mesh'):
        p=args.xml.parent/meshdir/mesh.get('file');inputs[str(p.resolve())]=sha(p)
    usd=Path(spec['asset_path'])
    if sha(usd)!=spec['asset_sha256']:raise ValueError('native USD SHA differs')
    inputs[str(usd)]=spec['asset_sha256']
    # Compare CAD zero-pose translation and mass without loading Isaac.
    from pxr import Usd,UsdGeom,UsdPhysics
    stage=Usd.Stage.Open(str(usd));cache=UsdGeom.XformCache();parity=[]
    for body in ('robot','left_upper_leg','right_upper_leg','left_active_link','right_active_link','left_wheel','right_wheel'):
        p=next(p for p in stage.Traverse() if p.GetName()==body and p.HasAPI(UsdPhysics.RigidBodyAPI))
        bid=obj(model,mujoco.mjtObj.mjOBJ_BODY,body)
        pos=np.asarray(cache.GetLocalToWorldTransform(p).ExtractTranslation())
        parity.append({'body':body,'initial_translation_error_m':float(np.linalg.norm(pos-data.xpos[bid])),
            'usd_mass_kg':float(UsdPhysics.MassAPI(p).GetMassAttr().Get()),'mj_mass_kg':float(model.body_mass[bid])})
    from native_stand.command_v6.domain.sim2sim_contract import resolve as contract_plan
    contract=contract_plan(spec)
    result={'semantic_contract':contract,'contract_status':'PASS_NATIVE_SEMANTICS_ONLY',
        'dynamics_parity_status':'UNKNOWN_NOT_CERTIFIED','checkpoint':info,'input_sha256':inputs,'topology':{'nq':model.nq,'nv':model.nv,'nu':model.nu,'neq':model.neq},
        'control':{'physics_dt':.001,'PD_dt':.005,'policy_dt':.01,'direct_physical_joints':JOINTS,
            'native_torque_limits_nm':native.tolist(),'motor_ctrl_limits':ctrl.tolist(),
            'transmission_gears':refs['gears'].tolist(),'compensation':False,'virtual_leg_mapping':False},
        'CAD_TO_UPRIGHT_FOR_GEOMETRY_ONLY':CAD_TO_UPRIGHT_REPORTING_ONLY.tolist(),
        'actor_observation_frame':'raw CAD body frame: initial gravity [0,-1,0]; native _motion_state',
        'velocity_convention':'vx=-linear_CAD_z, vy=-linear_CAD_x, yaw=angular_CAD_y, up=-gravity_CAD_y',
        'initial_state':initial,'CAD_parity':parity,
        'known_model_differences':{'ground_friction_MJ':model.geom_friction[refs['ground']].tolist(),
            'ground_friction_native':[.5,.5,0.],'active_MJ_damping':model.dof_damping[refs['dofs']].tolist(),
            'active_MJ_armature':model.dof_armature[refs['dofs']].tolist(),
            'collision_shapes':'reference MJCF proxies, not USD collider parity certified',
            'solver':'MuJoCo soft equality/contact vs PhysX; solver/inertia/guide-wheel parity not fully certified'},
        'protocol':{'commands':commands,
            'version':'native_mujoco_height034_v2' if spec['control']['height_command_m']==.34 else 'native_mujoco_legacy_v1',
            'height_mean_band_m':[.32,.36] if spec['control']['height_command_m']==.34 else [.34,.46],
            'duration_s':30,'schedule_s':[2,8,8,8],'hold_s':[10,18],'parking_s':[26,30],
            'seed':104,'environments_per_command':1,'physics_steps_per_command':30000},
        'simulation':0,'online_PPO':0,'files_written':0,
        'scope':'single deterministic reference-MJCF transfer diagnostic; not native multi-env certification',
        'budget_schema':'mujoco_diagnostic_budget_v1; distinct from native training ledger'}
    return spec,model,refs,result


def run_case(spec,model,refs,actor,target,deadline,viewer=None):
    from tensordict import TensorDict
    from native_stand.command_v6.domain.contract import frame,history,targets,effort
    from native_stand.command_v6.domain.command_schedule import effective
    data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    hist=torch.zeros(1,125);prev=torch.zeros(1,6);reference=torch.zeros(1,6)
    torque=np.zeros(6);leg=torch.zeros(1,4);wheel=torch.zeros(1,2)
    rows=[];failure=None;saturation=np.zeros(6);clipped_count=np.zeros(6)
    init=data.xpos[refs['root'],:2].copy();maximum=0.;actual_steps=0
    display=None
    start=time.monotonic()
    if viewer:
        from mujoco import viewer as mj_viewer
        display=mj_viewer.launch_passive(model,data)
        display.cam.type=mujoco.mjtCamera.mjCAMERA_TRACKING
        display.cam.trackbodyid=refs['root'];display.cam.distance=2.
        display.cam.azimuth=135.;display.cam.elevation=-15.
    try:
        return _advance_case(spec,model,refs,actor,target,deadline,data,hist,prev,reference,
            torque,leg,wheel,rows,failure,saturation,clipped_count,init,maximum,actual_steps,display,start)
    finally:
        if display:display.close()


def _advance_case(spec,model,refs,actor,target,deadline,data,hist,prev,reference,
                  torque,leg,wheel,rows,failure,saturation,clipped_count,init,maximum,actual_steps,display,start):
    from tensordict import TensorDict
    from native_stand.command_v6.domain.contract import frame,history,targets,effort
    from native_stand.command_v6.domain.command_schedule import effective
    for step in range(30000):
        if display and not display.is_running():failure='VIEWER_CLOSED';break
        if time.monotonic()>=deadline:failure='WALL_BUDGET';break
        if step%10==0:
            ang,grav,measure=state(model,data,refs)
            command=effective(torch.tensor([[target,0.]]),torch.tensor([data.time]),height=spec['control']['height_command_m'],entry=2,ramp=8,hold=8,exit=8)
            q=torch.tensor(data.qpos[refs['qpos']],dtype=torch.float32)[None,:]
            dq=torch.tensor(data.qvel[refs['dofs']],dtype=torch.float32)[None,:]
            obs=frame(torch.tensor(ang,dtype=torch.float32)[None,:],torch.tensor(grav,dtype=torch.float32)[None,:],command,q,dq,prev,reference)
            hist=history(hist,obs,torch.tensor([step==0]))
            action=actor(TensorDict({'policy':obs,'history':hist},batch_size=[1]),stochastic_output=False)
            if not torch.isfinite(action).all():failure='NONFINITE_ACTION';break
            clipped_count+=(action[0].abs()>1).numpy()
            prev,leg,wheel=targets(action,reference,leg_scale=spec['action']['leg_scale_rad'],combined_radius=spec['action']['leg_pair_radius_rad'],wheel_scale=spec['action']['wheel_scale_rad_s'])
        if step%5==0:
            q=torch.tensor(data.qpos[refs['qpos']],dtype=torch.float32)[None,:]
            dq=torch.tensor(data.qvel[refs['dofs']],dtype=torch.float32)[None,:]
            requested,applied=effort(q,dq,leg,wheel,leg_kp=spec['control']['leg_kp'],leg_kd=spec['control']['leg_kd'],wheel_kv=spec['control']['wheel_kv'])
            torque=applied[0].numpy();saturation+=(requested[0].abs()>=torch.tensor(spec['control']['effort_limits_nm'])).numpy()
            data.ctrl[refs['actuators']]=torque/refs['gears']
        mujoco.mj_step(model,data);actual_steps+=1
        if step%10==9:
            _,_,measure=state(model,data,refs)
            measure.update(time=float(data.time),command_vx=float(command[0,0]),action=prev[0].tolist(),
                actor_policy_25D=obs[0].tolist(),actor_history_125D=hist[0].tolist(),
                raw_action=action[0].tolist(),leg_target_rad=leg[0].tolist(),wheel_target_rad_s=wheel[0].tolist(),
                episode_id=0,policy_index=step//10,actor_sample_phase='pre_policy_step',
                state_sample_phase='post_policy_step',valid_pre_reset=True,
                joint_q=data.qpos[refs['qpos']].tolist(),joint_dq=data.qvel[refs['dofs']].tolist(),
                applied_joint_torque=torque.tolist(),actuator_joint_force=data.qfrc_actuator[refs['dofs']].tolist())
            rows.append(measure);maximum=max(maximum,np.linalg.norm(data.xpos[refs['root'],:2]-init))
            if display:
                display.sync()
                delay=data.time-(time.monotonic()-start)
                if delay>0:time.sleep(min(delay,.01))
            if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():failure='NONFINITE_STATE'
            elif measure['closure_m']>spec['control']['closure_fault_m']:failure='CLOSURE'
            elif measure['height']<spec['termination']['fall_root_height_m']:failure='HEIGHT'
            elif measure['up']<spec['termination']['minimum_up_cos']:failure='UPRIGHT'
            elif np.max(np.abs(data.qpos[refs['qpos']][[0,1,3,4]]))>spec['termination']['active_leg_angle_max_rad']:failure='JOINT_SAFETY'
            if failure:break
    hold=[r for r in rows if 10-1e-8<=r['time']<=18+1e-8]
    park=[r for r in rows if 26-1e-8<=r['time']<=30+1e-8]
    avg=lambda key,rs:float(np.mean([r[key] for r in rs])) if rs else None
    err=float(np.mean([abs(r['vx']-target) for r in hold])) if hold else None
    direction=float(np.mean([r['vx']*target>0 for r in hold])) if hold and target else None
    dual=float(np.mean([min(r['contact_force_n'])>5. for r in hold])) if hold else None
    failed=[]
    if failure:failed.append(failure)
    if actual_steps!=30000:failed.append('INCOMPLETE_EPISODE')
    if len(hold)<800:failed.append('MISSING_FULL_HOLD')
    if err is None or err>(.5 if target==0 else .3):failed.append('SPEED_ERROR')
    if target and (direction is None or direction<.95):failed.append('DIRECTION')
    if dual is None or dual<.95:failed.append('DUAL_CONTACT')
    if rows and max(r['tilt'] for r in rows)>.5:failed.append('TILT')
    height_band=(.32,.36) if spec['control']['height_command_m']==.34 else (.34,.46)
    if hold and not height_band[0]<=avg('height',hold)<=height_band[1]:failed.append('HEIGHT_MEAN')
    if hold and float(np.mean([abs(r['vy']) for r in hold]))>.02:failed.append('LATERAL_SPEED')
    if hold and float(np.mean([abs(r['yaw_rate']) for r in hold]))>.3:failed.append('YAW_LEAKAGE')
    summary={'target':target,'requested_physics_steps':30000,'completed_physics_steps':actual_steps,
        'continuous_s':actual_steps*.001,'full_window_completed':actual_steps==30000 and len(hold)>=800,
        'capability_certified':False,'passed_diagnostic_gate':not failed,'failed_checks':failed,'termination':failure,
        'hold_samples':len(hold),'vx_mean':avg('vx',hold),'MAE':err,'direction_fraction':direction,
        'dual_contact_fraction_5N':dual,'parking_abs_vx':float(np.mean([abs(r['vx']) for r in park])) if park else None,
        'peak_tilt':max((r['tilt'] for r in rows),default=None),
        'hold_roll_abs_mean':float(np.mean([abs(r['roll']) for r in hold])) if hold else None,
        'hold_wheel_offset_abs_mean_m':float(np.mean([abs(r['wheel_offset_m']) for r in hold])) if hold else None,
        'hold_left_leg_length_mean_m':float(np.mean([r['posture_geometry']['left_leg_length_m'] for r in hold])) if hold else None,
        'hold_right_leg_length_mean_m':float(np.mean([r['posture_geometry']['right_leg_length_m'] for r in hold])) if hold else None,
        'hold_leg_length_difference_abs_mean_m':float(np.mean([abs(r['posture_geometry']['leg_length_difference_m']) for r in hold])) if hold else None,
        'hold_ground_heading_offset_abs_mean_m':float(np.mean([abs(r['posture_geometry']['wheel_heading_offset_m']) for r in hold])) if hold else None,
        'closure_max_m':max((r['closure_m'] for r in rows),default=None),
        'height_hold_mean':avg('height',hold),'height_mean_band_m':list(height_band),'height_peak_full_m':max((r['height'] for r in rows),default=None),'max_excursion_m':float(maximum),
        'net_displacement_m':float(np.linalg.norm(data.xpos[refs['root'],:2]-init)),
        'PD_saturation_fraction_by_channel':(saturation/max(1,(actual_steps+4)//5)).tolist(),
        'action_clip_fraction_by_channel':(clipped_count/max(1,(actual_steps+9)//10)).tolist(),
        'final_policy_frame':obs[0].tolist() if rows else None}
    # Return full 100Hz traces only for these bounded diagnostics, never physics-step logs.
    return summary,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--xml',type=Path,default=Path('/home/kellen/wheel_leg_sim2sim/assets/wheeled_infantry.xml'))
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--wall-seconds',type=float,default=600.)
    p.add_argument('--commands',type=float,nargs='+',help='explicit targets; default full diagnostic list')
    p.add_argument('--viewer',action='store_true',help='passive MuJoCo GUI, real-time pacing, follows robot')
    p.add_argument('--run',action='store_true');a=p.parse_args()
    if a.output_dir.exists():raise FileExistsError(a.output_dir)
    task_started=time.monotonic()
    torch.set_num_threads(1)
    spec,model,refs,manifest=plan(a)
    if not a.run:print(json.dumps(manifest,indent=2));return
    from native_stand.command_v6.domain.experiment_naming import validate_new_experiment_name
    validate_new_experiment_name(a.output_dir.name)
    from native_stand.command_v6.learning import model as network
    from tensordict import TensorDict
    saved=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
    actor=network(TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]),actor=True,spec=spec)
    actor.load_state_dict(saved['actor'],strict=True);actor.eval()
    a.output_dir.mkdir(parents=True,exist_ok=False)
    save(a.output_dir/'manifest.json',manifest);save(a.output_dir/'spec.json',spec)
    started=task_started;deadline=started+a.wall_seconds-5.
    from native_stand.command_v6.completion import write as atomic_write
    summaries=[];attempts={};status='COMPLETED'
    try:
        with torch.inference_mode():
            for index,target in enumerate(manifest['protocol']['commands']):
                if time.monotonic()>=deadline:status='STOPPED_BOUNDED';break
                attempt=f'command_{index:02d}';attempts[attempt]={'status':'RUNNING','target':target,'online_PPO':0,
                    'case_identity_sha256':hashlib.sha256(json.dumps({'index':index,'target':target,
                        'checkpoint_sha256':manifest['checkpoint']['checkpoint_sha256'],'protocol':manifest['protocol']},sort_keys=True).encode()).hexdigest(),
                    'started_wall_s':time.monotonic()-started}
                atomic_write(a.output_dir/'budget.json',{'schema_version':'mujoco_diagnostic_budget_v1','authorization':'USER_REQUESTED_MUJOCO_VALIDATION',
                    'wall_limit_s':a.wall_seconds,'cleanup_reserve_s':5.,'max_cases':len(manifest['protocol']['commands']),'online_PPO_limit':0,'attempts':attempts})
                summary,trace=run_case(spec,model,refs,actor,target,deadline,viewer=a.viewer)
                summaries.append(summary);save(a.output_dir/f'{attempt}.json',{'summary':summary,'trace':trace})
                attempts[attempt].update(status='COMPLETED' if not summary['termination'] else 'STOPPED_BOUNDED',
                    actual_physics_steps=summary['completed_physics_steps'],settled=True,finished_wall_s=time.monotonic()-started)
                print(json.dumps(summary),flush=True)
                if summary['termination'] in ('NONFINITE_ACTION','NONFINITE_STATE','CLOSURE'):
                    status='FAILED';break
                if summary['termination'] in ('VIEWER_CLOSED','WALL_BUDGET'):
                    status='STOPPED_BOUNDED';break
    except BaseException as exc:
        status='FAILED'
        for record in attempts.values():
            if record['status']=='RUNNING':record.update(status='FAILED',settled=True,actual_physics_steps=None,
                reason=repr(exc),finished_wall_s=time.monotonic()-started)
        save(a.output_dir/'runtime_failure.json',{'error':repr(exc)})
        raise
    finally:
        result={'status':status,'wall_s':time.monotonic()-started,'online_PPO':0,'results':summaries,
            'process_completed':status=='COMPLETED',
            'all_windows_completed':all(r['full_window_completed'] for r in summaries) and len(summaries)==len(manifest['protocol']['commands']),
            'capability_certified':False,
            'all_passed':len(summaries)==len(manifest['protocol']['commands']) and all(r['passed_diagnostic_gate'] for r in summaries),
            'scope':manifest['scope'],'checkpoint_sha256':manifest['checkpoint']['checkpoint_sha256']}
        save(a.output_dir/'terminal_report.json',result)
        atomic_write(a.output_dir/'budget.json',{'schema_version':'mujoco_diagnostic_budget_v1','authorization':'USER_REQUESTED_MUJOCO_VALIDATION',
            'wall_limit_s':a.wall_seconds,'cleanup_reserve_s':5.,'wall_used_s':result['wall_s'],'online_PPO_limit':0,
            'actual_online_PPO':0,'attempts':attempts})
        lines=['# Native → MuJoCo transfer diagnostic','',manifest['scope'],'',
            '|command|completed s|vx|MAE|contact|roll abs|wheel offset m|failures|',
            '|---|---:|---|---|---|---|---|---|']
        for r in summaries:lines.append(f"|{r['target']}|{r['continuous_s']}|{r['vx_mean']}|{r['MAE']}|{r['dual_contact_fraction_5N']}|{r['hold_roll_abs_mean']}|{r['hold_wheel_offset_abs_mean_m']}|{r['failed_checks']}|")
        lines+=['','Model physics differences are recorded in manifest.json. No compensation or virtual-leg mapping.',
                'Failure on this reference MJCF does not establish native policy failure or physical impossibility.']
        with (a.output_dir/'report.md').open('x') as f:f.write('\n'.join(lines)+'\n')


if __name__=='__main__':main()
