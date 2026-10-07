"""Concentrated read-only source evidence report; exclusive new output only."""
import argparse
import ctypes
import errno
import hashlib
import json
import os
import platform
from pathlib import Path
import select
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wait_monitor(pid):
    try:
        if hasattr(os,'pidfd_open'):
            fd=os.pidfd_open(pid)
        else:
            if platform.machine() not in ('x86_64','aarch64'):
                raise RuntimeError('pidfd syscall unsupported on this architecture')
            libc=ctypes.CDLL(None,use_errno=True)
            fd=libc.syscall(434,pid,0)
            if fd<0:
                code=ctypes.get_errno()
                raise OSError(code,os.strerror(code))
    except OSError as exc:
        if exc.errno==errno.ESRCH:return
        raise
    try:
        select.select([fd],[],[])
    finally:
        os.close(fd)


def report(output,physical_run=None):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    spec_path=ROOT/'configs/experiments/motion_recheck_20261007/spec.json'
    spec=json.loads(spec_path.read_text())
    from native_stand.command_v6.domain.recipe import resolve
    from native_stand.command_v6.tools.execution_identity import identity
    from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec
    from native_stand.command_v6.tools.preflight import check
    models={name:ROOT/path for name,path in {
        'B250':'runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt',
        'new250':'runs/motion_high_speed_course_20261007/formal/model_update_250.pt',
        'new500':'runs/motion_high_speed_course_20261007/formal/model_update_500.pt'}.items()}
    import torch
    metadata={}
    for name,path in models.items():
        checkpoint=torch.load(path,map_location='cpu',weights_only=False)
        metadata[name]={'path':str(path),'sha256':sha(path),
            'internal':{key:checkpoint.get(key) for key in ('update','source_sha256','asset_sha256','spec_sha256')},
            'actor_shapes':{key:list(value.shape) for key,value in checkpoint['actor'].items()},
            'critic_shapes':{key:list(value.shape) for key,value in checkpoint['critic'].items()},
            'finite':all(torch.isfinite(value).all().item() for model in ('actor','critic') for value in checkpoint[model].values()),
            'Adam_states':len(checkpoint['optimizer']['state']),
            'Adam_lr':[group['lr'] for group in checkpoint['optimizer']['param_groups']],
            'source_action_std':checkpoint['actor']['distribution.std_param'].tolist(),
            'RNG_fields':[key for key in checkpoint if 'rng' in key],
            'task_curriculum':checkpoint.get('task_curriculum')}
    evidence=json.loads((ROOT/'isolated/motion_recheck_20261007/high_speed_rescore/rescore.json').read_text())
    selected={}
    for row in evidence['evaluations']:
        model=next((name for name,meta in metadata.items() if meta['sha256']==row.get('checkpoint_sha256')),None)
        if not model:continue
        if model!='B250' and '/formal/' not in row['path']:continue
        key=(model,tuple(row['target'][:2]))
        selected[key]=row
    matrix=[]
    for model in models:
        for vx in (0.,.5,-.5,1.,-1.,1.5,-1.5,2.,-2.):
            row=selected.get((model,(vx,0.)))
            if not row:
                matrix.append({'model':model,'command':[vx,0.],'status':'MISSING_EVIDENCE'});continue
            envs=row['per_env'];n=len(envs)
            matrix.append({'model':model,'command':[vx,0.],
                'status':'PASSED_RESCORE' if row['new_gate']['accepted'] else 'FAILED_RESCORE',
                'old_passed_envs':row['old_gate']['passed_envs'],'new_passed_envs':row['new_gate']['passed_envs'],
                'mean_vx':sum(env['mean_vx_mps'] for env in envs)/n,
                'mean_absolute_error':sum(env['mean_abs_vx_error_mps'] for env in envs)/n,
                'worst_absolute_error':max(env['mean_abs_vx_error_mps'] for env in envs),
                'peak_tilt':max(env['peak_tilt_rad'] for env in envs),
                'minimum_contact':min(env['dual_contact_fraction'] for env in envs),
                'per_env':envs,'failed_checks':row['new_gate']['per_env'],
                'evidence':row['path'],'evidence_sha256':sha(row['path'])})
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,memory.free','--format=csv'],text=True)
    processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,process_name,used_memory','--format=csv'],text=True)
    book=json.loads(spec_path.with_name('budget.json').read_text())
    result={'models':metadata,'matrix':matrix,'protocol':protocol_for_spec(spec,30.,True),
        'spec_path':str(spec_path),'spec_sha256':sha(spec_path),'asset_sha256':sha(spec['asset_path']),
        'effective_recipe':resolve(spec)[1],'execution_identity':identity(spec),
        'evaluation_preflight':check(spec_path,ROOT/'runs/motion_recheck_20261007/attempt1','evaluate'),
        'GPU_snapshot':gpu,'compute_processes':processes,'ledger':book,
        'actual_new_online_updates':0,'actual_offline_optimizer_updates':0,
        'actual_new_physical_evaluations':0,'physical_status':'NOT_STARTED_GPU_OCCUPIED',
        'historical_trace_rescoring_is_not_new_learning':True,
        'source_missing_commands':[[1.5,0],[-1.5,0],[2,0],[-2,0]],
        'recommended_existing_candidate':'new250 under new historical trace rescore; B250 remains physical rollback',
        'training_decision':'NO_SUBMISSION; GPU conflict and current-version full bilateral +/-1.5 recheck missing',
        'next_training_variable':'command endpoint composition only: preserve verified old endpoints, add +/-1.5 instead of jumping +/-2; reward/PPO unchanged',
        'limitations':['No new simulator evidence because another GPU0 compute task occupies the device.',
            'No yaw or acute braking certificate. 100Hz efforts are not every5ms PD samples.',
            'Mixed old/new code results cannot silently certify one current execution version.',
            'Historic base training configuration declarations do not prove separate/fixed/per-command behavior.']}
    if physical_run:
        run=Path(physical_run).resolve()
        manifest=json.loads((run/'manifest.json').read_text())
        terminal=json.loads((run/'terminal_report.json').read_text())
        monitor=json.loads((run/'monitor_exit.json').read_text())
        physical_spec=json.loads((run/'source_snapshot/spec.json').read_text())
        physical_book=json.loads((ROOT/'configs/experiments/motion_recheck_20261007_gpu1/budget.json').read_text())
        completed=[]
        for item in terminal['completed']:
            raw=json.loads((run/item['path']).read_text())
            per_env=[{key:value for key,value in row.items() if key!='trace'} for row in raw['per_env']]
            n=len(per_env)
            completed.append({**item,'path':str(run/item['path']),'sha256':sha(run/item['path']),
                'per_env':per_env,'gate':raw['capability_gate'],
                'mean_vx':sum(row['mean_vx_mps'] for row in per_env)/n,
                'mean_absolute_error':sum(row['mean_abs_vx_error_mps'] for row in per_env)/n,
                'max_absolute_error':max(row['mean_abs_vx_error_mps'] for row in per_env),
                'max_tilt':max(row['peak_tilt_rad'] for row in per_env),
                'minimum_contact':min(row['dual_contact_fraction'] for row in per_env),
                'protocol_sha256':raw['effective_protocol']['scoring_protocol_sha256']})
        attempt=physical_book['attempts'][manifest['attempt_id']]
        if attempt['status']!=monitor['status'] or attempt['updates']!=0:
            raise ValueError('monitor/ledger status or PPO counter conflict')
        result.update(physical_status=monitor['status'],physical_run=str(run),
            physical_results=completed,physical_terminal=terminal,physical_monitor=monitor,
            ledger=physical_book,physical_spec_sha256=sha(run/'source_snapshot/spec.json'),
            physical_execution_identity=manifest['execution_identity'],
            physical_GPU=physical_spec['device'],actual_new_physical_evaluations=len(completed),
            physical_completed_policy_samples_all_envs=len(completed)*64*3000,
            physical_scored_samples=sum(round(row['continuous_s']/.01) for item in completed for row in item['per_env']),
            physical_wall_including_cleanup_s=attempt['wall_s'],
            limitations=[lim for lim in result['limitations'] if not lim.startswith('No new simulator')])
        result['physical_snapshot_valid']=all(sha(run/'source_snapshot'/name)==expected
            for name,expected in manifest['source_snapshot_sha256'].items())
        result['checkpoint_SHA_still_match']=all(sha(meta['path'])==meta['sha256'] for meta in metadata.values())
        result['same_code_completed_command_sets']={name:[item['target'] for item in completed if
            item['checkpoint_sha256']==meta['sha256']] for name,meta in metadata.items()}
        result['physical_samples_note']='all-env count covers completed items only; partial interrupted item is excluded, not declared zero'
        source_items=[item for item in completed if item['checkpoint_sha256']==metadata['B250']['sha256']]
        source_commands={tuple(item['target'][:2]) for item in source_items if item['gate']['accepted']}
        source_required={(vx,0.) for vx in (0.,1.,-1.,1.5,-1.5,2.,-2.)}
        source_complete=source_required<=source_commands
        result['source_missing_commands']=[list(command) for command in sorted(source_required-source_commands)]
        result['recommended_existing_candidate']='B250: current physical 0/+-1/+-1.5/+-2 passed' if source_complete else 'Incomplete physical evidence; no new complete candidate certificate'
        result['training_decision']='PREPARED_ONLY: recommend B250, next straight endpoints +/-2.5; this turn authorizes PPO0 only' if source_complete else 'NO_GO: source physical boundary incomplete or failed'
        result['next_training_variable']='Endpoint composition only: retain verified old endpoints, introduce +/-2.5; no reward/PPO change' if source_complete else 'Complete the specific missing/failed source boundary before selecting a new course'
        result['limitations'].append('Current-run source +/-0.5 was not re-collected; historical evidence remains separately identified. No automatic training authorization.')
    output.mkdir(parents=True,exist_ok=False)
    with (output/'result.json').open('x') as stream:json.dump(result,stream,indent=2)
    if physical_run:
        content='# Motion physical recheck result\n\n'
        content+=f"Status: {result['physical_status']}; online/offline optimizer 0; wall {result['physical_wall_including_cleanup_s']:.3f}s.\n\n"
        content+='|Model SHA|command|mean vx|MAE|max env MAE|pass|peak tilt|\n|---|---|---|---|---|---|---|\n'
        for item in completed:
            content+=f"|{item['checkpoint_sha256'][:12]}|{item['target']}|{item['mean_vx']:.6f}|{item['mean_absolute_error']:.6f}|{item['max_absolute_error']:.6f}|{item['gate']['passed_envs']}/8|{item['max_tilt']:.6f}|\n"
        content+='\nFull per-env metrics, gates, failures, missing requests and identities: result.json.\n'
        content+='No yaw, acute-stop or new learned capability claim. Old/new-code evidence remains separate.\n'
        with (output/'report.md').open('x') as stream:stream.write(content)
    print(json.dumps({'result':str(output/'result.json'),'physical_status':result['physical_status']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    from native_stand.command_v6.tools.entrypoints import add_historical_option,require_historical_option
    add_historical_option(parser)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--physical-run',type=Path)
    parser.add_argument('--wait-for-pid',type=int,
        help='Background report delivery: wait for the exact monitor exit through pidfd, without log polling.')
    args=parser.parse_args()
    require_historical_option(parser,args)
    if args.wait_for_pid is not None:
        wait_monitor(args.wait_for_pid)
    report(args.output_dir,args.physical_run)
