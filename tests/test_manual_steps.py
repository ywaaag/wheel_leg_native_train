"""Human CLI tests: no automatic validation, authorization or launch."""
import importlib.util,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
def module():
 folder=ROOT/'manual_train/recovery';sys.path.insert(0,str(folder))
 try:
  s=importlib.util.spec_from_file_location('manual_steps_test',folder/'steps.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 finally:sys.path.pop(0)

def test_publish_plan_never_calls_subprocess(tmp_path,monkeypatch):
 m=module();bundle=tmp_path/'src/native_stand';bundle.mkdir(parents=True);(bundle/'a.py').write_text('x=1')
 draft=tmp_path/'draft.json';draft.write_text(json.dumps({'folder':str(tmp_path),'bundle':str(bundle.parent),'modules':m.modules(bundle)}))
 monkeypatch.setattr(m.w,'project_path',lambda p:Path(p));monkeypatch.setattr(m,'invoke',lambda *a,**k:pytest.fail('plan called a process'))
 assert m.publish(draft,False)['write'] is False
 (bundle/'a.py').write_text('x=2')
 with pytest.raises(ValueError,match='冻结源码'):m.publish(draft,False)

def test_init_plan_does_not_create_editable_or_invoke_training(tmp_path,monkeypatch):
 m=module();monkeypatch.setattr(m.w,'WORK',tmp_path);monkeypatch.setattr(m.w,'settings',lambda p:{})
 monkeypatch.setattr(m.w,'make_bundle',lambda *a:pytest.fail('plan copied source'))
 assert m.init_source('fixture',False)['simulation']==0
 assert not (tmp_path/'editable').exists()

def test_authorization_requires_explicit_approval_before_reading_files():
 m=module()
 with pytest.raises(ValueError,match='批准说明'):m.authorize('nonexistent',None,True)
