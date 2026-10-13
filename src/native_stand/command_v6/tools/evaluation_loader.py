"""Identity-bound raw evidence references; compact registries never stand in for traces."""
import hashlib
import json
from pathlib import Path


def load(folder,entry,*,spec_sha256,checkpoint_sha256,asset_sha256,required_fields=()):
    folder=Path(folder).resolve()
    reference=entry.get('evaluation')
    if not isinstance(reference,str):raise ValueError('raw evaluation reference missing')
    path=(folder/reference).resolve()
    if not path.is_relative_to(folder):raise ValueError('evaluation reference escapes run')
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('spec_sha256')!=spec_sha256 or manifest.get('asset_sha256')!=asset_sha256:
        raise ValueError('raw evidence manifest identity differs')
    if entry.get('checkpoint_sha256')!=checkpoint_sha256:raise ValueError('registry checkpoint identity differs')
    payload=path.read_bytes();digest=hashlib.sha256(payload).hexdigest()
    if entry.get('evaluation_sha256') and entry['evaluation_sha256']!=digest:
        raise ValueError('raw evaluation SHA differs')
    from .evaluation_storage import read
    result=read(path)
    if result.get('spec_sha256')!=spec_sha256 or result.get('checkpoint_sha256')!=checkpoint_sha256:
        raise ValueError('raw evaluation identity differs')
    if result.get('asset_sha256',asset_sha256)!=asset_sha256:raise ValueError('raw evaluation asset differs')
    rows=result.get('per_env')
    if not rows or any(row.get(field) is None for row in rows for field in required_fields):
        raise ValueError('raw evaluation required fields missing')
    return result,{'path':str(path),'sha256':digest,'asset_sha256':asset_sha256,
        'checkpoint_sha256':checkpoint_sha256,'scope':'raw persisted evaluation,not candidate summary'}
