"""CPU identities for actual project and external algorithm implementations."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys


def verify_frozen_root(root, expected, spec):
    """Accept a relocated worker only against its immutable submission receipt."""
    root=Path(root).resolve()
    snapshot=root.parent
    if snapshot.name!='source_snapshot':
        raise ValueError('execution_source_root differs from actual loaded project src')
    manifest=json.loads((snapshot.parent/'manifest.json').read_text())
    frozen=(snapshot/'spec.json').read_bytes()
    if (json.loads(frozen)!=spec or
            hashlib.sha256(frozen).hexdigest()!=manifest.get('spec_sha256') or
            manifest.get('declared_execution_source_root')!=str(Path(expected).resolve())):
        raise ValueError('frozen execution spec/source receipt identity differs')
    actual={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*.py'))}
    if not actual or actual!=manifest.get('execution_modules_sha256'):
        raise ValueError('frozen execution module identities differ')
    return {'frozen_root':str(snapshot),'receipt':str(snapshot.parent/'manifest.json'),
            'declared_source_root':str(Path(expected).resolve())}


def identity(spec):
    root = Path(__file__).resolve().parents[2]
    expected = spec.get('execution_source_root')
    frozen_identity=None
    # The imported package is authoritative. A different declared path is a
    # provenance difference, never permission to silently switch implementations.
    source_mismatch=bool(expected and Path(expected).resolve()!=root.parent.resolve())
    dependencies = {}
    for package in ('torch', 'rsl-rl-lib', 'tensordict', 'isaaclab', 'isaacsim'):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = 'distribution metadata unavailable'
    distribution = importlib.metadata.distribution('rsl-rl-lib')
    algorithm = Path(distribution.locate_file('rsl_rl/algorithms/ppo.py')).resolve()
    relative={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(root.rglob('*.py'))}
    modules={str((root/path).resolve()):sha for path,sha in relative.items()}
    source_digest=hashlib.sha256(json.dumps(relative,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    scoped=execution_dependencies(relative,spec.get('task','motion'))
    return {'source_root': str(root.parent.resolve()),
            'declared_source_root':str(Path(expected).resolve()) if expected else None,
            'actual_execution_root':str(root.parent.resolve()),
            'location_independent_modules_sha256':source_digest,
            'relative_modules_sha256':relative,'execution_dependencies':scoped,
            'declared_source_differs':source_mismatch,'python': sys.executable,
            'modules': modules, 'dependencies': dependencies,
            'PPO_path': str(algorithm), 'PPO_sha256': hashlib.sha256(algorithm.read_bytes()).hexdigest()}


def execution_dependencies(relative,task):
    """Task subsystem plus explicit non-runtime tool boundaries, all exclusions recorded.

    The full snapshot remains recorded. Related execution code is never excluded
    just because it changed; excluded preparation/audit tools must remain outside
    the trainer/evaluator runtime call graph.
    """
    recovery_tools={'command_v6/domain/recovery_course.py','command_v6/tools/prepare_recovery_course.py',
        'command_v6/tools/prepare_recovery_retry.py','command_v6/tools/recovery_batch.py',
        'command_v6/tools/recovery_progress_baseline.py','command_v6/tools/review_recovery_events.py',
        'command_v6/tools/review_recovery_takeoff.py','command_v6/tools/frozen_rollout_probe.py',
        'command_v6/domain/rollout_probe.py'}
    selected={};excluded={}
    for path,sha in relative.items():
        reason=None
        if path.startswith('tests/') or '/tests/' in path:reason='test-only; separately validated'
        elif task!='recovery' and path.startswith('recovery/'):reason='Recovery subsystem; Motion environment/actor/reward do not call it'
        elif task!='recovery' and path in recovery_tools:reason='Recovery preparation/audit/probe; not Motion training/evaluation execution'
        if reason:excluded[path]={'sha256':sha,'reason':reason}
        else:selected[path]=sha
    return {'version':'task_subsystem_v2','task':task,'modules_sha256':selected,
        'sha256':hashlib.sha256(json.dumps(selected,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'excluded_modules':excluded,
        'scope':'conservative task dependencies; explicit tool exclusions recorded, related changes need per-file review'}


def recorded(folder,manifest):
    """Read run identities without importing/re-hashing current execution source."""
    data=manifest.get('execution_identity',{})
    if data.get('source_identity_reference'):
        identity_path=Path(folder)/'identity.json'
        if data.get('sha256')!=hashlib.sha256(identity_path.read_bytes()).hexdigest():raise ValueError('Recorded manifest identity SHA differs')
        from .source_identity import read_identity
        record=read_identity(folder)
        relative=record['relative_modules_sha256'];root=record['source_root']
        return {'source_root':str(Path(root).parent),'relative_modules_sha256':relative,
            'location_independent_modules_sha256':record['tree_digest'],
            'execution_dependencies':execution_dependencies(relative,manifest.get('task','motion')),
            'modules':{str(Path(root)/name):sha for name,sha in relative.items()},
            'PPO_sha256':record['PPO']['sha256'],'dependencies':record['dependencies']}
    return data


def reference(folder):
    path=Path(folder)/'identity.json'
    if not path.is_file():return {'status':'MISSING_EVIDENCE','source_identity_reference':str(path.resolve()),'scope':'identity write unavailable; never treat as verified'}
    return {'source_identity_reference':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'scope':'derive module views from recorded identity; not live source'}
