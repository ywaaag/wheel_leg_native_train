"""Bounded serial A/B owner; reuses phase monitors, exact ledgers and HAPI completion."""
import argparse
import fcntl
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
from native_stand.command_v6.completion import identity,notify,read,sha,write
from native_stand.command_v6.ledger import Ledger
from native_stand.command_v6.tools.preflight import check


def summary(path):
    data=read(path)
    rows=[]
    for row,gate in zip(data['per_env'],data['capability_gate']['per_env']):
        trace=row.get('trace',[])
        parked=[step for index,step in enumerate(trace) if (index+1)*data['dt']>=26.]
        rows.append({**{key:value for key,value in row.items() if key!='trace'},
            'accepted':gate['accepted'],'failed_checks':gate['failed_checks'],
            'parking_mean_abs_vx_mps':sum(abs(step[3]) for step in parked)/len(parked) if parked else None})
    fields=('mean_vx_mps','mean_abs_vx_error_mps','hold_direction_fraction',
        'horizontal_speed_p95_mps','net_drift_m','dual_contact_fraction',
        'peak_tilt_rad','saturation_fraction','parking_mean_abs_vx_mps')
    means={key:sum(row[key] for row in rows)/len(rows) if rows and all(row.get(key) is not None for row in rows) else None
           for key in fields}
    return {'path':str(path),'sha256':sha(path),'command':data['target'],
            'passed_envs':data['capability_gate']['passed_envs'],'per_env':rows,'means':means}


def finish(chain,config,phases,status,failure,started):
    arms={}
    for label in config['arms']:
        folder=chain/label
        evaluations=[]
        if folder.exists():
            for path in sorted(folder.glob('*/evaluation_*.json')):
                data=read(path,{})
                if 'capability_gate' in data:
                    evaluations.append(summary(path))
        baseline={tuple(row['command']):row for row in evaluations if '/source_eval/' in row['path']}
        for row in evaluations:
            source=baseline.get(tuple(row['command']))
            if source and '/formal/' in row['path']:
                row['candidate_minus_source']={key:value-source['means'][key]
                    if value is not None and source['means'][key] is not None else None
                    for key,value in row['means'].items()}
        selection=read(folder/'formal/candidate_selection.json',{})
        arms[label]={'budget':read(Path(config['arms'][label]['spec']).with_name('budget.json')),
                     'evaluations':evaluations,'selection':selection}
    online=sum(arm['budget']['used']['smoke']+arm['budget']['used']['formal'] for arm in arms.values())
    event=identity({'run':str(chain),'attempt':read(chain/'manifest.json')['attempt_id']})[:24]
    result={'event_id':event,'status':status,'failure':failure,'arms':arms,'phases':phases,
        'actual_online_updates':online,'actual_samples':online*8192,'wall_s':time.monotonic()-started,
        'budget_wall_limit_s':config['wall_limit_s'],'no_automatic_long_training':True}
    accepted=[arm['selection'].get('accepted_candidate') for arm in arms.values()]
    accepted=[row for row in accepted if row]
    selection={'accepted_candidate':accepted[0] if accepted else None,
        'best_observed_candidate':accepted[0] if accepted else None,
        'warning':'A/B comparison requires same completed update count; no single-seed causality generalization'}
    write(chain/'chain_terminal_report.json',result)
    write(chain/'analysis.json',result)
    write(chain/'candidate_selection.json',selection)
    lines=['# Cohort tracking-width A/B completion',f'Event: {event}',f'Terminal: {status}; failure={failure}',
        f'Actual online updates/samples: {online}/{online*8192}',f'Wall: {result["wall_s"]:.1f}s',
        'Source B retained. No promotion or high-speed continuation is authorized.',
        'A: all linear denominators 1. B: old episode-target cohorts .04; new +/-1 1.',
        'Raw evaluations and per-environment evidence: analysis.json.',
        '| arm | phase / checkpoint | command | pass | mean vx | error | zero p95 | parking | drift | contact |',
        '|---|---|---|---|---|---|---|---|---|---|']
    def number(value):
        return f'{value:.4f}' if value is not None else 'UNKNOWN'
    for label,arm in arms.items():
        for row in arm['evaluations']:
            means=row['means']
            lines.append(f'| {label} | {Path(row["path"]).parent.name}/{Path(row["path"]).stem} | {row["command"]} | {row["passed_envs"]}/8 | '+
                ' | '.join(number(means[key]) for key in ('mean_vx_mps','mean_abs_vx_error_mps',
                'horizontal_speed_p95_mps','parking_mean_abs_vx_mps','net_drift_m','dual_contact_fraction'))+' |')
    (chain/'completion_report.md').write_text('\n\n'.join(lines)+'\n')
    write(chain/'report_ready.json',{'event_id':event,'status':'report_ready',
        'report_sha256':sha(chain/'completion_report.md'),'time':time.time()})
    notify(chain)


def worker(args):
    config=read(args.config)
    chain=args.output_dir.resolve()
    started=time.monotonic()
    deadline=started+config['wall_limit_s']-60
    phases=[]
    status='FAILED'
    failure=None
    try:
        for label,arm in config['arms'].items():
            spec=Path(arm['spec'])
            if sha(spec)!=arm['sha256']:
                raise ValueError('arm spec SHA changed after submission')
            for phase in ('source_eval','smoke','formal'):
                output=chain/label/phase
                output.parent.mkdir(parents=True,exist_ok=True)
                remaining=deadline-time.monotonic()
                if remaining<120:
                    status='STOPPED_BOUNDED'
                    failure='cumulative wall budget exhausted'
                    return 0
                plan=check(spec,output,phase)
                if plan['status']!='PASS':
                    raise ValueError(f'{label}/{phase} preflight: {plan["errors"]}')
                attempt=uuid.uuid4().hex
                Ledger(spec.with_name('budget.json')).reserve(attempt,phase,output,approval=plan)
                initial=not phases
                if initial:
                    writer=args.handshake_fd
                else:
                    reader,writer=os.pipe()
                bound=min(read(spec)['budget'][phase+'_wall_s'],remaining)
                command=[sys.executable,str(ROOT/'monitor.py'),'--spec',str(spec),'--phase',phase,
                    '--output-dir',str(output),'--attempt-id',attempt,'--handshake-fd',str(writer),
                    '--wall-limit-s',str(bound)]
                write(chain/'chain_progress.json',{'status':'RUNNING','arm':label,'phase':phase,
                    'supervisor_pid':os.getpid(),'active_run':str(output),'completed_phases':phases})
                with output.with_name(phase+'.log').open('x') as stream:
                    try:
                        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,pass_fds=(writer,))
                    except OSError as exc:
                        Ledger(spec.with_name('budget.json')).finalize(attempt,output,'FAILED',
                            exit_code=127,reason=f'monitor spawn failed: {exc}',wall_s=0.)
                        if not initial:
                            os.close(writer)
                            os.close(reader)
                        raise
                    write(output.with_name(phase+'.monitor.json'),{'attempt_id':attempt,'monitor_pid':child.pid,'command':command})
                    code=child.wait()
                if not initial:
                    os.close(writer)
                    os.close(reader)
                terminal=read(output/'terminal_report.json',{})
                progress=read(output/'progress.json',{})
                phases.append({'arm':label,'phase':phase,'status':terminal.get('status','UNKNOWN'),
                    'actual_updates':terminal.get('actual_updates',0),'exit_code':code,'run':str(output)})
                book=read(spec.with_name('budget.json'))
                attempt_row=book['attempts'][attempt]
                if attempt_row['status']=='RUNNING' or attempt_row['updates']!=terminal.get('actual_updates',0):
                    raise ValueError('exact attempt terminal accounting differs')
                if code!=0 or terminal.get('status') not in ('COMPLETED','STOPPED_BOUNDED'):
                    raise RuntimeError(f'{label}/{phase} runtime failure: {terminal.get("failure")}')
                if phase=='source_eval' and not progress.get('source_pass'):
                    status='STOPPED_BOUNDED'
                    failure=f'{label}: source B lacks required old-cohort capability under full30s protocol'
                    return 0
                if phase=='smoke' and (terminal.get('actual_updates')!=1 or not progress.get('actor_parameters_changed')):
                    raise RuntimeError('smoke did not verify one finite actor update')
                if phase=='smoke':
                    from native_stand.command_v6.wiring import smoke_certificate
                    certificate=smoke_certificate(output,read(spec))
                    write(output/'wiring_certificate.json',certificate)
                    if certificate['status']!='PASSED':raise RuntimeError(certificate['errors'])
        status='COMPLETED'
    except BaseException as exc:
        failure=repr(exc)
    finally:
        write(chain/'chain_progress.json',{'status':status,'phase':'finished','failure':failure,'supervisor_pid':os.getpid()})
        try:
            finish(chain,config,phases,status,failure,started)
        except Exception as exc:
            write(chain/'completion_error.json',{'error':repr(exc),'original_failure':failure})
        os.close(args.handshake_fd)
    return 0 if status in ('COMPLETED','STOPPED_BOUNDED') else 1


def launch(args):
    config=read(args.config)
    chain=args.output_dir.resolve()
    if config['hapi_session']!=os.environ.get('HAPI_SESSION_ID'):
        raise ValueError('notification target must be the current worker session')
    for arm in config['arms'].values():
        if sha(arm['spec'])!=arm['sha256']:
            raise ValueError('frozen arm spec changed')
        plan=check(arm['spec'],chain/'PLAN_SOURCE','source_eval')
        if plan['status']!='PASS':
            raise ValueError(plan)
    with args.config.with_name('ab_submission.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if args.config.with_name('ab_submission.json').exists():
            raise ValueError('A/B already submitted; no duplicate chain or retries')
        chain.mkdir(parents=True,exist_ok=False)
        from native_stand.command_v6.tools.source_identity import record_identity
        first=next(iter(config['arms'].values()))
        recorded=record_identity(read(first['spec']),chain)
        token=uuid.uuid4().hex
        write(chain/'manifest.json',{'attempt_id':token,'hapi_session':config['hapi_session'],
            'kind':'cohort_width_ab','submitted_unix_s':time.time(),'config_sha256':sha(args.config),
            'code_sha256':recorded['tree_digest'],'source_code_copied_bytes':0,
            'source_sha256':config['source_sha256'],'physical_gpu':1,'config':config})
        reader,writer=os.pipe()
        command=[sys.executable,str(ROOT/'motion_width_ab.py'),
            '--config',str(args.config.resolve()),'--output-dir',str(chain),'--worker','--handshake-fd',str(writer)]
        with (chain/'chain.log').open('x') as stream:
            child=subprocess.Popen(command,env={**os.environ,'CUDA_VISIBLE_DEVICES':'1',
                'PYTHONPATH':str(ROOT.parents[1])},start_new_session=True,stdin=subprocess.DEVNULL,
                stdout=stream,stderr=subprocess.STDOUT,pass_fds=(writer,))
        os.close(writer)
        write(args.config.with_name('ab_submission.json'),{'supervisor_pid':child.pid,'command':command,'run':str(chain),'attempt_id':token})
    ready,_,_=select.select([reader],[],[],60)
    handshake={'status':'UNKNOWN','reason':'one runtime handshake not ready; background evidence authoritative'}
    if ready:
        raw=os.read(reader,65536).split(b'\n',1)[0]
        if raw:
            handshake=json.loads(raw)
    os.close(reader)
    handshake.update(supervisor_pid=child.pid,run=str(chain))
    write(chain/'handshake.json',handshake)
    print(json.dumps(handshake,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--launch',action='store_true')
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--handshake-fd',type=int)
    args=parser.parse_args()
    if args.worker:
        return worker(args)
    if args.launch:
        launch(args)
    else:
        config=read(args.config)
        plans={label:check(arm['spec'],args.output_dir/label/'source_eval','source_eval')
               for label,arm in config['arms'].items()}
        print(json.dumps({'arms':plans,'budget':config,'files_written':0,'simulation':0,'ppo':0},indent=2))
        return 0 if all(plan['status']=='PASS' for plan in plans.values()) else 2
    return 0


if __name__=='__main__':
    raise SystemExit(main())
