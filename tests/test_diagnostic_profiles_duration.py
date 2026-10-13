import json
from pathlib import Path
import pytest
from native_stand.command_v6.domain.diagnostic_profiles import resolve
from native_stand.command_v6.tools.recovery_batch import validate_request
from native_stand.command_v6.tools.prepare_checkpoint_diagnostic import prepare

ROOT=Path(__file__).resolve().parents[1]

def test_rising_omitted_seconds_uses_task_duration():
    spec=json.loads((ROOT/'configs/experiments/2026_10_7-15_58__recovery_rise_low_from50/spec.json').read_text())
    result=validate_request(spec,{'checkpoint':'model.pt','sha256':'a'*64,'target':[0,0],'family':'R1'})
    assert result['seconds']==23.
    with pytest.raises(ValueError):validate_request(spec,{**result,'seconds':10.})

def test_profiles_declare_fields_and_missing_requirements():
    assert resolve('full_transition')['full_trace']
    assert resolve('failure_tail')['scope'].startswith('last')
    with pytest.raises(ValueError,match='lacks required'):resolve('summary',required=['geometry'])
    with pytest.raises(ValueError):resolve('full_transition',required=['geometry'],task='motion')
    assert resolve(None) is None
    with pytest.raises(ValueError):resolve(None,required=['geometry'])

def test_diagnostic_preparation_is_exclusive_and_unauthorized(tmp_path):
    parent=ROOT/'configs/experiments/recovery_r0_hold10_from50_20261007/spec.json'
    spec=json.loads(parent.read_text())
    output=tmp_path/'2026_10_7-21_00__checkpoint_diagnostic'
    result=prepare(parent,spec['source_checkpoint'],output,family='R0',
        protocol=spec['evaluation']['protocol_identity'],session='fixture',physical_gpu=1,gpu_uuid='GPU-fixture')
    assert not result['runtime_authorized']
    book=json.loads((output/'budget.json').read_text())
    assert book['authorization']=='UNAUTHORIZED' and book['limits']['formal']==0
    with pytest.raises(FileExistsError):prepare(parent,spec['source_checkpoint'],output,family='R0',
        protocol=spec['evaluation']['protocol_identity'],session='fixture',physical_gpu=1,gpu_uuid='GPU-fixture')
