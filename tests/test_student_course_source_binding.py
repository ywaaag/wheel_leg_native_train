"""Subprocess source identity records actual shared imports, without source copies."""
FROZEN_TEST_SCOPE='PORTABLE'
import json,os,subprocess,sys
from pathlib import Path
from native_stand.students.course_io import submission_environment


def test_child_does_not_reuse_parent_bundle_and_records_difference(tmp_path):
 root=Path(__import__('native_stand').__file__).resolve().parent.parent
 child=tmp_path/'spec.json';child.write_text(json.dumps({'effective_recipe_version':1,'execution_source_root':str(tmp_path/'old_bundle')}))
 environment=submission_environment(child,{'PYTHONPATH':str(tmp_path/'old_bundle'),'HAPI_SESSION_ID':'owner','CUDA_VISIBLE_DEVICES':'0'})
 assert environment['PYTHONPATH']==str(root)
 assert environment['HAPI_SESSION_ID']=='owner' and environment['CUDA_VISIBLE_DEVICES']=='0'
 code='import json,sys;from native_stand.command_v6.tools.execution_identity import identity;print(json.dumps(identity(json.load(open(sys.argv[1])))))'
 r=subprocess.run([sys.executable,'-c',code,str(child)],cwd=tmp_path,env={**os.environ,**environment,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
 assert r.returncode==0,r.stderr
 record=json.loads(r.stdout)
 assert record['actual_execution_root']==str(root) and record['declared_source_differs']
 assert not list(tmp_path.rglob('*.py'))
