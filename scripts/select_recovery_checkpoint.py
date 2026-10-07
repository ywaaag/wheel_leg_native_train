"""Rank saved Recovery checkpoints without starting Isaac or PPO.

Independent evaluation evidence outranks rollout proxies. Unreviewed checkpoints
remain visible and are never promoted to accepted.
"""
import argparse, hashlib, json
from pathlib import Path

def sha(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run',type=Path,required=True); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); run=a.run.resolve(); metrics={}
    for line in (run/'metrics.jsonl').read_text().splitlines():
        try:
            row=json.loads(line); metrics[row.get('actual_update')]=row
        except ValueError: pass
    evaluated={}
    for f in run.glob('evaluation_*_0_0.json'):
        d=json.loads(f.read_text()); u=int(f.name.split('_')[1]); rows=d.get('per_env',[])
        if rows:
            evaluated[u]={'protocol':d.get('success_protocol'), 'accepted':d.get('accepted',False),
                'passed_envs':d.get('passed_envs',0),'outcome_counts':d.get('outcome_counts'),
                'height_final_m':sum(x.get('height_final_m',0) for x in rows)/len(rows),
                'tilt_peak_rad':sum(x.get('tilt_peak_rad',0) for x in rows)/len(rows),
                'dual_contact_fraction':sum(x.get('dual_contact_fraction',0) for x in rows)/len(rows),
                'continuous_s':sum(x.get('continuous_s',0) for x in rows)/len(rows), 'path':str(f)}
    records=[]
    for f in sorted(run.glob('model_update_*.pt'),key=lambda p:int(p.stem.rsplit('_',1)[1])):
        u=int(f.stem.rsplit('_',1)[1]); m=metrics.get(u,{}); ro=m.get('rollout',{}); ev=evaluated.get(u)
        records.append({'update':u,'checkpoint':str(f),'sha256':sha(f),
            'evaluation':ev,'review_status':'INDEPENDENTLY_EVALUATED' if ev else 'UNREVIEWED',
            'rollout_proxy':{'weighted_lift':ro.get('weighted_mean',{}).get('lift'),
                'weighted_upright':ro.get('weighted_mean',{}).get('upright'),
                'tilt_terminations':ro.get('termination_count',{}).get('tilt'),
                'dual_contact_fraction':ro.get('dual_contact_fraction'),
                'saturation_fraction':ro.get('saturation_fraction')}})
    def key(r):
        e=r['evaluation']
        if e: return (int(e['accepted']),e['passed_envs'],e['continuous_s'],e['dual_contact_fraction'],-e['tilt_peak_rad'])
        p=r['rollout_proxy']; return (-1,-1,0,p.get('dual_contact_fraction') or 0,0)
    ranked=sorted(records,key=key,reverse=True)
    out={'run':str(run),'selection_scope':'No new simulation; independent evaluations outrank rollout proxies.',
        'accepted_candidate':next((r for r in ranked if r['evaluation'] and r['evaluation']['accepted']),None),
        'best_independently_evaluated':next((r for r in ranked if r['evaluation']),None),
        'best_rollout_proxy':max(records,key=lambda r:(r['rollout_proxy'].get('weighted_lift') or -1)),
        'records':records,'ranked_updates':[r['update'] for r in ranked]}
    outpath=a.output or (run/'checkpoint_selection.json'); outpath.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({k:out[k] for k in ('accepted_candidate','best_independently_evaluated','best_rollout_proxy','ranked_updates')},indent=2))
if __name__=='__main__':main()
