"""Evidence fixtures represent runtime artifacts without Isaac or online PPO."""
import hashlib
import json
import pytest

@pytest.fixture
def complete_smoke_fixture():
    def write(folder,spec_path,updates):
        spec=json.loads(spec_path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        def save(name,value):
            path=folder/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(value))
        save('source_snapshot/spec.json',spec)
        save('manifest.json',{'source_sha256':spec.get('source_sha256'),'spec_sha256':sha(folder/'source_snapshot/spec.json')})
        save('terminal_report.json',{'status':'COMPLETED','actual_updates':updates,'failure':None})
        checkpoint=folder/'model_fixture.pt';checkpoint.write_bytes(b'CPU wiring checkpoint fixture')
        n=spec.get('evaluation',{}).get('scored_envs',8)
        result={'per_env':[{'env_id':i,'outcome':'completed','continuous_s':1.} for i in range(n)],
            'outcome_counts':{'runtime_fault':0},'checkpoint':str(checkpoint.resolve()),
            'checkpoint_sha256':sha(checkpoint),'source_sha256':spec.get('source_sha256'),
            'asset_sha256':spec.get('asset_sha256'),'spec_sha256':sha(folder/'source_snapshot/spec.json')}
        from native_stand.command_v6.domain.evidence import effective_protocol
        result['effective_protocol']=effective_protocol({},requested_seconds=1,steady_window_s=[.5,1],
            sample_rate_hz=100,scored_envs=n,termination_semantics='CPU fixture first episode')
        save('evaluation_fixture.json',result)
        save('progress.json',{'actual_updates':updates,'actor_parameters_changed':True,
            'evaluations':[{'cases':[{'path':'evaluation_fixture.json'}]}],
            'latest_checkpoint':{'path':str(checkpoint),'sha256':sha(checkpoint)}})
        from native_stand.command_v6.wiring import smoke_certificate
        save('wiring_certificate.json',smoke_certificate(folder,spec))
    return write
