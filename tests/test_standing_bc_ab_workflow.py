import json
from types import SimpleNamespace

from native_stand.command_v6 import retention_ab
from native_stand.command_v6.completion import write


def test_pair_runs_sequentially_gradient_before_formal(tmp_path,monkeypatch):
    run=tmp_path/'run';run.mkdir();config=tmp_path/'config';config.mkdir()
    calls=[]
    def phase(spec,phase,output,handshake_fd=None):
        arm=spec.parent.name;calls.append((arm,phase));output.mkdir()
        if phase=='smoke':(output/'metrics.jsonl').write_text('\n'.join(json.dumps({
            'actual_update':u,'task_metrics':{'standing_retention':{'coefficient':.02,
            'gradient_comparison':{'cosine':None if u==1 else -.5,'weighted_norm_ratio':.01}}}})
            for u in (1,2,3))+'\n')
        return {'exit_code':0,'status':'COMPLETED','terminal':{'actual_updates':3 if phase=='smoke' else 100},
                'progress':{'actor_parameters_changed':True}}
    monkeypatch.setattr(retention_ab,'run_phase',phase)
    results=[];monkeypatch.setattr(retention_ab,'finish_pair',lambda a,s,p,f:results.append((s,f)))
    args=SimpleNamespace(output_dir=run,config_dir=config,handshake_fd=-1)
    assert retention_ab.worker(args)==0
    assert calls==[(a,p) for a in retention_ab.ARMS for p in ('source_eval','smoke','formal')]
    assert results==[('COMPLETED',None)]
    review=json.loads((run/'A_fixed/gradient_smoke_review.json').read_text())
    assert review['negative_cosine_fraction']==1 and review['defined_cosines']==2


def test_missing_gradient_or_runtime_failure_stops_pair(tmp_path,monkeypatch):
    run=tmp_path/'run';run.mkdir();calls=[]
    def phase(spec,phase,output,handshake_fd=None):
        calls.append(phase);output.mkdir()
        if phase=='smoke':(output/'metrics.jsonl').write_text('{}\n')
        return {'exit_code':0,'status':'COMPLETED','terminal':{'actual_updates':3},
                'progress':{'actor_parameters_changed':True}}
    monkeypatch.setattr(retention_ab,'run_phase',phase)
    results=[];monkeypatch.setattr(retention_ab,'finish_pair',lambda a,s,p,f:results.append((s,f)))
    args=SimpleNamespace(output_dir=run,config_dir=tmp_path/'config',handshake_fd=-1)
    assert retention_ab.worker(args)==1
    assert calls==['source_eval','smoke'] and results[0][0]=='FAILED'
    assert 'gradient evidence missing' in results[0][1]


def test_user_stop_never_starts_following_arm(tmp_path,monkeypatch):
    run=tmp_path/'run';run.mkdir();calls=[]
    def phase(spec,phase,output,handshake_fd=None):
        calls.append(phase)
        return {'exit_code':0,'status':'STOPPED_BOUNDED',
                'terminal':{'stop_kind':'user_signal'},'progress':{}}
    monkeypatch.setattr(retention_ab,'run_phase',phase)
    monkeypatch.setattr(retention_ab,'finish_pair',lambda *a:None)
    assert retention_ab.worker(SimpleNamespace(output_dir=run,config_dir=tmp_path/'config',handshake_fd=-1))==0
    assert calls==['source_eval']
