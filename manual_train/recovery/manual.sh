#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$TASK_DIR/../../src"
exec /home/kellen/anaconda3/envs/issaclab/bin/python "$TASK_DIR/steps.py" "$@"
