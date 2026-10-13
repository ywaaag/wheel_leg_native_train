"""CPU-only identity check for source or project-native evaluation actors."""
import hashlib
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(path,spec,spec_path):
    import torch
    path=Path(path)
    identity=digest(path)
    checkpoint=torch.load(path,map_location="cpu",weights_only=False)
    state=checkpoint.get("actor")
    if not isinstance(state,dict) or "mlp.0.weight" not in state:
        raise ValueError("actor state dictionary is incomplete")
    width=state["mlp.0.weight"].shape[-1]
    if width==132:
        if identity!=spec["source_sha256"]:
            raise ValueError("132D checkpoint is not the frozen B200 source")
        kind="B200_SOURCE_EXPAND"
    elif width==150:
        if identity==spec['source_sha256'] and spec.get('source_input_dim')==150:
            if checkpoint.get('update')!=spec['source_update'] or checkpoint.get('asset_sha256')!=spec.get('source_asset_sha256',spec['asset_sha256']):
                raise ValueError('native source internal identity differs')
            kind='NATIVE_SOURCE_STRICT'
            if checkpoint.get('initialization_candidate'):
                from native_stand.recovery.initialization_candidate import verify
                c=verify(checkpoint,path)
                if spec.get('initialization_candidate',{}).get('sha256')!=c['sha256']:raise ValueError('Candidate declaration missing or differs')
                kind='UNTRAINED_LEG_INITIALIZATION_SOURCE'
        elif (not spec.get('diagnostic_identity_only') and
              (checkpoint.get("spec_sha256")!=digest(spec_path) or
               checkpoint.get("asset_sha256")!=spec["asset_sha256"])):
            raise ValueError("150D candidate spec or asset identity differs")
        else:
            kind="NATIVE_CANDIDATE"
    else:
        raise ValueError("actor input width must be source 132D or native 150D")
    if tuple(state["mlp.0.weight"].shape)!=(spec["ppo"]["hidden_dims"][0],width):
        raise ValueError("actor first-layer hidden dimension differs")
    return {"checkpoint_sha256":identity,"kind":kind,"actor_input_dim":width}
