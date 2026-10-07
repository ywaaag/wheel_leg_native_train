import importlib.util
import json
from pathlib import Path

import pytest
import torch

from native_stand.recovery.standing import retention_sample_indices

ROOT=Path(__file__).resolve().parents[1]


def test_uniform_coverage_count_validity_and_rng():
    mask=torch.ones(8192,dtype=torch.bool)
    rng=torch.get_rng_state().clone()
    first=retention_sample_indices(mask,256,'first')
    uniform=retention_sample_indices(mask,256,'uniform_rollout')
    assert first.tolist()==list(range(256))
    assert len(uniform.unique())==256 and uniform.min()==16 and uniform.max()==8176
    assert torch.equal(rng,torch.get_rng_state())
    mask[::3]=False
    indices=retention_sample_indices(mask,256,'uniform_rollout')
    assert mask[indices].all() and len(indices.unique())==256
    assert indices[-1]>8000


def test_empty_and_small_selection():
    assert not len(retention_sample_indices(torch.zeros(8,dtype=torch.bool),256,'uniform_rollout'))
    mask=torch.tensor([False,True,False,True])
    assert retention_sample_indices(mask,256,'uniform_rollout').tolist()==[1,3]
    with pytest.raises(ValueError):retention_sample_indices(mask,2,'unknown')


def test_optimizer_hook_keeps_selected_observations_metadata_aligned():
    import copy
    from tensordict import TensorDict
    from native_stand.command_v6.learning import model
    from native_stand.recovery.standing import StandingRetention
    obs=TensorDict({'policy':torch.randn(32,25),'history':torch.randn(32,125)},[32])
    actor=model(obs,actor=True,spec={'ppo':{'hidden_dims':[16]}})
    teacher=copy.deepcopy(actor)
    retention=StandingRetention(actor,teacher,coefficient=.02,max_samples=4,max_grad_norm=1.,
                                sample_selection='uniform_rollout')
    optimizer=torch.optim.SGD(actor.parameters(),lr=1e-5)
    optimizer.register_step_pre_hook(retention.before_step)
    retention.begin_rollout(1,phase='formal')
    meta=torch.stack((torch.arange(32),torch.zeros(32),torch.zeros(32)),-1)
    mask=torch.ones(32,dtype=torch.bool);mask[5]=False
    retention.capture(obs,mask,metadata=meta)
    indices=retention_sample_indices(mask,4,'uniform_rollout')
    optimizer.zero_grad();actor(obs,stochastic_output=False).square().mean().backward()
    rng=torch.get_rng_state().clone();optimizer.step()
    torch.testing.assert_close(retention.observations['policy'],obs['policy'][indices])
    assert retention.selected_metadata[:,0].tolist()==indices.tolist()
    assert torch.equal(rng,torch.get_rng_state())


def test_prepared_pair_differs_only_in_selection_and_metadata(tmp_path):
    definition=importlib.util.spec_from_file_location('coverage_prepare',ROOT/'scripts/prepare_recovery_coverage.py')
    module=importlib.util.module_from_spec(definition);definition.loader.exec_module(module)
    parent=ROOT/'configs/experiments/recovery_r0_hold10_from50_20261007/spec.json'
    name='2026_10_7-14_27__pair'
    cases=module.prepare(parent,tmp_path/name,'test',False)
    a,b=cases['A_first'][0],cases['B_uniform'][0]
    for k in ['reward','ppo','control','action','ground','curriculum','evaluation']:
        assert a[k]==b[k]
    ar=a['recovery']['standing_task']['retention'].copy()
    br=b['recovery']['standing_task']['retention'].copy()
    assert ar.pop('sample_selection')=='first' and br.pop('sample_selection')=='uniform_rollout'
    assert ar==br and ar['coefficient']==.02 and ar['max_samples_per_rollout']==256
    s=cases['source_capability'][0]
    assert Path(s['execution_source_root'])==ROOT/'src'
    assert len(s['evaluation_requests'])==4
    from types import SimpleNamespace
    from native_stand.command_v6.tools.evaluate_checkpoint import batch_plan
    p=tmp_path/name/'source_capability/spec.json'
    plan=batch_plan(SimpleNamespace(spec=p,output=tmp_path/'fresh',attempt_id=None),s)
    assert all(r['effective_protocol']['requested_seconds']==10. for r in plan['requests'])
    assert not (tmp_path/'fresh').exists()
