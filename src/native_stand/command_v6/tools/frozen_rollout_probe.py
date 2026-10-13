"""Owned evaluator adapter: two real PPO rollouts,returns only,never optimizer.step."""
import copy,time
from pathlib import Path
import numpy as np
import torch


def tree_equal(a,b):
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(tree_equal(v,b[k]) for k,v in a.items())
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(tree_equal(x,y) for x,y in zip(a,b))
    return a==b


def _collect(actor,wrapped,env,*,spec,output,stop_requested):
    from rsl_rl.algorithms import PPO
    from rsl_rl.storage import RolloutStorage
    from native_stand.command_v6.tools.model_factory import model
    from native_stand.command_v6.domain.warmstart import initialize_adam
    from native_stand.command_v6.tools.experiment_preparation import digest
    from native_stand.recovery.domain import Mode
    from native_stand.command_v6.domain.rollout_probe import validate
    validate(spec)
    saved=torch.load(spec['source_checkpoint'],map_location='cpu',weights_only=False)
    if digest(spec['source_checkpoint'])!=spec['source_sha256']:raise ValueError('Source changed')
    env.curriculum_training=True;env.continuous_evaluation=False
    torch.manual_seed(spec['seed']);obs,_=env.reset();obs=wrapped.get_observations()
    critic=model(obs,actor=False,spec=spec).to(env.device);critic.load_state_dict(saved['critic'],strict=True)
    storage=RolloutStorage('rl',64,128,obs,[6],env.device)
    ppo=PPO(actor,critic,storage,num_learning_epochs=spec['ppo']['epochs'],num_mini_batches=spec['ppo']['minibatches'],
        clip_param=.2,gamma=spec['ppo']['gamma'],lam=spec['ppo']['lam'],value_loss_coef=.5,
        entropy_coef=spec['ppo']['entropy_coef'],learning_rate=spec['ppo']['learning_rate'],
        max_grad_norm=1.,use_clipped_value_loss=False,schedule='fixed',desired_kl=.01,device=env.device)
    old=[('actor.'+n,p) for n,p in saved['actor'].items()]+[('critic.'+n,p) for n,p in saved['critic'].items()]
    new=[('actor.'+n,p) for n,p in actor.named_parameters()]+[('critic.'+n,p) for n,p in critic.named_parameters()]
    initialize_adam(saved['optimizer'],ppo.optimizer,old,new,input_dim=150,learning_rate=spec['ppo']['learning_rate'])
    before=[copy.deepcopy(x.state_dict()) for x in (actor,critic,ppo.optimizer)]
    oldmode=(actor.training,critic.training);actor.train();critic.train()
    arrays=[];names=None;family=[p['family'] for p in env.pose_library['poses']];family_names=list(dict.fromkeys(family))
    family_codes=torch.tensor([family_names.index(f) for f in family],device=env.device)
    try:
        with torch.inference_mode():
            for rollout in range(2):
                rows={}
                def put(k,v):rows.setdefault(k,[]).append(v.detach().clone())
                for step in range(128):
                    if stop_requested():raise TimeoutError('Frozen rollout wall/stop reached')
                    controlled=env.initialization_checked&(env.fsm.mode==int(Mode.RECOVERY))
                    put('pre_obs150',torch.cat((obs['policy'],obs['history']),-1))
                    put('pre_metadata',torch.stack((family_codes[env.initial_pose_index],env.reset_count,controlled,env.rise_hold.entry),-1))
                    put('pre_best',env.support_record.best)
                    if spec.get('rollout_full_joint_capture'):
                        put('pre_joint_pos',env.robot.data.joint_pos.torch)
                        put('pre_joint_vel',env.robot.data.joint_vel.torch)
                    action=ppo.act(obs)
                    put('sample',action);put('mean',actor.output_mean);put('std',actor.output_std)
                    obs,reward,dones,extras=wrapped.step(action.to(env.device).clone());obs=obs.clone()
                    if not torch.isfinite(reward).all() or not torch.isfinite(obs['policy']).all() or env.terminal_causes['nonfinite'].any() or env.terminal_causes['closure'].any():
                        raise RuntimeError('Nonfinite/native fault in frozen rollout')
                    put('reward',reward);put('done',dones);put('timeouts',extras.get('time_outs',torch.zeros_like(dones)))
                    put('post_state',env.recovery_snapshot);put('post_control',env.recovery_control_snapshot)
                    put('post_geometry',env.wheel_geometry_snapshot);put('record_transition',env.support_record.snapshot)
                    if spec.get('rollout_full_joint_capture'):
                        put('post_joint_pos',env.robot.data.joint_pos.torch)
                        put('post_joint_vel',env.robot.data.joint_vel.torch)
                    current=list(env.reward_raw)
                    if names is not None and current!=names:raise ValueError('Reward layout changed')
                    names=current
                    put('raw_reward',torch.stack([env.reward_raw[n] for n in names],-1))
                    put('weighted_reward',torch.stack([env.reward_weighted[n] for n in names],-1))
                    ppo.process_env_step(obs,reward,dones,extras)
                ppo.compute_returns(obs)
                data={k:torch.stack(v) for k,v in rows.items()}
                data.update(value=storage.values.clone(),returns=storage.returns.clone(),
                    advantage_normalized=storage.advantages.clone(),advantage_raw=storage.returns-storage.values,
                    storage_reward=storage.rewards.clone())
                arrays.append({k:v.cpu().numpy().copy() for k,v in data.items()});storage.clear()
    finally:
        actor.train(oldmode[0]);critic.train(oldmode[1])
    unchanged=all(tree_equal(b,x.state_dict()) for b,x in zip(before,(actor,critic,ppo.optimizer)))
    if not unchanged:raise RuntimeError('Frozen actor/critic/Adam changed')
    data={k:np.stack([a[k] for a in arrays]) for k in arrays[0]}
    if sum(a.nbytes for a in data.values())>spec['rollout_probe']['max_storage_bytes']:raise ValueError('Probe capture byte ceiling exceeded')
    target=Path(output)/'frozen_rollout.npz'
    with target.open('xb') as stream:np.savez_compressed(stream,**data)
    if target.stat().st_size>spec['rollout_probe']['max_storage_bytes']:raise ValueError('Compressed capture byte ceiling exceeded')
    return {'engineering_diagnostic_only':True,'recovery_gate':{'accepted':False,'status':'NOT_RUN'},'per_env':[],
        'checkpoint_sha256':spec['source_sha256'],'optimizer_updates':0,'collected_transitions':16384,
        'frozen_state_unchanged':unchanged,'capture':{'path':target.name,'sha256':digest(target),'bytes':target.stat().st_size,
        'array_shapes':{k:list(v.shape) for k,v in data.items()},'family_names':family_names,'reward_names':names,
        'joint_names':env.robot.joint_names if spec.get('rollout_full_joint_capture') else None,
        'active_indices':list(env.ids) if spec.get('rollout_full_joint_capture') else None,
        'post_joint_validity':'exclude done transitions: direct engine data may be reset; post_control/geometry/state remain pre-reset',
        'axes':'rollout,policy_step,environment,feature','pre_metadata_columns':['family_code','episode_id','controlled','entry_time'],
        'post_state_schema':'recovery_policy_trace_v1','post_control_schema':'recovery_policy_trace_v1'},
        'limitation':'two frozen rollouts; not capability gate or training convergence evidence'}


def collect(actor,wrapped,env,*,spec,output,stop_requested):
    cpu_rng=torch.get_rng_state();cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    mode=actor.training
    try:return _collect(actor,wrapped,env,spec=spec,output=output,stop_requested=stop_requested)
    finally:
        actor.train(mode);torch.set_rng_state(cpu_rng)
        if cuda_rng is not None:torch.cuda.set_rng_state_all(cuda_rng)
