"""Native physical-joint standing task on the immutable colleague USD."""
import math
import torch
from gymnasium import spaces
from pxr import UsdGeom, UsdPhysics

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply, quat_apply_inverse

from agent_world.assets.rmuc_wheel_leg import RMUC_WHEEL_LEG_CFG
from native_stand.contract import (JOINT_NAMES,LEG_COLUMNS,WHEEL_COLUMNS,PHYSICAL_LIMITS,
                                   targets,physical_pd,frame_observation,update_history,stand_reward)

LOOPS=(
    ("left_node_link","left_upper_leg",(.005250,.088675,.069231),(.009000,-.064325,.069228)),
    ("left_parallel_link","left_lower_leg",(.006625,-.078620,.084618),(-.001500,.059840,.025380)),
    ("right_node_link","right_upper_leg",(-.005250,.088675,.069231),(-.009000,-.064325,.069228)),
    ("right_parallel_link","right_lower_leg",(-.006625,-.078620,.084618),(.001500,.059840,.025380)),
)


@configclass
class NativeSceneCfg(InteractiveSceneCfg):
    contact_forces=ContactSensorCfg(prim_path="{ENV_REGEX_NS}/Robot/.*",history_length=3)


@configclass
class NativeStandCfg(DirectRLEnvCfg):
    seed=20260930
    decimation=10
    episode_length_s=4.0
    fixed_base=False
    ground_static_friction=0.5
    ground_dynamic_friction=0.5
    ground_restitution=0.0
    ground_height_m=0.0
    ground_normal_axis="Z"
    ground_width_m=128.0
    ground_length_m=128.0
    ground_material_path="/World/native_ground_material"
    leg_position_scale_rad=0.1
    leg_pair_radius_rad=0.12
    wheel_speed_scale_rad_s=6.0
    leg_kp=60.0
    leg_kd=2.0
    wheel_kv=1.0
    pd_interval_steps=5
    closure_fault_m=0.005
    fall_root_height_m=0.20
    minimum_up_cos=0.5
    body_contact_max_n=200.0
    active_leg_angle_max_rad=0.5
    sim=SimulationCfg(dt=.001,device="cuda:0",render_interval=10)
    scene=NativeSceneCfg(num_envs=1,env_spacing=3.,replicate_physics=True)
    robot_cfg=RMUC_WHEEL_LEG_CFG.replace(prim_path="/World/envs/env_.*/Robot")
    observation_space={"policy":spaces.Box(-1e6,1e6,shape=(22,)),
                       "history":spaces.Box(-1e6,1e6,shape=(110,))}
    action_space=spaces.Box(-1.,1.,shape=(6,))
    state_space=spaces.Box(-1e6,1e6,shape=(22,))


class NativeStandEnv(DirectRLEnv):
    cfg:NativeStandCfg

    def __init__(self,cfg,**kwargs):
        cfg.robot_cfg=cfg.robot_cfg.copy()
        cfg.robot_cfg.init_state.pos=(0.,0.,0.)
        cfg.robot_cfg.init_state.rot=(0.,0.,0.,1.)
        cfg.robot_cfg.spawn.articulation_props.fix_root_link=bool(cfg.fixed_base)
        for group in ("leg_motors","wheel_motors"):
            cfg.robot_cfg.actuators[group].stiffness=0.
            cfg.robot_cfg.actuators[group].damping=0.
        super().__init__(cfg,**kwargs)
        self.ids=[int(self.robot.find_joints(name)[0][0]) for name in JOINT_NAMES]
        if len(set(self.ids))!=6:
            raise RuntimeError("Physical active joint binding is not one-to-one")
        self.body_ids={name:i for i,name in enumerate(self.robot.body_names)}
        self.wheel_body_ids=[self.body_ids[f"{side}_wheel"] for side in ("left","right")]
        self.wheel_sensor_ids=[self.sensor.body_names.index(f"{side}_wheel") for side in ("left","right")]
        self.forbidden_sensor_ids=[i for i,name in enumerate(self.sensor.body_names)
                                   if name not in ("left_wheel","right_wheel")
                                   and not name.startswith("guide_wheel_")]
        self.reference=torch.zeros((self.num_envs,6),device=self.device)
        self.action=torch.zeros((self.num_envs,6),device=self.device)
        self.previous_action=torch.zeros_like(self.action)
        self.history=torch.zeros((self.num_envs,110),device=self.device)
        self.history_needs_init=torch.ones(self.num_envs,dtype=torch.bool,device=self.device)
        self.leg_target=torch.zeros((self.num_envs,4),device=self.device)
        self.wheel_target=torch.zeros((self.num_envs,2),device=self.device)
        self.effort_pre=torch.zeros((self.num_envs,6),device=self.device)
        self.effort=torch.zeros_like(self.effort_pre)
        self.contact_force=torch.zeros((self.num_envs,2),device=self.device)
        self.slip_proxy=torch.zeros((self.num_envs,2),device=self.device)
        self.closure_each=torch.zeros((self.num_envs,4),device=self.device)
        self.root_height=torch.zeros(self.num_envs,device=self.device)
        self.up=torch.ones(self.num_envs,device=self.device)
        self.vx=torch.zeros(self.num_envs,device=self.device)
        self.vy=torch.zeros(self.num_envs,device=self.device)
        self.yaw=torch.zeros(self.num_envs,device=self.device)
        self.terminal_causes={}
        self.terminal_snapshot=[None for _ in range(self.num_envs)]
        self.reset_count=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.pd_counter=0

    def _setup_scene(self):
        self.robot=Articulation(self.cfg.robot_cfg)
        if not self.cfg.fixed_base:
            stage=self.sim.stage
            if stage.GetPrimAtPath("/World/ground").IsValid():
                raise RuntimeError("Ground prim already exists; overlapping colliders refused")
            ground=UsdGeom.Plane.Define(stage,"/World/ground")
            ground.CreateAxisAttr(self.cfg.ground_normal_axis)
            ground.CreateWidthAttr(self.cfg.ground_width_m)
            ground.CreateLengthAttr(self.cfg.ground_length_m)
            ground.AddTranslateOp().Set((0.,0.,self.cfg.ground_height_m))
            UsdPhysics.CollisionAPI.Apply(ground.GetPrim())
            material_path=self.cfg.ground_material_path
            material=sim_utils.RigidBodyMaterialCfg(
                static_friction=self.cfg.ground_static_friction,
                dynamic_friction=self.cfg.ground_dynamic_friction,
                restitution=self.cfg.ground_restitution)
            material.func(material_path,material)
            sim_utils.bind_physics_material("/World/ground",material_path,stage=stage)
            binding=ground.GetPrim().GetRelationship("material:binding:physics")
            if not binding.IsValid() or [str(path) for path in binding.GetTargets()]!=[material_path]:
                raise RuntimeError("Plane ground material binding failed")
        self.scene.clone_environments(copy_from_source=False)
        self.scene.articulations["robot"]=self.robot
        self.sensor=ContactSensor(self.cfg.scene.contact_forces)
        self.scene.sensors["contact_forces"]=self.sensor

    def _closure(self):
        pos=self.robot.data.body_pos_w.torch
        quat=self.robot.data.body_quat_w.torch
        out=[]
        for a,b,local_a,local_b in LOOPS:
            ia,ib=self.body_ids[a],self.body_ids[b]
            pa=torch.tensor(local_a,device=self.device,dtype=pos.dtype).expand(self.num_envs,-1)
            pb=torch.tensor(local_b,device=self.device,dtype=pos.dtype).expand(self.num_envs,-1)
            out.append(torch.linalg.vector_norm(pos[:,ia]+quat_apply(quat[:,ia],pa)
                                                -pos[:,ib]-quat_apply(quat[:,ib],pb),dim=-1))
        self.closure_each.copy_(torch.stack(out,dim=-1))

    def _motion_state(self):
        data=self.robot.data;root=data.root_quat_w.torch
        gravity=quat_apply_inverse(root,torch.tensor([[0.,0.,-1.]],device=self.device).expand(self.num_envs,-1))
        angular=quat_apply_inverse(root,data.root_ang_vel_w.torch)
        linear=quat_apply_inverse(root,data.root_lin_vel_w.torch)
        self.root_height.copy_(data.root_pos_w.torch[:,2])
        self.up.copy_(-gravity[:,1])
        self.vx.copy_(-linear[:,2]);self.vy.copy_(-linear[:,0])
        self.yaw.copy_(angular[:,1])
        return angular,gravity

    def _pre_physics_step(self,actions):
        self.previous_action.copy_(self.action)
        clipped,leg,wheel=targets(actions,self.reference,
            leg_scale=self.cfg.leg_position_scale_rad,
            wheel_scale=self.cfg.wheel_speed_scale_rad_s,
            combined_radius=self.cfg.leg_pair_radius_rad)
        self.action.copy_(clipped);self.leg_target.copy_(leg);self.wheel_target.copy_(wheel)
        self.pd_counter=0

    def _apply_action(self):
        if self.pd_counter%self.cfg.pd_interval_steps==0:
            data=self.robot.data
            q=data.joint_pos.torch[:,self.ids]
            dq=data.joint_vel.torch[:,self.ids]
            pre,effort=physical_pd(q,dq,self.leg_target,self.wheel_target,
                kp=self.cfg.leg_kp,kd=self.cfg.leg_kd,kv=self.cfg.wheel_kv)
            self.effort_pre.copy_(pre);self.effort.copy_(effort)
        self.robot.set_joint_effort_target_index(target=self.effort,joint_ids=self.ids)
        self.pd_counter+=1

    def _get_dones(self):
        data=self.robot.data
        self._motion_state();self._closure()
        forces=torch.linalg.vector_norm(self.sensor.data.net_forces_w.torch[:,self.wheel_sensor_ids],dim=-1)
        self.contact_force.copy_(forces)
        root=data.root_pos_w.torch
        wheel_vel=data.body_lin_vel_w.torch[:,self.wheel_body_ids]
        wheel_omega=data.body_ang_vel_w.torch[:,self.wheel_body_ids]
        r=torch.tensor([0.,0.,-.06],device=self.device).expand_as(wheel_vel)
        point_v=wheel_vel+torch.cross(wheel_omega,r,dim=-1)
        self.slip_proxy.copy_(torch.linalg.vector_norm(point_v[:,:,:2],dim=-1))
        body_force=torch.linalg.vector_norm(self.sensor.data.net_forces_w.torch[:,self.forbidden_sensor_ids],dim=-1).amax(-1)
        q=data.joint_pos.torch[:,self.ids]
        nonfinite=(~torch.isfinite(data.root_state_w.torch).all(-1)|
                   ~torch.isfinite(data.joint_pos.torch).all(-1)|
                   ~torch.isfinite(data.joint_vel.torch).all(-1)|
                   ~torch.isfinite(self.effort).all(-1))
        closure=self.closure_each.amax(-1)>self.cfg.closure_fault_m
        self.terminal_causes={"nonfinite":nonfinite,"closure":closure,
            "height":root[:,2]<self.cfg.fall_root_height_m,
            "tilt":self.up<self.cfg.minimum_up_cos,
            "body_contact":body_force>self.cfg.body_contact_max_n,
            "joint_safety":(q[:,list(LEG_COLUMNS)].abs()>self.cfg.active_leg_angle_max_rad).any(-1)}
        ordinary=(self.terminal_causes["height"]|self.terminal_causes["tilt"]|
                  self.terminal_causes["body_contact"]|self.terminal_causes["joint_safety"])
        fault=nonfinite|closure
        terminated=ordinary|fault
        time_out=self.episode_length_buf>=self.max_episode_length-1
        for i in torch.nonzero(terminated|time_out,as_tuple=False).flatten().tolist():
            self.terminal_snapshot[i]={"env_id":i,"episode_id":int(self.reset_count[i]),
                "root_pos_w":root[i].detach().cpu().tolist(),
                "root_quat_xyzw":data.root_quat_w.torch[i].detach().cpu().tolist(),
                "vx_mps":float(self.vx[i]),"vy_mps":float(self.vy[i]),
                "yaw_rad_s":float(self.yaw[i]),"up_cos":float(self.up[i]),
                "q_active":q[i].detach().cpu().tolist(),
                "dq_active":data.joint_vel.torch[i,self.ids].detach().cpu().tolist(),
                "wheel_contact_n":self.contact_force[i].detach().cpu().tolist(),
                "closure_each_m":self.closure_each[i].detach().cpu().tolist(),
                "slip_proxy_mps":self.slip_proxy[i].detach().cpu().tolist(),
                "effort_nm":self.effort[i].detach().cpu().tolist(),
                "causes":{name:bool(mask[i]) for name,mask in self.terminal_causes.items()},
                "time_out":bool(time_out[i])}
        return terminated,time_out

    def _get_rewards(self):
        q=self.robot.data.joint_pos.torch[:,self.ids]
        reward,raw,weighted=stand_reward(self.root_height,self.up,self.vx,self.vy,self.yaw,
            self.contact_force>2.,self.effort,self.action,self.previous_action,
            q[:,list(LEG_COLUMNS)],self.reset_terminated,dt=self.step_dt)
        self.extras["native_stand"]={"raw":{k:float(v.mean()) for k,v in raw.items()},
            "weighted":{k:float(v.mean()) for k,v in weighted.items()},
            "termination_counts":{k:int(v.sum()) for k,v in self.terminal_causes.items()},
            "contact_fraction":float((self.contact_force>2.).all(-1).float().mean()),
            "closure_max_m":float(self.closure_each.max()),
            "slip_proxy_contact_mean_mps":float((self.slip_proxy*(self.contact_force>2.)).mean())}
        return reward

    def _get_observations(self):
        angular,gravity=self._motion_state()
        data=self.robot.data
        q=data.joint_pos.torch[:,self.ids];dq=data.joint_vel.torch[:,self.ids]
        frame=frame_observation(angular,gravity,q,dq,self.action,self.reference)
        self.history.copy_(update_history(self.history,frame,self.history_needs_init))
        self.history_needs_init.fill_(False)
        return {"policy":frame,"history":self.history.clone()}

    def _reset_idx(self,env_ids):
        if env_ids is None:
            env_ids=torch.arange(self.num_envs,device=self.device)
        super()._reset_idx(env_ids)
        ids=env_ids.to(dtype=torch.long)
        n=len(ids)
        pose=torch.zeros((n,7),device=self.device)
        pose[:,:3]=self.scene.env_origins[ids]
        pose[:,2]+=.4
        pose[:,3]=math.sqrt(.5);pose[:,6]=math.sqrt(.5)
        self.robot.write_root_pose_to_sim_index(root_pose=pose,env_ids=ids)
        self.robot.write_root_velocity_to_sim_index(root_velocity=torch.zeros((n,6),device=self.device),env_ids=ids)
        q=torch.zeros((n,self.robot.num_joints),device=self.device)
        self.robot.write_joint_position_to_sim_index(position=q,env_ids=ids)
        self.robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q),env_ids=ids)
        self.action[ids]=0.;self.previous_action[ids]=0.
        self.effort[ids]=0.;self.effort_pre[ids]=0.
        self.history[ids]=0.;self.history_needs_init[ids]=True
        self.reset_count[ids]+=1
