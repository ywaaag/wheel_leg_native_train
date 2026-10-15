"""Explicit bounded pre-update evidence; no sampling, optimizer step or model export."""
import io,json,os
from pathlib import Path
from ..domain.artifact_policy import validate


def capture(output,spec,phase,update,actor,critic,optimizer):
    validate(spec);config=spec.get('artifacts',{}).get('optimizer_capture')
    if config is None or update not in config['updates'].get(phase,[]):return None
    import torch,random
    import numpy as np
    output=Path(output);path=output/f'optimizer_before_update_{update}.pt'
    if path.exists():raise FileExistsError(path)
    cpu=torch.get_rng_state().clone()
    cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None
    try:
        payload={'version':'optimizer_capture_v1','phase':phase,'next_update':update,
            'completed_updates':update-1,'actor':actor.state_dict(),'critic':critic.state_dict(),
            'optimizer':optimizer.state_dict(),'python_rng':random.getstate(),'numpy_rng':np.random.get_state(),'parameter_names':{'actor':list(dict(actor.named_parameters())),
                'critic':list(dict(critic.named_parameters()))},'cpu_rng':cpu,'cuda_rng':cuda,
            'source_sha256':spec.get('source_sha256'),'scope':'pre-update state; not historical shuffle or physical state'}
        from .submission_receipt import digest,stable
        frozen=output/'source_snapshot/spec.json'
        identity=output/'identity.json'
        payload.update(effective_declaration_sha256=stable(spec),
            recorded_spec_sha256=digest(frozen) if frozen.is_file() else None,
            source_identity_sha256=digest(identity) if identity.is_file() else None)
        buffer=io.BytesIO();torch.save(payload,buffer);data=buffer.getvalue()
        previous=list(output.glob('optimizer_before_update_*.pt'))
        if len(data)+sum(p.stat().st_size for p in previous)>config['max_bytes']:
            raise OSError('declared optimizer capture byte ceiling exceeded')
        from .source_identity import exclusive_bytes
        exclusive_bytes(path,data)
        from .submission_receipt import digest
        from ..completion import write
        write(output/f'optimizer_before_update_{update}.json',{'path':path.name,'sha256':digest(path),
            'bytes':len(data),'next_update':update,'phase':phase,'effective_declaration_sha256':payload['effective_declaration_sha256'],
            'recorded_spec_sha256':payload['recorded_spec_sha256'],'source_identity_sha256':payload['source_identity_sha256'],'optimizer_steps_executed':0})
        return {'path':str(path),'sha256':digest(path),'bytes':len(data)}
    finally:
        torch.set_rng_state(cpu)
        if cuda is not None:torch.cuda.set_rng_state_all(cuda)
