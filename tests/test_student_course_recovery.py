FROZEN_TEST_SCOPE='PROJECT_DATA'
import copy,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
from native_stand.students.course_io import recover_unstarted_block,prepare_block
from native_stand.students.data import sha
ROOT=Path(__file__).resolve().parents[1]
PRIOR=ROOT/'isolated/recovery_continuous_course_20261012/task/task_manifest.json'

def test_recovery_zero_write_and_immutable_prior_accounting(tmp_path):
 ledger=PRIOR.with_name('task_ledger.json');before={p:sha(p) for p in [PRIOR,ledger]}
 old=json.loads(ledger.read_text());r=recover_unstarted_block(PRIOR,tmp_path/'absent','用户新批准修复接线并恢复B',write_files=False)
 assert r['files_written']==0 and not (tmp_path/'absent').exists()
 assert r['preserved_totals']==old['totals'] and r['state']==old['state']
 assert all(sha(p)==h for p,h in before.items())

def test_settled_failed_course_new_reward_preserves_totals_and_old_files(tmp_path):
 from native_stand.students.course_io import recover_failed_block
 from native_stand.students.course import CONTACT_SUFFIX_RECIPE
 prior=ROOT/'isolated/recovery_course_source_binding_repair_20261012/recovered_task/task_manifest.json'
 ledger=prior.with_name('task_ledger.json');before={p:sha(p) for p in (prior,ledger)}
 r=recover_failed_block(prior,tmp_path/'absent','本次新授权无限预算，增加入口后失触成本',write_files=False)
 assert r['files_written']==0 and not (tmp_path/'absent').exists()
 assert r['preserved_totals']==json.loads(ledger.read_text())['totals']
 assert r['requested_manifest']['dynamic_recipe']==CONTACT_SUFFIX_RECIPE
 assert r['requested_manifest']['recovery_origin']['unsaved_updates_not_restored']==85
 assert all(sha(p)==h for p,h in before.items())
 # Publish fixture task outside production isolated tree only via explicit test root.
 import native_stand.students.course_io as io
 from unittest.mock import patch
 with patch.object(io,'PROJECT',tmp_path):
  out=tmp_path/'isolated/task';out.parent.mkdir()
  result=recover_failed_block(prior,out,'explicit test approval',write_files=True)
 s=json.loads(out.joinpath('task_ledger.json').read_text())
 assert s['totals']==r['preserved_totals'] and s['status']=='READY'
 block=tmp_path/'2026_10_12-13_00__contact_fixture'
 prepare_block(result['manifest'],source=r['source'],state=s['state'],index=len(s['blocks']),write_files=True,output=block)
 from native_stand.command_v6.config import validate
 spec=json.loads((block/'spec.json').read_text())
 assert validate(spec)==[] and spec['student_training']['version']==CONTACT_SUFFIX_RECIPE
 assert not spec['recovery_course']['resume'] and spec['budget']['smoke_updates']==12


def test_unsettled_or_started_child_cannot_be_retried(tmp_path,monkeypatch):
 import native_stand.students.course_io as io
 monkeypatch.setattr(io,'PROJECT',tmp_path)
 task=tmp_path/'task';task.mkdir();m=json.loads(PRIOR.read_text());prior_book=json.loads(PRIOR.with_name('task_ledger.json').read_text())
 child=tmp_path/'configs/experiments/2026_10_12-11_17__fixture';child.mkdir(parents=True)
 actual=json.loads(Path(prior_book['active_spec']).read_text());p=child/'spec.json';p.write_text(json.dumps(actual))
 mpath=task/'task_manifest.json';mpath.write_text(json.dumps(m));book=copy.deepcopy(prior_book);book['active_spec']=str(p);(task/'task_ledger.json').write_text(json.dumps(book))
 (child/'budget.json').write_text(json.dumps({'attempts':{'already':{'status':'RUNNING'}},'used':{'formal':0}}))
 with pytest.raises(ValueError,match='unstarted'):recover_unstarted_block(mpath,tmp_path/'new','explicit repair',write_files=True)
 assert not (tmp_path/'new').exists()


def test_frozen_owner_prepares_and_plans_child_using_its_declared_source(tmp_path):
 # Exercise the actual preparer, public supervisor and identity path in a subprocess.
 src=ROOT/'src/native_stand';snapshot=tmp_path/'parent/source_snapshot';snapshot.mkdir(parents=True)
 shutil.copytree(src,snapshot/'native_stand',ignore=shutil.ignore_patterns('__pycache__'))
 output=tmp_path/'2026_10_12-12_00__source_dispatch_fixture'
 code='''import json,subprocess,sys
from pathlib import Path
from native_stand.students.course_io import prepare_block,submission_environment
from native_stand.students.course import initial_state
s=initial_state();s.update(stage='B',prefix=180,previous_prefix=180)
r=prepare_block(Path(sys.argv[1]),state=s,output=Path(sys.argv[2]),write_files=True)
p=Path(r['spec']);decl=json.load(open(p));assert decl['execution_source_root']==sys.argv[3]
import native_stand.students.course_io as fixture_io
fixture_io.PROJECT=Path(sys.argv[3]).parent.parent # explicit temporary source fixture, not production rule relaxation
cmd=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',str(p),'--output-dir',str(p.parent/'NO_RUN')]
child=subprocess.run(cmd,env=submission_environment(p),capture_output=True,text=True)
assert child.returncode==0,child.stderr
result=json.loads(child.stdout);assert result['preflight']['execution_identity']['actual_execution_root']==decl['execution_source_root']
assert not (p.parent/'NO_RUN').exists()
print('frozen owner/public child plan matched; no simulation')
'''
 env={**os.environ,'PYTHONPATH':str(snapshot),'PYTHONDONTWRITEBYTECODE':'1'}
 r=subprocess.run([sys.executable,'-c',code,str(PRIOR),str(output),str(snapshot)],env=env,cwd=tmp_path,capture_output=True,text=True)
 assert r.returncode==0,r.stderr
 assert 'matched' in r.stdout
