"""Future PPO assembly only; no online rollout or optimizer step on import."""
import torch
from .model import load,Student

def assemble(checkpoint,observations,*,steps_per_env=128,recipe=None):
    from rsl_rl.storage import RolloutStorage
    from native_stand.recovery.controlled_ppo import ControlledPPO,KEY
    actor,data=load(checkpoint)
    mcu=data['interface_version']=='multiskill_mcu_v2'
    if mcu:
        from .training_recipe import validate_instance
        if recipe is None:raise ValueError('MCU v2 reward undefined without explicit training recipe')
        validate_instance(recipe,(recipe or {}).get('source_actor_sha256'))
        actor.log_std.requires_grad_(False)
    critic=Student(False,version=data['interface_version'],critic_privileged_version=(recipe or {}).get('critic_privileged_version'))
    if observations['student_actor'].shape[-1]!=(31 if mcu else 1182) or observations['student_critic'].shape[-1]!=(49 if mcu and (recipe or {}).get('critic_privileged_version') in ('standing_privileged49_v1','motion_privileged49_v1') else 40 if mcu else 1191):raise ValueError('Student PPO observation dimensions differ')
    if KEY not in observations or observations[KEY].dtype!=torch.bool:raise ValueError('Student PPO requires pre-action control metadata')
    device=str(observations['student_actor'].device)
    storage=RolloutStorage('rl',observations.batch_size[0],steps_per_env,observations,[6],device=device)
    ppo=ControlledPPO(actor,critic,storage,learning_rate=3e-5,schedule='fixed',num_learning_epochs=4,num_mini_batches=4,entropy_coef=.001,clip_param=.2,gamma=.99,lam=.95,value_loss_coef=.5,max_grad_norm=1.,use_clipped_value_loss=False,device=device)
    if ppo.optimizer.state:raise RuntimeError('New student PPO Adam must be empty')
    return ppo

def demonstration_loss(actor,independent_demo_batch):
    """Independent BC data only; never added to on-policy rollout storage."""
    from .distill import loss
    return loss(actor(independent_demo_batch['x']),independent_demo_batch['y'])
