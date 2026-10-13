FROZEN_TEST_SCOPE="PROJECT_DATA"
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from native_stand.recovery import sampling
from native_stand.recovery.rising import validate_rise,rise_protocol
from native_stand.recovery.standing import pose_sampling
from native_stand.command_v6.config import validate,schedule
from native_stand.command_v6.tools.evaluate_checkpoint import protocol_for_spec


def legacy():
    return {'active_family':'Swing','rising_task':{
        'version':'autonomous_rise_min_height_v2','recovery_deadline_s':11.5,
        'post_rise_hold_s':10.,'entry_dwell_s':.2,'minimum_height_m':.3,
        'sampling_version':'explicit_retained_pose_weights_v1',
        'retained_families':['DrawBack','R0'],'retained_fraction':.6},
        'curriculum':{'levels':[{'pose_family':'Swing'}]}}


def modern():
    c=legacy();c['rising_task']=sampling.scoring_config(c['rising_task'])
    c['sampling']={'version':'family_weights_v1','family_weights':{'Swing':.4,'DrawBack':.4,'R0':.2}}
    c['assessment']={'families':['Swing','DrawBack','R0'],'retained_families':['DrawBack','R0']}
    return c


def poses():
    return [{'family':f,'split':split,'offline_valid':True,'sample_weight':mass/n}
        for split in ('train','holdout') for f,n,mass in [('Swing',2,.4),('DrawBack',3,.4),('R0',4,.2)] for _ in range(n)]


def test_legacy_adapter_no_mutation_equal_probabilities_and_scoring():
    old=legacy();before=copy.deepcopy(old);new=modern();p=poses()
    for split in ('train','holdout'):
        a=sampling.sample_poses(p,old,'Swing',split,training=True,stage=0)
        b=sampling.sample_poses(p,new,'Swing',split,training=True,stage=0)
        assert dict(zip(a[0],a[1]))==pytest.approx(dict(zip(b[0],b[1])))
        assert sampling.retained_families(old,'Swing')==sampling.retained_families(new,'Swing')
    assert rise_protocol({},old['rising_task'])==rise_protocol({},new['rising_task'])
    assert old==before
    assert sampling.effective(old)['declaration']=='legacy_read_only_adapter'
    assert sampling.effective(new)['declaration']=='explicit'
    with pytest.raises(ValueError):validate_rise(old['rising_task'])
    assert validate_rise(new['rising_task'])==new['rising_task']


def test_weights_do_not_change_scoring_or_protection_scope():
    c=modern();score=rise_protocol({},c['rising_task']);protected=sampling.retained_families(c,'Swing')
    c['sampling']['family_weights']={'Swing':.8,'DrawBack':.15,'R0':.05}
    assert sampling.validate_explicit(c)
    assert rise_protocol({},c['rising_task'])==score
    assert sampling.retained_families(c,'Swing')==protected
    ids,prob=sampling.sample_poses(poses(),c,'Swing','train',training=True)
    assert sum(v for i,v in zip(ids,prob) if poses()[i]['family']=='R0')==pytest.approx(.05)


def test_eval_reset_only_requested_family_and_partial_reset():
    c=modern();p=poses()
    for f in c['assessment']['families']:
        ids,weights=sampling.sample_poses(p,c,f,'holdout',training=False)
        assert sum(weights)==pytest.approx(1.) and all(p[i]['family']==f for i in ids)
    # Execute the actual reset method up to its first RNG boundary, without Isaac.
    from native_stand.command_v6.tools.test_resources import source_file
    path=source_file('recovery/runtime.py')
    tree=ast.parse(path.read_text());klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RecoveryEnv')
    method=copy.deepcopy(next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='_reset_idx'))
    stop=next(i for i,n in enumerate(method.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='candidates' for t in n.targets))
    method.body=method.body[:stop]+[ast.Return(value=ast.Tuple(elts=[ast.Name(id='eligible',ctx=ast.Load()),ast.Name(id='weights',ctx=ast.Load())],ctx=ast.Load()))]
    class Base:
        def _reset_idx(self,ids):self.reset_ids=ids
    mod=ast.Module(body=[ast.ClassDef(name='RecoveryEnv',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=[method],decorator_list=[])],type_ignores=[])
    ns={'Base':Base,'torch':torch};exec(compile(ast.fix_missing_locations(mod),str(path),'exec'),ns)
    env=ns['RecoveryEnv']();env.recovery_ready=True;env.curriculum_training=True;env.reverse_curriculum=None
    env.recovery_config=c;env.family='Swing';env.split='train';env.pose_library={'poses':p};env.num_envs=3;env.device='cpu'
    ids=torch.tensor([1]);got=env._reset_idx(ids)
    assert torch.equal(env.reset_ids,ids)
    expected=sampling.sample_poses(p,c,'Swing','train',training=True)
    assert got==expected


@pytest.mark.parametrize('change',[
    lambda c:c['rising_task'].update(retained_fraction=.6),
    lambda c:c['curriculum']['levels'][0].update(retained_families=['R0']),
    lambda c:c['sampling'].update(version='unknown'),
    lambda c:c['sampling']['family_weights'].update(R0=float('nan')),
    lambda c:c['assessment'].update(retained_families=['R0','R0']),
    lambda c:c['assessment'].update(families=['Swing','R0']),
    lambda c:c.pop('assessment'),
])
def test_conflict_missing_and_nonfinite_fail(change):
    c=modern();change(c)
    with pytest.raises(ValueError):sampling.validate_explicit(c)


def test_legacy_stage_override_and_eval_isolation():
    c=legacy();c['curriculum']['levels'].append({'pose_family':'Swing','retained_families':['R0'],'retained_fraction':.2})
    p=poses();a=sampling.sample_poses(p,c,'Swing','train',training=True,stage=1)
    b=pose_sampling(p,'Swing','train',retained_families=['R0'],retained_fraction=.2)
    assert a==b
    ids,_=sampling.sample_poses(p,c,'Swing','train',training=False,stage=1)
    assert all(p[i]['family']=='Swing' for i in ids)


def test_missing_family_split_rejected():
    p=[p for p in poses() if not (p['family']=='R0' and p['split']=='holdout')]
    with pytest.raises(ValueError,match='Missing'):sampling.sample_poses(p,modern(),'Swing','holdout',training=True)


def test_actual_evaluator_checks_each_assessment_family_once():
    from native_stand.command_v6.tools.test_resources import source_file
    path=source_file('recovery/recipe.py')
    tree=ast.parse(path.read_text());method=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_actor')
    block=next(n for n in ast.walk(method) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='retained_results' for t in x.targets) for x in n.body))
    start=next(i for i,n in enumerate(block.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='retained_results' for t in n.targets))
    end=next(i for i,n in enumerate(block.body[start:],start) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='passed' for t in n.targets))
    calls=[]
    def evaluate(*args,**kwargs):
        calls.append(kwargs['family']);assert kwargs['check_retained'] is False
        return {'accepted':True}
    c=modern();env=SimpleNamespace(recovery_config=c,reverse_curriculum=object())
    ns={'env':env,'rising':c['rising_task'],'standing':{'protocol':{'objective':'survival_level'}},
        'check_retained':True,'evaluation_family':'Swing','seconds':23.,'seed':104,
        'actor':None,'wrapped':None,'stop_requested':lambda:False,'full_trace':False,
        'diagnostics':False,'diagnostic_profile':None,'episodes':[],'evaluate_actor':evaluate}
    mod=ast.Module(body=block.body[start:end],type_ignores=[])
    exec(compile(ast.fix_missing_locations(mod),str(path),'exec'),ns)
    assert calls==['DrawBack','R0']
    assert len(ns['retained_results'])==2


def test_real_config_parser_and_evaluator_old_new_protocol_equal():
    import json
    root=Path(__file__).resolve().parents[1]
    frozen=root/'configs/experiments/2026_10_8-14_51__recovery_level3_swing_from_b25/spec.json'
    old=json.loads(frozen.read_text());new=copy.deepcopy(old);c=new['recovery']
    current=c['active_family'];retained=c['rising_task']['retained_families']
    c['rising_task']=sampling.scoring_config(c['rising_task'])
    c['sampling']={'version':'family_weights_v1','family_weights':{current:.4,retained[0]:.4,retained[1]:.2}}
    c['assessment']={'families':[current,*retained],'retained_families':retained}
    assert not validate(old) and not validate(new)
    assert protocol_for_spec(old,23.)==protocol_for_spec(new,23.)
    assert [u for u in range(1,101) if schedule(u,'formal',new['evaluation'])['full']]==[25,50,100]
    bad=copy.deepcopy(new);bad['recovery']['rising_task']['retained_fraction']=.6
    assert any('conflict' in x for x in validate(bad))
    assert frozen.read_text()==json.dumps(old,indent=2)+'\n' or json.loads(frozen.read_text())==old
