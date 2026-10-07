"""Sequential BC A/B orchestration over shared phases; no new trainer/optimizer."""
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
from native_stand.command_v6.completion import read,write,sha,identity,notify
from native_stand.command_v6.stand_chain import run_phase
from native_stand.command_v6.tools.preflight import check

ARMS=('A_fixed','B_annealed')


def gradient_review(folder):
    rows=[]
    for line in (folder/'metrics.jsonl').read_text().splitlines():
        try:row=json.loads(line)
        except ValueError:continue
        bc=row.get('task_metrics',{}).get('standing_retention',{})
        if bc.get('gradient_comparison') is not None:
            rows.append({'update':row['actual_update'],'coefficient':bc['coefficient'],
                         **bc['gradient_comparison']})
    cosines=[r['cosine'] for r in rows if r.get('cosine') is not None]
    ratios=[r['weighted_norm_ratio'] for r in rows if r.get('weighted_norm_ratio') is not None]
    return {'probed_updates':len(rows),'defined_cosines':len(cosines),
        'negative_cosine_fraction':sum(c<0 for c in cosines)/len(cosines) if cosines else None,
        'mean_cosine':sum(cosines)/len(cosines) if cosines else None,
        'mean_weighted_norm_ratio':sum(ratios)/len(ratios) if ratios else None,
        'channel_components':{label:{
            'defined_cosines':sum(r.get(label,{}).get('cosine') is not None for r in rows),
            'negative_cosine_fraction':(lambda vs:sum(v<0 for v in vs)/len(vs) if vs else None)(
                [r[label]['cosine'] for r in rows if r.get(label,{}).get('cosine') is not None])}
            for label in ('legs','wheels')},
        'rows':rows,'interpretation':'Opposing actor PPO+entropy and BC directions on different batches; not a reward-specific causal proof.'}


def finish_pair(args,status,phases,failure):
    run=args.output_dir;results={};evidence={};consumed=0
    for arm in ARMS:
        spec=args.config_dir/arm/'spec.json';book=read(spec.with_name('budget.json'))
        consumed+=book['used']['smoke']+book['used']['formal']
        results[arm]={'budget':book,'selection':read(run/arm/'formal/candidate_selection.json'),
                     'formal_terminal':read(run/arm/'formal/terminal_report.json')}
        evidence[arm]={}
        for phase in ('smoke','formal'):
            folder=run/arm/phase
            if (folder/'metrics.jsonl').exists():evidence[arm][phase]=gradient_review(folder)
    event=identity({'pair':str(run),'attempt':read(run/'manifest.json')['attempt_id']})[:24]
    analysis={'status':status,'event_id':event,'failure':failure,'phases':phases,
        'actual_updates':consumed,'samples':consumed*8192,'arms':results,
        'gradient_evidence':evidence,'wall_s':time.time()-read(run/'manifest.json')['submitted_unix_s'],
        'followup':'Wheel-only/mirror BC are not automatically launched. Review same-budget behavioral tradeoffs and gradient size before allocating another portion of unused quota.'}
    write(run/'analysis.json',analysis);write(run/'terminal_report.json',analysis)
    candidates=[r['selection'].get('accepted_candidate') for r in results.values() if r.get('selection')]
    accepted=next((c for c in candidates if c),None)
    # Do not pretend a shared ranking across different evidence identities.
    write(run/'candidate_selection.json',{'best_observed_candidate':accepted,
        'accepted_candidate':accepted,'per_arm_selections':{k:v['selection'] for k,v in results.items()},
        'ranking_note':'Per-arm selection only; no overall winner when no candidate passes. Read comparison table.'})
    report=['# Standing BC schedule A/B completion',f'Event: {event}',f'Terminal: {status}; failure={failure}',
        f'Updates/samples: {consumed}/{consumed*8192}; wall={analysis["wall_s"]:.2f}s',
        '|Arm/checkpoint|10s complete|Pass|Height m|vx m/s|yaw rad/s|Excursion m|Mirror rad|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm in ARMS:
        for label,path in [('source',run/arm/'source_eval/evaluation_source.json')]+[
                (str(u),run/arm/'formal'/f'evaluation_{u}_0_0.json') for u in (50,100)]:
            data=read(path)
            if data is None:continue
            env=data['per_env']
            def mean(key):return sum(e['standing_metrics'][key] for e in env)/len(env)
            report.append(f'|{arm}/{label}|{sum(e["continuous_window_completed"] for e in env)}/8|{data["passed_envs"]}/8|'+
                '|'.join(f'{mean(k):.5f}' for k in ('height_steady_mean_m','mean_abs_vx_mps',
                'mean_abs_yaw_rad_s','max_excursion_m','mean_mirror_error_rad'))+'|')
    report.extend(['','## Gradient directional evidence',json.dumps(evidence,indent=2),
        '## Next step',analysis['followup'],
        'No automatic extension; original USD/control/reward/protocol stay unchanged. Completion is not acceptance.'])
    (run/'completion_report.md').write_text('\n'.join(report)+'\n')
    write(run/'report_ready.json',{'event_id':event,'status':'report_ready','report_sha256':sha(run/'completion_report.md'),'time':time.time()})
    notify(run)


def worker(args):
    status='FAILED';failure=None;phases=[]
    try:
        for arm in ARMS:
            spec=args.config_dir/arm/'spec.json';folder=args.output_dir/arm;folder.mkdir()
            for phase in ('source_eval','smoke','formal'):
                write(args.output_dir/'progress.json',{'status':'RUNNING','arm':arm,'phase':phase,
                    'active_run':str(folder/phase),'worker_pid':os.getpid()})
                row=run_phase(spec,phase,folder/phase,args.handshake_fd if arm==ARMS[0] and phase=='formal' else None)
                phases.append({'arm':arm,**row})
                if row['terminal'].get('stop_kind')=='user_signal':
                    status='STOPPED_BOUNDED';return 0
                if row['exit_code']!=0 or row['status'] not in ('COMPLETED','STOPPED_BOUNDED'):
                    raise RuntimeError(f'{arm}/{phase} runtime failure; see phase terminal')
                if phase=='smoke':
                    if row['terminal'].get('actual_updates')!=3 or not row['progress'].get('actor_parameters_changed'):
                        raise RuntimeError('Smoke finite actor-update wiring incomplete')
                    gradient=gradient_review(folder/phase)
                    if gradient['probed_updates']!=3:raise RuntimeError('BC/PPO gradient evidence missing')
                    write(folder/'gradient_smoke_review.json',gradient)
            write(folder/'terminal_summary.json',{'phases':[r for r in phases if r['arm']==arm]})
        status='COMPLETED'
    except BaseException as exc:failure=repr(exc)
    finally:
        write(args.output_dir/'progress.json',{'status':status,'phase':'finished','failure':failure})
        try:finish_pair(args,status,phases,failure)
        except Exception as exc:write(args.output_dir/'completion_error.json',{'error':repr(exc)})
        try:os.close(args.handshake_fd)
        except OSError:pass
    return 0 if status=='COMPLETED' else 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--hapi-session',required=True);p.add_argument('--launch',action='store_true')
    p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--handshake-fd',type=int,help=argparse.SUPPRESS);a=p.parse_args()
    a.config_dir=a.config_dir.resolve();a.output_dir=a.output_dir.resolve()
    if a.worker:return worker(a)
    plans={arm:check(a.config_dir/arm/'spec.json',a.output_dir/arm/'source_eval','source_eval') for arm in ARMS}
    if not a.launch:print(json.dumps(plans,indent=2));return 0
    if any(p['status']!='PASS' for p in plans.values()):raise ValueError(plans)
    for arm in ARMS:
        if read(a.config_dir/arm/'spec.json')['authorization']['hapi_session']!=a.hapi_session:
            raise ValueError('HAPI target differs')
    submission=a.config_dir/'submission.json'
    with submission.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if submission.exists():raise ValueError('pair already submitted; no duplicate')
        a.output_dir.mkdir(parents=True,exist_ok=False)
        snapshot=a.output_dir/'execution_snapshot'
        shutil.copytree(ROOT.parent,snapshot/'src/native_stand',ignore=shutil.ignore_patterns('__pycache__'))
        for arm in ARMS:
            for name in ('spec.json','budget.json'):
                dest=snapshot/'configs'/arm/name;dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(a.config_dir/arm/name,dest)
        manifest={'attempt_id':uuid.uuid4().hex,'hapi_session':a.hapi_session,'submitted_unix_s':time.time(),
            'config_dir':str(a.config_dir),'arm_spec_sha256':{arm:sha(a.config_dir/arm/'spec.json') for arm in ARMS}}
        write(a.output_dir/'manifest.json',manifest)
        reader,writer=os.pipe()
        cmd=[sys.executable,str(snapshot/'src/native_stand/command_v6/retention_ab.py'),
            '--config-dir',str(a.config_dir),'--output-dir',str(a.output_dir),
            '--hapi-session',a.hapi_session,'--worker','--handshake-fd',str(writer)]
        with (a.output_dir/'supervisor.log').open('x') as log:
            child=subprocess.Popen(cmd,cwd=a.output_dir,stdin=subprocess.DEVNULL,stdout=log,
                stderr=subprocess.STDOUT,pass_fds=(writer,),start_new_session=True,
                env={**os.environ,'CUDA_VISIBLE_DEVICES':'0'})
        os.close(writer);write(submission,{'worker_pid':child.pid,'command':cmd,**manifest})
    ready,_,_=select.select([reader],[],[],240)
    message={'status':'UNKNOWN','reason':'one formal handshake not ready; do not restart'}
    if ready:
        raw=os.read(reader,65536).split(b'\n',1)[0]
        if raw:message=json.loads(raw)
    os.close(reader)
    if message.get('status')=='RUNNING':
        path=a.output_dir/ARMS[0]/'formal';pid=message.get('trainer_pid')
        proc=Path(f'/proc/{pid}/cmdline')
        if not proc.is_file() or str(path) not in proc.read_bytes().replace(b'\0',b' ').decode() or read(path/'progress.json',{}).get('actual_updates',0)<1:
            message={'status':'UNKNOWN','reason':'formal identity/actual update handshake differs'}
    write(a.output_dir/'handshake.json',{'pair':str(a.output_dir),'worker_pid':child.pid,**message})
    print(json.dumps(read(a.output_dir/'handshake.json'),indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
