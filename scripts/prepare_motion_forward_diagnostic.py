"""Create a fresh diagnostic spec with live external YAML identity."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runs/motion_retention_ab_20261006/off_formal/source_snapshot/spec.json'
OUTPUT = ROOT / 'isolated/root_cause_audit_20261006/forward_diagnostic_spec.json'


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    spec = json.loads(SOURCE.read_text())
    spec['experiment'] = 'motion_forward_diagnostic_20261006'
    spec['colleague_config_sha256'] = hashlib.sha256(
        Path(spec['colleague_config_path']).read_bytes()).hexdigest()
    spec['diagnostic_identity_only'] = True
    OUTPUT.write_text(json.dumps(spec, indent=2) + '\n')
    print(OUTPUT, hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
          spec['colleague_config_sha256'])


if __name__ == '__main__':
    main()
