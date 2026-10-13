"""Real subprocess imports bind the child spec, across shared/frozen execution roots."""
FROZEN_TEST_SCOPE='PORTABLE'
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
from native_stand.students.course_io import submission_environment
from native_stand.command_v6.tools.execution_identity import identity

def snapshot(folder):
 src=Path(__import__('native_stand').__file__).resolve().parent
 snap=folder/'source_snapshot';snap.mkdir(parents=True);shutil.copytree(src,snap/'native_stand',ignore=shutil.ignore_patterns('__pycache__'))
 return snap

def run(root,spec):
 code='import json;from native_stand.command_v6.tools.execution_identity import identity;s=json.load(open('+repr(str(spec))+'));print(json.dumps(identity(s)))'
 return subprocess.run([sys.executable,'-c',code],cwd=spec.parent,env={**os.environ,'PYTHONPATH':str(root),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)

def test_original_counterexample_and_child_environment_fix(tmp_path,monkeypatch):
 root=Path(__import__('native_stand').__file__).resolve().parent.parent
 bundle=snapshot(tmp_path/'parent');child=tmp_path/'child.json'
 child.write_text(json.dumps({'task':'recovery','effective_recipe_version':1,'execution_source_root':str(bundle)}))
 old=run(root,child)
 assert old.returncode!=0
 # A relocated root additionally checks its real receipt; both reject this wrong child spec.
 assert any(message in old.stderr for message in ('execution_source_root differs from actual loaded project src','frozen execution spec/source receipt identity differs'))
 # Portable fixture project authorization root, leaving actual verification strict.
 monkeypatch.setattr('native_stand.students.course_io.PROJECT',tmp_path)
 env=submission_environment(child,{'PYTHONPATH':str(root),'HAPI_SESSION_ID':'owner','CUDA_VISIBLE_DEVICES':'0'})
 assert env['PYTHONPATH']==str(bundle) and env['HAPI_SESSION_ID']=='owner' and env['CUDA_VISIBLE_DEVICES']=='0'
 fixed=run(env['PYTHONPATH'],child);assert fixed.returncode==0,fixed.stderr
 assert json.loads(fixed.stdout)['actual_execution_root']==str(bundle)

def test_fresh_worker_relocation_receipt_stays_strict(tmp_path):
 declared=Path(__import__('native_stand').__file__).resolve().parent.parent
 snap=snapshot(tmp_path/'worker');s={'task':'recovery','effective_recipe_version':1,'execution_source_root':str(declared)}
 p=snap/'spec.json';p.write_text(json.dumps(s))
 modules={str(x.relative_to(snap/'native_stand')):hashlib.sha256(x.read_bytes()).hexdigest() for x in (snap/'native_stand').rglob('*.py')}
 m={'spec_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'declared_execution_source_root':str(declared),'execution_modules_sha256':modules}
 receipt=snap.parent/'manifest.json';receipt.write_text(json.dumps(m))
 r=run(snap,p);assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['frozen_identity']['declared_source_root']==str(declared)
 m['spec_sha256']='0'*64;receipt.write_text(json.dumps(m));bad=run(snap,p)
 assert bad.returncode!=0 and 'receipt identity differs' in bad.stderr

def test_child_source_tampering_not_hidden_by_environment(tmp_path,monkeypatch):
 bundle=snapshot(tmp_path/'parent');p=tmp_path/'child.json';p.write_text(json.dumps({'execution_source_root':str(tmp_path/'absent')}))
 monkeypatch.setattr('native_stand.students.course_io.PROJECT',tmp_path)
 with pytest.raises(ValueError,match='missing'):submission_environment(p)
