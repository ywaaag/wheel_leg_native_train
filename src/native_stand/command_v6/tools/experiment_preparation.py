"""Shared file-boundary helpers for exclusive, auditable experiment preparation."""
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_input(path, expected=None):
    path=Path(path).resolve()
    actual=digest(path)
    if expected is not None and actual!=expected:
        raise ValueError('input SHA differs: '+str(path))
    return str(path), actual


def differences(before, after, prefix=''):
    if isinstance(before,dict) and isinstance(after,dict):
        rows=[]
        for key in sorted(set(before)|set(after)):
            name=f'{prefix}.{key}' if prefix else key
            if key not in before or key not in after:
                rows.append({'field':name,'before':before.get(key),'after':after.get(key)})
            else:rows.extend(differences(before[key],after[key],name))
        return rows
    return [] if before==after else [{'field':prefix,'before':before,'after':after}]


def publish(output, payloads, inputs, *, completion_marker=False, raw_files=None, serialized_files=None):
    """Fresh transactional publication, marker last. Opaque JSON bytes preserve authored
    Infinity limits; ordinary payloads remain strict finite JSON. raw_files requires
    source SHA; serialized_files requires the prepared content SHA. Neither is an
    authorization or semantic validation bypass. Process errors roll back; a power
    loss requires detecting a missing marker rather than claiming completeness.
    """
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    encoded={}
    def validate_name(name):
        path=Path(name)
        if (path.is_absolute() or '..' in path.parts or len(path.parts)>2 or path.suffix!='.json'
                or name=='publication_complete.json' or str(path)!=name):
            raise ValueError('payload must be a JSON file at root or one semantic arm level')
    for name,value in payloads.items():
        validate_name(name)
        encoded[name]=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    raw_inputs={}
    for name,(source,expected) in (raw_files or {}).items():
        validate_name(name)
        if name in encoded:raise ValueError('duplicate publication destination')
        if not isinstance(expected,str) or len(expected)!=64:raise ValueError('raw input expected SHA required')
        source,actual=checked_input(source,expected)
        if source in inputs and inputs[source]!=actual:raise ValueError('raw input conflicts with frozen inputs')
        raw_inputs[source]=actual
        encoded[name]=Path(source).read_bytes()
        if hashlib.sha256(encoded[name]).hexdigest()!=actual:raise ValueError('raw input changed during read')
    for name,(content,expected) in (serialized_files or {}).items():
        validate_name(name)
        if name in encoded:raise ValueError('duplicate publication destination')
        if not isinstance(content,bytes) or hashlib.sha256(content).hexdigest()!=expected:
            raise ValueError('serialized artifact SHA differs')
        encoded[name]=content
    if any(str(Path(name).parent) in encoded for name in encoded):raise ValueError('payload path conflict')
    if completion_marker:
        encoded['publication_complete.json']=json.dumps({'status':'COMPLETE','files':{
            name:hashlib.sha256(value).hexdigest() for name,value in encoded.items()}},indent=2).encode()+b'\n'
    for path, expected in {**inputs,**raw_inputs}.items():checked_input(path,expected)
    output.mkdir(parents=True,exist_ok=False)
    created=[];directories=[]
    try:
        for name, value in encoded.items():
            path=output/name
            if path.parent!=output and not path.parent.exists():
                path.parent.mkdir();directories.append(path.parent)
            with path.open('xb') as stream:
                created.append(path)
                stream.write(value)
    except BaseException:
        for path in reversed(created):path.unlink()
        for path in reversed(directories):path.rmdir()
        output.rmdir()
        raise


def verify_publication(spec_path,*,authorized=False):
    """Single-arm and enclosing multi-arm markers; old declarations explicit legacy.

    Authorization may replace spec/budget only against its bound receipt. Mutable
    budget SHA after reservation is not claimed equal to the authorization snapshot.
    """
    spec_path=Path(spec_path).resolve();markers=[p for p in
        (spec_path.parent/'publication_complete.json',spec_path.parent.parent/'publication_complete.json') if p.is_file()]
    if not markers:return {'status':'LEGACY_NO_MARKER','markers':[]}
    result=[]
    for marker in markers:
        data=json.loads(marker.read_text());files=data.get('files')
        if data.get('status')!='COMPLETE' or not isinstance(files,dict) or not files:raise ValueError('publication incomplete')
        if str(spec_path.relative_to(marker.parent)) not in files:raise ValueError('publication does not cover spec')
        for relative,expected in files.items():
            path=(marker.parent/relative).resolve()
            if not path.is_relative_to(marker.parent):raise ValueError('publication reference escapes root')
            if authorized and path.name in ('spec.json','budget.json'):
                receipt_path=path.parent/'authorization_receipt.json'
                if receipt_path.is_file():
                    receipt=json.loads(receipt_path.read_text())
                    if path.name=='spec.json':checked_input(path,receipt['spec_sha256'])
                    else:
                        book=json.loads(path.read_text())
                        if book.get('authorization')!='AUTHORIZED' or book.get('approval_id')!=receipt.get('approval_id'):
                            raise ValueError('authorized ledger receipt differs')
                    continue
            checked_input(path,expected)
        result.append({'path':str(marker),'sha256':digest(marker),'files':len(files)})
    return {'status':'VERIFIED','markers':result}
