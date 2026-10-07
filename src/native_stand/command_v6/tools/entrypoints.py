"""Read-only public entry catalog and safeguards for retained historical tools."""
import argparse
import json
import sys


ENTRIES = (
    {"entry": "native_stand.command_v6.supervisor", "role": "submission", "status": "CURRENT",
     "note": "Only public submission entry; plan-only by default. Launch needs fresh authorization."},
    {"entry": "native_stand.command_v6.tools.health_check", "role": "read_only", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.preflight", "role": "read_only", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.completion", "role": "report", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.correct_evidence", "role": "offline_correction", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.engineering_recovery", "role": "offline_recovery_plan", "status": "CURRENT"},
    {"entry": "scripts/audit_recovery_survival.py", "role": "offline_audit", "status": "CURRENT"},
    {"entry": "scripts/prepare_recovery_coverage.py", "role": "explicit_preparer", "status": "CURRENT"},
    {"entry": "scripts/prepare_recovery_rise.py", "role": "explicit_preparer", "status": "CURRENT"},
    {"entry": "scripts/review_recovery_coverage.py", "role": "offline_review", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.launcher", "role": "phase_launch", "status": "INTERNAL"},
    {"entry": "native_stand.command_v6.monitor", "role": "monitor", "status": "INTERNAL"},
    {"entry": "native_stand.command_v6.stand_chain", "role": "chain_worker", "status": "INTERNAL"},
    {"entry": "scripts/submit_motion_high_speed_formal.py", "role": "compatibility", "status": "DEPRECATED"},
    {"entry": "scripts/continue_motion_high_speed_submission.py", "role": "compatibility", "status": "DEPRECATED"},
    {"entry": "scripts/run_motion_high_speed_preparation.py", "role": "frozen_runtime", "status": "RETIRED",
     "note": "Hardcoded historical runtime CLI is disabled; use the explicit supervisor."},
    *({"entry": entry, "role": "recipe_generator", "status": "HISTORICAL"} for entry in (
        "scripts/prepare_motion_overnight_20261005.py",
        "scripts/prepare_motion_endpoint_20261005.py",
        "scripts/prepare_motion_high_speed_course.py")),
    *({"entry": entry, "role": "recipe_specific", "status": "HISTORICAL"} for entry in (
        "scripts/prepare_motion_recheck_20261007.py",
        "scripts/report_motion_recheck_20261007.py",
        "scripts/prepare_motion_course_plan.py",
        "scripts/prepare_recovery_hold.py")),
    *({"entry": entry, "role": "recipe_specific", "status": "HISTORICAL"} for entry in (
        "scripts/create_motion_retention_ab_20261006.py",
        "scripts/create_retention_spec.py",
        "scripts/make_retention_reeval_spec.py",
        "scripts/review_recovery_settling.py")),
    {"entry":"scripts/watch_recovery_submission.py", "role":"frozen_runtime", "status":"RETIRED"},
    *({'entry':entry,'role':'old_recovery_workflow','status':'HISTORICAL'} for entry in (
        'native_stand.recovery.chain','native_stand.recovery.train_stages','native_stand.recovery.extend_training')),
)


def add_historical_option(parser):
    parser.add_argument('--historical-replay', action='store_true',
        help='Explicitly acknowledge a historical recipe/tool; grants no runtime permission.')


def require_historical_option(parser, args):
    if not args.historical_replay:
        parser.error('HISTORICAL_ENTRY: explicit --historical-replay required; use supervisor for new submissions')


def historical_cli_guard(entry, argv=None):
    """Reject old zero-argument write/launch paths before reading any evidence."""
    record = next(item for item in ENTRIES if item["entry"] == entry)
    parser = argparse.ArgumentParser(description=f'HISTORICAL: {entry}. See TOOL_INDEX_HISTORY.md.')
    parser.add_argument("--historical-replay", action="store_true",
                        help="Acknowledge this frozen recipe generator; this is not runtime authorization.")
    args = parser.parse_args(argv)
    if record["status"] == "RETIRED":
        parser.error("RETIRED_ENTRY: fixed GPU/run/session runtime is disabled; use "
                     "python -m native_stand.command_v6.supervisor --spec ... --output-dir ...")
    if not args.historical_replay:
        parser.error("HISTORICAL_ENTRY: not a generic preparation tool; explicit --historical-replay required")
    print("HISTORICAL_ENTRY: frozen recipe only; old authorization is not current permission.", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-historical", action="store_true")
    args = parser.parse_args(argv)
    entries = [item for item in ENTRIES if args.include_historical or item["status"] == "CURRENT"]
    print(json.dumps({"entries": entries, "simulation": 0, "ppo": 0, "files_written": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
