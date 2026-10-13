"""Persist completed actor-update proof independent of later evaluator/progress failures."""
import torch
from .experiment_preparation import checked_input


def compare(source,candidate):
    old=torch.load(source,map_location='cpu',weights_only=False);new=torch.load(candidate,map_location='cpu',weights_only=False)
    if set(old['actor'])!=set(new['actor']):raise ValueError('actor parameter names differ')
    differences=[]
    for key,a in old['actor'].items():
        b=new['actor'][key]
        if a.shape!=b.shape or not torch.isfinite(a).all() or not torch.isfinite(b).all():raise ValueError('actor shape/finite differs')
        differences.append({'parameter':key,'max_abs_difference':float((a-b).abs().max())})
    return {'version':1,'source':checked_input(source),'candidate':checked_input(candidate),
        'actor_parameters_changed':any(r['max_abs_difference']>0 for r in differences),
        'parameter_differences':differences,'update':new.get('update'),
        'asset_sha256':new.get('asset_sha256'),'spec_sha256':new.get('spec_sha256'),
        'scope':'saved actor tensor difference; not evidence of capability improvement'}
