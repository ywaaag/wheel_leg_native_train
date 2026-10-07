"""Prepare endpoint-oriented motion gates without rewriting prior experiments."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "configs/experiments/motion_overnight_20261005/spec.json"
DEST = ROOT / "configs/experiments/motion_endpoint_20261005"
OUTPUT = ROOT / "runs/motion_endpoint_20261005"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    if DEST.exists() or OUTPUT.exists():
        raise FileExistsError("new endpoint experiment identity already exists")
    spec = json.loads(BASE.read_text())
    spec["experiment"] = "motion_endpoint_20261005"
    spec["experiment_variable"] = "endpoint-oriented error gates with minimum signed response"
    spec["evaluation"] = {**spec["evaluation"],
        "motion_vx_error_floor_mps": .03,
        "motion_vx_error_fraction": .175,
        "motion_vx_error_cap_mps": .7,
        "motion_vx_min_speed_fraction": .5,
        "motion_yaw_error_floor_rad_s": .05,
        "motion_yaw_error_fraction": .175,
        "motion_yaw_error_cap_rad_s": .7,
        "motion_yaw_min_speed_fraction": .5,
        "gate_identity": "endpoint_error_fraction_0.175_cap_0.7_min_response_0.5"}
    spec["budget"] = {**spec["budget"], "formal_updates": 9774,
                       "formal_samples": 9774 * 64 * 128,
                       "sample_limit": 9774 * 64 * 128}
    spec["previous_experiment_reference"] = {
        "run": str(ROOT / "runs/motion_overnight_20261005_retry2/formal"),
        "terminal": "STOPPED_BOUNDED", "actual_updates": 225,
        "note": "read-only evidence; update225 is not a starting checkpoint"}
    DEST.mkdir(parents=True)
    (DEST / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    (DEST / "budget.json").write_text(json.dumps({
        "authorization": "UNAUTHORIZED",
        "limits": {"source_eval": 0, "smoke": 1, "formal": 9774, "evaluate": 0, "play": 0},
        "used": {"source_eval": 0, "smoke": 0, "formal": 0, "evaluate": 0, "play": 0},
        "attempts": {}, "source_eval_wall_used_s": 0.0}, indent=2) + "\n")
    print(json.dumps({"spec": str(DEST / "spec.json"), "ledger": str(DEST / "budget.json"),
                      "output": str(OUTPUT), "base_sha256": sha(BASE)}, indent=2))

if __name__ == "__main__":
    main()
