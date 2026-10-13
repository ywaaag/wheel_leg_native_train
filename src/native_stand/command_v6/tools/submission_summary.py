"""Summarize frozen authorization and one existing handshake, never query progress."""
import argparse
import json
from pathlib import Path
from .experiment_preparation import checked_input


def summarize(spec_path,receipt_path,handshake_path):
    inputs={}
    def read(path):
        path,sha=checked_input(path);inputs[path]=sha
        return json.loads(Path(path).read_text())
    spec=read(spec_path);receipt=read(receipt_path);handshake=read(handshake_path)
    expected=inputs[str(Path(spec_path).resolve())]
    if receipt.get('spec_sha256')!=expected:raise ValueError('Authorization receipt must bind spec SHA')
    if handshake.get('hapi_session') and spec.get('authorization',{}).get('hapi_session')!=handshake['hapi_session']:
        raise ValueError('Handshake owner differs')
    for data in (receipt,handshake):
        if data.get('spec_sha256') is not None and data['spec_sha256']!=expected:raise ValueError('Submission spec SHA differs')
    return {'spec_sha256':expected,'source_checkpoint':spec.get('source_checkpoint'),'source_sha256':spec.get('source_sha256'),
        'phase_limits':spec['budget'],'cumulative_quota_reference':spec.get('cumulative_quota_reference'),
        'device':spec.get('device'),'current_declared_stage':spec['curriculum']['active_stage'],
        'handshake':handshake,'handshake_spec_identity': 'BOUND' if handshake.get('spec_sha256')==expected else 'MISSING_EVIDENCE',
        'formal_first_update_verified':handshake.get('formal_first_update_verified',False) is True and handshake.get('spec_sha256')==expected,
        'authorized_owner':spec.get('authorization',{}).get('hapi_session') if isinstance(spec.get('authorization'),dict) else None,
        'notifications':spec.get('notifications'),'inputs_sha256':inputs,'files_written':0,
        'scope':'frozen handoff evidence only; not live process or current progress verification'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('spec','receipt','handshake'):p.add_argument('--'+flag,type=Path,required=True)
    a=p.parse_args();print(json.dumps(summarize(a.spec,a.receipt,a.handshake),indent=2,allow_nan=False))

if __name__=='__main__':main()
