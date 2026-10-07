"""Read-only ledger identity and aggregate audit."""
import argparse
import json
from pathlib import Path


def validate(book, *, run_root=None):
    errors = []
    totals = {name:0 for name in book["used"]}
    paths = set()
    for attempt_id,row in book["attempts"].items():
        output = row.get("output_dir")
        if not output or output in paths:
            errors.append(f"{attempt_id}: duplicate or missing output")
        paths.add(output)
        phase = row.get("phase")
        if phase not in totals:
            errors.append(f"{attempt_id}: unknown phase")
            continue
        totals[phase] += (1 if row.get("status")!="RUNNING" else 0) if phase in ("source_eval","evaluate","play") else row.get("updates",0)
        if run_root and row.get("status") != "RUNNING":
            run = Path(output)
            terminal=(run.with_name(run.stem+".terminal.json") if phase=="evaluate"
                      else run if phase=="play" else run/"terminal_report.json")
            if not terminal.exists():
                errors.append(f"{attempt_id}: missing terminal report")
    for phase,used in totals.items():
        if used != book["used"][phase]:
            errors.append(f"{phase}: ledger used={book['used'][phase]}, attempts={used}")
        if used > book["limits"][phase]:
            errors.append(f"{phase}: limit exceeded")
    return {"status":"PASS" if not errors else "FAIL","errors":errors,"totals":totals}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger",type=Path,required=True)
    parser.add_argument("--check-terminals",action="store_true")
    args=parser.parse_args()
    result=validate(json.loads(args.ledger.read_text()),run_root=args.ledger.parent if args.check_terminals else None)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 2)


if __name__=="__main__":
    main()
