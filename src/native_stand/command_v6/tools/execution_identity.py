"""CPU identities for actual project and external algorithm implementations."""
import hashlib
import importlib.metadata
from pathlib import Path
import sys


def identity(spec):
    root = Path(__file__).resolve().parents[2]
    expected = spec.get('execution_source_root')
    if spec.get('effective_recipe_version') == 1 and expected and Path(expected).resolve() != root.parent.resolve():
        raise ValueError('execution_source_root differs from actual loaded project src')
    modules = {}
    for path in sorted(root.rglob('*.py')):
        modules[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    dependencies = {}
    for package in ('torch', 'rsl-rl-lib', 'tensordict', 'isaaclab', 'isaacsim'):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = 'distribution metadata unavailable'
    distribution = importlib.metadata.distribution('rsl-rl-lib')
    algorithm = Path(distribution.locate_file('rsl_rl/algorithms/ppo.py')).resolve()
    return {'source_root': str(root.parent.resolve()), 'python': sys.executable,
            'modules': modules, 'dependencies': dependencies,
            'PPO_path': str(algorithm), 'PPO_sha256': hashlib.sha256(algorithm.read_bytes()).hexdigest()}
