"""One authorized detached standing chain; no polling or automatic new chain."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from native_stand.command_v6.completion import write,read,sha,identity,notify
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.tools.preflight import check
from native_stand.command_v6.domain.evidence import resolve_gate
from native_stand.command_v6.domain.execution_plan import samples_for_updates,smoke_plan
from native_stand.command_v6.tools.run_state import RunState, record as record_state, state_from_stage, write_handshake


def chain_event(fd, event):
    """Best-effort startup events; a closed client pipe never stops a child."""
    if fd is None:return
    try:os.write(fd,(json.dumps(event)+'\n').encode())
    except OSError:pass


def read_startup_events(fd, *, wait_s, wait_for_formal=False):
    """Wait only on owned child events; never read or poll training logs."""
    if not isinstance(wait_s,(int,float)) or not 0<=wait_s<=600:
        raise ValueError('handshake wait must be within0..600seconds')
    deadline=time.monotonic()+wait_s
    message={'status':'SUBMITTED','current_stage':'submission','formal_first_update_verified':False,
             'started':False,'identity_verified':False,
             'reason':'owned worker submitted; formal first update not yet verified'}
    pending=b''
    while True:
        ready,_,_=select.select([fd],[],[],max(0.,deadline-time.monotonic()))
        if not ready:return message
        chunk=os.read(fd,65536)
        if not chunk:return message
        pending+=chunk
        while b'\n' in pending:
            encoded,pending=pending.split(b'\n',1)
            try:event=json.loads(encoded)
            except (ValueError,UnicodeError):
                return {'status':'UNKNOWN','started':False,'formal_first_update_verified':False,
                        'current_stage':message['current_stage'],'reason':'malformed child startup event'}
            if not isinstance(event,dict):
                return {'status':'UNKNOWN','started':False,'formal_first_update_verified':False,
                        'current_stage':message['current_stage'],'reason':'malformed child startup event'}
            if event.get('event_type') in ('stage_started','stage_finished'):
                message.update(current_stage=event['phase'],stage_event=event)
                if event.get('event_type')=='stage_finished' and event.get('exit_code')!=0:
                    return {**message,'status':'FAILED','reason':'owned phase exited unsuccessfully'}
                if not wait_for_formal:return message
            elif event.get('event_type')=='chain_finished':
                return {**message,'status':event.get('status','UNKNOWN'),'current_stage':'finished',
                        'reason':'chain ended before formal first-update verification','chain_event':event}
            else:
                # Formal trainer's first-update message has no chain event_type.
                return {**event,'current_stage':'formal','formal_first_update_verified':False,
                        'started':False,'identity_verified':False}
        if time.monotonic()>=deadline:return message


def run_phase(spec_path,phase,output,handshake_fd=None):
    spec=read(spec_path)
    if phase=='smoke' and smoke_plan(spec)['budget_sufficient'] is False:
        raise ValueError('smoke sampling budget cannot cover the required event')
    result=check(spec_path,output,phase)
    if result['status']!='PASS':
        raise ValueError(f'{phase} preflight: {result}')
    attempt=uuid.uuid4().hex
    Ledger(spec_path.with_name('budget.json')).reserve(attempt,phase,output)
    temporary_pipe=handshake_fd is None
    if temporary_pipe:
        reader,writer=os.pipe()
    else:
        writer=handshake_fd
    command=[sys.executable,str(ROOT/'monitor.py'),'--spec',str(spec_path),'--phase',phase,
        '--output-dir',str(output),'--attempt-id',attempt,'--handshake-fd',str(writer)]
    with output.with_name(output.name+'.log').open('x') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,pass_fds=(writer,))
        write(output.with_name(output.name+'.monitor.json'),{'attempt_id':attempt,'monitor_pid':child.pid,
            'command':command,'output_dir':str(output),'hapi_session':None,
            'process_started_unix_s':__import__('native_stand.command_v6.tools.health_check',fromlist=['own_process_start']).own_process_start(child.pid)})
        code=child.wait()
    if temporary_pipe:
        os.close(writer)
        os.close(reader)
    terminal=read(output/'terminal_report.json',{})
    progress=read(output/'progress.json',{})
    if phase=='smoke' and code==0 and terminal.get('status') in ('COMPLETED','STOPPED_BOUNDED'):
        from native_stand.command_v6.wiring import smoke_certificate
        certificate=smoke_certificate(output,spec)
        # run_phase is the only generation owner; other entry points validate.
        with (output/'wiring_certificate.json').open('x') as stream:
            json.dump(certificate,stream,indent=2,allow_nan=False)
            stream.write('\n')
    return {'phase':phase,'run':str(output),'exit_code':code,'terminal':terminal,'progress':progress,
        'analysis':str(output/'analysis.json'),'status':terminal.get('status','UNKNOWN')}


def correct_smoke_receipt(spec_path, evidence_folder, output):
    """Phase-owner offline correction in a fresh file; original receipt stays intact."""
    from native_stand.command_v6.wiring import smoke_certificate
    old=read(Path(evidence_folder)/'wiring_certificate.json')
    if old.get('errors')!=['smoke did not observe the required completed_episode']:
        raise ValueError('unexpected smoke failure; correction is not a general bypass')
    certificate=smoke_certificate(Path(evidence_folder),read(spec_path))
    if certificate['status']!='PASSED':raise ValueError(certificate['errors'])
    with Path(output).open('x') as stream:
        json.dump(certificate,stream,indent=2);stream.write('\n')
    return certificate


def reconcile_durability(spec_path,output,code,wall_s):
    ledger=spec_path.with_name('budget.json')
    book=read(ledger)
    matches=[(key,row) for key,row in book['attempts'].items() if row['output_dir']==str(output.resolve())]
    if len(matches)>1:
        raise ValueError('duplicate durability attempt')
    if matches and matches[0][1]['status']=='RUNNING':
        attempt,row=matches[0]
        status='TERMINATED' if code in (124,137,-9,-15) else 'FAILED'
        Ledger(ledger).finalize(attempt,output,status,exit_code=code,wall_s=wall_s,
            reason='durability process did not finalize itself')
    result=read(output,{}) or {}
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    spec=read(spec_path)
    expected=protocol_for_spec(spec,result.get('seconds',spec['evaluation'].get('durability_seconds',100)))
    gate=resolve_gate(result,'recovery' if result.get('task')=='recovery' else 'standing',
        expected_envs=spec['evaluation']['scored_envs'],expected_protocol=expected)
    return {'exit_code':code,'wall_s':wall_s,'result':str(output),
        'terminal':read(output.with_name(output.stem+'.terminal.json')),
        'standing_gate':result.get('standing_gate'),'gate_evidence':gate}


def chain_report(chain,spec_path,phase_results,status,failure,durability):
    formal=next((row for row in phase_results if row['phase']=='formal'),None)
    source=next((row for row in phase_results if row['phase']=='source_eval'),None)
    selected=read(Path((formal or source)['run'])/'candidate_selection.json',{}) if formal or source else {}
    book=read(spec_path.with_name('budget.json'))
    spec=read(spec_path)
    event=identity({'chain':str(chain),'attempt':read(chain/'manifest.json')['attempt_id']})[:24]
    analysis={'event_id':event,'status':status,'failure':failure,'phase_results':[
        {key:value for key,value in row.items() if key!='progress'} for row in phase_results],
        'budget':book,'formal_updates':book['used']['formal'],'smoke_updates':book['used']['smoke'],
        'formal_samples':samples_for_updates(spec,book['used']['formal']),
        'smoke_samples':samples_for_updates(spec,book['used']['smoke']),
        'remaining_formal_updates':book['limits']['formal']-book['used']['formal'],
        'candidate_selection':selected,'durability':durability,
        'training_acceptance_is_not_durability_acceptance':True}
    analysis['task_curriculum']=(formal or {}).get('terminal',{}).get('task_curriculum')
    analysis['best_motion_candidate']=(formal or {}).get('terminal',{}).get('best_motion_candidate')
    analysis['chain_wall_s']=time.time()-read(chain/'manifest.json').get('submitted_unix_s',time.time())
    write(chain/'chain_terminal_report.json',analysis)
    write(chain/'analysis.json',analysis)
    write(chain/'candidate_selection.json',selected)
    report=['# Native standing long-run completion',f'Event: {event}',f'Chain: {chain}',
        f'Terminal: {status}; failure={failure}',
        f"Smoke updates/samples: {analysis['smoke_updates']} / {analysis['smoke_samples']}",
        f"Formal updates/samples: {analysis['formal_updates']} / {analysis['formal_samples']}; remaining={analysis['remaining_formal_updates']}",
        f"Best: {selected.get('best_observed_candidate',{}).get('checkpoint') if selected.get('best_observed_candidate') else None}",
        f"10-second accepted: {bool(selected.get('accepted_candidate'))}; durability gate status={(durability.get('gate_evidence') or {}).get('status',durability.get('status','MISSING_EVIDENCE')) if durability else 'NOT_RUN'}",
        f"Task curriculum: {analysis['task_curriculum']}",
        f"Best verified motion: {analysis['best_motion_candidate']}",
        f"Chain wall seconds: {analysis['chain_wall_s']}",
        '## Phase quantitative reports']
    for row in phase_results:
        path=Path(row['run'])/'completion_report.md'
        report.extend([f"{row['phase']}: {row['status']}, exit={row['exit_code']}, report={path}",
                       f'Quantitative evidence: {path}; raw evaluation JSON remains in {Path(row["run"])}.'
                       if path.is_file() else 'Report missing; see phase log/terminal.'])
    from native_stand.command_v6.completion import compact_report_value
    report+=['## Final durability',json.dumps(compact_report_value(durability),indent=2),
        'Ordinary falls are task results. Missing/unfinished evaluation is not standing success. No automatic continuation is authorized.']
    (chain/'completion_report.md').write_text('\n\n'.join(report)+'\n')
    write(chain/'report_ready.json',{'event_id':event,'status':'report_ready',
        'report_sha256':sha(chain/'completion_report.md'),'time':time.time()})
    notify(chain)


def worker(args):
    chain=args.output_dir.resolve()
    spec=args.spec.resolve()
    phases=[]
    failure=None
    durability=None
    status='FAILED'
    try:
        if not (chain/'run_state.json').exists():
            # Direct internal workers and old CPU fixtures still get the canonical receipt.
            record_state(chain,RunState.SUBMITTED.value,phase='submission')
        for phase in ('source_eval','smoke','formal'):
            record_state(chain,state_from_stage(phase),phase=phase,worker_pid=os.getpid(),
                active_run=str(chain/phase),finished_phases=[row['phase'] for row in phases])
            chain_event(args.handshake_fd,{'event_type':'stage_started','phase':phase,
                'worker_pid':os.getpid(),'active_run':str(chain/phase)})
            row=run_phase(spec,phase,chain/phase,args.handshake_fd if phase=='formal' else None)
            phases.append(row)
            chain_event(args.handshake_fd,{'event_type':'stage_finished','phase':phase,
                'worker_pid':os.getpid(),'exit_code':row['exit_code'],'status':row['status']})
            if row['terminal'].get('stop_kind')=='user_signal':
                if row['exit_code']!=0 or row['status']!='STOPPED_BOUNDED':
                    raise RuntimeError(f'{phase} user-stop terminal/exit conflict')
                status='STOPPED_BOUNDED'
                durability={'status':'NOT_RUN','reason':'user stopped chain'}
                return 0
            if row['exit_code']!=0 or row['status'] not in ('COMPLETED','STOPPED_BOUNDED'):
                raise RuntimeError(f'{phase} runtime/infrastructure failure: see {row["run"]}')
            geometry=read(spec).get('diagnostics',{}).get('wheel_geometry_readback_gate')
            if phase=='source_eval' and geometry:
                from native_stand.recovery.asset_poses import verify_wheel_readback
                config=read(spec)
                review=verify_wheel_readback(read(chain/'source_eval/evaluation_source.json'),
                    config['asset_path'],read(Path(config['recovery']['pose_library'])),
                    tolerance_m=geometry['tolerance_m'],samples_per_env=geometry['samples_per_env'])
                write(chain/'wheel_geometry_readback.json',review)
                if not review['passed']:raise RuntimeError('Runtime/USD wheel geometry mismatch; no PPO started')
            if phase=='smoke' and (row['terminal'].get('actual_updates',0)!=read(spec)['budget']['smoke_updates'] or
                    not row['progress'].get('actor_parameters_changed')):
                raise RuntimeError('smoke did not verify a finite actual actor update')
            if phase=='smoke':
                from native_stand.command_v6.wiring import validate_persisted_certificate
                certificate=validate_persisted_certificate(chain/'smoke',read(spec))
                if certificate['status']!='PASSED':raise RuntimeError(certificate['errors'])
        selected=read(chain/'formal/candidate_selection.json',{})
        best=selected.get('accepted_candidate')
        if best and read(spec).get('evaluation',{}).get('run_final_durability',True):
            record_state(chain,RunState.FORMAL.value,phase='durability',worker_pid=os.getpid(),
                checkpoint=best['checkpoint'])
            output=chain/'durability_100s.json'
            final_wall=read(spec).get('budget',{}).get('durability_wall_s',600)
            command=['timeout','--signal=TERM','--kill-after=15s',f'{final_wall-30}s',sys.executable,
                str(ROOT/'tools/evaluate_checkpoint.py'),'--spec',str(spec),'--checkpoint',best['checkpoint'],
                '--output',str(output),'--seconds','100','--full-trace','--run']
            start=time.monotonic()
            with (chain/'durability.log').open('x') as stream:
                code=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT).returncode
            durability=reconcile_durability(spec,output,code,time.monotonic()-start)
        else:
            durability={'status':'NOT_RUN','reason':'durability not included in this controlled test' if best else 'no identity-matched accepted standing candidate'}
        status='COMPLETED'
    except BaseException as exc:
        failure=repr(exc)
    finally:
        record_state(chain,status if status in ('COMPLETED','STOPPED_BOUNDED') else RunState.FAILED.value,
            phase='finished',worker_pid=os.getpid(),failure=failure)
        chain_event(args.handshake_fd,{'event_type':'chain_finished','status':status,
            'worker_pid':os.getpid(),'failure':failure})
        try:
            chain_report(chain,spec,phases,status,failure,durability)
        except Exception as exc:
            write(chain/'completion_error.json',{'error':repr(exc),'failure':failure})
        try:
            os.close(args.handshake_fd)
        except OSError:
            pass
    return 0 if status=='COMPLETED' else 1


def launch(args):
    spec=args.spec.resolve()
    chain=args.output_dir.resolve()
    preflight=check(spec,chain/'source_eval','source_eval')
    if preflight['status']!='PASS':
        raise ValueError(preflight)
    if not args.hapi_session:
        raise ValueError('this chain requires an explicit confirmed HAPI target')
    configured=read(spec).get('authorization',{}).get('hapi_session')
    if configured and args.hapi_session!=configured:
        raise ValueError('HAPI target differs from the authorized spec')
    explicit_wait=getattr(args,'handshake_wait_s',None)
    wait_s=explicit_wait if explicit_wait is not None else read(spec).get('submission',{}).get('handshake_timeout_s',5.)
    if not isinstance(wait_s,(int,float)) or not 0<=wait_s<=600:
        raise ValueError('handshake wait must be within0..600seconds')
    submission=spec.with_name('chain_submission.json')
    with spec.with_name('chain_submission.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if submission.exists():
            raise ValueError('this authorization already has a chain submission; no duplicate/restart')
        chain.mkdir(parents=True,exist_ok=False)
        (chain/'source_snapshot').mkdir()
        shutil.copy2(spec,chain/'source_snapshot/spec.json')
        shutil.copytree(ROOT.parent,chain/'source_snapshot/native_stand',ignore=shutil.ignore_patterns('__pycache__'))
        attempt=uuid.uuid4().hex
        resource={'resource_policy':getattr(args,'resource_policy',None),
                  'resource_review':getattr(args,'resource_review',None)}
        write(chain/'manifest.json',{'attempt_id':attempt,'hapi_session':args.hapi_session,
            'spec_path':str(spec),'spec_sha256':sha(spec),'kind':'standing_chain',
            'declared_execution_source_root':read(spec).get('execution_source_root'),
            'execution_modules_sha256':{str(p.relative_to(chain/'source_snapshot/native_stand')):sha(p)
                for p in sorted((chain/'source_snapshot/native_stand').rglob('*.py'))},
            'submitted_unix_s':time.time(),**resource})
        reader,writer=os.pipe()
        command=[sys.executable,str(chain/'source_snapshot/native_stand/command_v6/stand_chain.py'),'--spec',str(spec),'--output-dir',str(chain),
            '--hapi-session',args.hapi_session,'--worker','--handshake-fd',str(writer),
            '--attempt-id',attempt]
        record_state(chain,RunState.SUBMITTED.value,phase='submission',attempt_id=attempt)
        with (chain/'chain.log').open('x') as stream:
            child=subprocess.Popen(command,env={**os.environ,'CUDA_VISIBLE_DEVICES':str(getattr(args,'physical_gpu',0))},start_new_session=True,
                pass_fds=(writer,),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
        os.close(writer)
        write(submission,{'chain':str(chain),'worker_pid':child.pid,'command':command,
            'hapi_session':args.hapi_session,'attempt_id':attempt,
            'process_started_unix_s':__import__('native_stand.command_v6.tools.health_check',fromlist=['own_process_start']).own_process_start(child.pid),
            **resource})
    try:
        handshake=read_startup_events(reader,wait_s=wait_s,wait_for_formal=explicit_wait is not None)
    finally:os.close(reader)
    if handshake.get('status')=='RUNNING':
        from native_stand.command_v6.submission import validate_handshake
        monitor=read(chain/'formal.monitor.json',{})
        handshake=validate_handshake(handshake,spec_path=spec,output=chain/'formal',
            attempt_id=monitor.get('attempt_id'),monitor_pid=monitor.get('monitor_pid'),
            monitor_started_unix_s=monitor.get('process_started_unix_s'))
        handshake['formal_first_update_verified']=handshake.get('started',False)
    from native_stand.command_v6.tools.health_check import process_identity
    submission_record=read(submission,{})
    worker_evidence=process_identity(child.pid,output_dir=chain,attempt_id=attempt,
        command_token='stand_chain.py',started_unix_s=submission_record.get('process_started_unix_s'),
        spec_path=spec,physical_gpu=getattr(args,'physical_gpu',0),hapi_session=args.hapi_session)
    if handshake.get('status')=='SUBMITTED' and worker_evidence['status']!='OK':
        handshake.update(status='UNKNOWN',reason='submission receipt present but worker identity unverified')
    result={'chain':str(chain),'worker_pid':child.pid,'hapi_session':args.hapi_session,
        'submitted':True,'submission_verified':worker_evidence['status']=='OK',
        'worker_evidence':worker_evidence,'handshake_wait_s':wait_s,
        'run_state':read(chain/'run_state.json',{}).get('state',RunState.SUBMITTED.value),**resource,**handshake}
    result=write_handshake(chain,result)
    print(json.dumps(result,indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session',default=os.environ.get('HAPI_SESSION_ID'))
    parser.add_argument('--launch',action='store_true')
    parser.add_argument('--handshake-wait-s',type=float,default=None,
        help='optional bounded wait for formal first update; default reports the first owned phase event')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--handshake-fd',type=int,help=argparse.SUPPRESS)
    parser.add_argument('--attempt-id',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        return worker(args)
    if args.launch:
        launch(args)
    else:
        print(json.dumps(check(args.spec,args.output_dir/'source_eval','source_eval'),indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
