"""Shared source -> wiring smoke -> formal chain, with a read-only default plan."""
import argparse
import json
import os
from pathlib import Path
from .tools.health_check import inspect_project
from .tools.preflight import check


def submission_readiness(args, spec, preflight, health=None):
    from .domain.submission_contract import metadata
    from .tools.health_check import submission_health
    output = args.output_dir / 'formal' if args.formal_only else args.output_dir
    result = metadata(spec, target_session=args.hapi_session,
        current_session=os.environ.get('HAPI_SESSION_ID'), physical_gpu=args.physical_gpu,
        output_available=not output.exists(), duplicate_submission=(
            not args.formal_only and not args.evaluation_only and
            args.spec.with_name('chain_submission.json').exists()))
    result.update(configuration_status='VALID' if preflight['status']=='PASS' else 'NOT_READY',
                  resource_verified=False, submit_ready=False)
    if preflight['status']!='PASS':
        result['errors'].append('preflight prerequisite: '+str(preflight.get('errors',preflight['status'])))
        result['reason_code']=preflight.get('reason_code','MISSING_EVIDENCE')
    if not result['errors'] and health is not None:
        try:
            result['resource_review']=submission_health(health,
                current_session=os.environ.get('HAPI_SESSION_ID'),target_session=args.hapi_session,
                phase='evaluate' if args.evaluation_only else 'formal' if args.formal_only else 'source_eval',
                physical_gpu=args.physical_gpu,resource_policy=args.resource_policy)
            expected_uuid=spec.get('device',{}).get('uuid')
            devices=(health.get('gpu') or {}).get('devices',[])
            if expected_uuid and not any(row['index']==args.physical_gpu and
                                        row['uuid']==expected_uuid for row in devices):
                raise ValueError('physical GPU UUID differs from spec')
            if spec.get('recovery_course'):
                selected=[d for d in devices if d['index']==args.physical_gpu]
                if len(selected)!=1:raise ValueError('Recovery course GPU inventory missing')
                free=float(selected[0]['memory_total_mib'])-float(selected[0]['memory_used_mib'])
                if free<4096:raise ValueError('Recovery course requires4096MiB available GPU memory; no preemption/wait/switch')
                result['resource_review']['course_available_memory_mib']=free
                result['resource_review']['course_minimum_available_memory_mib']=4096
            result['resource_verified']=True
            result['submit_ready']=True
        except ValueError as exc:
            result['errors'].append(str(exc))
            result['reason_code']='IDENTITY_ERROR' if 'UUID differs' in str(exc) else 'MISSING_EVIDENCE'
    result['status']=('NOT_READY' if result['errors'] else
                      'READY' if result['submit_ready'] else 'READY_METADATA')
    if result['status']=='READY_METADATA':
        result['reason_code']='MISSING_EVIDENCE'
        result['action']='use --check-submission for one read-only resource check'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session')
    parser.add_argument('--physical-gpu',type=int,choices=(0,1))
    parser.add_argument('--launch',action='store_true')
    parser.add_argument('--check-submission',action='store_true',
        help='read-only full submission contract/resource check; does not reserve or launch')
    parser.add_argument('--formal-only',action='store_true',help='reuse verified source/smoke from this same chain')
    parser.add_argument('--evaluation-only',action='store_true',help='PPO0 requests via shared evaluator/monitor')
    parser.add_argument('--wait',action='store_true',help='wait for owned bounded evaluation monitor, no log polling')
    parser.add_argument('--resource-mode',choices=('exclusive','shared'),default=None)
    parser.add_argument('--sharing-authorization',help='explicit user approval and reason for shared GPU use')
    parser.add_argument('--handshake-wait-s',type=float,default=None)
    args=parser.parse_args()
    if args.check_submission and args.launch:
        parser.error('--check-submission is read-only; do not combine it with --launch')
    from .domain.resource_policy import resolve_resources
    spec=json.loads(args.spec.read_text())
    args.resource_policy=resolve_resources(spec,
        mode=args.resource_mode,sharing_authorization=args.sharing_authorization)
    if args.handshake_wait_s is not None and not 0<=args.handshake_wait_s<=600:
        raise ValueError('handshake-wait-s must be in [0,600]')
    if spec.get('engineering_recovery') and args.evaluation_only:
        parser.error('engineering recovery cannot be used for new PPO0')
    if args.evaluation_only:
        return evaluate_submission(args)
    if spec.get('engineering_recovery'):
        args.formal_only=True
    phase='formal' if args.formal_only else 'source_eval'
    from native_stand.students.course_requests import project_root_for
    project=project_root_for(spec,Path(__file__).resolve().parents[3])
    result=check(args.spec,args.output_dir/phase,phase)
    plan={'preflight':result,'health':inspect_project(project,spec_path=args.spec,
            include_processes=args.launch or args.check_submission,hapi_session=args.hapi_session),
          'stages':(['formal','terminal_reconciliation'] if spec.get('engineering_recovery') else ['source_eval','smoke','formal','terminal_reconciliation']),
          'hapi_session':args.hapi_session,'resource_policy':args.resource_policy,
          'simulation':0,'ppo':0,'files_written':0}
    plan['submission_contract']=submission_readiness(args,spec,result,
        plan['health'] if args.launch or args.check_submission else None)
    if not args.launch:
        print(json.dumps(plan,indent=2))
        return 2 if args.check_submission and not plan['submission_contract']['submit_ready'] else 0
    if result['status']!='PASS':raise ValueError(result)
    if not plan['submission_contract']['submit_ready']:
        raise ValueError(plan['submission_contract']['errors'])
    args.resource_review=plan['submission_contract']['resource_review']
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
    health=None
    if args.launch or args.check_submission:
        from native_stand.students.course_requests import project_root_for
        health=inspect_project(project_root_for(spec,Path(__file__).resolve().parents[3]),spec_path=args.spec,
            include_processes=True,hapi_session=args.hapi_session)
    plan['submission_contract']=submission_readiness(args,spec,plan['preflight'],health)
    if not args.launch:
        print(json.dumps(plan,indent=2))
        return 2 if args.check_submission and not plan['submission_contract']['submit_ready'] else 0
    if not plan['submission_contract']['submit_ready']:
        raise ValueError(plan['submission_contract']['errors'])
    if plan['preflight']['status']!='PASS':raise ValueError(plan['preflight'])
    if args.physical_gpu!=spec['device']['physical_index']:
        raise ValueError('explicit physical GPU differs from evaluation spec')
    snapshot=health['gpu']
    devices={row['index']:row['uuid'] for row in snapshot.get('devices',[])}
    if devices.get(args.physical_gpu)!=spec['device']['uuid']:
        raise ValueError('physical GPU UUID differs')
    resource_review=plan['submission_contract']['resource_review']
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
