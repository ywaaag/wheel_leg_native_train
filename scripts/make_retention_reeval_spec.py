import json, hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = json.loads((root / 'runs/motion_retention_20261005/formal/source_snapshot/spec.json').read_text())
src['experiment'] = 'motion_retention_reeval_20261005'
src['colleague_config_sha256'] = hashlib.sha256(Path(src['colleague_config_path']).read_bytes()).hexdigest()
src['zero_mode'] = 'low_speed'
src['zero_mean_abs_vx_max_mps'] = .5
src['evaluation'] = {**src['evaluation'], 'zero_mode': 'low_speed', 'zero_mean_abs_vx_max_mps': .5}
src['diagnostic_identity_only'] = True
out = root / 'runs/motion_retention_reeval_20261005/spec.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(src, indent=2) + '\n')
print(out)
