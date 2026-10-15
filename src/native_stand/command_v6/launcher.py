"""Detached v6 launcher: preflight, one pipe handshake, then return."""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from native_stand.command_v6.config import PHASES
from native_stand.command_v6.tools.preflight import check
from native_stand.command_v6.completion import plan as runtime_plan
from native_stand.command_v6.ledger import Ledger


def launch(spec,phase,output,hapi_session=None,*,resource_review=None):
    spec=Path(spec).resolve()
    output=Path(output).resolve()
    plan=check(spec,output,phase)
    if plan["status"]!="PASS":
        raise ValueError(f"preflight failed: {plan['errors']}")
    attempt_id=uuid.uuid4().hex
    output.parent.mkdir(parents=True,exist_ok=True)
    pipe_in,pipe_out=os.pipe()
    wall=json.loads(spec.read_text())["budget"]
    bound=wall["source_eval_wall_s"] if phase=="source_eval" else (
        wall["smoke_wall_s"] if phase=="smoke" else wall["formal_wall_s"])
    command=[sys.executable,str(ROOT/"monitor.py"),"--spec",str(spec),"--phase",phase,
             "--output-dir",str(output),"--attempt-id",attempt_id,
             "--handshake-fd",str(pipe_out)]
    if hapi_session:
        command += ['--hapi-session',hapi_session]
    env={**os.environ,"CUDA_VISIBLE_DEVICES":os.environ.get("NATIVE_PHYSICAL_GPU","0")}
    log=output.with_name(output.name+".launcher.log")
    plan.resource_review=resource_review
    Ledger(spec.with_name('budget.json')).reserve(attempt_id,phase,output,approval=plan)
    submission={'attempt_id':attempt_id,'output_dir':str(output),'phase':phase,
        'resource_review':resource_review,
        'hapi_session':hapi_session,'spec_path':str(spec),'spec_sha256':plan['spec_sha256'],
        'run_plan':runtime_plan(json.loads(spec.read_text()),phase),'submitted_unix_s':time.time()}
    try:
        with output.with_name(output.name+'.submission.json').open('x') as handle:
            json.dump(submission,handle,indent=2)
        with log.open("x") as handle:
            supervisor=subprocess.Popen(command,cwd=str(ROOT.parents[1]),env=env,
                stdin=subprocess.DEVNULL,stdout=handle,stderr=subprocess.STDOUT,
                pass_fds=(pipe_out,),start_new_session=True)
    except BaseException as exc:
        os.close(pipe_in)
        os.close(pipe_out)
        Ledger(spec.with_name('budget.json')).finalize(attempt_id,output,'FAILED',
            reason=f'detached monitor spawn failed: {exc}',wall_s=0.)
        raise
    os.close(pipe_out)
    metadata={"attempt_id":attempt_id,"monitor_pid":supervisor.pid,
              "command":command,"output_dir":str(output.resolve()),
              "log":str(log),"started_unix_s":time.time(),
              "hard_timeout_s":bound,"handshake_wait_s":120}
    from native_stand.command_v6.tools.health_check import own_process_start
    metadata['process_started_unix_s']=own_process_start(supervisor.pid)
    metadata['hapi_session']=hapi_session
    output.with_name(output.name+".launcher.json").write_text(json.dumps(metadata,indent=2)+"\n")
    ready,_,_=select.select([pipe_in],[],[],120)
    message={"status":"UNKNOWN","reason":"single handshake not ready; inspect progress and terminal later"}
    if ready:
        raw=os.read(pipe_in,65536).split(b"\n",1)[0]
        if raw:
            message=json.loads(raw)
    os.close(pipe_in)
    if message.get("status")=="RUNNING":
        from native_stand.command_v6.submission import validate_handshake
        message=validate_handshake(message,spec_path=spec,output=output,
            attempt_id=attempt_id,monitor_pid=supervisor.pid,
            monitor_started_unix_s=metadata['process_started_unix_s'])
    message.update(attempt_id=attempt_id,output_dir=str(output),monitor_pid=supervisor.pid)
    sidecar=output/"handshake.json" if output.is_dir() else output.with_name(output.name+".handshake.json")
    sidecar.write_text(json.dumps(message,indent=2)+"\n")
    return message


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec",type=Path,default=ROOT.parents[2]/"configs/experiments/stand_plane.json")
    parser.add_argument("--phase",choices=PHASES,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--launch",action="store_true")
    parser.add_argument('--hapi-session',default=os.environ.get('HAPI_SESSION_ID'))
    args=parser.parse_args()
    if not args.launch:
        print(json.dumps({**check(args.spec,args.output_dir,args.phase),
            'run_plan':runtime_plan(json.loads(args.spec.read_text()),args.phase),
            'hapi_session':args.hapi_session},indent=2))
        return
    print(json.dumps(launch(args.spec,args.phase,args.output_dir,args.hapi_session),indent=2))


if __name__=="__main__":
    main()
