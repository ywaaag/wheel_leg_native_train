"""File boundary validation of an untrained calibrated source, not reapplication."""
import hashlib
from pathlib import Path
import torch

def verify(saved,path):
    c=saved.get('initialization_candidate')
    if not isinstance(c,dict) or c.get('version')!='recovery_leg_output_calibration_v1' or c.get('trained') is not False:raise ValueError('Invalid initialization candidate identity')
    if c['calibration_max_error_rad']>.03 or c['anchor_rms_change_rad']>.05:raise ValueError('Unqualified leg candidate')
    original=Path(c['source_checkpoint']);sha=hashlib.sha256(original.read_bytes()).hexdigest()
    if sha!=c['source_sha256']:raise ValueError('Original lineage SHA differs')
    old=torch.load(original,map_location='cpu',weights_only=False)
    for role in ('actor','critic'):
        for n,v in old[role].items():
            current=saved[role][n]
            if role=='actor' and n in ('mlp.6.weight','mlp.6.bias'):
                if not torch.equal(v[[2,5]],current[[2,5]]):raise ValueError('Wheel rows changed')
            elif not torch.equal(v,current):raise ValueError('Forbidden candidate mutation '+role+'.'+n)
    if old['optimizer']['param_groups']!=saved['optimizer']['param_groups']:raise ValueError('Adam groups changed')
    for k,state in old['optimizer']['state'].items():
        if any(not torch.equal(v,saved['optimizer']['state'][k][n]) for n,v in state.items()):raise ValueError('Adam changed')
    return {**c,'path':str(Path(path).resolve()),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'scope':'untrained source loaded verbatim once per phase; no runtime transform'}
