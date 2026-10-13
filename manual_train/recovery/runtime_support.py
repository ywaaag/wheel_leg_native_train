"""Copied into a manual experiment bundle; shared physics/trainer remain unchanged."""
import json,fcntl
from pathlib import Path
import torch
from .manual_parameters import SETTINGS, REWARD_SHA, SOURCE_TRAINING_RECIPE
RECIPE = 'manual_recovery_ppo_v1'
REWARD = 'manual_recovery_reward_v1'

def recipe(source_sha):
    from .training_recipe import declaration
    # A previously produced manual source is verified against its own frozen recipe.
    if SOURCE_TRAINING_RECIPE and SOURCE_TRAINING_RECIPE['version']==RECIPE and source_sha==SOURCE_TRAINING_RECIPE['source_actor_sha256']:
        return SOURCE_TRAINING_RECIPE
    r=declaration('student_recovery_ppo_dynamic_suffix_contact_v10',source_actor_sha256=source_sha)
    from .recovery_task import configuration
    r.update(version=RECIPE,reward=configuration(REWARD),milestones=milestones(),
             training_family='motion_native_normal' if SETTINGS['mode']=='standing' else 'swing_candidate_from_historical_r1')
    return r

def milestones():
    n=SETTINGS['formal_updates']
    return sorted(set([v for v in (25,50,100,200,300) if v<=n]+[n]))

def configuration(base):
    from . import manual_reward
    r=manual_reward.configuration(base)
    if r.get('version')!=REWARD or r.get('dt')!=.01:raise ValueError('manual reward version/dt must remain declared')
    r['manual_implementation_sha256']=REWARD_SHA
    if set(r['weights'])!=set(base['weights']):raise ValueError('manual reward six named weights required')
    import math
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in r['weights'].values()):raise ValueError('manual reward nonfinite weight')
    return r

def evaluate(context,base,cfg):
    from . import manual_reward
    result=manual_reward.evaluate(context,base,cfg)
    if set(result)!=set(base):raise ValueError('manual reward must retain original named result fields')
    if any(not isinstance(v,torch.Tensor) or v.shape!=base[k].shape or not torch.isfinite(v).all() for k,v in result.items()):raise ValueError('manual reward shape/nonfinite error')
    # User extra reward cannot turn initialization/teacher/fault into student reward.
    result['total']=result['total']*(context['controlled']&~context['fault'])
    return result

def budget(resume=False):
    smoke=0 if resume else 12
    return dict(source_eval_updates=0,source_eval_wall_s=900,smoke_updates=smoke,smoke_wall_s=0 if resume else 900,
                formal_updates=SETTINGS['formal_updates'],formal_wall_s=SETTINGS['chain_wall_s']-900-(0 if resume else 900),
                chain_wall_s=SETTINGS['chain_wall_s'],sample_limit=(SETTINGS['formal_updates']+smoke)*8192)

def verify_task(spec,task,path):
    from .data import sha
    if task.get('authorization')!='UNAUTHORIZED':raise ValueError('manual task authority is supplied by fresh public budget receipt only')
    if task['manual_experiment']!={'version':'manual_experiment_v1','reward_sha256':REWARD_SHA,'settings':SETTINGS}:raise ValueError('manual task/settings/implementation differs')
    if spec['authorization']['status']!='AUTHORIZED' or task['session']!=spec['authorization']['hapi_session'] or spec['device']['uuid']!=task['gpu_uuid']:raise ValueError('manual budget/session/GPU not authorized')
    book=json.loads(path.with_name('task_ledger.json').read_text())
    if book['status']!='RUNNING' or book['active_spec']!=str(Path(task['project_root'])/'configs/experiments'/spec['experiment']/'spec.json') or path.with_name('STOP').exists():raise ValueError('manual task stopped or wrong exact experiment')
    return task

def finish(spec_path,chain,status,failure):
    from .data import sha
    from native_stand.command_v6.completion import write
    spec=json.loads(Path(spec_path).read_text());m=Path(spec['recovery_course']['task_manifest']);ledger=m.with_name('task_ledger.json')
    with ledger.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);d=json.loads(ledger.read_text());t=json.loads((Path(chain)/'chain_terminal_report.json').read_text());b=json.loads(Path(spec_path).with_name('budget.json').read_text())
        if d['active_spec']!=str(Path(spec_path).resolve()) or d['blocks']:raise ValueError('manual exact-ID already settled')
        updates=b['used']['smoke']+b['used']['formal']
        record={'spec':str(spec_path),'spec_sha256':sha(spec_path),'status':status,'updates':updates,'formal_updates':b['used']['formal'],'samples':updates*8192,
                'effective_actor_samples':sum(p.get('terminal',{}).get('effective_actor_samples',0) for p in t['phase_results']),
                'score_episodes':sum(len(e.get('per_env',[])) for p in t['phase_results'] for e in p.get('terminal',{}).get('evaluations',[])),
                'wall_s':t['chain_wall_s'],'chain':str(chain),'failure':failure}
        d['blocks']=[record];d['totals']={k:record[k] for k in d['totals']};d.update(active_spec=None,status=status,next_decision={'action':'STOP','reason':'manual finite experiment finished; no automatic new run'})
        write(ledger,d)
