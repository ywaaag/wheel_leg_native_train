"""Local report regeneration, explicit notification, or human review acknowledgement."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from native_stand.command_v6.completion import finalize_report, notify, acknowledge


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--corrected-output',type=Path,help='fresh independent report; old run stays read-only')
    operations=parser.add_mutually_exclusive_group()
    operations.add_argument('--notify',action='store_true')
    operations.add_argument('--notify-only',action='store_true',
        help='notify from an already-ready terminal report; do not regenerate or poll')
    operations.add_argument('--acknowledge-review',action='store_true')
    parser.add_argument('--expected-session',help='require the manifest notification target to match this current session')
    args=parser.parse_args(argv)
    if args.corrected_output and (args.notify or args.notify_only or args.acknowledge_review):
        parser.error('Corrected offline report does not send or acknowledge original notification')
    if args.expected_session is not None:
        from native_stand.command_v6.completion import read
        session=(read(args.run_dir/'manifest.json',{}) or {}).get('hapi_session')
        if not args.expected_session or session!=args.expected_session:
            parser.error('manifest HAPI target differs from explicitly expected current session')
    if args.acknowledge_review:
        acknowledge(args.run_dir)
    elif args.notify_only:
        print(json.dumps({'notification':notify(args.run_dir),
            'report_regenerated':False,'simulation':0,'ppo':0},indent=2))
    else:
        result=finalize_report(args.run_dir,corrected_output=args.corrected_output)
        if args.notify:
            result['notification']=notify(args.run_dir)
        print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
