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
    parser.add_argument('--evaluation-only',action='store_true',help='PPO0 requests via shared evaluator/monitor')
    parser.add_argument('--wait',action='store_true',help='wait for owned bounded evaluation monitor, no log polling')
    parser.add_argument('--resource-mode',choices=('exclusive','shared'),default=None)
    parser.add_argument('--sharing-authorization',help='explicit user approval and reason for shared GPU use')
    parser.add_argument('--handshake-wait-s',type=float,default=None)
    args=parser.parse_args()
    from .domain.resource_policy import resolve_resources
    args.resource_policy=resolve_resources(json.loads(args.spec.read_text()),
        mode=args.resource_mode,sharing_authorization=args.sharing_authorization)
    if args.handshake_wait_s is not None and not 0<=args.handshake_wait_s<=600:
        raise ValueError('handshake-wait-s must be in [0,600]')
    if args.evaluation_only:
        return evaluate_submission(args)
    phase='formal' if args.formal_only else 'source_eval'
    result=check(args.spec,args.output_dir/phase,phase)
    plan={'preflight':result,'health':inspect_project(Path(__file__).resolve().parents[3],spec_path=args.spec,
            include_processes=args.launch,hapi_session=args.hapi_session),
          'stages':['source_eval','smoke','formal','terminal_reconciliation'],
          'hapi_session':args.hapi_session,'resource_policy':args.resource_policy,
          'simulation':0,'ppo':0,'files_written':0}
    if not args.launch:
        print(json.dumps(plan,indent=2));return
    if result['status']!='PASS':raise ValueError(result)
    if args.physical_gpu is None:raise ValueError('explicit physical GPU is required for submission')
    from .tools.health_check import submission_health
    args.resource_review=submission_health(plan['health'],current_session=os.environ.get('HAPI_SESSION_ID'),
        target_session=args.hapi_session,phase=phase,physical_gpu=args.physical_gpu,resource_policy=args.resource_policy)
    if args.formal_only:
        from .launcher import launch
        os.environ['NATIVE_PHYSICAL_GPU']=str(args.physical_gpu)
        print(json.dumps(launch(args.spec,'formal',args.output_dir/'formal',args.hapi_session,
                               resource_review=args.resource_review),indent=2))
        return
    from .stand_chain import launch
    launch(args)


def evaluate_submission(args):
    import subprocess
    import sys
    import uuid
    from types import SimpleNamespace
    from .tools.evaluate_checkpoint import batch_plan
    from .ledger import Ledger
    spec=json.loads(args.spec.read_text())
    plan=batch_plan(SimpleNamespace(spec=args.spec,output=args.output_dir,attempt_id=None),spec)
    plan.update(physical_gpu=args.physical_gpu,resource_policy=args.resource_policy,
        entry='shared supervisor -> monitor -> evaluate_checkpoint --batch')
    if not args.launch:
        print(json.dumps(plan,indent=2));return 0
    if plan['preflight']['status']!='PASS':raise ValueError(plan['preflight'])
    if args.physical_gpu!=spec['device']['physical_index']:
        raise ValueError('explicit physical GPU differs from evaluation spec')
    from .tools.health_check import gpu_snapshot,submission_health
    snapshot=gpu_snapshot()
    devices={row['index']:row['uuid'] for row in snapshot.get('devices',[])}
    if devices.get(args.physical_gpu)!=spec['device']['uuid']:
        raise ValueError('physical GPU UUID differs')
    resource_review=submission_health({'findings':[],'gpu':snapshot},
        current_session=os.environ.get('HAPI_SESSION_ID'),target_session=args.hapi_session,
        phase='evaluate',physical_gpu=args.physical_gpu,resource_policy=args.resource_policy)
    book=json.loads(args.spec.with_name('budget.json').read_text())
    if sum(float(row.get('wall_s') or 0.) for row in book['attempts'].values()) >= spec['budget']['evaluation_wall_s']:
        raise ValueError('cumulative evaluation wall exhausted')
    attempt_id=uuid.uuid4().hex
    Ledger(args.spec.with_name('budget.json')).reserve(attempt_id,'evaluate',args.output_dir)
    environment={**os.environ,'CUDA_VISIBLE_DEVICES':str(args.physical_gpu),
                 'PYTHONPATH':spec['execution_source_root']}
    args.output_dir.parent.mkdir(parents=True,exist_ok=True)
    log=args.output_dir.with_suffix('.monitor.log')
    with log.open('x') as stream:
        child=subprocess.Popen([sys.executable,'-m','native_stand.command_v6.monitor',
            '--spec',str(args.spec.resolve()),'--phase','evaluate','--output-dir',str(args.output_dir.resolve()),
            '--attempt-id',attempt_id],env=environment,stdout=stream,stderr=subprocess.STDOUT,
            start_new_session=True)
    from .completion import write
    write(args.output_dir.with_suffix('.submission.json'),{'attempt_id':attempt_id,'monitor_pid':child.pid,
        'GPU_snapshot':snapshot,'resource_review':resource_review,'spec_sha256':plan['preflight']['spec_sha256'],
        'output':str(args.output_dir.resolve()),'log':str(log.resolve()),'online_PPO':0})
    print(json.dumps({'monitor_pid':child.pid,'attempt_id':attempt_id,'log':str(log)},indent=2),flush=True)
    return child.wait() if args.wait else 0


if __name__=='__main__':raise SystemExit(main())
