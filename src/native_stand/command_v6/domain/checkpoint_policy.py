"""Pure opt-in checkpoint retention. Referenced evidence always wins over quota."""

def resolve(spec):
    value=spec.get('artifacts',{}).get('checkpoint_retention')
    if value is None:return None
    if (not isinstance(value,dict) or set(value)!={'version','keep_last','milestone_updates'} or
            value['version']!='checkpoint_retention_v1' or type(value['keep_last']) is not int or value['keep_last']<1 or
            not isinstance(value['milestone_updates'],list) or
            any(type(u) is not int or u<0 for u in value['milestone_updates'])):
        raise ValueError('invalid explicit checkpoint retention policy')
    return value


def select(inventory,policy,protected_paths):
    if policy is None:return {'retain':inventory,'remove':[]}
    ordered=sorted(inventory,key=lambda r:r['update'])
    keep={r['path'] for r in ordered[-policy['keep_last']:]}|set(protected_paths)
    milestones=set(policy['milestone_updates'])|{0}
    keep.update(r['path'] for r in ordered if r['update'] in milestones)
    return {'retain':[r for r in ordered if r['path'] in keep],
            'remove':[r for r in ordered if r['path'] not in keep]}
