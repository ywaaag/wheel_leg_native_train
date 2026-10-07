"""Create the authorized overnight motion spec and a fresh ledger."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "configs/experiments/motion_recipe_per_command_norm_online_seed20261001_20261004/spec.json"
CANDIDATE_SPEC = BASE
CANDIDATE_RUN = ROOT / "runs/motion_recipe_per_command_norm_online_seed20261001_20261004_retry1"
CANDIDATE = CANDIDATE_RUN / "model_update_30.pt"
DEST = ROOT / "configs/experiments/motion_overnight_20261005"
OUTPUT = ROOT / "runs/motion_overnight_20261005"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pair(magnitude, yaw=False):
    return [[0, magnitude], [0, -magnitude]] if yaw else [[magnitude, 0], [-magnitude, 0]]


def build_stages():
    linear = [.1, .2, .3, .5, .75, 1., 1.5, 2., 2.5, 3., 3.5, 4.]
    yaw = [.25, .5, .75, 1., 1.5, 2., 2.5, 3., 3.5, 4.]
    stages = [{"id": 0, "name": "L0", "commands": [[0, 0]],
               "weights": [1.], "boundary": [[0, 0]], "command_mode": "fixed",
               "schedule_s": [1., 1., 4., 1.], "episode_length_s": 9.}]
    unlocked = []
    for index, magnitude in enumerate(linear, start=1):
        unlocked += pair(magnitude)
        commands = [[0, 0]] + unlocked
        weight = .6 / (len(commands) - 1)
        stages.append({"id": index, "name": f"L{index}", "commands": commands,
                       "weights": [.4] + [weight] * (len(commands) - 1),
                       "boundary": pair(magnitude), "command_mode": "fixed",
                       "schedule_s": [1., 1., 4., 1.], "episode_length_s": 9.})
    linear_unlocked = list(unlocked)
    for index, magnitude in enumerate(yaw, start=len(linear) + 1):
        unlocked += pair(magnitude, yaw=True)
        commands = [[0, 0]] + linear_unlocked + unlocked[len(linear_unlocked):]
        weight = .6 / (len(commands) - 1)
        stages.append({"id": index, "name": f"Y{index-len(linear)}", "commands": commands,
                       "weights": [.4] + [weight] * (len(commands) - 1),
                       "boundary": pair(magnitude, yaw=True), "command_mode": "fixed",
                       "schedule_s": [1., 1., 4., 1.], "episode_length_s": 9.})
    return stages


def main():
    from native_stand.command_v6.tools.entrypoints import historical_cli_guard
    historical_cli_guard('scripts/prepare_motion_overnight_20261005.py')
    if DEST.exists() or OUTPUT.exists():
        raise FileExistsError("overnight output/spec identity already exists")
    spec = json.loads(BASE.read_text())
    spec.pop("diagnostic_trajectory", None)
    spec["ppo_diagnostics"] = {"updates": 0}
    stages = build_stages()
    stage_linear = {"0": .01}
    for row in stages[1:13]:
        target = abs(row["boundary"][0][0])
        stage_linear[str(row["id"])] = max(.04, target * target)
    for row in stages[13:]:
        stage_linear[str(row["id"])] = 16.
    stage_yaw = {str(row["id"]): .09 for row in stages[:13]}
    for row in stages[13:]:
        target = abs(row["boundary"][0][1])
        stage_yaw[str(row["id"])] = max(.09, target * target)
    spec.update({
        "experiment": "motion_overnight_20261005",
        "source_checkpoint": str(CANDIDATE),
        "source_sha256": sha(CANDIDATE),
        "source_update": 30,
        "source_input_dim": 150,
        "source_spec_sha256": sha(CANDIDATE_SPEC),
        "seed": 20261005,
        "restore_source_rng": True,
        "cuda_visible_devices": "0",
        "objective": "per_command_adv_norm",
        "wheel_envelope_conversion": {"source_scale_rad_s": 100., "destination_scale_rad_s": 100.},
        "curriculum": {
            "active_stage": 1,
            "episode_length_s": 9.0,
            "schedule_s": [1., 1., 4., 1.],
            "minimum_zero_fraction": .4,
            "stages": stages,
            "task_progression": {
                "initial_stage": 1, "max_enabled_stage": len(stages)-1,
                "consecutive_confirmations": 3,
                "standing_regression_confirmations": 2,
                "confirmation_spacing_updates": 50,
                "merge_nearby_updates": 0,
                "blocked_reason": "all_discrete_linear_then_yaw_levels_are_explicit",
                "stages": stages},
            "retention": {"full_every_updates": 25, "consecutive_failures": 2,
                          "stop_on_failure": True, "commands": [[0, 0]],
                          "protocol": "zero-command standing only; missing is failure",
                          "motion_progress_is_not_retention": True},
            "episode_curriculum": None},
        "reward": {**spec["reward"], "stage_linear_denominators": stage_linear,
                   "stage_yaw_denominators": stage_yaw,
                   "linear_error_denominator": stage_linear["1"],
                   "yaw_error_denominator": stage_yaw["1"]},
        "evaluation": {**spec["evaluation"], "full_every_updates": 50,
                        "checkpoint_every_updates": 50, "light_every_updates": 0,
                        "motion_commands": [], "command_mode": "fixed",
                        "motion_protocol": "fixed", "stop_window_s": 0.,
                        "yaw_drift_max_m": .20, "yaw_excursion_max_m": .25},
        "budget": {"source_eval_wall_s": 120, "smoke_wall_s": 600,
                   "formal_wall_s": 28800, "source_eval_updates": 0,
                   "smoke_updates": 1, "formal_updates": 9999,
                   "sample_limit": 81920000, "formal_samples": 81911808,
                   "wall_limit_enabled": True, "terminal_reserve_s": 180},
        "external_prerequisites": [{"run": str(CANDIDATE_RUN),
            "satisfies": "source_eval",
            "manifest_source_sha256": "fc51370b5d02e3337f8c73af0cb4223e82635e6a36640a0977fd80a429e631e1",
            "sha256": {"model_update_30.pt": sha(CANDIDATE)}}],
        "artifacts": {"checkpoint_name": "model_update_{update}.pt"},
        "experiment_variable": "strict discrete linear then yaw curriculum with per-command advantage normalization"})
    DEST.mkdir(parents=True)
    (DEST / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    (DEST / "budget.json").write_text(json.dumps({
        "authorization": "AUTHORIZED",
        "limits": {"source_eval": 0, "smoke": 1, "formal": 9999, "evaluate": 0, "play": 0},
        "used": {"source_eval": 0, "smoke": 0, "formal": 0, "evaluate": 0, "play": 0},
        "attempts": {}, "source_eval_wall_used_s": 0.}, indent=2) + "\n")
    print(json.dumps({"spec": str(DEST / "spec.json"), "ledger": str(DEST / "budget.json"),
                      "output": str(OUTPUT), "stages": len(stages),
                      "source_sha256": spec["source_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
