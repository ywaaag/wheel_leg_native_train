"""CPU GUI identity/initialization contract; no resource query or simulation."""
import contextlib
import hashlib
import importlib
import io
from pathlib import Path
import shlex
import sys


def model_identity(spec,checkpoint,*,family=None):
    import torch
    from tensordict import TensorDict
    from .model_factory import model
    from ..domain.action_distribution import validate
    validate(spec)
    saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    width=saved['actor']['mlp.0.weight'].shape[-1]
    # Constructor initialization must not consume the caller's training RNG.
    with torch.random.fork_rng(devices=[]),contextlib.redirect_stdout(io.StringIO()):
        dummy=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
        actor=model(dummy,actor=True,spec=spec)
        state=saved['actor']
        if width==132:
            from ..domain.warmstart import expand_state
            state=expand_state(state,actor.state_dict())
        actor.load_state_dict(state,strict=True)
    if not all(torch.isfinite(t).all() for t in actor.state_dict().values()):raise ValueError('Preview actor has nonfinite parameters')
    distribution=actor.distribution
    module=importlib.import_module(type(distribution).__module__)
    path=Path(module.__file__).resolve()
    version=(spec['action_distribution']['version'] if spec.get('action_distribution') else
        'native_wheel_scaled_gaussian_v1' if spec.get('wheel_envelope_conversion') else 'rsl_gaussian_v1')
    return {'version':version,'class':type(distribution).__module__+':'+type(distribution).__name__,
        'implementation_path':str(path),'implementation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'declaration':spec.get('action_distribution'),'actor_strict_load':True,
        'actor_parameter_shapes':{k:list(t.shape) for k,t in actor.state_dict().items()},
        'checkpoint_std':state['distribution.std_param'].tolist(),
        'pose_family':family,'scope':'strict parameter loading plus explicit output semantics; not behavior certification'}


def recovery_selection(spec,*,family=None):
    import json
    config=spec['recovery'];family=family or config.get('preview_family',config['active_family'])
    library=json.loads(Path(config['pose_library']).read_text())
    poses=[p['pose_id'] for p in library['poses'] if p['family']==family and p['split']=='holdout' and p.get('offline_valid')]
    if not poses:raise ValueError('Preview family has no offline-valid holdout pose: '+family)
    return {'family':family,'split':'holdout','pose_ids':poses,'num_envs':1,
        'training_allocation_enabled':False,'scope':'single holdout reset selection; runtime geometry remains unverified'}


def command(spec_path,checkpoint,physical_gpu,*,family=None):
    args=[sys.executable,'-m','native_stand.command_v6.tools.play','--spec',str(Path(spec_path).resolve()),
        '--checkpoint',str(Path(checkpoint).resolve()),'--preview','--strict-identities','--physical-gpu',str(physical_gpu)]
    if family:args+=['--preview-family',family]
    return {'argv':args,'cpu_plan':'PYTHONPATH=src '+shlex.join(args),
        'gui_command':'PYTHONPATH=src '+shlex.join(args+['--run']),
        'gui_run_requires_explicit_authorization':True}
