"""Explicit authorized continuation after an existing chain; no concurrent trainer."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from native_stand.command_v6.launcher import launch


def continuation_plan(spec,book,terminal,progress,wall_used):
    if terminal['status']!='COMPLETED':
        raise ValueError('Preceding chain did not complete normally; no automatic retry')
    if any(r['status']=='RUNNING' for r in book['attempts'].values()):
        raise ValueError('Another attempt remains running')
    remaining=book['limits']['formal']-book['used']['formal']
    wall=spec['budget']['formal_wall_s']-wall_used
    if remaining<=0 or wall<120:
        raise ValueError('No remaining update/wall budget')
    source=Path(progress['latest_checkpoint']['path'])
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    spec=json.loads(json.dumps(spec))
    spec.update(initialization='warmstart',source_checkpoint=str(source),source_sha256=sha,source_input_dim=150)
    spec['budget']['formal_updates']=remaining
    spec['budget']['formal_wall_s']=wall
    spec['continuation']={'total_formal_cap':book['limits']['formal'],
        'prior_actual_formal_updates':book['used']['formal'],'remaining_formal_updates':remaining,
        'strict_actor_critic_adam':True,'environment_reset':True}
    return spec


def main():
    p=argparse.ArgumentParser(description=__doc__)
    from native_stand.command_v6.tools.entrypoints import add_historical_option,require_historical_option
    add_historical_option(p)
    p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--chain',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--hapi-session',required=True)
    a=p.parse_args()
    require_historical_option(p,a)
    deadline=time.monotonic()+8100
    status=a.output_dir.with_suffix('.continuation.json')
    def record(value):status.write_text(json.dumps(value,indent=2)+'\n')
    record({'status':'WAITING','total_formal_cap':1000,'predecessor':str(a.chain)})
    try:
        terminal_path=a.chain/'chain_terminal_report.json'
        while not terminal_path.exists():
            if time.monotonic()>deadline:raise TimeoutError('Predecessor wait bounded timeout')
            time.sleep(15)  # Detached supervisor only; never blocks interactive session.
        terminal=json.loads(terminal_path.read_text())
        book=json.loads(a.spec.with_name('budget.json').read_text())
        spec=json.loads(a.spec.read_text())
        used_wall=sum(r['wall_including_cleanup_s'] for r in terminal['stages'] if r['stage']=='formal')
        progress=json.loads((a.chain/'formal/progress.json').read_text())
        planned=continuation_plan(spec,book,terminal,progress,used_wall)
        path=a.spec.with_name('spec_continue_to1000.json')
        with path.open('x') as f:json.dump(planned,f,indent=2)
        result=launch(path,'formal',a.output_dir,a.hapi_session)
        record({'status':'SUBMITTED','submission':result,'continuation':planned['continuation']})
    except Exception as e:
        record({'status':'NOT_SUBMITTED','reason':repr(e),'no_automatic_retry':True})
        raise


if __name__=='__main__':main()
