"""Read-only CAD-frame, recorded Isaac first-action and control parity audit."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import mujoco
import numpy as np
import torch
from pxr import Usd,UsdPhysics,Gf
from tensordict import TensorDict

ROOT=Path(__file__).resolve().parents[4]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(output,*,spec_path,checkpoint,checkpoint_sha256,raw_path,frozen,xml):
    from native_stand.command_v6.domain.contract import frame, history
    from native_stand.command_v6.learning import model as actor_model
    inputs={str(Path(__file__).resolve()):digest(Path(__file__))}
    def read(p):
        inputs[str(p)]=digest(p)
        return json.loads(p.read_text())
    spec_path,checkpoint,raw_path,frozen,xml=map(lambda p:Path(p).resolve(),(spec_path,checkpoint,raw_path,frozen,xml))
    spec=read(spec_path)
    if digest(checkpoint)!=checkpoint_sha256:
        raise ValueError('checkpoint SHA differs')
    inputs[str(checkpoint)]=digest(checkpoint)
    from native_stand.command_v6.tools.evaluation_loader import load
    from native_stand.command_v6.tools.trace_loader import control_tensor,group
    from native_stand.command_v6.domain.sim2sim_contract import resolve as native_contract
    manifest=read(raw_path.parent/'manifest.json')
    raw,evidence=load(raw_path.parent,{'evaluation':raw_path.name,'checkpoint_sha256':checkpoint_sha256},
        spec_sha256=manifest['spec_sha256'],checkpoint_sha256=checkpoint_sha256,asset_sha256=spec['asset_sha256'])
    inputs[evidence['path']]=evidence['sha256']
    if raw['checkpoint_sha256']!=inputs[str(checkpoint)]:raise ValueError('Isaac checkpoint identity differs')
    inputs[str(frozen)]=digest(frozen)
    source=frozen.read_text()
    if 'self.up.copy_(-gravity[:,1])' not in source or 'self.vx.copy_(-linear[:,2])' not in source:
        raise ValueError('frozen native body convention differs')
    script=ROOT/'scripts/validate_native_mujoco.py'
    inputs[str(script)]=digest(script)
    module_spec=importlib.util.spec_from_file_location('native_mj_parity',script)
    adapter=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(adapter)
    inputs[str(xml)]=digest(xml)
    mj=mujoco.MjModel.from_xml_path(str(xml));refs=adapter.binding(mj);data=mujoco.MjData(mj)
    mujoco.mj_forward(mj,data)
    angular,gravity,initial=adapter.state(mj,data,refs)
    usd=Path(spec['asset_path']);inputs[str(usd)]=digest(usd)
    if inputs[str(usd)]!=spec['asset_sha256']:raise ValueError('USD SHA differs')
    stage=Usd.Stage.Open(str(usd));axes=[]
    for prim in stage.Traverse():
        if not prim.IsA(UsdPhysics.RevoluteJoint):continue
        joint=UsdPhysics.RevoluteJoint(prim)
        index=mujoco.mj_name2id(mj,mujoco.mjtObj.mjOBJ_JOINT,prim.GetName())
        if index<0:continue
        axis=Gf.Vec3d(*{'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[joint.GetAxisAttr().Get()])
        q=joint.GetLocalRot0Attr().Get();rotation=Gf.Rotation(Gf.Quatd(q.GetReal(),Gf.Vec3d(q.GetImaginary())))
        usd_axis=np.array(rotation.TransformDir(axis))
        axes.append({'joint':prim.GetName(),'USD_axis_in_parent':usd_axis.tolist(),
            'MJ_axis':mj.jnt_axis[index].tolist(),'max_difference':float(np.max(np.abs(usd_axis-mj.jnt_axis[index])))})
    contract=native_contract(spec)
    obs=frame(torch.tensor(angular,dtype=torch.float32)[None,:],
        torch.tensor(gravity,dtype=torch.float32)[None,:],torch.tensor([[0.,0.,spec['control']['height_command_m']]]),
        torch.zeros(1,6),torch.zeros(1,6),torch.zeros(1,6),torch.zeros(1,6))
    hist=history(torch.zeros(1,125),obs,torch.tensor([True]))
    actor=actor_model(TensorDict({'policy':obs,'history':hist},batch_size=[1]),actor=True,spec=spec)
    actor.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=False)['actor']);actor.eval()
    with torch.inference_mode():
        action=actor(TensorDict({'policy':obs,'history':hist},batch_size=[1]),stochastic_output=False)[0].numpy()
        wrong=obs.clone();wrong[:,3:6]=torch.tensor([[0.,0.,-1.]])
        wrong_action=actor(TensorDict({'policy':wrong,'history':wrong.repeat(1,5)},batch_size=[1]),stochastic_output=False)[0].numpy()
    trace=control_tensor(raw,allow_legacy_axes=True)
    controls=trace['values'];valid=trace['valid']
    if not len(controls) or not valid[0,0]:raise ValueError('First native control sample unavailable')
    native_first=group(trace,'raw_action')[0]
    clipped=group(trace,'clipped_action');targets=group(trace,'leg_target_after_projection')
    output_applied=group(trace,'actuator_applied_nm');physical=group(trace,'physical_clipped_nm')
    def maximum(value):
        selected=value[valid]
        return float(np.max(np.abs(selected))) if selected.size else None
    dynamics=[{'property':'root_body_mass_kg','native':None,'reference':float(mj.body_mass[refs['root']]),'status':'UNKNOWN_NATIVE_COMPILED_VALUE'},
        {'property':'ground_friction','native_declared':spec['ground'],'reference':mj.geom_friction[refs['ground']].tolist(),'status':'DIFFERENT_REPRESENTATIONS'},
        {'property':'active_damping','native':None,'reference':mj.dof_damping[refs['dofs']].tolist(),'status':'UNKNOWN_NATIVE_RUNTIME'},
        {'property':'active_armature','native':None,'reference':mj.dof_armature[refs['dofs']].tolist(),'status':'UNKNOWN_NATIVE_RUNTIME'},
        {'property':'solver','native':'PhysX','reference':'MuJoCo','status':'DIFFERENT'},
        {'property':'collider_inertia_drive_parity','native':None,'reference':None,'status':'UNKNOWN_NOT_CERTIFIED'}]
    result={'semantic_contract':contract,'evidence':evidence,
        'dynamics_difference_table':dynamics,'dynamics_parity_status':'NOT_CERTIFIED',
        'trace_schema':{k:trace[k] for k in ('schema_version','axes','shape','axis_identity_origin')},
        'input_sha256':inputs,'native_frozen_convention':{
        'actor_angular_gravity':'raw CAD body frame, NOT Fudan canonical frame',
        'up':'-gravity[1]','vx':'-linear[2]','vy':'-linear[0]','yaw':'angular[1]'},
        'initial_gravity':gravity.tolist(),'initial_policy_frame':obs[0].tolist(),
        'corrected_initial_action':action.tolist(),'wrong_frame_initial_action':wrong_action.tolist(),
        'native_recorded_initial_actions':[r.tolist() if ok else None for r,ok in zip(native_first,valid[0])],
        'corrected_action_max_difference':float(np.max(np.abs(native_first[0]-action))),
        'wrong_action_max_difference':float(np.max(np.abs(native_first[0]-wrong_action))),
        'first_action_difference_by_env':[float(np.max(np.abs(r-action))) if ok else None for r,ok in zip(native_first,valid[0])],
        'initial_action_scope':'env0 zero-state parity; other envs may have different reset/readback and are reported without equality claim',
        'reset_history_matches_repeat':bool(torch.equal(hist,obs.repeat(1,5))),
        'joint_axis_parity':axes,
        'native_leg_target_vs_clipped_action_max_difference':maximum(targets-clipped[:,:,[0,1,3,4]]*spec['action']['leg_scale_rad']),
        'native_actuator_vs_physical_clipped_max_difference_Nm':maximum(output_applied-physical),
        'native_control_records':int(valid.sum()),
        'native_control_layout':'policy_time, scored_env, channel',
        'PD_replay_limitation':'native records policy-end q/dq with preceding5ms held torque; cannot recompute exact PD request using end-state',
        'initial_model_state':initial,'new_Isaac_simulation':0,'PPO_updates':0,
        'scope':'static zero-pose/frame and actual recorded first-action parity; full dynamic root-state parity not certified'}
    result['static_first_action_gate_passed']=result['corrected_action_max_difference']<=1e-5
    result['full_dynamic_parity']='MISSING_EVIDENCE:matched full actor inputs/root state in both engines'
    result['leg_target_comparison_scope']='declared scales with zero reference; cannot certify arbitrary reset references from control trace alone'
    if 'paired_state' in raw:
        from native_stand.command_v6.tools.trace_loader import paired_tensor
        pairs=paired_tensor(raw);indices=np.argwhere(pairs['valid'] & valid)[:64]
        policy=group(pairs,'actor_policy_25D');history_values=group(pairs,'actor_history_125D')
        action_values=group(pairs,'raw_action')
        if len(indices):
            tt,ee=indices.T
            with torch.inference_mode():
                replay=actor(TensorDict({'policy':torch.tensor(policy[tt,ee],dtype=torch.float32),
                    'history':torch.tensor(history_values[tt,ee],dtype=torch.float32)},batch_size=[len(indices)]),stochastic_output=False).numpy()
            result['captured_actor_replay']={'samples':len(indices),'indices_time_env':indices.tolist(),
                'max_raw_action_error':float(np.max(np.abs(replay-action_values[tt,ee]))),
                'scope':'CPU actor replay on measured frozen inputs; not new physical trajectory'}
    else:result['captured_actor_replay']={'status':'MISSING_EVIDENCE:actor input/history'}
    if output is not None:
        from native_stand.command_v6.tools.experiment_preparation import publish
        publish(output,{'parity.json':result},inputs,completion_marker=True)
    print(json.dumps({k:result[k] for k in ('initial_gravity','corrected_action_max_difference',
        'wrong_action_max_difference','native_control_records','native_actuator_vs_physical_clipped_max_difference_Nm')},indent=2))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path)
    for name in ('spec','checkpoint','evaluation','native-env-source','xml'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--checkpoint-sha256',required=True);a=p.parse_args()
    audit(a.output_dir,spec_path=a.spec,checkpoint=a.checkpoint,checkpoint_sha256=a.checkpoint_sha256,
        raw_path=a.evaluation,frozen=a.native_env_source,xml=a.xml)

if __name__=='__main__':main()
