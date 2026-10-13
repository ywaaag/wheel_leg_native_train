"""One application boundary for training/evaluation/preview switches."""
from ..domain.environment_mode import resolve

def apply(env,mode,*,envs=None,family=None):
    plan=resolve(mode,envs=envs if envs is not None else env.num_envs)
    env.execution_mode=mode
    env.capture_terminal=plan['capture_terminal']
    if hasattr(env,'recovery_config'):
        env.curriculum_training=plan['curriculum_training']
        if mode!='training':
            selected=family or env.family
            if mode=='preview':selected=family or env.recovery_config.get('preview_family',env.recovery_config.get('active_family',env.family))
            env.select_initial_family(selected,plan['split'])
            plan['family']=selected
    return plan
