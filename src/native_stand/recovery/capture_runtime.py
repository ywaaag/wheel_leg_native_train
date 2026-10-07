"""Manual collection environment. No actor, reward learning, or automatic task reset."""
import torch
from native_stand.env import NativeStandEnv
from native_stand.command_v6.domain.contract import effort
from native_stand.recovery.capture_controls import clearance


class CaptureEnv(NativeStandEnv):
    def __init__(self,cfg,*,pose,controls,geometry,limits):
        self._is_closed=True
        self.capture_ready=False;self.initial_pose=pose;self.controls=controls
        self.executed_mode='PASSIVE'
        self.geometry=geometry;self.authored_limits=limits;self.fault=None
        super().__init__(cfg)
        self.shapes=[{**shape,'body_index':self.body_ids[shape['body']]} for shape in geometry]
        self.all_limits=torch.tensor([limits.get(n,[-float('inf'),float('inf')])
            for n in self.robot.joint_names],device=self.device)
        self.capture_ready=True

    def _reset_idx(self,env_ids):
        super()._reset_idx(env_ids)
        if not self.capture_ready:return
        ids=torch.arange(self.num_envs,device=self.device)
        p=self.initial_pose
        q=torch.tensor([[p['joint_pos'].get(n,0.) for n in self.robot.joint_names]],device=self.device)
        root=torch.tensor([[0.,0.,p['root_height_m'],*p['root_quaternion_xyzw']]],device=self.device)
        root[:,:3]+=self.scene.env_origins[ids]
        self.robot.write_root_pose_to_sim_index(root_pose=root,env_ids=ids)
        self.robot.write_root_velocity_to_sim_index(root_velocity=torch.zeros((1,6),device=self.device),env_ids=ids)
        self.robot.write_joint_position_to_sim_index(position=q,env_ids=ids)
        self.robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q),env_ids=ids)
        self.fault=None
        self.executed_mode='PASSIVE'

    def _pre_physics_step(self,actions):
        self.pd_counter=0
        self.executed_mode=self.controls.mode
        self.leg_target.copy_(torch.tensor([self.controls.targets],device=self.device))
        self.wheel_target.zero_()

    def _apply_action(self):
        if self.pd_counter%self.cfg.pd_interval_steps==0:
            if self.executed_mode=='PASSIVE':
                self.effort_pre.zero_();self.effort.zero_()
            else:
                d=self.robot.data
                request,applied=effort(d.joint_pos.torch[:,self.ids],d.joint_vel.torch[:,self.ids],
                    self.leg_target,self.wheel_target,leg_kp=self.cfg.leg_kp,
                    leg_kd=self.cfg.leg_kd,wheel_kv=self.cfg.wheel_kv)
                self.effort_pre.copy_(request);self.effort.copy_(applied)
        self.robot.set_joint_effort_target_index(target=self.effort,joint_ids=self.ids)
        self.pd_counter+=1

    def _get_dones(self):
        self._motion_state();self._closure()
        d=self.robot.data
        self.contact_force.copy_(self.sensor.data.net_forces_w.torch[:,self.wheel_sensor_ids].norm(dim=-1))
        self.gaps=clearance(d.body_pos_w.torch[0],d.body_quat_w.torch[0],self.shapes,self.cfg.ground_height_m)
        finite=torch.isfinite(d.root_state_w.torch).all()&torch.isfinite(d.joint_pos.torch).all()&torch.isfinite(d.joint_vel.torch).all()&torch.isfinite(self.effort).all()&torch.isfinite(self.gaps).all()
        q=d.joint_pos.torch[0]
        outside=((q<self.all_limits[:,0]-.001)|(q>self.all_limits[:,1]+.001)).any()
        causes={'nonfinite':not bool(finite),'closure':bool(self.closure_each.max()>self.cfg.closure_fault_m),
            'ground_penetration':bool(self.gaps.min()<-.005),'joint_limit':bool(outside)}
        if any(causes.values()):
            self.fault=causes
            raise RuntimeError(f'Manual pose physical fault: {causes}; no automatic reset')
        zeros=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        return zeros,zeros

    def _get_rewards(self):return torch.zeros(self.num_envs,device=self.device)
    def _get_observations(self):return {'policy':self.robot.data.joint_pos.torch[:,self.ids].clone()}
