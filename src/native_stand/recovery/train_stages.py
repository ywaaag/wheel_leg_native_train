"""Sequential authorized smoke/formal using the shared launcher and exact ledger."""
import argparse
import json
import os
from pathlib import Path
import time
import subprocess
import sys
from native_stand.command_v6.launcher import launch

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--hapi-session',required=True)
    p.add_argument('--tensorboard-logdir',type=Path)
    a=p.parse_args();a.output_dir.mkdir(exist_ok=False,parents=True)
    spec=json.loads(a.spec.read_text())
    formal_wall=spec['budget']['formal_wall_s']
    deadline=(time.monotonic()+spec['budget']['smoke_wall_s']+formal_wall+60) if formal_wall is not None else float('inf')
    for phase in ('smoke','formal'):
        run=a.output_dir/phase
        submission=launch(a.spec,phase,run,a.hapi_session if phase=='formal' else None)
        bridge=None
        (a.output_dir/'stage.json').write_text(json.dumps({'stage':phase,'submission':submission},indent=2)+'\n')
        while not (run/'monitor_exit.json').exists():
            if a.tensorboard_logdir is not None and bridge is None and (run/'metrics.jsonl').is_file():
                bridge=subprocess.Popen([sys.executable,'-m','native_stand.command_v6.tools.metrics_tensorboard',
                    '--metrics',str(run/'metrics.jsonl'),'--log-dir',str(a.tensorboard_logdir/phase),'--follow'],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            if time.monotonic()>deadline:raise TimeoutError('Bounded supervisor exceeded phase budget')
            time.sleep(5)
        t=json.loads((run/'terminal_report.json').read_text());m=json.loads((run/'monitor_exit.json').read_text())
        if bridge is not None:
            bridge.terminate()
            try: bridge.wait(timeout=10)
            except subprocess.TimeoutExpired: bridge.kill()
        if phase=='smoke':
            progress=json.loads((run/'progress.json').read_text())
            if t['status']!='COMPLETED' or m['exit_code']!=0 or t['actual_updates']!=spec['budget']['smoke_updates'] or not progress.get('actor_parameters_changed'):
                raise RuntimeError('Smoke wiring failed; formal not started')
    (a.output_dir/'stage.json').write_text(json.dumps({'stage':'terminal','formal_terminal':t},indent=2)+'\n')

if __name__=='__main__':main()
