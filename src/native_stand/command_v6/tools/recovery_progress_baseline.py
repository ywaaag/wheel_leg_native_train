"""CLI-boundary loader for full source evidence; candidate summaries omit traces."""
import hashlib
import json
from pathlib import Path


def load(folder, entry, *, spec_sha256, source_sha256, asset_sha256):
    folder=Path(folder)
    if entry.get('role')!='source' or entry.get('evaluation')!='evaluation_source.json':
        raise ValueError('Progress baseline must identify the source evaluation')
    if entry.get('checkpoint_sha256')!=source_sha256:
        raise ValueError('Progress source checkpoint identity differs')
    manifest=json.loads((folder/'manifest.json').read_text())
    for key,value in (('spec_sha256',spec_sha256),('source_sha256',source_sha256),
                      ('asset_sha256',asset_sha256)):
        if manifest.get(key)!=value:raise ValueError('Progress source manifest identity differs: '+key)
    from .evaluation_loader import load as load_raw
    result,evidence=load_raw(folder,entry,spec_sha256=spec_sha256,
        checkpoint_sha256=source_sha256,asset_sha256=asset_sha256,
        required_fields=('control_diagnostics_100hz',))
    return result,{**evidence,'source_sha256':source_sha256,
                   'scope':'full persisted source evaluation,not compact candidate summary'}
