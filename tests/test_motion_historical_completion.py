"""Historical reporting is independent of a new-run recovery permission."""
FROZEN_TEST_SCOPE='PORTABLE'
import json
import copy
import hashlib
import pytest
from native_stand.command_v6.tools import motion_recovery_certificate as module


def test_frozen_report_rejects_receipt_or_archive_tampering(tmp_path,monkeypatch):
    snapshot=tmp_path/'snapshot';snapshot.mkdir()
    spec={'engineering_recovery':{'certificate':str(tmp_path/'cert.json'),'sha256':None}}
    monkeypatch.setattr(module,'behavior',lambda s:{'behavior':'fixed'})
    code=snapshot/'config.py';code.write_text('frozen implementation')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'spec_sha256':None,'source_snapshot_sha256':{'config.py':digest(code)},
        'execution_identity':{'execution_dependencies':{'sha':'frozen'},'PPO_sha256':'ppo',
            'dependencies':{'torch':'version'},'modules':{'/retired/src/config.py':digest(code)}}}
    record={'status':'READY','version':module.VERSION,
        'behavior_sha256':module.stable_hash({'behavior':'fixed'}),
        'facts':{'code_migration':{'target_identity':copy.deepcopy(manifest['execution_identity'])}},
        'inputs_sha256':{'/retired/src/config.py':digest(code)}}
    cert=tmp_path/'cert.json';cert.write_text(json.dumps(record))
    spec['engineering_recovery']['sha256']=digest(cert)
    (snapshot/'spec.json').write_text(json.dumps(spec));manifest['spec_sha256']=digest(snapshot/'spec.json')
    assert module.historical_report_certificate(spec,manifest,snapshot)['status']=='READY'
    wrong=copy.deepcopy(manifest);wrong['execution_identity']['PPO_sha256']='different'
    with pytest.raises(ValueError,match='dependency'):
        module.historical_report_certificate(spec,wrong,snapshot)
    code.write_text('tampered archive')
    with pytest.raises(ValueError,match='SHA'):
        module.historical_report_certificate(spec,manifest,snapshot)


def test_corrected_report_does_not_overwrite_or_notify(tmp_path):
    from native_stand.command_v6.completion import finalize_report
    from native_stand.command_v6.tools.completion import main
    run=tmp_path/'run';run.mkdir();out=tmp_path/'corrected';out.mkdir()
    with pytest.raises(FileExistsError):finalize_report(run,corrected_output=out)
    with pytest.raises(ValueError,match='outside'):
        finalize_report(run,corrected_output=run/'nested')
    with pytest.raises(SystemExit):main(['--run-dir',str(run),'--corrected-output',str(out),'--notify'])
