"""Checkpoint structure and strict loading shared by CPU, health and runtime."""
from collections.abc import Mapping
import torch


class ModelAdapter:
    def __init__(self,checkpoint):
        if not isinstance(checkpoint,Mapping):raise ValueError('checkpoint must be a mapping')
        self.checkpoint=checkpoint

    def state(self,role,*,required=True):
        state=self.checkpoint.get(role)
        if state is None and not required:return None
        if not isinstance(state,Mapping) or not state:raise ValueError(role+' state dictionary missing')
        for name,value in state.items():
            if not isinstance(name,str) or not isinstance(value,torch.Tensor):raise ValueError(role+' state must contain named tensors')
            if not torch.isfinite(value).all():raise ValueError(role+' contains nonfinite '+name)
        return state

    def layers(self,role,*,required=True):
        state=self.state(role,required=required)
        if state is None:return []
        rows=[(name,value) for name,value in state.items() if name.endswith('.weight') and value.ndim==2]
        if not rows:raise ValueError(role+' has no linear weights')
        # Registered parameter order is preserved; do not infer coordinates from width.
        for (_,left),(_,right) in zip(rows,rows[1:]):
            if left.shape[0]!=right.shape[1]:raise ValueError(role+' linear topology is not a supported sequential model')
        return [{'parameter':name,'shape':list(value.shape)} for name,value in rows]

    def describe(self):
        data=self.checkpoint;actor=self.layers('actor');critic=self.layers('critic',required=False)
        state=self.state('actor');std=None;parameterization=None
        if 'log_std' in state:std=state['log_std'].exp();parameterization='log'
        elif 'distribution.std_param' in state:
            std=state['distribution.std_param'];parameterization='declared by spec distribution'
        return {**{key:data.get(key) for key in ('interface_version','critic_privileged_version','role','update','asset_sha256','spec_sha256','source_sha256','dataset_sha256','manifest_sha256','offline_bc_steps')},
            'actor_input_shape':actor[0]['shape'],'critic_input_shape':critic[0]['shape'] if critic else None,
            'actor_output_dim':actor[-1]['shape'][0],'actor_layers':actor,'critic_layers':critic,
            'std':std.tolist() if std is not None else None,'std_parameterization':parameterization,
            'optimizer_present':isinstance(data.get('optimizer'),dict),
            'optimizer_lr':[g.get('lr') for g in data.get('optimizer',{}).get('param_groups',[])],
            'RNG_present':any(key in data for key in ('rng','rng_state','training_rng','cpu_rng')),
            'RNG_fields':[key for key in ('rng','rng_state','training_rng','cpu_rng','cuda_rng') if key in data],
            'missing_optional':[key for key in ('critic','optimizer') if key not in data]}

    def validate(self,spec=None,*,require_optimizer=False):
        description=self.describe()
        if description['actor_output_dim']!=6:raise ValueError('declared native actor must output six physical channels')
        critic=description['critic_layers']
        if critic and critic[-1]['shape'][0]!=1:raise ValueError('critic must output one value')
        if spec is not None:
            version=spec.get('interface_version')
            expected={'multiskill_mcu_v2':31,'multiskill_student_v1':1182}
            if version in expected:
                if description['interface_version']!=version or description['actor_input_shape'][1]!=expected[version]:
                    raise ValueError('checkpoint explicit interface differs from declaration')
            elif version not in (None,'legacy150D'):raise ValueError('unknown declared model interface')
        if require_optimizer and not description['optimizer_present']:raise ValueError('explicit Adam restoration requires optimizer state')
        return description

    def load(self,network,role):
        state=self.state(role)
        expected=network.state_dict()
        if set(expected)!=set(state):raise ValueError(role+' parameter names differ from declared model')
        if any(expected[k].shape!=state[k].shape for k in expected):raise ValueError(role+' parameter shape differs from declared model')
        network.load_state_dict(state,strict=True)
        return network


def read(path):
    return ModelAdapter(torch.load(path,map_location='cpu',weights_only=False))
