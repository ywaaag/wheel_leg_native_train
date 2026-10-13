"""Meaningful std initialization invariants; no simulator or project evidence required."""
import copy
from types import SimpleNamespace
import torch
import pytest
from rsl_rl.modules.distribution import GaussianDistribution
from native_stand.recovery.exploration import VERSION,initialize,validate


def config(factor=.5):
    return {'version':VERSION,'wheel_std_multiplier':factor,'channels':[2,5],
        'apply_phases':['smoke','formal'],'optimizer_moments':'preserve_all','std_parameterization':'positive_scalar'}


class Actor(torch.nn.Module):
    def __init__(self):
        super().__init__();self.mlp=torch.nn.Linear(3,6);self.distribution=GaussianDistribution(6,std_type='scalar')
    def forward(self,x):return self.mlp(x)


def test_only_wheel_std_changes_preserves_mean_adam_and_rng():
    a=Actor();optimizer=torch.optim.Adam(a.parameters(),lr=3e-5)
    # Meaningful existing Adam history, including std parameter.
    loss=a(torch.ones(2,3)).square().sum()+a.distribution.std_param.square().sum()
    loss.backward();optimizer.step();optimizer.zero_grad()
    before=copy.deepcopy(a.state_dict());adam=copy.deepcopy(optimizer.state_dict());rng=torch.get_rng_state().clone()
    x=torch.ones(2,3);mean=a(x).detach().clone();report=initialize(a,config(),wheel_scale_rad_s=100.)
    for name,value in a.state_dict().items():
        expected=before[name].clone()
        if name=='distribution.std_param':expected[[2,5]]*=.5
        torch.testing.assert_close(value,expected,rtol=0,atol=0)
    torch.testing.assert_close(a(x),mean,rtol=0,atol=0)
    torch.testing.assert_close(rng,torch.get_rng_state(),rtol=0,atol=0)
    current=optimizer.state_dict();assert current['param_groups']==adam['param_groups']
    for key,old in adam['state'].items():
        for name,value in old.items():torch.testing.assert_close(current['state'][key][name],value,rtol=0,atol=0)
    assert report['optimizer_moments']=='preserved'
    # New stochastic distribution reflects the change, not a stale cached sample distribution.
    a.distribution.update(a(x));assert torch.equal(a.distribution._distribution.scale[0],a.distribution.std_param)
    assert a.distribution.std_param.requires_grad


def test_a_identity_initialization_and_b_physical_scales():
    a=Actor();before=a.distribution.std_param.clone()
    initialize(a,config(1.),wheel_scale_rad_s=100.)
    torch.testing.assert_close(a.distribution.std_param,before,rtol=0,atol=0)
    r=initialize(a,config(.5),wheel_scale_rad_s=100.)
    assert r['after_physical_wheel_std_rad_s']==pytest.approx([x*.5 for x in r['before_physical_wheel_std_rad_s']])


@pytest.mark.parametrize('field,value',[('channels',[0,3]),('wheel_std_multiplier',.25),('optimizer_moments','clear'),('apply_phases',['source_eval']),('std_parameterization','log')])
def test_rejects_undeclared_intervention(field,value):
    c=config();c[field]=value
    spec={'task':'recovery','initialization':'warmstart','source_input_dim':150,
        'action':{'wheel_scale_rad_s':100.},'ppo':{},'recovery':{'exploration_initialization':c}}
    with pytest.raises(ValueError):validate(spec)
