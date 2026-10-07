import pytest
import torch

from native_stand.command_v6.domain.retention import (
    RetentionBatch, balanced_subset, command_mask, load_reference,
    validate_observed_commands, validate_reference,
)


def batch(commands, ages=(10., 10., 10.)):
    return RetentionBatch(torch.zeros(len(commands), 4), torch.tensor(commands),
                          torch.tensor(ages), {"source": "test"})


def test_retention_mask_excludes_future_commands():
    commands = torch.tensor([[0., 0.], [.5, 0.], [-.5, 0.], [1., 0.]])
    assert command_mask(commands).tolist() == [True, True, True, False]


def test_reference_requires_balanced_tail():
    validate_reference(batch([[0., 0.], [.5, 0.], [-.5, 0.]]))
    with pytest.raises(ValueError, match="balanced"):
        validate_reference(batch([[0., 0.], [0., 0.], [.5, 0.]]))
    with pytest.raises(ValueError, match="episode tail"):
        validate_reference(batch([[0., 0.], [.5, 0.], [-.5, 0.]], ages=(1., 1., 1.)),
                          min_episode_age_s=5.)


def test_reference_is_frozen_and_balanced():
    ref = batch([[0., 0.], [.5, 0.], [-.5, 0.]])
    assert not ref.observations.requires_grad
    validate_reference(ref, min_episode_age_s=5.)


def test_reference_rejects_labels_that_disagree_with_actor_command(tmp_path):
    observations = torch.zeros(3, 150)
    commands = torch.tensor([[0., 0.], [.5, 0.], [-.5, 0.]])
    ages = torch.full((3,), 4.)
    payload = {'observations': observations, 'commands': commands,
               'episode_age_s': ages, 'min_episode_age_s': 3.,
               'metadata': {'schedule_s': [1., 1., 4., 1.]}}
    path = tmp_path / 'reference.pt'
    torch.save(payload, path)
    with pytest.raises(ValueError, match='labels differ'):
        load_reference(path)
    observations[:, 6] = commands[:, 0] * 2.
    validate_observed_commands(RetentionBatch(observations, commands, ages, payload['metadata']))


def test_balanced_subset_spans_each_command_history():
    commands = torch.tensor([[0., 0.]] * 10 + [[.5, 0.]] * 10 + [[-.5, 0.]] * 10)
    ages = torch.arange(10.).repeat(3)
    ref = RetentionBatch(torch.zeros(30, 150), commands, ages, {})
    chosen = balanced_subset(ref, 3)
    validate_reference(chosen)
    assert chosen.episode_age_s.tolist() == [0., 4., 9.] * 3
