"""GUI-only command input; same native physics, targets, PD and observation layout."""
import torch
from native_stand.command_v6.runtime.env import CommandEnv
from native_stand.command_v6.domain import contract


class InteractiveCommandEnv(CommandEnv):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.manual_command=torch.zeros(self.num_envs,3,device=self.device)
        self.manual_command[:,2]=self.command_height

    def _reset_idx(self,env_ids):
        super()._reset_idx(env_ids)
        if hasattr(self,'manual_command'):
            self.manual_command[slice(None) if env_ids is None else env_ids,:2]=0.

    def _pre_physics_step(self,actions):
        super()._pre_physics_step(actions)
        self.command.copy_(self.manual_command)

    def _get_observations(self):
        if not hasattr(self,'manual_command'):
            return super()._get_observations()
        angular,gravity=self._motion_state()
        data=self.robot.data
        self.command.copy_(self.manual_command)
        frame=contract.frame(angular,gravity,self.command,data.joint_pos.torch[:,self.ids],
            data.joint_vel.torch[:,self.ids],self.action,self.reference)
        self.history.copy_(contract.history(self.history,frame,self.history_needs_init))
        self.history_needs_init.fill_(False)
        return {'policy':frame,'history':self.history.clone()}
