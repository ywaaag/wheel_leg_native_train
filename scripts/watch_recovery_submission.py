"""Report a stopped sequential supervisor; reuse the existing HAPI notifier.

No simulation, PPO, ledger mutation, retries, or second training submission.
Formal monitor owns normal notification; this guard covers failure before formal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
from native_stand.command_v6.completion import write, read, notify

def finish(output, session):
    formal=output/'formal'
    if (formal/'hapi_notification.json').exists():
        return {'status':'formal_monitor_owns_notification'}
    # A formal monitor can outlive a killed sequential supervisor.
    if formal.exists() and not (formal/'monitor_exit.json').exists():
        return {'status':'formal_monitor_still_running'}
    stage=read(output/'stage.json',{})
    spec=read(output.with_suffix('.submission.json'))
    specpath=Path(spec['command'][spec['command'].index('--spec')+1])
    book=read(specpath.with_name('budget.json'))
    rows=[r for r in book['attempts'].values() if Path(r['output_dir']).parent==output]
    status=stage.get('formal_terminal',{}).get('status','FAILED')
    analysis={'status':status,'actual_updates':sum(r['updates'] for r in rows),
        'attempts':rows,'stage':stage,'reason':'Sequential supervisor exited; see phase terminal reports and supervisor log.'}
    write(output/'analysis.json',analysis)
    write(output/'candidate_selection.json',read(formal/'candidate_selection.json',{}))
    write(output/'manifest.json',{'hapi_session':session,'spec_path':str(specpath)})
    report='# Recovery supervisor completion\n\n'+json.dumps(analysis,indent=2)+'\n\nNo automatic continuation.\n'
    (output/'completion_report.md').write_text(report)
    write(output/'report_ready.json',{'event_id':hashlib.sha256(str(output).encode()).hexdigest()[:24],
        'report_sha256':hashlib.sha256(report.encode()).hexdigest()})
    return notify(output)

def main():
    from native_stand.command_v6.tools.entrypoints import historical_cli_guard
    historical_cli_guard('scripts/watch_recovery_submission.py')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--hapi-session',required=True)
    a=p.parse_args();output=a.output_dir.resolve()
    submission=read(output.with_suffix('.submission.json'));pid=submission['pid']
    expected=str(output).encode()
    while True:
        path=Path(f'/proc/{pid}/cmdline')
        if not path.exists() or expected not in path.read_bytes():break
        time.sleep(5)
    # Await an already-running formal monitor, never restart it.
    while (output/'formal').exists() and not (output/'formal/monitor_exit.json').exists():time.sleep(5)
    print(json.dumps(finish(output,a.hapi_session)),flush=True)

if __name__=='__main__':main()
