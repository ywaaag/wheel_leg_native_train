"""One policy/value network constructor for training, evaluation and playback."""


def model(obs, *, actor, spec):
    from rsl_rl.models import MLPModel
    name="actor" if actor else "critic"
    settings={"hidden_dims":tuple(spec["ppo"]["hidden_dims"]),
              "activation":"elu","obs_normalization":False}
    if actor:
        settings["distribution_cfg"]={
            "class_name":"rsl_rl.modules.distribution:GaussianDistribution",
            "init_std":.2,"std_type":"scalar"}
        if spec.get('wheel_envelope_conversion'):
            settings['distribution_cfg'].update(
                class_name='native_stand.command_v6.learning_distribution:WheelScaledGaussianDistribution',
                wheel_factor=spec['wheel_envelope_conversion']['source_scale_rad_s']/spec['action']['wheel_scale_rad_s'])
    return MLPModel(obs,{name:["policy","history"]},name,6 if actor else 1,**settings)
