import hashlib
import json
from pathlib import Path
import pytest
from native_stand.command_v6.tools.experiment_preparation import publish,digest
from native_stand.command_v6.domain.recovery_course import parse_request
from native_stand.command_v6.tools.prepare_recovery_course import inheritance
from native_stand.recovery.standing import pose_sampling


def request():
    return {'purpose':'recovery_fixture','level_id':'Level3','current_family':'Swing',
        'retained_families':['DrawBack','R0'],'family_weights':{'Swing':.4,'DrawBack':.4,'R0':.2},
        'smoke_updates':10,'formal_updates':100,'evaluation_updates':[25,50,100],
        'wall_s':{'source_eval':900,'smoke':900,'formal':7200}}


def test_raw_identity_copy_keeps_infinite_limits_and_all_file_marker(tmp_path):
    source=tmp_path/'old.json';source.write_bytes(b'{"limits":[-Infinity,Infinity]}\n')
    before=source.read_bytes();root=tmp_path/'new'
    publish(root,{'spec.json':{}},{},raw_files={'poses.json':(source,digest(source))},completion_marker=True)
    assert (root/'poses.json').read_bytes()==before==source.read_bytes()
    marker=json.loads((root/'publication_complete.json').read_text())
    assert set(marker['files'])=={'spec.json','poses.json'}
    assert all(digest(root/name)==sha for name,sha in marker['files'].items())
    with pytest.raises(ValueError,match='SHA'):publish(tmp_path/'bad',{}, {},raw_files={'poses.json':(source,'0'*64)})
    assert not (tmp_path/'bad').exists()
    with pytest.raises(ValueError):publish(tmp_path/'finite',{'spec.json':{'value':float('inf')}},{})


@pytest.mark.parametrize('failure',['poses.json','publication_complete.json'])
def test_pose_or_marker_failure_rolls_back_whole_declaration(tmp_path,monkeypatch,failure):
    content=b'{"limit":Infinity}\n';sha=hashlib.sha256(content).hexdigest();original=Path.open
    def broken(path,*args,**kwargs):
        if path.name==failure:raise OSError('disk failure')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',broken)
    with pytest.raises(OSError):publish(tmp_path/'new',{'spec.json':{},'budget.json':{}},{},
        serialized_files={'poses.json':(content,sha)},completion_marker=True)
    assert not (tmp_path/'new').exists()


@pytest.mark.parametrize('mutation',[
    lambda d:d['family_weights'].update(R0=.3),
    lambda d:d.update(retained_families=['R0','R0']),
    lambda d:d.update(evaluation_updates=[25,50]),
    lambda d:d['wall_s'].update(formal=float('nan')),
    lambda d:d.update(smoke_updates=True),
    lambda d:d.update(reward={'upright':99})])
def test_course_rejects_unsupported_or_incomplete_request(mutation):
    d=request();mutation(d)
    with pytest.raises(ValueError):parse_request(d)


def test_sampling_compilation_preserves_scoring_and_pose_counts():
    d=parse_request(request());poses=[{'family':f,'split':split,'offline_valid':True,'sample_weight':mass/n}
        for split in ('train','holdout') for f,n,mass in [('Swing',2,.4),('DrawBack',3,.4),('R0',4,.2)] for _ in range(n)]
    for split in ('train','holdout'):
        ids,weights=pose_sampling(poses,d['current_family'],split,retained_families=d['retained_families'],retained_fraction=.6)
        actual={f:sum(w for i,w in zip(ids,weights) if poses[i]['family']==f) for f in d['family_weights']}
        assert actual==pytest.approx(d['family_weights'])


def test_inheritance_inventory_includes_removed_std_and_unchanged_reward():
    old={'reward':{'a':1},'recovery':{'exploration_initialization':{'factor':.5},'family':'old'}}
    new={'reward':{'a':1},'recovery':{'family':'new'}}
    report=inheritance(old,new)
    assert 'reward' in report['inherited_sections']
    assert report['deleted'][0]['field']=='recovery.exploration_initialization'
    assert report['overridden'][0]['field']=='recovery.family'
