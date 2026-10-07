"""Local report regeneration, explicit notification, or human review acknowledgement."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from native_stand.command_v6.completion import finalize_report, notify, acknowledge


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--notify',action='store_true')
    parser.add_argument('--acknowledge-review',action='store_true')
    args=parser.parse_args()
    if args.acknowledge_review:
        acknowledge(args.run_dir)
    else:
        result=finalize_report(args.run_dir)
        if args.notify:
            result['notification']=notify(args.run_dir)
        print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
