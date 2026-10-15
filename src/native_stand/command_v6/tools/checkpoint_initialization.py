"""CPU-only strict warmstart/std intervention audit, no optimizer step or exported model."""
import copy
import torch
from tensordict import TensorDict
from .model_factory import model
from ..domain.action_std import readback


def audit(spec,saved):
    rng=torch.get_rng_state().clone()
    try:
        if spec.get('student_training',{}).get('version')=='student_motion31_training_v1':
            from native_stand.students.model import load,Student
            actor,data=load(spec['source_checkpoint'],'MotionZeroStudent')
            if any(not torch.equal(v,data['actor'][k]) for k,v in actor.state_dict().items()):raise ValueError('Motion Actor restoration differs')
            critic=Student(False,version='multiskill_mcu_v2',critic_privileged_version='motion_privileged49_v1')
            actor.log_std.requires_grad_(False)
            optimizer=torch.optim.Adam([*actor.parameters(),*critic.parameters()],lr=spec['ppo']['learning_rate'])
            continuation=spec['motion_training']['resume']
            successor=spec['motion_training'].get('successor')
            course=spec.get('motion_course')
            if course:
                from native_stand.students.motion_course_requests import verify
                verify(spec);critic.load_state_dict(data['critic']);optimizer.load_state_dict(data['optimizer'])
            if successor:
                from native_stand.students.motion_successor import verify
                verify(spec);critic.load_state_dict(data['critic']);optimizer.load_state_dict(data['optimizer'])
                if any(not torch.equal(v,data['critic'][k]) for k,v in critic.state_dict().items()):raise ValueError('successor Critic restoration differs')
                restored=optimizer.state_dict()
                if restored['param_groups']!=data['optimizer']['param_groups']:raise ValueError('successor Adam groups differ')
                for index,state in data['optimizer']['state'].items():
                    for key,value in state.items():
                        actual=restored['state'][index][key]
                        if isinstance(value,torch.Tensor):
                            if not torch.equal(actual,value):raise ValueError('successor Adam tensors differ')
                        elif actual!=value:raise ValueError('successor Adam state differs')
            if continuation:
                from native_stand.students.motion_training_requests import verify_continuation
                verify_continuation(spec);critic.load_state_dict(data['critic']);optimizer.load_state_dict(data['optimizer'])
            return {'strict_actor':True,'critic_version':'motion_privileged49_v1','critic_shape':list(critic.mlp[0].weight.shape),
                'source_critic_loaded':bool(continuation or successor or course),'Adam_preserved':bool(continuation or successor or course),'new_Adam_empty':not optimizer.state,
                'source_std_normalized':actor.log_std.exp().detach().tolist(),'actual_LR':[g['lr'] for g in optimizer.param_groups],
                'optimizer_steps_executed':0,'RNG_available':data.get('training_rng') is not None,
                'scope':'CPU shape/Actor/std/Adam initialization; no physical simulation or optimizer step'}
        observation=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
        actor=model(observation,actor=True,spec=spec);critic=model(observation,actor=False,spec=spec)
        from .model_adapter import ModelAdapter
        adapter=ModelAdapter(saved);adapter.validate(spec,require_optimizer=True);adapter.load(actor,'actor');adapter.load(critic,'critic')
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
