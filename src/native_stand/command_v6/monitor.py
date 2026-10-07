"""Own one diagnostic child; reconcile only its exact attempt on abnormal exit."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.completion import finalize_report, notify, write


def reconcile(ledger_path,attempt_id,output,exit_code):
    output=Path(output)
    book=json.loads(Path(ledger_path).read_text())
    row=book["attempts"].get(attempt_id)
    if row is None or row["output_dir"]!=str(output.resolve()):
        raise ValueError("monitor attempt identity differs")
    if row["status"]!="RUNNING":
        return {"status":row["status"],"reconciled":False}
    terminal=output/"terminal_report.json"
    if terminal.is_file():
        result=json.loads(terminal.read_text())
        status=result.get("status","FAILED")
    else:
        status="TERMINATED" if exit_code in (124,137,143,-15,-9) else "FAILED"
        result={"status":status,"attempt_id":attempt_id,"phase":row["phase"],
                "actual_updates":row["updates"],"exit_code":exit_code,
                "reason":"trainer exited without terminal report; historical progress may be stale",
                "stop_kind":"hard_timeout" if exit_code==124 else "signal_or_kill" if exit_code in (137,143,-15,-9) else "exception",
                "source":"background monitor exact-attempt reconciliation"}
        if output.is_dir():
            with terminal.open("x") as handle:
                handle.write(json.dumps(result,indent=2)+"\n")
        else:
            terminal=output.with_name(output.name+".terminal_report.json")
            with terminal.open("x") as handle:
                handle.write(json.dumps(result,indent=2)+"\n")
    if row['phase']=='evaluate' and exit_code not in (0,):
        status='TERMINATED' if exit_code in (124,137,143,-15,-9) else 'FAILED'
        result={**result,'status':status,'cleanup_exit_code':exit_code}
        write(output/'supervisor_terminal.json',result)
    wall_s=max(0.,time.time()-row["started_unix_s"]) if row["phase"] in ('source_eval','evaluate') else None
    Ledger(ledger_path).finalize(attempt_id,output,status,exit_code=exit_code,
                                reason=result.get("reason"),wall_s=wall_s)
    return {"status":status,"reconciled":True,"terminal_report":str(terminal)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,required=True)
    parser.add_argument("--phase",required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--attempt-id",required=True)
    parser.add_argument("--handshake-fd",type=int,default=None)
    parser.add_argument('--hapi-session',default=None)
    parser.add_argument('--wall-limit-s',type=float,default=None)
    args=parser.parse_args()
    spec=json.loads(args.spec.read_text())
    if args.phase=='evaluate':
        return evaluation_main(args,spec)
    bound=spec["budget"]["source_eval_wall_s"] if args.phase=="source_eval" else (
        spec["budget"]["smoke_wall_s"] if args.phase=="smoke" else spec["budget"]["formal_wall_s"])
    if spec['evaluation'].get('protocol_identity')=='capability_v2':
        book=json.loads(args.spec.with_name('budget.json').read_text())
        spent=sum(float(row.get('wall_s') or 0.) for key,row in book['attempts'].items()
                  if key!=args.attempt_id)
        bound=min(bound,max(1.,64800.-spent))
        if spec.get('straight_high_speed_course') and book.get('chain_started_unix_s'):
            bound=min(bound,max(1.,64800.-(time.time()-book['chain_started_unix_s'])))
    if args.wall_limit_s is not None:
        if not 60<=args.wall_limit_s<=bound:
            raise ValueError('monitor wall override must narrow the frozen phase budget')
        bound=args.wall_limit_s
    command=[sys.executable,str(ROOT/"train.py"),"--spec",str(args.spec),
             "--phase",args.phase,"--output-dir",str(args.output_dir),
             "--attempt-id",args.attempt_id,"--handshake-fd",str(args.handshake_fd),"--run"]
    if bound is not None:
        command=["timeout","--signal=TERM","--kill-after=30s",f"{max(1,bound-40)}s",*command]
    if args.hapi_session:
        command += ['--hapi-session',args.hapi_session]
    launch_failure=None
    try:
        child=subprocess.Popen(command,cwd=str(ROOT.parents[1]),
                               pass_fds=(args.handshake_fd,))
        os.close(args.handshake_fd)
        exit_code=child.wait()
    except OSError as exc:
        os.close(args.handshake_fd)
        launch_failure=repr(exc)
        exit_code=127
    if not args.output_dir.exists():
        args.output_dir.mkdir()
        (args.output_dir/'source_snapshot').mkdir()
        write(args.output_dir/'source_snapshot/spec.json',spec)
        write(args.output_dir/'manifest.json',{'attempt_id':args.attempt_id,'phase':args.phase,
            'hapi_session':args.hapi_session,'artifact_origin':'monitor after trainer exit without artifacts'})
    result=reconcile(args.spec.with_name("budget.json"),args.attempt_id,
                     args.output_dir,exit_code)
    if args.output_dir.is_dir():
        book=json.loads(args.spec.with_name('budget.json').read_text())
        row=book['attempts'][args.attempt_id]
        write(args.output_dir/'monitor_exit.json',{'exit_code':exit_code,**result,
            'launch_failure':launch_failure,
            'attempt_wall_including_cleanup_s':time.time()-row['started_unix_s'],
            'ledger_updates':row['updates']})
        try:
            finalize_report(args.output_dir,exit_code)
            notify(args.output_dir)
        except Exception as exc:
            write(args.output_dir/'completion_error.json',{'status':'report_or_notification_failed',
                'error':repr(exc),'training_accounting_unchanged':True})
    print(json.dumps({"child_exit_code":exit_code,**result}),flush=True)
    return exit_code


def evaluation_main(args,spec):
    """Existing monitor ownership for a PPO0 evaluator batch; no notification."""
    book=json.loads(args.spec.with_name('budget.json').read_text())
    row=book['attempts'][args.attempt_id]
    spent=sum(float(item.get('wall_s') or 0.) for key,item in book['attempts'].items() if key!=args.attempt_id)
    bound=min(spec['budget']['evaluation_wall_s']-spent,args.wall_limit_s or float('inf'))
    remaining=bound-(time.time()-row['started_unix_s'])
    command=['timeout','--signal=TERM','--kill-after=20s',f'{max(1.,remaining-35.)}s',
        sys.executable,str(ROOT/'tools/evaluate_checkpoint.py'),'--spec',str(args.spec),
        '--output',str(args.output_dir),'--batch','--attempt-id',args.attempt_id,
        '--wall-limit-s',str(bound),'--run']
    failure=None
    try:
        child=subprocess.Popen(command,cwd=str(ROOT.parents[2]))
        exit_code=child.wait()
    except OSError as exc:
        exit_code=127;failure=repr(exc)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    result=reconcile(args.spec.with_name('budget.json'),args.attempt_id,args.output_dir,exit_code)
    book=json.loads(args.spec.with_name('budget.json').read_text())
    write(args.output_dir/'monitor_exit.json',{'exit_code':exit_code,**result,'launch_failure':failure,
        'ledger':book['attempts'][args.attempt_id],
        'attempt_wall_including_cleanup_s':time.time()-row['started_unix_s']})
    return 0 if result['status'] in ('COMPLETED','STOPPED_BOUNDED') and exit_code==0 else 1


if __name__=="__main__":
    raise SystemExit(main())
