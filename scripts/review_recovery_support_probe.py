"""Read completed bounded PPO0 once; distinguish requested pose from settled pose."""
import argparse
import json
from pathlib import Path
import numpy as np
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def review(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json'
    spec=json.loads(sp.read_text());terminal=json.loads((run/'terminal_report.json').read_text())
    if terminal['status'] not in ('COMPLETED','STOPPED_BOUNDED','FAILED'):raise ValueError('Completed run required')
    library=Path(spec['recovery']['pose_library']);poses={p['pose_id']:p for p in json.loads(library.read_text())['poses']}
    inputs=dict(checked_input(p) for p in (sp,library,run/'terminal_report.json',run/'manifest.json'))
    groups=[];names=['left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch']
    for item in terminal['completed']:
        path=run/item['path'];inputs.update([checked_input(path)])
        data=json.loads(path.read_text());rows=[]
        if data['checkpoint_sha256']!=spec['source_sha256'] or data['asset_sha256']!=spec['asset_sha256']:
            raise ValueError('Runtime identity differs')
        for e in data['per_env']:
            state=np.asarray(e['compact_trace_100hz']);control=np.asarray(e['control_diagnostics_100hz']);pose=poses[e['pose_id']]
            requested=np.array([pose['joint_pos'][n] for n in names])
            ids=np.flatnonzero((state[:,0]>0)&(state[:,29]>0)&(state[:,32]!=7))
            # Last initialization sample precedes control; prefer it to first
            # post-control q, which can already move substantially under PD.
            i=int(ids[0]-1) if len(ids) and ids[0]>0 else None
            settled=control[i,[0,1,3,4]] if i is not None else None
            rows.append({'env_id':e['env_id'],'initial_valid':e['initial_valid'],
                'requested_active_q_rad':requested.tolist(),'settled_active_q_rad':settled.tolist() if settled is not None else None,
                'settled_q_difference_max_rad':float(abs(settled-requested).max()) if settled is not None else None,
                'settled_height_m':float(state[i,6]) if i is not None else None,
                'requested_height_m':pose['root_height_m'],'height_peak_m':e.get('height_peak_m'),
                'entry_s':e.get('recovery_s'),'hold_prefix_s':e.get('diagnostic_hold_prefix_s'),
                'passed':e['success'],'termination_reason':e['termination_reason'],
                'failed_checks':e.get('standing_failed_checks'),
                'pose_fidelity_scope':'last recorded initialization sample; not complete passive state'})
        groups.append({'family':data['evaluation_family'],'initial_valid_count':sum(x['initial_valid'] for x in rows),
            'passed_count':sum(x['passed'] for x in rows),'rows':rows})
    result={'status':terminal['status'],'wall_s':terminal.get('wall_s'),'PPO':0,'inputs_sha256':inputs,
        'groups':groups,'missing_requests':terminal.get('missing_requests'),
        'scope':'Same frozen actor per requested static family; valid init alone does not establish pose fidelity or skill'}
    publish(output,{'review.json':result},inputs);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();d=review(a.run,a.output_dir);print(json.dumps({'status':d['status'],'groups':[
        {k:x[k] for k in ('family','initial_valid_count','passed_count')} for x in d['groups']]},indent=2))
