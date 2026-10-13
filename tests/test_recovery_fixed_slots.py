FROZEN_TEST_SCOPE="PORTABLE"
import ast
import copy
from pathlib import Path
import pytest
import torch
from native_stand.recovery.sampling import fixed_reset_choices,sample_poses,validate_explicit
from native_stand.command_v6.domain.recovery_course import parse_request

def config():
    return {'active_family':'Swing','sampling':{'version':'fixed_environment_families_v1',
        'family_weights':{'Swing':.5,'DrawBack':.25,'R0':.25},
        'environment_counts':{'Swing':2,'DrawBack':1,'R0':1}},
        'assessment':{'families':['Swing','DrawBack','R0'],'retained_families':['DrawBack','R0']}}

def poses():
    return [{'family':f,'split':split,'offline_valid':True} for split in ('train','holdout')
        for f in ('Swing','DrawBack','R0') for _ in range(2)]

def test_partial_resets_never_change_slot_family():
    c=config();p=poses()
    for ids in (torch.arange(4),torch.tensor([3,0]),torch.tensor([1,2]),torch.tensor([],dtype=torch.long)):
        q=fixed_reset_choices(p,c,'train',ids,4)
        for i,j in zip(ids.tolist(),q.tolist()):
            assert p[j]['family']==('Swing' if i<2 else 'DrawBack' if i==2 else 'R0')
            assert p[j]['split']=='train'
    with pytest.raises(ValueError):fixed_reset_choices(p,c,'train',torch.arange(4),5)

def test_actual_runtime_eval_bypasses_training_allocation():
    from native_stand.recovery import sampling
    from native_stand.command_v6.tools.test_resources import source_file
    path=source_file('recovery/runtime.py')
    cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='RecoveryEnv')
    method=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_reset_idx'))
    end=next(i for i,n in enumerate(method.body) if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Subscript) and isinstance(t.value,ast.Attribute) and t.value.attr=='initial_pose_index' for t in n.targets))
    method.body=method.body[:end]+[ast.Return(value=ast.Name(id='choice',ctx=ast.Load()))]
    class Base:
        def _reset_idx(self,ids):pass
    mod=ast.Module(body=[ast.ClassDef(name='RecoveryEnv',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=[method],decorator_list=[])],type_ignores=[])
    ns={'Base':Base,'torch':torch};exec(compile(ast.fix_missing_locations(mod),str(path),'exec'),ns)
    env=ns['RecoveryEnv']();env.recovery_ready=True;env.reverse_curriculum=None;env.recovery_config=config()
    env.pose_library={'poses':poses()};env.num_envs=4;env.device='cpu';env.family='R0';env.split='train'
    env.curriculum_training=True;env.continuous_evaluation=False
    chosen=env._reset_idx(torch.arange(4));assert [poses()[i]['family'] for i in chosen]==['Swing','Swing','DrawBack','R0']
    env.curriculum_training=False;env.continuous_evaluation=True;env.split='holdout'
    chosen=env._reset_idx(torch.arange(4));assert all(poses()[i]['family']=='R0' for i in chosen)

def test_fixed_schema_does_not_accept_inconsistent_mass():
    c=config();assert validate_explicit(c)
    c['sampling']['environment_counts']['Swing']=3
    with pytest.raises(ValueError):validate_explicit(c)
    c=config();c['sampling']['environment_counts']['R0']=True
    with pytest.raises(ValueError):validate_explicit(c)
