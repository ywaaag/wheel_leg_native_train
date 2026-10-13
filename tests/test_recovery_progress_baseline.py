import json
import pytest
from native_stand.command_v6.tools.recovery_progress_baseline import load
from native_stand.recovery.min_height import ProgressGuard


def write_fixture(folder):
    manifest={'spec_sha256':'a'*64,'source_sha256':'b'*64,'asset_sha256':'c'*64}
    row={'recovery_s':.2,'entry_confirmation_index':19,
         'control_diagnostics_100hz':[[0.]*54 for _ in range(400)]}
    result={'spec_sha256':manifest['spec_sha256'],'checkpoint_sha256':manifest['source_sha256'],
            'per_env':[row]}
    compact={k:v for k,v in row.items() if k!='control_diagnostics_100hz'}
    entry={'role':'source','checkpoint_sha256':manifest['source_sha256'],
           'evaluation':'evaluation_source.json','result':{'per_env':[compact]}}
    (folder/'manifest.json').write_text(json.dumps(manifest))
    (folder/'evaluation_source.json').write_text(json.dumps(result))
    (folder/'candidate_registry.json').write_text(json.dumps([entry]))
    # Load the persisted summary, matching the actual source->smoke boundary.
    return json.loads((folder/'candidate_registry.json').read_text())[0],manifest


def test_guard_uses_raw_persisted_source_not_compact_registry(tmp_path):
    entry,identity=write_fixture(tmp_path)
    config={'entry_count_drop':2,'confirmations':2,'delta_min_rad_s':10.,'alternation_fraction_min':.8,'limit_fraction_min':.5}
    with pytest.raises(ValueError,match='control trace missing'):ProgressGuard(entry['result'],config)
    raw,evidence=load(tmp_path,entry,**identity)
    guard=ProgressGuard(raw,config)
    assert guard.source_entries==1 and guard.source_oscillation==[False]
    assert evidence['path'].endswith('evaluation_source.json') and len(evidence['sha256'])==64
    assert not guard.observe(raw)['stop']


@pytest.mark.parametrize('field',['spec_sha256','source_sha256','asset_sha256'])
def test_loader_rejects_manifest_identity_conflict(tmp_path,field):
    entry,identity=write_fixture(tmp_path);identity[field]='d'*64
    with pytest.raises(ValueError,match='identity differs'):load(tmp_path,entry,**identity)


def test_raw_missing_trace_remains_error_not_measured_zero(tmp_path):
    entry,identity=write_fixture(tmp_path)
    result=json.loads((tmp_path/'evaluation_source.json').read_text())
    result['per_env'][0].pop('control_diagnostics_100hz')
    (tmp_path/'evaluation_source.json').write_text(json.dumps(result))
    with pytest.raises(ValueError,match='required fields missing'):load(tmp_path,entry,**identity)
