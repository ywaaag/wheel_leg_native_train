"""Apply one validated experiment spec to an Isaac Lab environment config."""


def verify_asset_import(spec, *, allow_colleague_config_drift=False):
    import hashlib
    from pathlib import Path
    import sys
    module=sys.modules.get("agent_world.assets.rmuc_wheel_leg")
    expected=Path(spec["asset_module_path"]).resolve()
    if module is None or Path(module.__file__).resolve()!=expected:
        raise RuntimeError("Imported colleague asset module path differs from spec")
    if hashlib.sha256(expected.read_bytes()).hexdigest()!=spec["asset_module_sha256"]:
        raise RuntimeError("Imported colleague asset module SHA differs from spec")
    yaml=Path(spec["colleague_config_path"])
    yaml_sha256=hashlib.sha256(yaml.read_bytes()).hexdigest()
    if yaml_sha256!=spec["colleague_config_sha256"] and not allow_colleague_config_drift:
        raise RuntimeError("Colleague YAML changed after preflight")
    result={"module_path":str(expected),"module_sha256":spec["asset_module_sha256"],
            "yaml_path":str(yaml),"yaml_sha256":yaml_sha256}
    if yaml_sha256!=spec["colleague_config_sha256"]:
        result["identity_warning"]=(
            "colleague YAML differs from the frozen run identity; preview uses the "
            "current YAML while the USD and asset module remain SHA-checked")
        result["expected_yaml_sha256"]=spec["colleague_config_sha256"]
    return result


def apply(cfg,spec,*,envs):
    control=spec["control"]
    ground=spec["ground"]
    termination=spec["termination"]
    cfg.seed=spec["seed"]
    cfg.scene.num_envs=envs
    # The colleague asset module supplies the default immutable USD.  An
    # experiment may explicitly select an isolated diagnostic copy; keep the
    # override at the application boundary so domain code remains unchanged.
    if spec.get('asset_path'):
        from pathlib import Path
        # Lightweight CPU fixtures may omit the Isaac robot config. Runtime
        # configs always provide it; leave such fixtures usable for contract tests.
        if hasattr(cfg, 'robot_cfg'):
            cfg.robot_cfg=cfg.robot_cfg.copy()
            cfg.robot_cfg.spawn.usd_path=str(Path(spec['asset_path']).resolve())
    cfg.episode_length_s=spec["curriculum"]["episode_length_s"]
    cfg.is_finite_horizon=False
    cfg.episode_curriculum=spec['curriculum'].get('episode_curriculum')
    cfg.sim.dt=control["physics_dt_s"]
    cfg.decimation=round(control["policy_dt_s"]/control["physics_dt_s"])
    cfg.sim.render_interval=cfg.decimation
    cfg.pd_interval_steps=round(control["pd_dt_s"]/control["physics_dt_s"])
    cfg.ground_static_friction=ground["static_friction"]
    cfg.ground_dynamic_friction=ground["dynamic_friction"]
    cfg.ground_restitution=ground["restitution"]
    cfg.ground_height_m=ground["height_m"]
    cfg.ground_normal_axis=ground["normal_axis"]
    cfg.ground_width_m=ground["width_m"]
    cfg.ground_length_m=ground["length_m"]
    cfg.ground_material_path=ground["material_path"]
    cfg.leg_position_scale_rad=spec["action"]["leg_scale_rad"]
    cfg.leg_pair_radius_rad=spec["action"]["leg_pair_radius_rad"]
    cfg.wheel_speed_scale_rad_s=spec["action"]["wheel_scale_rad_s"]
    cfg.leg_kp=control["leg_kp"]
    cfg.leg_kd=control["leg_kd"]
    cfg.wheel_kv=control["wheel_kv"]
    cfg.closure_fault_m=control["closure_fault_m"]
    cfg.fall_root_height_m=termination["fall_root_height_m"]
    cfg.minimum_up_cos=termination["minimum_up_cos"]
    cfg.body_contact_max_n=termination["body_contact_max_n"]
    cfg.active_leg_angle_max_rad=termination["active_leg_angle_max_rad"]
    return cfg
