FROZEN_TEST_SCOPE='PORTABLE'
import pytest
import torch
from native_stand.command_v6.domain.observation_diagnostics import summarize,labels

def test_time_variance_not_confused_with_episode_offset():
    x=torch.zeros(4,150);x[2:,0]=2.;x[:,1]=torch.tensor([0.,2.,0.,2.])
    d=summarize(x,episode_ids=['a','a','b','b'])['dimensions']
    assert d[0]['variance']==1 and d[0]['within_episode_time_variance']==0
    assert d[0]['between_episode_mean_variance']==1
    assert d[1]['within_episode_time_variance']==1 and d[1]['between_episode_mean_variance']==0

def test_actual_inputs_unmodified_rng_unchanged():
    x=torch.arange(300.).reshape(2,150);old=x.clone();rng=torch.get_rng_state().clone()
    r=summarize(x,episode_ids=[('env0',1),('env0',1)])
    assert len(r['dimensions'])==150 and len(labels())==150
    assert torch.equal(x,old) and torch.equal(torch.get_rng_state(),rng)
    assert labels()[0]=='current/angular_body_x' and labels()[149].endswith('previous_clipped_action_5')

def test_empty_single_sample_and_nonfinite_are_explicit():
    assert summarize(torch.empty(0,150),episode_ids=[])['status']=='NO_SAMPLES'
    d=summarize(torch.zeros(1,150),episode_ids=['a'])['dimensions'][0]
    assert d['within_episode_time_variance'] is None and d['near_constant_in_observed_samples']
    with pytest.raises(ValueError):summarize(torch.full((2,150),float('nan')),episode_ids=['a','a'])
    with pytest.raises(ValueError):summarize(torch.zeros(2,25),episode_ids=['a','a'])
