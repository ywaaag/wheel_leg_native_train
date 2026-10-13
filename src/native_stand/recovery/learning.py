"""Recovery actor construction; state/Adam names remain stable across distributions."""
def model(obs,*,actor,spec):
    from native_stand.command_v6.domain.action_distribution import validate
    validate(spec)
    if not actor or not spec.get('action_distribution'):
        from native_stand.command_v6.learning import model as base
        return base(obs,actor=actor,spec=spec)
    from rsl_rl.models import MLPModel
    return MLPModel(obs,{'actor':['policy','history']},'actor',6,
        hidden_dims=tuple(spec['ppo']['hidden_dims']),activation='elu',obs_normalization=False,
        distribution_cfg={'class_name':'native_stand.recovery.learning_distribution:WheelBoundedMeanGaussianDistribution',
            'init_std':.2,'std_type':'scalar'})
