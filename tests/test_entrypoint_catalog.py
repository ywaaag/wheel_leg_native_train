import importlib.util
import json
from pathlib import Path
import sys

import pytest

from native_stand.command_v6.tools.entrypoints import ENTRIES, historical_cli_guard, main


ROOT = Path(__file__).resolve().parents[1]


def test_only_supervisor_is_current_submission(capsys):
    assert main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert [row['entry'] for row in result['entries'] if row['role'] == 'submission'] == [
        'native_stand.command_v6.supervisor']
    assert all(row['status'] == 'CURRENT' for row in result['entries'])
    assert result['files_written'] == result['simulation'] == result['ppo'] == 0


def test_catalog_entries_exist_and_are_unique():
    assert len({row['entry'] for row in ENTRIES}) == len(ENTRIES)
    for row in ENTRIES:
        if row['entry'].endswith('.py'):
            assert (ROOT / row['entry']).is_file()
        else:
            assert (ROOT / 'src' / (row['entry'].replace('.', '/') + '.py')).is_file()


@pytest.mark.parametrize('entry', [row['entry'] for row in ENTRIES if row['role'] == 'recipe_generator'])
def test_historical_generator_needs_acknowledgment(entry):
    with pytest.raises(SystemExit) as error:
        historical_cli_guard(entry, [])
    assert error.value.code == 2
    historical_cli_guard(entry, ['--historical-replay'])


@pytest.mark.parametrize('args', [[], ['--historical-replay']])
def test_old_runtime_entry_cannot_launch(args):
    with pytest.raises(SystemExit) as error:
        historical_cli_guard('scripts/run_motion_high_speed_preparation.py', args)
    assert error.value.code == 2


@pytest.mark.parametrize('name', ['run_motion_high_speed_preparation', 'prepare_motion_high_speed_course',
                                'prepare_motion_overnight_20261005', 'prepare_motion_endpoint_20261005'])
def test_old_entry_rejects_before_evidence_reads_or_writes(name, monkeypatch):
    module_spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    monkeypatch.setattr(sys, 'argv', [name])
    def forbidden(*args, **kwargs):
        pytest.fail('historical entry touched evidence before rejecting invocation')
    for method in ('read_text', 'read_bytes', 'mkdir', 'write_text'):
        monkeypatch.setattr(Path, method, forbidden)
    with pytest.raises(SystemExit) as error:
        module.main()
    assert error.value.code == 2


def test_high_speed_recipe_never_overwrites_existing_directory(monkeypatch, tmp_path):
    module_spec = importlib.util.spec_from_file_location('old_course', ROOT / 'scripts/prepare_motion_high_speed_course.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    old = tmp_path / 'spec.json'
    old.write_text('immutable old spec')
    monkeypatch.setattr(module, 'OUT', tmp_path)
    monkeypatch.setattr(sys, 'argv', ['old_course', '--historical-replay'])
    with pytest.raises(FileExistsError):
        module.main()
    assert old.read_text() == 'immutable old spec'
