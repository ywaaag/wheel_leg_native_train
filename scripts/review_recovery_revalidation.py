"""One-shot completed Recovery batch verification, no runtime or historical writes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def review(run,output):
    run=Path(run).resolve();terminal=json.loads((run/'terminal_report.json').read_text());manifest=json.loads((run/'manifest.json').read_text())
    inputs=dict([checked_input(run/'terminal_report.json'),checked_input(run/'manifest.json'),checked_input(run/'monitor_exit.json')])
    requests=manifest['requests'];completed=terminal.get('completed',[]);rows=[];identities={}
    for i,req in enumerate(requests):
        path=run/f'evaluation_{i:02d}.json'
        if not path.exists():rows.append({'item':i,'family':req['family'],'seed':req['seed'],'evidence_status':'MISSING','accepted':False});continue
        inputs.update([checked_input(path)]);d=json.loads(path.read_text())
        if d['checkpoint_sha256']!=req['sha256'] or d['spec_sha256']!=manifest['spec_sha256'] or d['asset_sha256']!=manifest['asset_sha256']:raise ValueError('Identity conflict')
        if len(d['per_env'])!=8 or {e['env_id'] for e in d['per_env']}!=set(range(8)):raise ValueError('Scored environment mismatch')
        for e in d['per_env']:
            s=np.asarray(e['compact_trace_100hz']);c=np.asarray(e['control_diagnostics_100hz']);g=np.asarray(e['wheel_geometry_trace_100hz'])
            if s.shape[1]!=39 or c.shape!=(len(s),54) or g.shape!=(len(s),13):raise ValueError('Full aligned first episode missing')
            # Entire initialization segment and first controlled state, plus pose ID.
            active=np.flatnonzero((s[:,0]>0)&s[:,29].astype(bool)&(s[:,32]!=7));end=int(active[0])+1 if len(active) else len(s)
            state=np.concatenate((s[:end,6:16],s[:end,19:25],c[:end,:12]),axis=1)
            digest=hashlib.sha256(e['pose_id'].encode()+state.tobytes()).hexdigest()
            identities.setdefault((req['family'],e['env_id']),[]).append({'seed':req['seed'],'pose_id':e['pose_id'],'initialization_digest':digest})
        gate=d['recovery_gate'];accepted=gate['accepted']
        if accepted and not all(e['success'] and e['post_rise_observed_s']==10. and not e['standing_failed_checks'] for e in d['per_env']):raise ValueError('Conflicting gate')
        rows.append({'item':i,'family':req['family'],'seed':req['seed'],'checkpoint_sha256':req['sha256'],'accepted':accepted,'passed_envs':gate['passed_envs'],'per_env':[{'env_id':e['env_id'],'pose_id':e['pose_id'],'initial_valid':e['initial_valid'],'recovery_s':e['recovery_s'],'prefix_s':e['diagnostic_hold_prefix_s'],'failed_checks':e['standing_failed_checks'],'metrics':e['standing_metrics']} for e in d['per_env']]})
    coverage=[{'family':f,'env_id':e,'initializations':v,'distinct_initialization_count':len({x['initialization_digest'] for x in v})} for (f,e),v in identities.items()]
    report={'terminal_status':terminal['status'],'required_items':len(requests),'measured_items':sum(r.get('evidence_status')!='MISSING' for r in rows),'all_accepted':terminal['status']=='COMPLETED' and len(rows)==len(requests) and all(r['accepted'] for r in rows),'rows':rows,'seed_initialization_coverage':coverage,'all_seeds_same_initializations':bool(coverage and all(x['distinct_initialization_count']==1 for x in coverage)),'input_sha256':inputs,'scope':'Completed PPO0 first episodes; seeds label evaluations,coverage requires actual initial states','PPO':0,'simulation_this_review':0}
    publish(Path(output),{'review.json':report},inputs);print(json.dumps({k:v for k,v in report.items() if k not in ('rows','seed_initialization_coverage','input_sha256')},indent=2));return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();review(a.run,a.output_dir)
