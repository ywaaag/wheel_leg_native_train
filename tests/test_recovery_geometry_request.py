import pytest
from native_stand.command_v6.tools.recovery_batch import validate_request


def test_explicit_rise_only_accepts_full23s():
    request={'checkpoint':'model.pt','sha256':'a'*64,'target':[0,0],
             'family':'drawback_manual0001','seconds':23.,'seed':104}
    spec={'task':'recovery','recovery':{'rising_task':{
        'version':'autonomous_rise_v1','recovery_deadline_s':11.5,
        'post_rise_hold_s':10.,'retained_families':['R0'],'retained_fraction':.4}}}
    assert validate_request(spec,request)['seconds']==23.
    with pytest.raises(ValueError):validate_request({'task':'recovery'},request)
    with pytest.raises(ValueError):validate_request(spec,{**request,'seconds':10.})
    with pytest.raises(ValueError):validate_request(spec,{**request,'seconds':100.})


def test_diagnostic_prepare_drops_training_trace_updates(tmp_path,monkeypatch):
    import json
    from native_stand.command_v6.tools import prepare_checkpoint_diagnostic as tool
    files={}
    for name in ('asset','asset_module','colleague_config','checkpoint'):
        path=tmp_path/name;path.write_text(name);files[name]=path
    library=tmp_path/'poses.json';library.write_text(json.dumps({'poses':[{'family':'R0'}]}))
    spec={'task':'recovery','evaluation':{'protocol_identity':'x','full_trace_updates':[25,50,100]},
        'recovery':{'pose_library':str(library),'pose_library_sha256':tool.sha(library)},'budget':{},
        'artifacts':{},'control':{'policy_dt_s':.01}}
    for name in ('asset','asset_module','colleague_config'):
        spec[name+'_path']=str(files[name]);spec[name+'_sha256']=tool.sha(files[name])
    parent=tmp_path/'spec.json';parent.write_text(json.dumps(spec));captured=[]
    monkeypatch.setattr(tool,'inspect',lambda *a:{})
    monkeypatch.setattr(tool,'validate_request',lambda s,r:r)
    monkeypatch.setattr(tool,'batch_seconds',lambda s:23.)
    monkeypatch.setattr(tool,'validate',lambda s:captured.append(s) or [])
    tool.prepare(parent,files['checkpoint'],tmp_path/'2026_10_8-12_12__cpu_diagnostic',
        family='R0',protocol='x',session='session',physical_gpu=0,gpu_uuid='uuid')
    assert captured[0]['evaluation']['full_trace_updates']==[]
    assert json.loads(parent.read_text())['evaluation']['full_trace_updates']==[25,50,100]
