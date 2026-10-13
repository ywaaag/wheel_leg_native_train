"""Identity-bound compressed numeric traces; JSON summaries remain small.

New outputs only. Existing JSON is readable unchanged. Never mutate history.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import numpy as np
from ..domain.evidence_summary import RAW_KEYS
VERSION='evaluation_numeric_npz_v1'


def read(path):
    path=Path(path).resolve();result=json.loads(path.read_text())
    storage=result.get('numeric_trace_storage')
    if storage is None:return result
    if storage.get('version')!=VERSION:raise ValueError('Unknown numeric trace encoding')
    archive=(path.parent/storage['path']).resolve()
    if not archive.is_relative_to(path.parent):raise ValueError('Numeric trace archive escapes evaluation directory')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=storage['sha256']:raise ValueError('Numeric trace SHA differs')
    arrays=np.load(archive,allow_pickle=False)
    seen=set()
    def hydrate(value):
        if isinstance(value,dict) and 'numeric_trace_reference' in value:
            reference=value['numeric_trace_reference'];name=reference['array'];seen.add(name)
            array=arrays[name]
            if list(array.shape)!=reference['shape'] or str(array.dtype)!=reference['dtype']:
                raise ValueError('Numeric trace shape/dtype differs')
            if array.dtype.kind in 'fc':
                def finite(v):
                    if isinstance(v,list):return [finite(x) for x in v]
                    return None if not np.isfinite(v) else v
                return finite(array.tolist())
            return array.tolist()
        if isinstance(value,dict):return {k:hydrate(v) for k,v in value.items()}
        if isinstance(value,list):return [hydrate(v) for v in value]
        return value
    try:
        output=hydrate(result)
        if seen!=set(arrays.files):raise ValueError('Numeric trace references/arrays differ')
        return output
    finally:arrays.close()


def write(path,result):
    path=Path(path).resolve()
    if path.exists() or path.with_suffix('.traces.npz').exists():raise FileExistsError('Evaluation output already exists')
    arrays={};manifest=[]
    def pack(value,key='',location=()):
        numeric_field=key in RAW_KEYS or (key in ('rows','valid') and any(p in ('control_diagnostics','paired_state') for p in location))
        if numeric_field and isinstance(value,list) and value:
            try:
                array=np.asarray(value)
                if array.dtype.kind=='O':array=np.asarray(value,dtype=np.float64)
            except (ValueError,TypeError):array=None
            if array is not None and array.ndim>=2 and array.dtype.kind in 'bifu':
                name=f'trace_{len(arrays):04d}';arrays[name]=array
                axes=(['policy_time','scored_env'] if key=='valid' else ['policy_time','channel']) if array.ndim==2 else ['policy_time','scored_env','channel'] if array.ndim==3 else None
                reference={'array':name,'shape':list(array.shape),'dtype':str(array.dtype),
                    'axes':axes,'field':key,'json_location':list(location)}
                manifest.append(reference)
                return {'numeric_trace_reference':reference}
        if isinstance(value,dict):return {k:pack(v,k,location+(k,)) for k,v in value.items()}
        if isinstance(value,list):return [pack(v,key,location+(i,)) for i,v in enumerate(value)]
        return value
    packed=pack(result)
    archive=path.with_suffix('.traces.npz');created=[];temporary=None
    try:
        if arrays:
            # Exclusive sidecar first; JSON receipt published last. On process error
            # roll back, on process death an orphan sidecar is not a valid receipt.
            with archive.open('xb') as stream:
                created.append(archive);np.savez_compressed(stream,**arrays);stream.flush();os.fsync(stream.fileno())
            packed['numeric_trace_storage']={'version':VERSION,'path':archive.name,
                'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'arrays':manifest,
                'scope':'numeric fields only; original units/validity/windows remain declared in evaluation'}
        fd,temporary=tempfile.mkstemp(prefix='.evaluation-',dir=path.parent)
        with os.fdopen(fd,'w') as stream:
            json.dump(packed,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        # Atomic and exclusive publication; never replace historical output.
        os.link(temporary,path);created.append(path)
        return {'json_bytes':path.stat().st_size,'numeric_bytes':archive.stat().st_size if arrays else 0,
            'arrays':len(arrays),'version':VERSION}
    except BaseException:
        for item in reversed(created):item.unlink()
        raise
    finally:
        if temporary and Path(temporary).exists():Path(temporary).unlink()
