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


def run_phase(spec_path,phase,output,handshake_fd=None):
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
        write(output/'wiring_certificate.json',smoke_certificate(output,read(spec_path)))
    return {'phase':phase,'run':str(output),'exit_code':code,'terminal':terminal,'progress':progress,
        'analysis':str(output/'analysis.json'),'status':terminal.get('status','UNKNOWN')}


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
    event=identity({'chain':str(chain),'attempt':read(chain/'manifest.json')['attempt_id']})[:24]
    analysis={'event_id':event,'status':status,'failure':failure,'phase_results':[
        {key:value for key,value in row.items() if key!='progress'} for row in phase_results],
        'budget':book,'formal_updates':book['used']['formal'],'smoke_updates':book['used']['smoke'],
        'formal_samples':book['used']['formal']*8192,'smoke_samples':book['used']['smoke']*8192,
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
                       path.read_text() if path.is_file() else 'Report missing; see phase log/terminal.'])
    report+=['## Final durability',json.dumps(durability,indent=2),
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
        for phase in ('source_eval','smoke','formal'):
            write(chain/'chain_progress.json',{'status':'RUNNING','stage':phase,'worker_pid':os.getpid(),
                'active_run':str(chain/phase),'finished_phases':[row['phase'] for row in phases]})
            row=run_phase(spec,phase,chain/phase,args.handshake_fd if phase=='formal' else None)
            phases.append(row)
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
                from native_stand.command_v6.wiring import smoke_certificate
                certificate=smoke_certificate(chain/'smoke',read(spec))
                write(chain/'smoke/wiring_certificate.json',certificate)
                if certificate['status']!='PASSED':raise RuntimeError(certificate['errors'])
        selected=read(chain/'formal/candidate_selection.json',{})
        best=selected.get('accepted_candidate')
        if best and read(spec).get('evaluation',{}).get('run_final_durability',True):
            write(chain/'chain_progress.json',{'status':'RUNNING','stage':'durability','worker_pid':os.getpid(),
                'checkpoint':best['checkpoint']})
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
        write(chain/'chain_progress.json',{'status':status,'stage':'finished','worker_pid':os.getpid(),
            'failure':failure})
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
        write(chain/'manifest.json',{'attempt_id':attempt,'hapi_session':args.hapi_session,
            'spec_path':str(spec),'spec_sha256':sha(spec),'kind':'standing_chain','submitted_unix_s':time.time()})
        reader,writer=os.pipe()
        command=[sys.executable,str(chain/'source_snapshot/native_stand/command_v6/stand_chain.py'),'--spec',str(spec),'--output-dir',str(chain),
            '--hapi-session',args.hapi_session,'--worker','--handshake-fd',str(writer)]
        with (chain/'chain.log').open('x') as stream:
            child=subprocess.Popen(command,env={**os.environ,'CUDA_VISIBLE_DEVICES':str(getattr(args,'physical_gpu',0))},start_new_session=True,
                pass_fds=(writer,),stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
        os.close(writer)
        write(submission,{'chain':str(chain),'worker_pid':child.pid,'command':command,
            'hapi_session':args.hapi_session,'attempt_id':attempt})
    ready,_,_=select.select([reader],[],[],240)
    handshake={'status':'UNKNOWN','reason':'single formal-start handshake not ready; background report authoritative'}
    if ready:
        message=os.read(reader,65536).split(b'\n',1)[0]
        if message:
            handshake=json.loads(message)
    os.close(reader)
    if handshake.get('status')=='RUNNING':
        from native_stand.command_v6.submission import validate_handshake
        monitor=read(chain/'formal.monitor.json',{})
        handshake=validate_handshake(handshake,spec_path=spec,output=chain/'formal',
            attempt_id=monitor.get('attempt_id'),monitor_pid=monitor.get('monitor_pid'),
            monitor_started_unix_s=monitor.get('process_started_unix_s'))
    result={'chain':str(chain),'worker_pid':child.pid,'hapi_session':args.hapi_session,**handshake}
    write(chain/'startup_handshake.json',result)
    print(json.dumps(result,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session',default=os.environ.get('HAPI_SESSION_ID'))
    parser.add_argument('--launch',action='store_true')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--handshake-fd',type=int,help=argparse.SUPPRESS)
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
