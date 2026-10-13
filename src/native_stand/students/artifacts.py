"""Atomic student evidence writes; bounded by frozen declarations, not date paths."""
import os
import tempfile
from pathlib import Path
import numpy as np
import torch


def atomic(path,writer):
    path=Path(path)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            writer(stream);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if Path(name).exists():Path(name).unlink()
    return path


def npz(path,arrays):return atomic(path,lambda stream:np.savez_compressed(stream,**arrays))
def checkpoint(path,data):return atomic(path,lambda stream:torch.save(data,stream))


def storage(spec):
    maximum=spec['student_training']['storage_max_bytes']
    case_maximum=spec['student_evaluation']['max_output_bytes']
    # Keep the original 128MiB tail reserve, now explicitly declared.
    reserve=spec.get('artifacts',{}).get('terminal_reserve_bytes',128*2**20)
    if any(type(v) is not int or v<=0 for v in (maximum,case_maximum,reserve)) or reserve>=maximum:
        raise ValueError('Invalid student declared storage limits')
    return {'chain_max_bytes':maximum,'evaluation_max_bytes':case_maximum,'terminal_reserve_bytes':reserve}


def secondary(error,name,operation):
    """A failed evidence save is diagnostic information, never the primary fault."""
    try:return operation()
    except BaseException as failure:
        error.add_note(name+' also failed: '+repr(failure))
        return None
