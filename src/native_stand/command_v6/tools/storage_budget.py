"""Read-only output-volume estimate and capacity gate; no cleanup or reservation."""
import math
import shutil
from pathlib import Path


def estimate(spec,phase):
    budget=spec.get('budget',{});evaluation=spec.get('evaluation',{});ppo=spec.get('ppo',{})
    source=Path(spec.get('source_checkpoint','__missing__'))
    checkpoint_bytes=source.stat().st_size if source.is_file() else 16*1024**2
    updates=budget.get(phase+'_updates',0) or 0;period=evaluation.get('checkpoint_every_updates',25)
    snapshots=math.ceil(updates/max(1,period))+2 if phase in ('smoke','formal') else 0
    seconds=evaluation.get('seconds',30);dt=spec.get('control',{}).get('policy_dt_s',.01)
    commands=len(spec.get('source_evaluation_commands',evaluation.get('motion_commands',[])))+1
    if spec.get('task')=='recovery':commands=len(spec.get('recovery',{}).get('assessment',{}).get('families',[])) or 3
    events=1 if phase not in ('formal',) else math.ceil(updates/max(1,evaluation.get('full_every_updates',50)))+len(evaluation.get('unlock_full_updates',[]))+1
    from ..domain.diagnostic_profiles import storage_plan
    plans=[]
    if spec.get('control',{}).get('policy_dt_s'):
        requests=spec.get('evaluation_requests',[]) if phase=='evaluate' else [{}]
        for request in requests or [{}]:
            plans.append(storage_plan(spec,full=True,request=request,legacy_full_trace=True,legacy_diagnostics=True))
    def channels(plan):
        fields=plan.get('fields')
        if fields is None:return 134
        count=0
        if 'state' in fields:count+=39 if spec.get('task')=='recovery' else 18
        if 'control' in fields:count+=54
        if 'posture' in fields:count+=10
        if 'geometry' in fields:count+=13
        if 'actor_input' in fields:count+=197
        return count
    widths=[channels(p) for p in plans] or [134]
    samples=math.ceil(seconds/dt)
    if plans and all(p['profile']=='failure_tail' for p in plans):samples=min(samples,math.ceil(1/dt))
    evaluation_bytes=65536+samples*evaluation.get('scored_envs',8)*max(widths)*32
    diagnostic_bytes=0
    if spec.get('rollout_probe'):
        diagnostic_bytes+=spec['rollout_probe']['max_storage_bytes']
    for section in ('diagnostics','selected_diagnostics'):
        capture=spec.get(section,{})
        if isinstance(capture,dict) and capture.get('enabled'):
            count=len(capture.get('updates',[]))
            diagnostic_bytes+=count*ppo.get('envs',64)*ppo.get('steps_per_env',128)*(150+125+64)*8
    if phase=='evaluate':events=max(1,len(spec.get('evaluation_requests',[])));commands=1
    artifacts=snapshots*checkpoint_bytes+events*commands*evaluation_bytes+diagnostic_bytes
    return {'schema_version':'artifact_budget_v1','phase':phase,'checkpoint_bytes':snapshots*checkpoint_bytes,
        'storage_profiles':[p.get('profile') for p in plans],
        'evaluation_bytes':events*commands*evaluation_bytes,'selected_capture_bytes':diagnostic_bytes,
        'estimated_artifact_bytes':artifacts,'atomic_temp_peak_bytes':max(evaluation_bytes,checkpoint_bytes),
        'terminal_reserve_bytes':512*1024**2,'estimate_note':'conservative JSON estimate; does not promise a hard byte cap'}


def check(spec,output,phase):
    path=Path(output).resolve()
    while not path.exists():path=path.parent
    plan=estimate(spec,phase);free=shutil.disk_usage(path).free
    required=plan['estimated_artifact_bytes']+plan['atomic_temp_peak_bytes']+plan['terminal_reserve_bytes']
    return {**plan,'output_partition_probe':str(path),'available_bytes':free,'required_bytes':required,
        'status':'PASS' if free>=required else 'INSUFFICIENT_STORAGE',
        'scope':'output filesystem before reserve/launcher; other tasks can consume space afterwards'}


def actual_bytes(folder):
    """One-shot completed artifact accounting; never follows symlinks."""
    folder=Path(folder)
    rows=[{'path':str(p.relative_to(folder)),'bytes':p.stat().st_size} for p in folder.rglob('*') if p.is_file() and not p.is_symlink()]
    return {'scope':'observed files at final report; later reports may add bytes','total_bytes':sum(r['bytes'] for r in rows),
        'files':len(rows),'largest':sorted(rows,key=lambda r:-r['bytes'])[:10]}
