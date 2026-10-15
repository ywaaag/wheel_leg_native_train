"""Bounded Recovery workflow; reuse probes, trainer monitor, exact ledger and HAPI notification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from native_stand.command_v6.completion import write,notify
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.monitor import reconcile
from native_stand.command_v6.tools.preflight import check
from native_stand.recovery.preflight import check as cpu_check


def read(path,default=None):
    return json.loads(Path(path).read_text()) if Path(path).is_file() else default


def gate_ok(mode,result,terminal,code):
    if code!=0 or terminal.get('status')!='COMPLETED' or not result:return False
    if mode=='r0':
        return result.get('standing_gate',{}).get('accepted') is True and len(result.get('per_env',[]))==8
    return result.get('passed') is True and result.get('validated_envs')==64


def baseline_ok(result,terminal,source_sha):
    if not result or terminal.get('status')!='COMPLETED' or terminal.get('exit_code')!=0:
        return False
    rows=result.get('per_env',[])
    protocol=result.get('success_protocol',{})
    return (result.get('checkpoint_sha256')==source_sha and len(rows)==8 and
        protocol.get('mode')=='autonomous_hold' and protocol.get('required_stable_s')==2. and
        protocol.get('teacher_control') is False and
        all(row.get('initial_valid') is True and row.get('outcome') in ('success','task_failure') and
            row.get('runtime_fault') is False for row in rows) and
        all(row.get('rejected',0)==0 for row in result.get('initialization',[])))


def run(args):
    spec_path=args.spec.resolve();output=args.output_dir.resolve()
    if output.exists():raise FileExistsError(output)
    preflight=cpu_check(spec_path,output)
    if not preflight['cpu_valid']:raise ValueError(preflight['errors'])
    book=read(spec_path.with_name('budget.json'))
    spec=read(spec_path)
    autonomous=spec['recovery']['fsm'].get('success_mode')=='autonomous_hold'
    baseline=Path(spec['recovery']['baseline_evidence']).resolve() if autonomous and spec['recovery'].get('baseline_evidence') else None
    if autonomous:
        if baseline is None or not baseline_ok(read(baseline/'result.json'),read(baseline/'terminal_report.json',{}),spec['source_sha256']):
            raise ValueError('Autonomous task requires completed fixed-source baseline; task failures are allowed')
        exact=[row for row in book['attempts'].values() if row['output_dir']==str(baseline)]
        if len(exact)!=1 or exact[0]['phase']!='source_eval' or exact[0]['status']!='COMPLETED':
            raise ValueError('Baseline exact ledger identity differs')
        if any(row['status']=='RUNNING' for row in book['attempts'].values()) or book['used']['smoke'] or book['used']['formal']:
            raise ValueError('Autonomous chain requires no prior PPO/live attempt')
    prior=read(args.reuse_r0/'chain_terminal_report.json',{}) if args.reuse_r0 else None
    if args.reuse_r0:
        if not prior or prior.get('actual_updates')!=0 or prior.get('stand_sha256')!=read(spec_path)['recovery']['stand_sha256']:
            raise ValueError('Reuse requires matching frozen STAND and zero prior PPO')
        if not gate_ok('r0',read(args.reuse_r0/'r0/result.json'),read(args.reuse_r0/'r0/terminal_report.json',{}),0):
            raise ValueError('Previous R0 has no passing evidence')
        if any(row['status']=='RUNNING' for row in book['attempts'].values()) or book['used']['smoke'] or book['used']['formal']:
            raise ValueError('Retry requires no live attempt or prior PPO')
    if book['authorization']!='AUTHORIZED' or (not autonomous and not args.reuse_r0 and (book['attempts'] or any(book['used'].values()))):
        raise ValueError('Chain requires this new authorized, unused exact ledger')
    spec=read(spec_path)
    started=time.monotonic();stages=[];failure=None;status='FAILED';stopped=False;child=None
    def on_stop(*unused):
        nonlocal stopped
        stopped=True
        if child is not None and child.poll() is None:child.terminate()
    signal.signal(signal.SIGTERM,on_stop);signal.signal(signal.SIGINT,on_stop)
    output.mkdir(parents=True,exist_ok=False)
    write(output/'manifest.json',{'task':'recovery_R1_chain','hapi_session':args.hapi_session,
        'attempt_id':uuid.uuid4().hex,'spec_path':str(spec_path),'pid':os.getpid(),
        'source_stand_sha256':spec['recovery']['stand_sha256'],'budget':spec['budget'],
        'only_final_chain_notification':True})
    write(output/'spec_before_physical_validation.json',spec)
    def progress(stage,**extra):
        write(output/'chain_progress.json',{'status':'RUNNING','stage':stage,
            'pid':os.getpid(),'wall_s':time.monotonic()-started,'stages':stages,**extra})
    def execute(command,folder,bound):
        nonlocal child
        t=time.monotonic()
        # Reserve kill/cleanup margin within the requested per-stage ceiling.
        timed=['timeout','--signal=TERM','--kill-after=15s',f'{max(1,bound-25):.2f}s',*command]
        with folder.with_suffix('.log').open('x') as stream:
            child=subprocess.Popen(timed,cwd=str(Path.cwd()),env={**os.environ,'CUDA_VISIBLE_DEVICES':'0'},
                stdout=stream,stderr=subprocess.STDOUT,
                pass_fds=(() if args.handshake_fd is None else (args.handshake_fd,)))
            progress(folder.name,child_pid=child.pid,command=timed)
            code=child.wait()
        elapsed=time.monotonic()-t
        stages.append({'stage':folder.name,'output':str(folder),'exit_code':code,'wall_including_cleanup_s':elapsed})
        return code
    try:
        diagnostic_start=time.monotonic()
        modes=() if autonomous or (spec['recovery'].get('runtime_initialization_validated') and spec['recovery'].get('handover_domain_validated')) else (('initial',) if args.reuse_r0 else ('r0','initial'))
        for mode in modes:
            folder=output/mode
            prior_wall=sum(row['wall_including_cleanup_s'] for row in prior['stages']) if prior else 0.
            remaining=600-prior_wall-(time.monotonic()-diagnostic_start)
            if remaining<60 or stopped:raise RuntimeError('Diagnostic budget/stop prevents next probe')
            command=[sys.executable,'-m','native_stand.recovery.probe','--spec',str(spec_path),
                '--output-dir',str(folder),'--mode',mode,'--run']
            if args.handshake_fd is not None:command+=['--handshake-fd',str(args.handshake_fd)]
            code=execute(command,folder,min(300,remaining))
            ledger=read(spec_path.with_name('budget.json'))
            for attempt,row in ledger['attempts'].items():
                if row['output_dir']==str(folder) and row['status']=='RUNNING':
                    reconcile(spec_path.with_name('budget.json'),attempt,folder,code)
            result=read(folder/'result.json');terminal=read(folder/'terminal_report.json',{})
            if not gate_ok(mode,result,terminal,code):raise RuntimeError(f'{mode} physical prerequisite did not pass; see {folder}')
        # No live child now. Publish measured gate evidence before smoke; probes have immutable snapshots.
        spec['recovery']['runtime_initialization_validated']=True
        spec['recovery']['handover_domain_validated']=True
        if autonomous:
            spec['recovery']['physical_gate_evidence']={'autonomous_baseline':str(baseline/'result.json')}
            spec['recovery']['handover_domain_scope']='Not used: Recovery controls autonomous2s success'
        elif modes:
            spec['recovery']['physical_gate_evidence']={'r0':str((args.reuse_r0 or output)/'r0/result.json'),
                'initial':str(output/'initial/result.json')}
            spec['recovery']['handover_domain_scope']='Four tested near-standing closed poses; not arbitrary disturbance domain'
        write(spec_path,spec)
        write(output/'spec_after_physical_validation.json',spec)
        for phase,bound in (('smoke',spec['budget']['smoke_wall_s']),('formal',spec['budget']['formal_wall_s'])):
            if stopped:raise RuntimeError('User stopped chain; no new phase launched')
            folder=output/phase
            result=check(spec_path,folder,phase)
            if result['status']!='PASS':raise RuntimeError(result['errors'])
            attempt=uuid.uuid4().hex
            Ledger(spec_path.with_name('budget.json')).reserve(attempt,phase,folder,approval=result)
            progress(phase,attempt_id=attempt)
            # Monitor receives a disposable pipe, not the user handshake pipe; notifications remain chain-only.
            forward=(autonomous and phase=='smoke' and args.handshake_fd is not None)
            if forward:
                fd_in=None;fd_out=args.handshake_fd
            else:
                fd_in,fd_out=os.pipe()
            command=[sys.executable,str(Path(__file__).resolve().parents[1]/'command_v6/monitor.py'),
                '--spec',str(spec_path),'--phase',phase,'--output-dir',str(folder),
                '--attempt-id',attempt,'--handshake-fd',str(fd_out)]
            t=time.monotonic()
            with folder.with_suffix('.log').open('x') as stream:
                child=subprocess.Popen(command,cwd=str(Path.cwd()),env={**os.environ,'CUDA_VISIBLE_DEVICES':'0'},
                    stdout=stream,stderr=subprocess.STDOUT,pass_fds=(fd_out,))
            if not forward:
                os.close(fd_out);os.close(fd_in)
            progress(phase,child_pid=child.pid,command=command)
            code=child.wait()
            stages.append({'stage':phase,'output':str(folder),'exit_code':code,
                'wall_including_cleanup_s':time.monotonic()-t})
            reconcile(spec_path.with_name('budget.json'),attempt,folder,code)
            terminal=read(folder/'terminal_report.json',{})
            used=read(spec_path.with_name('budget.json'))['used'][phase]
            smoke_progress=read(folder/'progress.json',{})
            if phase=='smoke' and (code!=0 or terminal.get('status')!='COMPLETED' or used!=spec['budget']['smoke_updates'] or
                    smoke_progress.get('actor_parameters_changed') is not True):
                raise RuntimeError(f"Smoke wiring did not finish{spec['budget']['smoke_updates']}finite updates; formal not launched")
            if phase=='formal':
                status=terminal.get('status','FAILED')
                if code!=0 and status=='COMPLETED':status='FAILED'
                failure=terminal.get('failure') or terminal.get('reason')
    except BaseException as exc:
        failure=repr(exc);status='STOPPED_BOUNDED' if stopped else 'FAILED'
    finally:
        book=read(spec_path.with_name('budget.json'))
        updates=book['used']['smoke']+book['used']['formal'];samples=updates*8192
        selection=read(output/'formal/candidate_selection.json',{})
        report={'status':status,'reason':failure,'wall_s':time.monotonic()-started,
            'actual_updates':updates,'samples':samples,'smoke_updates':book['used']['smoke'],
            'formal_updates':book['used']['formal'],'remaining_updates':book['limits']['formal']-book['used']['formal'],
            'stages':stages,'budget_path':str(spec_path.with_name('budget.json')),
            'success_mode':spec['recovery']['fsm'].get('success_mode','handover'),
            'baseline':str(baseline) if baseline else None,
            'stage':'R1','stand_frozen':True,'stand_sha256':spec['recovery']['stand_sha256']}
        write(output/'chain_terminal_report.json',report);write(output/'analysis.json',report)
        write(output/'candidate_selection.json',selection)
        text=f"# Recovery R1 chain\n\nTerminal: {status}\n\nReason: {failure}\n\nActual updates/samples: {updates}/{samples}\n\nWall including child cleanup: {report['wall_s']:.1f}s\n\nStages: {json.dumps(stages)}\n\nFrozen STAND: {spec['recovery']['stand_sha256']}\n\nCandidates: formal/candidate_selection.json; quantitative evaluation: formal/completion_report.md. Missing artifacts mean not reached, not zero performance.\n\nNo automatic R2, retry, or continuation authorized.\n"
        (output/'completion_report.md').write_text(text)
        event=hashlib.sha256(str(output).encode()).hexdigest()[:24]
        write(output/'report_ready.json',{'event_id':event,'status':'report_ready',
            'report_sha256':hashlib.sha256(text.encode()).hexdigest(),'time':time.time()})
        write(output/'chain_progress.json',{**report,'stage':'terminal'})
        try:notify(output)
        except Exception as exc:write(output/'notification_error.json',{'error':repr(exc),'training_accounting_unchanged':True})
    return 0 if status in ('COMPLETED','STOPPED_BOUNDED') else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    from native_stand.command_v6.tools.entrypoints import add_historical_option,require_historical_option
    add_historical_option(parser)
    parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session',default=None);parser.add_argument('--handshake-fd',type=int,default=None)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--reuse-r0',type=Path,default=None,help='Reuse a passed prior R0; preserve ledger consumption')
    args=parser.parse_args()
    require_historical_option(parser,args)
    if not args.run:print(json.dumps(cpu_check(args.spec,args.output_dir),indent=2));return 0
    return run(args)


if __name__=='__main__':raise SystemExit(main())
