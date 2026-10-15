"""Atomic numeric evidence and checkpoint writes; no historical cleanup."""
import os
import tempfile
from pathlib import Path


def atomic(path,writer):
    path=Path(path)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            writer(stream);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)
    return path


def checkpoint(path,data):
    import torch
    return atomic(path,lambda stream:torch.save(data,stream))


def npz(path,arrays):
    import numpy as np
    return atomic(path,lambda stream:np.savez_compressed(stream,**arrays))


def runtime_storage(output,spec):
    """Opt-in byte ceiling from the declaration, no deletion or other-run scan."""
    import errno
    maximum=spec.get('artifacts',{}).get('storage_max_bytes')
    if maximum is None:return None
    reserve=spec['artifacts'].get('terminal_reserve_bytes',128*2**20)
    if type(maximum) is not int or type(reserve) is not int or not 0<reserve<maximum:
        raise ValueError('invalid declared runtime storage ceiling/reserve')
    used=sum(p.stat().st_size for p in Path(output).rglob('*') if p.is_file() and not p.is_symlink())
    if used+reserve>maximum:raise OSError(errno.ENOSPC,'declared output byte ceiling reached; reserve kept for terminal')
    return {'actual_bytes':used,'maximum_bytes':maximum,'terminal_reserve_bytes':reserve}


def rotate_bytes(path,payload,*,maximum,backups):
    """Owner-only bounded log append. Never call on raw evaluation/checkpoints."""
    path=Path(path)
    if type(maximum) is not int or maximum<1 or type(backups) is not int or backups<1:
        raise ValueError('positive explicit log byte and backup limits required')
    offset=0
    while offset<len(payload):
        size=path.stat().st_size if path.exists() else 0
        if size>=maximum:
            path.with_name(path.name+'.'+str(backups)).unlink(missing_ok=True)
            for index in range(backups-1,0,-1):
                old=path.with_name(path.name+'.'+str(index))
                if old.exists():os.replace(old,path.with_name(path.name+'.'+str(index+1)))
            os.replace(path,path.with_name(path.name+'.1'));size=0
        take=min(maximum-size,len(payload)-offset)
        with path.open('ab') as stream:stream.write(payload[offset:offset+take])
        offset+=take
