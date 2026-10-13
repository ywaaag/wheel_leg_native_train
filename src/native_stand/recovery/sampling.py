"""Pure reset sampling and assessment contracts, independent of rise scoring.

Legacy fields are read only here; never mutate a historical declaration. New
contracts reject mixed declarations so no second sampling source can override them.
"""
import math

LEGACY_KEYS=('sampling_version','retained_families','retained_fraction')


def scoring_config(task):
    """Strip only recognized, fully validated historical sampling metadata."""
    legacy={k:task[k] for k in LEGACY_KEYS if k in task}
    if legacy:
        retained=legacy.get('retained_families');fraction=legacy.get('retained_fraction')
        explicit=legacy.get('sampling_version')=='explicit_retained_pose_weights_v1'
        if explicit:
            _families(retained)
            if 'R0' not in retained or not _finite(fraction) or not .4<=fraction<1.:
                raise ValueError('Legacy rise sampling requires R0 and >=40% retained mass')
        elif legacy!={'retained_families':['R0'],'retained_fraction':.4}:
            raise ValueError('Unknown or incomplete legacy rise sampling declaration')
    return {k:v for k,v in task.items() if k not in LEGACY_KEYS}


def _finite(v):
    return type(v) in (int,float) and math.isfinite(v)


def _families(values, *, empty=False):
    if (not isinstance(values,list) or (not empty and not values) or
            any(not isinstance(f,str) or not f.strip() for f in values) or len(set(values))!=len(values)):
        raise ValueError('Families must be unique nonempty names')


def validate_explicit(config):
    sampling=config.get('sampling');assessment=config.get('assessment')
    if sampling is None and assessment is None:return False
    fixed=isinstance(sampling,dict) and sampling.get('version')=='fixed_environment_families_v1'
    fields={'version','family_weights','environment_counts'} if fixed else {'version','family_weights'}
    if (not isinstance(sampling,dict) or set(sampling)!=fields or
            sampling['version'] not in ('family_weights_v1','fixed_environment_families_v1')):
        raise ValueError('Explicit sampling requires family_weights_v1')
    weights=sampling['family_weights']
    if (not isinstance(weights,dict) or not weights or any(not isinstance(f,str) or not f.strip() for f in weights)
            or any(not _finite(w) or w<=0 for w in weights.values()) or
            not math.isclose(sum(weights.values()),1.,abs_tol=1e-12)):
        raise ValueError('Sampling weights must be finite positive and sum to one')
    if fixed:
        counts=sampling['environment_counts']
        if (not isinstance(counts,dict) or set(counts)!=set(weights) or
                any(type(n) is not int or n<1 for n in counts.values())):
            raise ValueError('Fixed family slots require positive integer counts for every family')
        total=sum(counts.values())
        if any(not math.isclose(counts[f]/total,weights[f],abs_tol=1e-12) for f in weights):
            raise ValueError('Fixed family weights must equal declared environment counts')
    if (not isinstance(assessment,dict) or set(assessment)!={'families','retained_families'}):
        raise ValueError('Explicit assessment needs families and retained_families')
    _families(assessment['families']);_families(assessment['retained_families'],empty=True)
    if not set(assessment['families'])<=set(weights) or not set(assessment['retained_families'])<=set(assessment['families']):
        raise ValueError('Assessment families must be sampled; retained must be assessed')
    active=config.get('active_family')
    if active not in weights or active not in assessment['families'] or active in assessment['retained_families']:
        raise ValueError('Active family must be sampled and assessed, separate from retained skills')
    if set(assessment['families'])!={active,*assessment['retained_families']} or set(weights)!=set(assessment['families']):
        raise ValueError('Single-block sampling and assessment must cover active and all retained families')
    if any(k in config.get('rising_task',{}) for k in LEGACY_KEYS):
        raise ValueError('Explicit sampling conflicts with legacy rising_task sampling fields')
    levels=config.get('curriculum',{}).get('levels',[])
    if any('retained_families' in row or 'retained_fraction' in row for row in levels):
        raise ValueError('Explicit sampling conflicts with legacy level sampling fields')
    if any(row.get('pose_family') not in weights or row.get('pose_family') not in assessment['families'] for row in levels):
        raise ValueError('Curriculum families must be explicitly sampled and assessed')
    return True


def retained_families(config, family):
    """Protection scope comes from assessment, never inferred from sample weights."""
    if validate_explicit(config):
        return list(config['assessment']['retained_families'])
    task=config.get('rising_task')
    if task:
        scoring_config(task)
        return list(task.get('retained_families',[]))
    level=next((r for r in config.get('curriculum',{}).get('levels',[]) if r['pose_family']==family),{})
    return list(level.get('retained_families',[]))


def sample_poses(poses,config,family,split,*,training,stage=None):
    """Metadata-only weights; no RNG draws, no synthetic episode time or state."""
    explicit=validate_explicit(config)
    if explicit:
        weights=config['sampling']['family_weights'] if training else {family:1.}
        if family not in config['sampling']['family_weights']:raise ValueError('Unknown evaluation family')
        indices=[];probabilities=[]
        for group,mass in weights.items():
            ids=[i for i,p in enumerate(poses) if p['family']==group and p['split']==split and p['offline_valid']]
            if not ids:raise ValueError('Missing valid pose split for '+group)
            local=[poses[i].get('sample_weight',1.) for i in ids]
            if any(not _finite(v) or v<=0 for v in local):raise ValueError('Invalid within-family pose weight')
            total=sum(local)
            indices.extend(ids);probabilities.extend(mass*v/total for v in local)
        return indices,probabilities
    # Historical precedence exactly preserved: stage>0 overrides rise rehearsal.
    retained=();fraction=0.
    if training and config.get('rising_task'):
        task=config['rising_task'];scoring_config(task)
        retained=task.get('retained_families',());fraction=task.get('retained_fraction',0.)
    if training and stage:
        level=config['curriculum']['levels'][stage]
        retained=level.get('retained_families',());fraction=level.get('retained_fraction',0.)
    return legacy_pose_sampling(poses,family,split,retained_families=retained,retained_fraction=fraction)


def fixed_reset_choices(poses,config,split,env_ids,num_envs):
    """Draw only within each immutable training slot family; explicit inputs/RNG.

    Evaluation must bypass this function and use its requested family. Partial
    resets preserve each environment's family, regardless of episode length.
    """
    import torch
    validate_explicit(config)
    counts=config['sampling']['environment_counts']
    if sum(counts.values())!=num_envs:
        raise ValueError('Fixed family slots differ from actual training environment count')
    if bool(((env_ids<0)|(env_ids>=num_envs)).any()):raise ValueError('Reset environment ID outside allocation')
    choices=torch.empty_like(env_ids)
    start=0
    for family,count in counts.items():
        mask=(env_ids>=start)&(env_ids<start+count);start+=count
        n=int(mask.sum())
        if not n:continue
        eligible,weights=sample_poses(poses,config,family,split,training=False)
        candidates=torch.tensor(eligible,device=env_ids.device)
        probabilities=torch.tensor(weights,device=env_ids.device)
        choices[mask]=candidates[torch.multinomial(probabilities,n,replacement=True)]
    return choices


def effective(config):
    explicit=validate_explicit(config)
    if config.get('rising_task'):scoring_config(config['rising_task'])
    return {'declaration':'explicit' if explicit else 'legacy_read_only_adapter',
        'sampling':config.get('sampling') if explicit else {
            'rise_sampling':{k:v for k,v in config.get('rising_task',{}).items() if k in LEGACY_KEYS},
            'level_sampling':[{k:v for k,v in row.items() if k in (*LEGACY_KEYS,'pose_family')}
                              for row in config.get('curriculum',{}).get('levels',[])]},
        'assessment':config.get('assessment') if explicit else {
            'retained_families':retained_families(config,config.get('active_family'))}}


def legacy_pose_sampling(poses, family, split, *, retained_families=(), retained_fraction=0.):
    """Metadata-only weighted rehearsal; physics states are never altered."""
    current = [i for i, p in enumerate(poses)
               if p['family'] == family and p['split'] == split and p['offline_valid']]
    old = [i for i, p in enumerate(poses) if p['family'] in retained_families and
           p['family'] != family and p['split'] == split and p['offline_valid']]
    if not current or not 0. <= retained_fraction < 1. or (retained_fraction and not old):
        raise ValueError('Invalid standing pose sampling or missing rehearsal poses')
    indices, weights = [], []
    groups = [(current, 1.-retained_fraction), (old, retained_fraction)] if retained_fraction else [(current, 1.)]
    for group, mass in groups:
        total = sum(poses[i].get('sample_weight', 1.) for i in group)
        if total <= 0:
            raise ValueError('Pose sampling weights must have positive mass')
        indices.extend(group)
        weights.extend(mass*poses[i].get('sample_weight', 1.)/total for i in group)
    return indices, weights


def validate(config):
    """Whole sampling schema validation, separate from task scoring validation."""
    if validate_explicit(config):return
    if config.get('rising_task'):scoring_config(config['rising_task'])
    for index,level in enumerate(config.get('curriculum',{}).get('levels',[])):
        fraction=level.get('retained_fraction',0.)
        if (not isinstance(fraction,(int,float)) or not math.isfinite(fraction) or not 0<=fraction<1 or
                (fraction and (not index or not level.get('retained_families')))):
            raise ValueError('Standing curriculum rehearsal configuration invalid')


def allocation_plan(config,num_envs):
    """Submission-time quota authority; environment order follows authored counts."""
    validate(config)
    if type(num_envs) is not int or num_envs<1:raise ValueError('Training env count must be positive integer')
    declared=config.get('sampling',{})
    fixed=declared.get('version')=='fixed_environment_families_v1'
    mapping=None
    if fixed:
        counts=declared['environment_counts']
        if sum(counts.values())!=num_envs:raise ValueError('Fixed family slots differ from PPO environment count')
        mapping=[{'env_id':i,'family':f} for i,f in enumerate(f for f,n in counts.items() for _ in range(n))]
    return {'mode':'fixed_environment_families' if fixed else 'categorical_reset',
        'training_envs':num_envs,'environment_to_family':mapping,
        'declared_environment_counts':declared.get('environment_counts'),
        'nominal_family_mass':declared.get('family_weights'),
        'allocation_scope':'training only; evaluation selects requested family',
        'counts_note':'slot mass, reset assignments and valid transitions are different denominators'}


def coverage(plan,initializations,phases):
    """Explicit measured denominators; absent counters remain UNKNOWN."""
    families=set((plan.get('nominal_family_mass') or {}).keys())
    for row in initializations or []:families.add(row['family'])
    for row in phases or []:families.add(row['family'])
    attempts=sum(row['attempted'] for row in initializations or [])
    transitions=sum(row['transition_count'] for row in phases or [])
    result=[]
    for family in sorted(families):
        init=[r for r in initializations or [] if r['family']==family];phase=[r for r in phases or [] if r['family']==family]
        allocated=sum(r['attempted'] for r in init);count=sum(r['transition_count'] for r in phase)
        result.append({'family':family,'declared_slots':(plan.get('declared_environment_counts') or {}).get(family),
            'initialization_attempts':allocated if initializations is not None else None,
            'initialization_fraction':allocated/attempts if attempts else None,
            'valid_transition_count':count if phases is not None else None,
            'valid_transition_fraction':count/transitions if transitions else None,
            'phase_transition_counts':{p:sum(r['transition_count'] for r in phase if r['phase']==p) for p in {r['phase'] for r in phase}}})
    return {'families':result,'initialization_attempts_total':attempts if initializations is not None else None,
        'valid_transition_total':transitions if phases is not None else None,
        'initializations_scope':'cumulative runtime reset assignments; includes evaluation and cleanup resets when they run',
        'initialization_counts_include_evaluation_resets':True,
        'transitions_scope':'current rollout, excludes initialization and deterministic evaluation',
        'comparability':'initializations are cumulative; transitions are rollout-local; not equal-duration task exposure'}
