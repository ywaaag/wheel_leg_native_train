"""Record-only source identity: one identity.json per run/validation, no source copy.

Replaces the per-run / per-phase whole-tree ``source_snapshot`` copy with a single
recorded reference: spec identity, checkpoint source, the sorted relative module SHA
map, its tree digest, dependency versions, python interpreter and git commit/dirty.

Reading is record-only: no byte-level replay is guaranteed, and no SHA-mismatch
rejection is performed here. Consumers that still need task-scoped module views
derive them from the single ``relative_modules_sha256`` map at read time (see
``execution_identity``), never from a second stored copy.
"""
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import time
import os
import tempfile
from pathlib import Path

VERSION = "source_identity_v1"
SCOPE = "record-only; source may change after this point; no byte-level replay guaranteed"

# src/native_stand
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
# project root (/home/kellen/wheel_leg_native_train)
PROJECT_ROOT = PACKAGE_ROOT.parents[1]

_DEPS = ("torch", "rsl-rl-lib", "tensordict", "isaaclab", "isaacsim")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    return _sha256(path.read_bytes())


def tree_digest(root: Path = PACKAGE_ROOT) -> tuple[str, dict[str, str]]:
    """Return ``(tree_digest, relative_map)`` for every ``*.py`` under ``root``.

    ``relative_map`` maps ``path.relative_to(root)`` -> sha256, sorted by key.
    ``tree_digest`` is the stable digest of that sorted map, usable as a reference
    key without storing the tree a second time.
    """
    relative = {
        str(p.relative_to(root)): _file_sha(p)
        for p in sorted(root.rglob("*.py"))
    }
    digest = _sha256(
        json.dumps(relative, sort_keys=True, separators=(",", ":")).encode()
    )
    return digest, relative


def dependencies() -> dict[str, str]:
    """Version of external packages recorded once; missing metadata is explicit."""
    out = {}
    for package in _DEPS:
        try:
            out[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            out[package] = "distribution metadata unavailable"
    return out


def git_info(root: Path = PROJECT_ROOT) -> dict:
    """Commit + dirty flag, recorded once. Never raises; unavailable -> UNKNOWN."""
    info = {"commit": "UNKNOWN", "dirty": None}
    try:
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if commit.returncode == 0:
            info["commit"] = commit.stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        if status.returncode == 0:
            info["dirty"] = bool(status.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        info["commit"] = "UNKNOWN"
        info["dirty"] = None
    return info


def exclusive_bytes(path,payload):
    """Atomic, exclusive publication preserving the exact input bytes."""
    path=Path(path);fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        os.link(name,path)
    finally:
        Path(name).unlink(missing_ok=True)


def exclusive_json(path,value):
    exclusive_bytes(path,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode())


def record_identity(spec,output,*,spec_sha256=None,checkpoint_source=None):
    """Atomically record one identity, reuse chain identity when unchanged."""
    from ..completion import write
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    dest=output/'identity.json'
    if dest.exists():raise FileExistsError(dest)
    from .execution_identity import identity
    implementation=identity(spec)
    tree=implementation['location_independent_modules_sha256'];relative=implementation['relative_modules_sha256']
    parent=output.parent/'identity.json'
    previous=json.loads(parent.read_text()) if parent.is_file() else None
    record={'version':VERSION,'scope':SCOPE,'spec_sha256':spec_sha256,
        'checkpoint_source':checkpoint_source,'source_root':str(PACKAGE_ROOT),'python':sys.executable,
        'tree_digest':tree,'dependencies':dependencies(),'git':git_info(),'recorded_at_unix_s':time.time()}
    record['PPO']={'path':implementation['PPO_path'],'sha256':implementation['PPO_sha256']}
    if previous and previous.get('tree_digest')==tree:
        record['source_identity_reference']={'path':str(parent.resolve()),'sha256':_file_sha(parent)}
    else:
        if previous:
            record['source_identity_reference']={'path':str(parent.resolve()),'sha256':_file_sha(parent)}
        else:record['relative_modules_sha256']=relative
        if previous:
            from .experiment_preparation import differences
            before=read_identity(output.parent).get('relative_modules_sha256',{})
            record['phase_source_changes']=differences(before,relative)
            record['strict_same_code_comparison']=False
    exclusive_json(dest,record)
    return record


def read_identity(run):
    run=Path(run);path=run/'identity.json'
    if path.is_file():
        record=json.loads(path.read_text())
        reference=record.get('source_identity_reference')
        if reference:
            parent=Path(reference['path'])
            if _file_sha(parent)!=reference['sha256']:raise ValueError('Recorded source identity reference corrupt')
            inherited=read_identity(parent.parent)
            modules=dict(inherited['relative_modules_sha256'])
            for change in record.get('phase_source_changes',[]):
                if change['after'] is None:modules.pop(change['field'],None)
                else:modules[change['field']]=change['after']
            record['relative_modules_sha256']=modules
        return record
    legacy=run/'source_snapshot/spec.json'
    if legacy.is_file():return {'version':VERSION,'legacy':True,'spec':json.loads(legacy.read_text()),'spec_path':str(legacy)}
    raise FileNotFoundError('Recorded identity unavailable: '+str(run))


def record_configuration(output,spec_path):
    """Persist configuration bytes and execution identity, never executable copies."""
    from ..completion import write
    output=Path(output);spec_path=Path(spec_path)
    requested=json.loads(spec_path.read_text());sha=_file_sha(spec_path)
    folder=output/'source_snapshot';folder.mkdir(parents=True,exist_ok=True)
    destination=folder/'spec.json'
    if destination.exists():raise FileExistsError(destination)
    # Preserve original file-byte SHA without copying any Python/asset bytes.
    exclusive_bytes(destination,spec_path.read_bytes())
    from ..domain.recipe import resolve
    if requested.get('effective_recipe_version')==1:_,effective=resolve(requested)
    else:effective={'requested_interface':requested.get('interface_version'),'recipe':requested.get('student_training'),'scope':'versioned task declaration'}
    write(output/'configuration.json',{'version':'recorded_configuration_v1','requested':requested,'effective':effective,
        'spec_sha256':sha,'source_code_copied_bytes':0})
    identity=record_identity(requested,output,spec_sha256=sha,checkpoint_source={'path':requested.get('source_checkpoint'),'sha256':requested.get('source_sha256')})
    ledger=spec_path.with_name('budget.json')
    if ledger.is_file():
        book=json.loads(ledger.read_text())
        rows=[row for row in book.get('attempts',{}).values() if row.get('output_dir')==str(output.resolve())]
        if len(rows)==1 and rows[0].get('submission_receipt'):
            envelope=rows[0]['submission_receipt']
            exclusive_json(output/'submission_receipt.json',envelope)
            before=envelope['record'].get('execution_identity_at_check',{}).get('location_independent_modules_sha256')
            if before and before!=identity['tree_digest']:
                exclusive_json(output/'startup_source_difference.json',{'before':before,'after':identity['tree_digest'],
                    'strict_same_code_comparison':False,'exact_changed_modules':'UNKNOWN unless prior chain identity recorded',
                    'scope':'startup observed hashes; does not guarantee delayed imports stay unchanged'})
    return {'spec.json':sha}
