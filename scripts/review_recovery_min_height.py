"""P0 old traces rescored under minimum-height v2; no simulator or old writes."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import torch
from native_stand.recovery.min_height import protocol,score

def independent(s,a,p):
    # Deliberately separate NumPy loop, no scorer or domain predicate calls.
    streak=0;confirm=None
    for i,row in enumerate(s):
        ok=bool(row[29]) and row[0]>0 and row[32]!=7 and row[6]>=.30 and row[13]>0 and row[10]>2 and row[11]>2 and row[15]<=.18 and max(abs(a[i,0]),abs(a[i,1]))<=.10
        streak=streak+1 if ok else 0
        if streak>=20 and row[0]<=11.5+1e-5:confirm=i;break
    if confirm is None:return None,0.,False
    w=s[confirm+1:confirm+1001];angles=a[confirm+1:confirm+1001,:2]
    hard=(w[:,6]>=.30)&(w[:,13]>0)&(w[:,10]>2)&(w[:,11]>2)&(w[:,15]<=.18)&(np.abs(angles)<=.15).all(1)&(w[:,12]<=.005)
    ix=np.flatnonzero(~hard);prefix=(int(ix[0]) if len(ix) else len(w))*.01
    passed=(len(w)==1000 and hard.all() and (np.abs(angles).mean(0)<=.10).all() and w[:,17].mean()<=.05 and (s[:,12]<=.005).all())
    return confirm,prefix,bool(passed)

def main(run,out):
    if out.exists():raise FileExistsError(out)
    p=protocol();digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();inputs={};cases=[]
    paths=[('S50',run/'source_eval/evaluation_source.json')]+[(f'new{u}',run/f'formal/evaluation_{u}_0_0.json') for u in (25,50,100)]
    for label,path in paths:
        inputs[str(path.resolve())]=digest(path);d=json.loads(path.read_text());groups=[]
        frozen=path.parent/'source_snapshot/spec.json';f=json.loads(frozen.read_text());inputs[str(frozen.resolve())]=digest(frozen)
        checkpoint=Path(f['source_checkpoint']) if label=='S50' else path.parent/f'model_update_{label.removeprefix("new")}.pt'
        if digest(checkpoint)!=d['checkpoint_sha256']:raise ValueError('Evaluation model SHA mismatch')
        inputs[str(checkpoint.resolve())]=digest(checkpoint)
        inputs[str(Path(f['asset_path']).resolve())]=digest(Path(f['asset_path']))
        if digest(Path(f['asset_path']))!=f['asset_sha256']:raise ValueError('Asset SHA mismatch')
        for item in [d,*d.get('retained_evaluations',[])]:
            rows=[]
            for e in item['per_env']:
                if 'compact_trace_100hz' not in e or 'posture_trace_100hz' not in e:
                    rows.append({'env_id':e['env_id'],'pose_id':e['pose_id'],'accepted':None,'evidence_status':'MISSING_EVIDENCE','reason':'Full first-episode state/posture missing; no reconstruction from tail or aggregates'});continue
                s=np.array(e['compact_trace_100hz']);a=np.array(e['posture_trace_100hz'])
                result=score(torch.tensor(s),torch.tensor(a),dt=.01,p=p,initial_valid=e['initial_valid'],terminated=e['episode_result']['terminated'],runtime_fault=e['runtime_fault'])
                confirm,prefix,passed=independent(s,a,p)
                assert confirm==result['entry_confirmation_index']
                assert abs(prefix-result['diagnostic_hold_prefix_s'])<1e-8
                assert result['accepted']==(passed and e['initial_valid'] and not e['runtime_fault'] and not e['episode_result']['terminated'])
                geometry=e.get('wheel_geometry_trace_100hz')
                geometry_summary=None
                if geometry is not None:
                    g=np.asarray(geometry);v=g[:,:6].reshape(-1,2,3);direction=g[:,6:9]
                    direction=direction/np.maximum(np.linalg.norm(direction,axis=1,keepdims=True),1e-12)
                    offset=np.abs(((v[:,0]-v[:,1])*direction).sum(1))
                    geometry_summary={'definition':'wheel center separation projected on measured body forward; not contact patch','first_m':float(offset[0]),'last_m':float(offset[-1]),'peak_m':float(offset.max())}
                lost=np.flatnonzero((s[:,0]>0)&~((s[:,10:12]>2).all(1)))
                crossing=np.flatnonzero((s[:,0]>0)&(s[:,6]>=.30))
                rows.append({'env_id':e['env_id'],'pose_id':e['pose_id'],'episode_id':e['episode_id'],**result,'independent_crosscheck':True,
                    'first_height_crossing_s':float(s[crossing[0],0]) if len(crossing) else None,
                    'first_contact_loss_s':float(s[lost[0],0]) if len(lost) else None,
                    'geometry':geometry_summary})
            groups.append({'family':item['evaluation_family'],'passed':sum(e['accepted'] is True for e in rows),'unknown':sum(e['accepted'] is None for e in rows),'rows':rows})
        cases.append({'model':label,'checkpoint':str(checkpoint.resolve()),'checkpoint_sha256':d['checkpoint_sha256'],'asset_sha256':json.loads((path.parent/'source_snapshot/spec.json').read_text())['asset_sha256'],'old_accepted':d['accepted'],'groups':groups})
        print(label,[(g['family'],g['passed'],g['unknown'],[round(e.get('diagnostic_hold_prefix_s',0),2) for e in g['rows']]) for g in groups])
    assert all(digest(Path(f))==h for f,h in inputs.items())
    out.mkdir();(out/'review.json').write_text(json.dumps({'protocol':p,'protocol_sha256':hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'inputs_sha256':inputs,'cases':cases,'scope':'Offline rescore of frozen old traces, NOT new learning or new physical evaluation; R0 requires confirmed-entry protocol here, explicitly not fixed10s','simulation':0,'PPO':0,'candidate_decision':'No complete DrawBack+R0 certificate. Alignment candidates learned deterministic wheel oscillation; default P1 source S50 without geometry cost.'},indent=2,allow_nan=False)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True);a=parser.parse_args();main(a.run,a.output_dir)
