"""Shared source -> wiring smoke -> formal chain, with a read-only default plan."""
import argparse
import json
import os
from pathlib import Path
from .tools.health_check import inspect_project
from .tools.preflight import check


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session')
    parser.add_argument('--physical-gpu',type=int,choices=(0,1))
    parser.add_argument('--launch',action='store_true')
    parser.add_argument('--formal-only',action='store_true',help='reuse verified source/smoke from this same chain')
    args=parser.parse_args()
    phase='formal' if args.formal_only else 'source_eval'
    result=check(args.spec,args.output_dir/phase,phase)
    plan={'preflight':result,'health':inspect_project(Path(__file__).resolve().parents[3],spec_path=args.spec,
            include_processes=args.launch,hapi_session=args.hapi_session),
          'stages':['source_eval','smoke','formal','terminal_reconciliation'],
          'hapi_session':args.hapi_session,'simulation':0,'ppo':0,'files_written':0}
    if not args.launch:
        print(json.dumps(plan,indent=2));return
    if result['status']!='PASS':raise ValueError(result)
    if args.physical_gpu is None:raise ValueError('explicit physical GPU is required for submission')
    from .tools.health_check import submission_health
    submission_health(plan['health'],current_session=os.environ.get('HAPI_SESSION_ID'),
        target_session=args.hapi_session,phase=phase,physical_gpu=args.physical_gpu)
    if args.formal_only:
        from .launcher import launch
        os.environ['NATIVE_PHYSICAL_GPU']=str(args.physical_gpu)
        print(json.dumps(launch(args.spec,'formal',args.output_dir/'formal',args.hapi_session),indent=2))
        return
    from .stand_chain import launch
    launch(args)


if __name__=='__main__':main()
