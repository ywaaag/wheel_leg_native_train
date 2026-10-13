"""Read a single run's small state files without opening trajectories."""
import argparse
import json
from pathlib import Path


def summarize(run,ledger=None):
    run=Path(run)
    def read(name):
        file=run/name
        return json.loads(file.read_text()) if file.is_file() else None
    manifest=read("manifest.json")
    progress=read("progress.json")
    terminal=read("terminal_report.json")
    analysis=read('analysis.json')
    from native_stand.command_v6.domain.accounting import summary
    book=json.loads(Path(ledger).read_text()) if ledger else {}
    return {"run":str(run),"attempt_id":(manifest or progress or {}).get("attempt_id"),
            "phase":(manifest or progress or {}).get("phase"),
            "recorded_status":(progress or {}).get("status"),
            "terminal_status":(terminal or {}).get("status"),
            "actual_updates":(terminal or progress or {}).get("actual_updates"),
            "samples":(terminal or progress or {}).get("samples"),
            'update_accounting':summary(manifest or {},terminal or {},progress or {},book),
            "latest_metric":(progress or {}).get("latest_metric"),
            "evaluations":(terminal or progress or {}).get("evaluations",[]),
            "terminal_missing":terminal is None,
            "analysis":({key:analysis.get(key) for key in ('status','actual_updates','samples','wall_s',
                'rollout_samples_per_s','end_to_end_samples_per_s','terminal_exit_conflict')} if analysis else None),
            "report_ready":read('report_ready.json'),"notification":read('hapi_notification.json'),
            "process_live":"UNKNOWN; check PID command identity separately"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir",type=Path,required=True)
    parser.add_argument('--ledger',type=Path,help='explicit independent ledger for reserved/actual/settled summary')
    args=parser.parse_args()
    print(json.dumps(summarize(args.run_dir,args.ledger),indent=2))


if __name__=="__main__":
    main()
