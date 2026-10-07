"""Restore evaluation-only runtime switches and RNG, including setup failures."""
from functools import wraps
from inspect import signature
import sys
import torch


def failure_evidence(error,protocol,valid,dt,terminal_state=None):
    from native_stand.command_v6.domain.evidence import observed_protocol
    counts=valid.detach().long().sum(0).cpu().tolist()
    import math
    def json_value(value):
        if isinstance(value,list):return [json_value(item) for item in value]
        return value if not isinstance(value,float) or math.isfinite(value) else None
    error.evaluation_evidence={'effective_protocol':observed_protocol(protocol,[count*dt for count in counts]),
        'termination_reason':str(error),'completed':False,
        'terminal_pre_reset':json_value(terminal_state.detach().cpu().tolist()) if terminal_state is not None else None,
        'scope':'partial first-episode evidence; never capability acceptance'}
    return error


def isolated_evaluation(function):
    @wraps(function)
    def run(actor,wrapped,env,**kwargs):
        signature(function).bind(actor,wrapped,env,**kwargs)
        cpu_rng=torch.get_rng_state()
        cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
        actor_training=getattr(actor,'training',None)
        recovery=hasattr(env,'recovery_config')
        if recovery:
            saved=(env.family,env.split,env.curriculum_training,env.continuous_evaluation,
                   env.fsm.config['timeout_s'],env.recovery_config.get('gate_diagnostics',False))
        else:
            saved=(env.cfg.episode_length_s,env.schedule_s,getattr(env,'capture_terminal',False))
            forced_target=getattr(env,'forced_target',None)
        try:
            if actor_training is not None:actor.eval()
            return function(actor,wrapped,env,**kwargs)
        finally:
            original_error=sys.exception()
            try:
                if recovery:
                    family,split,training,continuous,timeout,diagnostics=saved
                    env.curriculum_training=training
                    env.continuous_evaluation=continuous
                    env.fsm.config['timeout_s']=timeout
                    env.recovery_config['gate_diagnostics']=diagnostics
                    env.select_initial_family(family,split)
                    env.reset()
                else:
                    env.cfg.episode_length_s,env.schedule_s,env.capture_terminal=saved
                    env.clear_evaluation_target()
                    if hasattr(env,'forced_target'):env.forced_target=forced_target
            except BaseException as cleanup_error:
                if original_error is None:raise
                original_error.add_note('evaluation cleanup also failed: '+repr(cleanup_error))
            finally:
                try:
                    if actor_training is not None:actor.train(actor_training)
                finally:
                    torch.set_rng_state(cpu_rng)
                    if cuda_rng is not None:torch.cuda.set_rng_state_all(cuda_rng)
    return run
