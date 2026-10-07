import json

import pytest

from native_stand.command_v6.completion import write
from native_stand.command_v6.tools import completion


def test_notify_only_does_not_rebuild_report_or_wait(tmp_path,monkeypatch,capsys):
    write(tmp_path/'manifest.json',{'hapi_session':'current-session'})
    calls=[]
    monkeypatch.setattr(completion,'finalize_report',lambda *_:pytest.fail('notify-only regenerated report'))
    monkeypatch.setattr(completion,'notify',lambda run:calls.append(run) or {'status':'sent','event_id':'fixture'})
    completion.main(['--run-dir',str(tmp_path),'--notify-only','--expected-session','current-session'])
    result=json.loads(capsys.readouterr().out)
    assert calls==[tmp_path]
    assert result['report_regenerated'] is False and result['simulation']==result['ppo']==0


def test_notification_session_mismatch_rejected_before_hook(tmp_path,monkeypatch):
    write(tmp_path/'manifest.json',{'hapi_session':'old-session'})
    monkeypatch.setattr(completion,'notify',lambda *_:pytest.fail('stale target was notified'))
    monkeypatch.setattr(completion,'finalize_report',lambda *_:pytest.fail('stale target generated report'))
    with pytest.raises(SystemExit) as error:
        completion.main(['--run-dir',str(tmp_path),'--notify-only','--expected-session','current-session'])
    assert error.value.code==2
    assert not (tmp_path/'hapi_notification.json').exists()


def test_notification_and_review_operations_cannot_be_combined(tmp_path):
    with pytest.raises(SystemExit) as error:
        completion.main(['--run-dir',str(tmp_path),'--notify-only','--acknowledge-review'])
    assert error.value.code==2
