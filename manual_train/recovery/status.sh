#!/usr/bin/env bash
set -euo pipefail
manual_work_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
manual_project_dir="$(cd -- "$manual_work_dir/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$manual_project_dir/src"
exec /home/kellen/anaconda3/envs/issaclab/bin/python "$manual_work_dir/workbench.py" status "$@"
