FROZEN_TEST_SCOPE='PORTABLE'
import importlib.util,json
from pathlib import Path
import pytest

def module():
 p=Path(__file__).resolve().parents[1]/'scripts/subscribe_training_terminal.py'
 spec=importlib.util.spec_from_file_location('terminal_subscription',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def fixture(tmp_path):
 m=module();s=tmp_path/'spec.json';s.write_text(json.dumps({'notifications':{'enabled':False}}))
 manifest={'attempt_id':'attempt','hapi_session':'current','notification_route':{'owner_session':'current','target_session':'current'},'spec_path':str(s),'spec_sha256':m.sha(s)}
 (tmp_path/'manifest.json').write_text(json.dumps(manifest));(tmp_path/'completion_report.md').write_text('complete')
 (tmp_path/'report_ready.json').write_text(json.dumps({'event_id':'event','report_sha256':m.sha(tmp_path/'completion_report.md')}))
 (tmp_path/'analysis.json').write_text(json.dumps({'status':'COMPLETED'}))
 return m,m.subscription(tmp_path,'current','user explicitly enables terminal notification','unit')

def test_late_authorization_delivers_once_without_spec_edit(tmp_path):
 m,r=fixture(tmp_path);before=(tmp_path/'spec.json').read_bytes();sent=[]
 send=lambda session,msg:sent.append((session,msg)) or {'status':'sent'}
 assert m.deliver(r,send)['status']=='sent';assert m.deliver(r,send)['status']=='sent'
 assert len(sent)==1 and (tmp_path/'spec.json').read_bytes()==before
 assert '不授权自动续训' not in sent[0][1]
 assert '按当前有效用户授权处理后续工作' in sent[0][1]

def test_unknown_delivery_not_retried(tmp_path):
 m,r=fixture(tmp_path)
 def fail(*a):raise TimeoutError('unknown')
 assert m.deliver(r,fail)['status']=='unknown_delivery'
 assert m.deliver(r,lambda *a:pytest.fail('duplicate'))['status']=='unknown_delivery'

def test_manifest_or_report_drift_rejected(tmp_path):
 m,r=fixture(tmp_path);(tmp_path/'completion_report.md').write_text('changed')
 with pytest.raises(ValueError,match='SHA'):m.deliver(r,lambda *a:None)
