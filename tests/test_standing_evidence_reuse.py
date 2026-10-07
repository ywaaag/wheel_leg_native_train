import json

from native_stand.command_v6.tools.preflight import reusable_spec


def test_metadata_only_reuse(tmp_path):
    previous = {'reward': {'pitch_level': -4}, 'action': {'leg_scale_rad': 1.6},
                'experiment': 'old', 'budget': {'formal_updates': 0}}
    path = tmp_path / 'spec.json'
    path.write_text(json.dumps(previous))
    current = {**previous, 'experiment': 'new', 'budget': {'formal_updates': 500}}
    assert reusable_spec(path, current)
    current['reward'] = {'pitch_level': -8}
    assert not reusable_spec(path, current)


def test_action_change_blocks_reuse(tmp_path):
    previous = {'action': {'leg_scale_rad': 1.6}}
    path = tmp_path / 'spec.json'
    path.write_text(json.dumps(previous))
    assert not reusable_spec(path, {'action': {'leg_scale_rad': 0.5}})
