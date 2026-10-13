"""Fresh student networks, bounded mean and unsquashed Gaussian sampling."""
import torch
from torch import nn
from .interface import ACTOR_DIM,CRITIC_DIM,VERSION
class Student(nn.Module):
    is_recurrent=False
    def __init__(self,actor=True,version=VERSION):
        super().__init__();self.is_actor=actor;self.interface_version=version
        if version not in (VERSION,"multiskill_mcu_v2"):raise ValueError("Unknown student interface version")
        dims=([31,128,64,32,6] if actor else [40,256,128,64,1]) if version=="multiskill_mcu_v2" else ([ACTOR_DIM,256,128,64,6] if actor else [CRITIC_DIM,256,128,64,1])
        layers=[]
        for i,(a,b) in enumerate(zip(dims,dims[1:])):
            layers.append(nn.Linear(a,b))
            if i<len(dims)-2:layers.append(nn.ELU(alpha=1.))
        self.mlp=nn.Sequential(*layers)
        if actor:self.log_std=nn.Parameter(torch.tensor([.05/1.5,.05/1.5,2/100,.05/1.5,.05/1.5,2/100]).log())
    def mean(self,x):return self.mlp(x).tanh()
    def distribution(self,x):return torch.distributions.Normal(self.mean(x),self.log_std.exp())
    def forward(self,x,stochastic_output=False):
        if isinstance(x,dict) or hasattr(x,'keys'):x=x['student_actor' if self.is_actor else 'student_critic']
        if not self.is_actor:return self.mlp(x)
        if stochastic_output:
            self._current_distribution=self.distribution(x)
            return self._current_distribution.sample()
        return self.mean(x)
    def log_prob(self,x,raw_action):return self.distribution(x).log_prob(raw_action).sum(-1)

    def get_hidden_state(self):return None
    def reset(self,dones=None):pass
    def update_normalization(self,obs):pass
    def get_output_log_prob(self,raw):return self._current_distribution.log_prob(raw).sum(-1)
    @property
    def output_distribution_params(self):return (self._current_distribution.mean,self._current_distribution.stddev)
    @property
    def output_entropy(self):return self._current_distribution.entropy().sum(-1)
    @property
    def output_mean(self):return self._current_distribution.mean
    @property
    def output_std(self):return self._current_distribution.stddev
    @staticmethod
    def get_kl_divergence(old,new):
        return torch.distributions.kl_divergence(torch.distributions.Normal(*old),torch.distributions.Normal(*new)).sum(-1)

def load(path,role=None):
    data=torch.load(path,map_location='cpu',weights_only=False)
    if data.get('interface_version') not in (VERSION,'multiskill_mcu_v2') or (role and data['role']!=role):raise ValueError('student identity/role differs')
    if data.get('recipe_version'):
        from .training_recipe import declaration
        recipe=declaration(data['recipe_version'],source_actor_sha256=data.get('source_sha256'))
        if data.get('temporal_regularization') is not None:
            from .temporal import declaration as temporal_declaration
            if data['temporal_regularization']!=temporal_declaration(data['temporal_regularization'].get('arm')):raise ValueError('temporal checkpoint declaration differs')
            recipe['milestones']=[50,100]
        if data.get('training_recipe')!=recipe:raise ValueError('student training checkpoint recipe identity differs')
        for key in ('source_sha256','dataset_sha256','manifest_sha256','asset_sha256','spec_sha256','source_code_sha256'):
            if not isinstance(data.get(key),str) or len(data[key])!=64:raise ValueError('training checkpoint missing bound '+key)
        if data['source_sha256']!=recipe['source_actor_sha256'] or data.get('BC_coefficient')!=0. or data.get('fixed_std') is not True:raise ValueError('student trained checkpoint intervention differs')
    with torch.random.fork_rng(devices=[]):
        actor=Student(True,version=data["interface_version"])
        actor.load_state_dict(data['actor'])
    return actor,data

def ppo_initialization(path):
    """Actor only; new critic and optimizer. BC Adam never imported."""
    actor,data=load(path);critic=Student(False,version=data["interface_version"])
    optimizer=torch.optim.Adam(list(actor.parameters())+list(critic.parameters()),lr=3e-5)
    return actor,critic,optimizer
