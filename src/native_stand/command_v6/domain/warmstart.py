"""Exact B200 132-to-150 input expansion and explicit run boundaries."""
from contextlib import contextmanager
import torch


def columns():
    old=[]
    new=[]
    for frame in range(6):
        old.extend(range(frame*22,frame*22+6))
        old.extend(range(frame*22+6,(frame+1)*22))
        new.extend(range(frame*25,frame*25+6))
        new.extend(range(frame*25+9,(frame+1)*25))
    return old,new


def expand_state(source,target):
    if set(source)!=set(target):
        raise ValueError("model parameter names differ")
    old_cols,new_cols=columns()
    mapped={}
    for name,expected in target.items():
        value=source[name]
        if name=="mlp.0.weight":
            if value.shape!=(expected.shape[0],132) or expected.shape[-1]!=150:
                raise ValueError("first-layer shape differs")
            out=torch.zeros_like(expected)
            out[:,new_cols]=value[:,old_cols].to(out.device)
            mapped[name]=out
        else:
            if value.shape!=expected.shape:
                raise ValueError(f"shape mismatch: {name}")
            mapped[name]=value.to(expected.device).clone()
    return mapped


def expand_adam(source,optimizer,source_named,target_named,*,learning_rate):
    if not 0. < learning_rate < 1.:
        raise ValueError("adaptation learning rate must be in (0,1)")
    src=list(source_named)
    dst=list(target_named)
    if [n for n,_ in src]!=[n for n,_ in dst]:
        raise ValueError("Adam parameter names/order differ")
    state=optimizer.state_dict()
    source_group=source["param_groups"]
    target_group=state["param_groups"]
    if len(source_group)!=1 or len(target_group)!=1:
        raise ValueError("Adam parameter groups differ")
    old_ids=source_group[0]["params"]
    new_ids=target_group[0]["params"]
    if len(old_ids)!=len(src) or len(new_ids)!=len(dst):
        raise ValueError("Adam parameter count differs")
    old_cols,new_cols=columns()
    state["state"]={}
    for (name,old_param),(_,new_param),old_id,new_id in zip(src,dst,old_ids,new_ids):
        if old_id not in source["state"]:
            raise ValueError(f"Adam state missing: {name}")
        mapped={}
        for key,value in source["state"][old_id].items():
            if key in ("exp_avg","exp_avg_sq","max_exp_avg_sq") and name.endswith("mlp.0.weight"):
                out=torch.zeros_like(new_param,device="cpu")
                out[:,new_cols]=value[:,old_cols].cpu()
                mapped[key]=out
            else:
                mapped[key]=value.clone() if torch.is_tensor(value) else value
        state["state"][new_id]=mapped
    for key,value in source_group[0].items():
        if key not in ("params","lr"):
            state["param_groups"][0][key]=value
    state["param_groups"][0]["lr"]=learning_rate
    optimizer.load_state_dict(state)
    actual=optimizer.param_groups[0]["lr"]
    if actual!=learning_rate:
        raise RuntimeError("optimizer learning rate differs after Adam transfer")


def initialize_state(source, target, *, input_dim=132):
    if input_dim == 132:
        return expand_state(source,target)
    if input_dim != 150 or set(source) != set(target):
        raise ValueError('strict native source parameter names/input differ')
    if any(source[name].shape != value.shape for name,value in target.items()):
        raise ValueError('strict native source parameter shape differs')
    return {name:source[name].to(value.device).clone() for name,value in target.items()}


def wheel_parameter_scales(named, old_scale, new_scale):
    """Coordinate conversion for normalized wheel actions, not a torque change."""
    ratio=old_scale/new_scale
    if not 0<ratio<=1:
        raise ValueError('wheel envelope must not contract in this conversion')
    scales={}
    for name,param in named:
        scale=torch.ones_like(param)
        if name.endswith('mlp.0.weight'):
            if param.shape[-1]!=150:
                raise ValueError('wheel conversion requires150D native input')
            cols=[frame*25+column for frame in range(6) for column in (21,24)]
            scale[:,cols]=1/ratio
        scales[name]=scale
    return scales


def convert_wheel_envelope(actor, critic=None, optimizer=None, *, old_scale, new_scale):
    named=[('actor.'+n,p) for n,p in actor.named_parameters()]
    if critic is not None:
        named += [('critic.'+n,p) for n,p in critic.named_parameters()]
    scales=wheel_parameter_scales(named,old_scale,new_scale)
    with torch.no_grad():
        for name,param in named:
            scale=scales[name]
            param.mul_(scale)
            if optimizer is not None:
                state=optimizer.state[param]
                # Moments are gradient-coordinate quantities: inverse parameter scaling.
                state['exp_avg'].div_(scale)
                state['exp_avg_sq'].div_(scale.square())
                if 'max_exp_avg_sq' in state:
                    state['max_exp_avg_sq'].div_(scale.square())
    return {'old_wheel_scale_rad_s':old_scale,'new_wheel_scale_rad_s':new_scale,
            'output_and_std_factor':old_scale/new_scale,
            'output_factor_implementation':'explicit RSL Gaussian distribution; trainable std remains in source coordinates',
            'previous_action_input_column_factor':new_scale/old_scale,
            'moment_semantics':'inverse coordinate conversion; not identical future Adam updates',
            'equivalence_domain':'old normalized raw wheel action within[-1,1]; old clipping beyond this is not globally equivalent'}


def initialize_adam(source, optimizer, source_named, target_named, *, learning_rate, input_dim=132):
    if input_dim == 132:
        return expand_adam(source,optimizer,source_named,target_named,learning_rate=learning_rate)
    src,dst=list(source_named),list(target_named)
    if input_dim != 150 or [n for n,_ in src] != [n for n,_ in dst]:
        raise ValueError('strict native Adam parameter names/order differ')
    if any(a.shape != b.shape for (_,a),(_,b) in zip(src,dst)):
        raise ValueError('strict native Adam parameter shapes differ')
    target=optimizer.state_dict()
    if len(source['param_groups'])!=1 or len(target['param_groups'])!=1:
        raise ValueError('strict native Adam group count differs')
    old_ids=source['param_groups'][0]['params'];new_ids=target['param_groups'][0]['params']
    if len(old_ids)!=len(src) or len(new_ids)!=len(dst) or set(old_ids)!=set(source['state']):
        raise ValueError('strict native Adam state count differs')
    mapped={}
    for (name,param),old_id,new_id in zip(dst,old_ids,new_ids):
        values=source['state'][old_id]
        if not {'step','exp_avg','exp_avg_sq'} <= set(values):
            raise ValueError(f'Adam moments missing: {name}')
        if any(values[key].shape!=param.shape for key in ('exp_avg','exp_avg_sq')):
            raise ValueError(f'Adam moment shapes differ: {name}')
        mapped[new_id]={k:v.clone() if torch.is_tensor(v) else v for k,v in values.items()}
    group={**source['param_groups'][0],'params':new_ids,'lr':learning_rate}
    optimizer.load_state_dict({'state':mapped,'param_groups':[group]})
    if optimizer.param_groups[0]['lr'] != learning_rate:
        raise RuntimeError('strict native actual LR differs')


def clear_first_moment(optimizer):
    """Clear Adam signed history while preserving adaptive variance state."""
    cleared = 0
    for state in optimizer.state.values():
        moment = state.get('exp_avg')
        if moment is not None:
            moment.zero_()
            cleared += 1
    return cleared


def seed_training(seed, *, source=None, restore_source_rng=False):
    """Seed a new run; source RNG restoration is explicit and opt-in."""
    torch.manual_seed(int(seed))
    if not restore_source_rng or source is None:
        return {"seed": int(seed), "restored_source_rng": False}
    cpu = source.get("cpu_rng")
    cuda = source.get("cuda_rng")
    if cpu is None or cuda is None:
        raise ValueError("restore_source_rng requires cpu_rng and cuda_rng")
    torch.set_rng_state(cpu.cpu())
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all([state.cpu() for state in cuda])
    return {"seed": int(seed), "restored_source_rng": True}


@contextmanager
def preserve_rng_state():
    """Prevent evaluation random draws from changing subsequent PPO sampling."""
    cpu = torch.get_rng_state()
    cuda = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    try:
        yield
    finally:
        torch.set_rng_state(cpu)
        if cuda is not None:
            torch.cuda.set_rng_state_all(cuda)
