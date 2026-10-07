import json, hashlib
from pathlib import Path

def main():
    from native_stand.command_v6.tools.entrypoints import historical_cli_guard
    historical_cli_guard('scripts/make_retention_reeval_spec.py')
    root = Path(__file__).resolve().parents[1]
    out = root / 'runs/motion_retention_reeval_20261005/spec.json'
    if out.parent.exists():
        raise FileExistsError('historical reeval directory exists; refusing overwrite')
    src = json.loads((root / 'runs/motion_retention_20261005/formal/source_snapshot/spec.json').read_text())
    src['experiment'] = 'motion_retention_reeval_20261005'
    src['colleague_config_sha256'] = hashlib.sha256(Path(src['colleague_config_path']).read_bytes()).hexdigest()
    src['zero_mode'] = 'low_speed'
    src['zero_mean_abs_vx_max_mps'] = .5
    src['evaluation'] = {**src['evaluation'], 'zero_mode': 'low_speed', 'zero_mean_abs_vx_max_mps': .5}
    src['diagnostic_identity_only'] = True
    out.parent.mkdir(parents=True, exist_ok=False)
    with out.open('x') as stream:
        stream.write(json.dumps(src, indent=2) + '\n')
    print(out)


if __name__ == '__main__':main()
