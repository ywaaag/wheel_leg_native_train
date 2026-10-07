"""Explicit GPU ownership policy; no process-name whitelist or runtime access."""


def resolve_resources(spec, *, mode=None, sharing_authorization=None):
    declared=spec.get('resources',{})
    if not isinstance(declared,dict):raise ValueError('resources must be an object')
    unknown=set(declared)-{'mode','sharing_authorized','authorization_note'}
    if unknown:raise ValueError('unknown resource fields: '+', '.join(sorted(unknown)))
    selected=mode or declared.get('mode','exclusive')
    if selected not in ('exclusive','shared'):raise ValueError('resource mode must be exclusive or shared')
    if 'sharing_authorized' in declared and type(declared['sharing_authorized']) is not bool:
        raise ValueError('resources sharing_authorized must be boolean')
    note=sharing_authorization or declared.get('authorization_note')
    if note is not None and (not isinstance(note,str) or not note.strip()):
        raise ValueError('sharing authorization must be a nonempty explanation')
    consent=bool(sharing_authorization) or declared.get('sharing_authorized',False)
    if selected=='shared' and (not consent or not note):
        raise ValueError('shared GPU mode requires explicit sharing_authorized and authorization_note')
    if selected=='exclusive' and sharing_authorization:
        raise ValueError('sharing authorization requires shared GPU mode')
    return {'mode':selected,'sharing_authorized':selected=='shared' and consent,
            'authorization_note':note if selected=='shared' else None,
            'origin':'explicit CLI' if mode is not None or sharing_authorization else 'spec' if declared else 'default exclusive'}


def occupied_gpu_allowed(policy):
    return policy.get('mode')=='shared' and policy.get('sharing_authorized') is True and bool(policy.get('authorization_note'))
