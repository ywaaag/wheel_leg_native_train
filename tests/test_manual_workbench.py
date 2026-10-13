FROZEN_TEST_SCOPE='PORTABLE'
import importlib.util,json,sys
from pathlib import Path
import pytest
# Workbench is intentionally outside shared src so it cannot drift an active A/B.
ROOT=Path(__file__).resolve().parents[1]

def module():
 p=ROOT/'manual_train/recovery/workbench.py'
 if not p.exists():pytest.skip('project tool is tested in project, not src-only copy')
 spec=importlib.util.spec_from_file_location('manual_workbench_fixture',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_config_validates_before_any_training(tmp_path,monkeypatch):
 m=module();root=tmp_path/'project';root.mkdir();cp=root/'cp.pt';cp.write_bytes(b'fixture');parent=root/'spec.json';parent.write_text('{}')
 monkeypatch.setattr(m,'ROOT',root)
 config=tmp_path/'settings.toml'
 text='''purpose="human_test"
mode="swing"
teacher_prefix_s=1.8
formal_updates=100
learning_rate=0.00003
seed=10
chain_wall_s=7200
source_checkpoint="cp.pt"
source_parent_spec="spec.json"
physical_gpu=0
resource_mode="shared"
'''
 config.write_text(text);assert m.settings(config)['formal_updates']==100
 config.write_text(text.replace('physical_gpu=0','physical_gpu=1'))
 with pytest.raises(ValueError,match='GPU0'):m.settings(config)
 config.write_text(text.replace('formal_updates=100','formal_updates=999999'))
 with pytest.raises(ValueError,match='6..300'):m.settings(config)
 config.write_text(text+'unknown=1\n')
 with pytest.raises(ValueError,match='字段'):m.settings(config)

def test_patch_refuses_public_source_drift_instead_of_bypassing_checks(tmp_path):
 m=module();p=tmp_path/'file.py';p.write_text('value=1\n')
 m.patch(p,'value=1','value=2');assert p.read_text()=='value=2\n'
 with pytest.raises(ValueError,match='公共接口变化'):m.patch(p,'absent','anything')
 assert p.read_text()=='value=2\n'

def test_train_without_run_only_calls_public_zero_write_plan(tmp_path,monkeypatch):
 m=module();info=tmp_path/'experiment.json';info.write_text(json.dumps({'bundle':'isolated/src','session':'manual-fixture','spec':'spec.json','run':'run'}))
 monkeypatch.setattr(m,'selected_experiment',lambda path:info);calls=[]
 monkeypatch.setattr(m,'invoke',lambda command,env,**kw:calls.append((command,env)))
 m.train(None,False,None)
 command,env=calls[0];assert 'native_stand.command_v6.supervisor' in command and '--launch' not in command
 assert env['HAPI_SESSION_ID']=='manual-fixture' and env['CUDA_VISIBLE_DEVICES']=='0'
 with pytest.raises(ValueError,match='approve'):m.train(None,True,None)
 assert len(calls)==1
