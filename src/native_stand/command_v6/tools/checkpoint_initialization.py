"""CPU-only strict warmstart/std intervention audit, no optimizer step or exported model."""
import copy
import torch
from tensordict import TensorDict
from .model_factory import model
from ..domain.action_std import readback


def audit(spec,saved):
    rng=torch.get_rng_state().clone()
    try:
        observation=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
        actor=model(observation,actor=True,spec=spec);critic=model(observation,actor=False,spec=spec)
        actor.load_state_dict(saved['actor'],strict=True);critic.load_state_dict(saved['critic'],strict=True)
        for role,network in (('actor',actor),('critic',critic)):
            if saved.get('parameter_names',{}).get(role)!=list(dict(network.named_parameters())):
                raise ValueError('strict Adam parameter-name mapping missing or differs')
        optimizer=torch.optim.Adam([*actor.parameters(),*critic.parameters()],lr=spec['ppo']['learning_rate'])
        optimizer.load_state_dict(saved['optimizer']);before=copy.deepcopy(optimizer.state_dict())
        old=copy.deepcopy(actor.state_dict());old_critic=copy.deepcopy(critic.state_dict())
        intervention=spec.get('recovery',{}).get('exploration_initialization')
        readout=None
        if intervention:
            from native_stand.recovery.exploration import validate,initialize
            validate(spec);readout=initialize(actor,intervention,wheel_scale_rad_s=spec['action']['wheel_scale_rad_s'],leg_scale_rad=spec['action']['leg_scale_rad'])
        delta=[]
        for role,previous,current in [('actor',old,actor.state_dict()),('critic',old_critic,critic.state_dict())]:
            for name,value in current.items():
                change=(value-previous[name]).abs().max().item()
                delta.append({'parameter':role+'.'+name,'max_abs_difference':change})
                if change and name!='distribution.std_param':raise ValueError('unexpected warmstart parameter mutation')
        after=optimizer.state_dict()
        if before['param_groups']!=after['param_groups']:raise ValueError('Adam parameter groups changed')
        for key,state in before['state'].items():
            for name,value in state.items():
                if not torch.equal(value,after['state'][key][name]):raise ValueError('Adam changed during initialization')
        config={'parameterization':actor.distribution.std_type,
            'output_factor':getattr(actor.distribution,'output_factor',1.),
            'leg_scale_rad':spec['action']['leg_scale_rad'],'wheel_scale_rad_s':spec['action']['wheel_scale_rad_s']}
        return {'strict_actor_critic':True,'Adam_preserved':True,'optimizer_steps_executed':0,
            'parameter_differences':delta,'source_std':readback(old['distribution.std_param'],**config),
            'initialized_std':readback(actor.distribution.std_param,**config),'intervention':readout,
            'scope':'CPU initialization only; later checkpoints report learned std separately'}
    finally:torch.set_rng_state(rng)
