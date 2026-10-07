"""Shared one-shot handshake validation for owned trainer/monitor processes."""
from pathlib import Path
import json
from .tools.health_check import process_identity,digest


def validate_handshake(message, *, spec_path, output, attempt_id, monitor_pid,monitor_started_unix_s=None):
    if message.get('status')!='RUNNING':return {**message,'identity_verified':False,'started':False}
    output=Path(output).resolve()
    errors=[]
    try:
        manifest=json.loads((output/'manifest.json').read_text())
        progress=json.loads((output/'progress.json').read_text())
    except (OSError,ValueError) as exc:
        return {'status':'UNKNOWN','reason':'handshake evidence missing','detail':str(exc),
                'identity_verified':False,'started':False}
    try:
        if manifest.get('spec_sha256')!=digest(spec_path):errors.append('spec SHA')
    except OSError:errors.append('spec missing')
    if manifest.get('attempt_id')!=attempt_id or progress.get('attempt_id')!=attempt_id:errors.append('attempt ID')
    if progress.get('actual_updates',0)<1:errors.append('first PPO update not verified')
    if progress.get('status')!='RUNNING':errors.append('progress not RUNNING')
    if message.get('attempt_id')!=attempt_id or message.get('output_dir')!=str(output):errors.append('message identity')
    if manifest.get('pid')!=message.get('trainer_pid'):errors.append('manifest trainer PID')
    for pid,token,started in ((message.get('trainer_pid'),'train.py',manifest.get('process_started_unix_s')),
                              (monitor_pid,'monitor.py',monitor_started_unix_s)):
        if started is None:errors.append(token+' start identity missing')
        check=process_identity(pid,output_dir=output,attempt_id=attempt_id,command_token=token,
            started_unix_s=started,spec_path=spec_path)
        if check['status']!='OK':errors.append(token+' '+check['status'])
    return ({**message,'status':'UNKNOWN','reason':'handshake identity validation failed','errors':errors,
             'identity_verified':False,'started':False}
            if errors else {**message,'identity_verified':True,'started':True})
