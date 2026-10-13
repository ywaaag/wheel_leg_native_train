"""Read-only public entry catalog and safeguards for retained historical tools."""
import argparse
import json
import sys


ENTRIES = (
    {'entry':'scripts/test_portable_cpu.py','role':'portable_CPU_contract_tests','status':'CURRENT'},
    {'entry':'scripts/prepare_student_recovery_ppo.py','role':'explicit_student_recipe_preparer','status':'CURRENT'},
    {'entry':'scripts/select_recovery_checkpoint.py','role':'legacy150D_selector','status':'HISTORICAL'},
    {"entry":"native_stand.command_v6.tools.play","role":"identity_bound_gui_preview","status":"CURRENT"},
    *({"entry":entry,"role":role,"status":"CURRENT"} for entry,role in (
        ('scripts/audit_recovery_action_distribution.py','offline_distribution_audit'),
        ('scripts/audit_recovery_mean_coefficient.py','offline_actor_mean_audit'),
        ('scripts/prepare_recovery_bounded_mean_probe.py','recipe_specific_wrapper'),
        ('scripts/review_recovery_bounded_mean_probe.py','offline_distribution_review'),
        ('scripts/prepare_recovery_bounded_mean_train.py','recipe_specific_wrapper'),
        ('scripts/audit_recovery_leg_execution.py','offline_control_event_audit'))),
    {"entry":"native_stand.command_v6.tools.prepare_engineering_recovery","role":"restricted_motion_recovery_plan_and_unauthorized_publication","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.audit_storage","role":"read_only_artifact_inventory","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.source_evidence","role":"read_only_source_reuse_certificate","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.audit_native_parity","role":"static_sim2sim_semantic_audit","status":"CURRENT"},
    {"entry":"scripts/validate_native_mujoco.py","role":"bounded_mujoco_diagnostic","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.review_recovery_events","role":"registry_event_review","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.review_recovery_takeoff","role":"geometry_event_review","status":"CURRENT"},
    {"entry":"scripts/review_recovery_swing_failure.py","role":"event_review_compatibility","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.compare_motion","role":"identity_bound_motion_comparison","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.submission_summary","role":"frozen_handoff_summary","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.prepare_recovery_course","role":"explicit_course_preparer","status":"CURRENT"},
    {"entry":"scripts/prepare_recovery_swing.py","role":"recipe_specific_wrapper","status":"CURRENT"},
    {"entry":"scripts/review_recovery_revalidation.py","role":"offline_revalidation_review","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.register_authorization","role":"explicit_authorization_registration","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.compare_arms","role":"finished_arm_comparison","status":"CURRENT"},
    {"entry":"scripts/review_recovery_takeoff.py","role":"offline_event_alignment","status":"CURRENT"},
    {"entry":"scripts/prepare_recovery_wheel_std_ab.py","role":"explicit_preparer","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.audit_entrypoints","role":"read_only_reference_audit","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.audit_terminal","role":"read_only_event_audit","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.validate_frozen_cpu","role":"CPU_validation_copy","status":"CURRENT"},
    {"entry":"native_stand.command_v6.tools.prepare_recovery_retry","role":"explicit_preparer","status":"CURRENT"},
    {"entry":"scripts/prepare_recovery_min_height.py","role":"explicit_preparer","status":"CURRENT"},
    {"entry":"scripts/review_recovery_min_height.py","role":"offline_review","status":"CURRENT"},
    {"entry": "native_stand.command_v6.supervisor", "role": "submission", "status": "CURRENT",
     "note": "Only public submission entry; plan-only by default. Launch needs fresh authorization."},
    {"entry": "native_stand.command_v6.tools.health_check", "role": "read_only", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.preflight", "role": "read_only", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.completion", "role": "report", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.correct_evidence", "role": "offline_correction", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.engineering_recovery", "role": "offline_recovery_plan", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.prepare_checkpoint_diagnostic", "role": "explicit_preparer", "status": "CURRENT"},
    {"entry": "native_stand.command_v6.tools.prepare_motion_experiment", "role": "explicit_preparer", "status": "CURRENT",
     "note": "Motion evaluation/single-stage course preparation; zero-write default, --write publishes UNAUTHORIZED only."},
    {"entry": "scripts/audit_recovery_survival.py", "role": "offline_audit", "status": "CURRENT"},
    {"entry": "scripts/prepare_recovery_coverage.py", "role": "historical_recipe", "status": "HISTORICAL"},
    {"entry": "scripts/prepare_recovery_rise.py", "role": "historical_recipe", "status": "HISTORICAL"},
    {"entry": "scripts/prepare_recovery_level2.py", "role": "historical_recipe", "status": "HISTORICAL"},
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
