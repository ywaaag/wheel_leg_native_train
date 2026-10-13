"""Identitybound latestpolicy localleg direction coverage,not global reachability."""
import argparse,json
from pathlib import Path
import numpy as np
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def review(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text());inputs=dict([checked_input(sp)])
    p=run/'terminal_report.json';t=json.loads(p.read_text());inputs.update([checked_input(p)])
    if t['status']!='COMPLETED':raise ValueError('Incomplete diagnostic')
    p=run/t['completed'][0]['path'];d=json.loads(p.read_text());inputs.update([checked_input(p)])
    if d['checkpoint_sha256']!=s['source_sha256'] or not d['frozen_state_unchanged']:raise ValueError('State/identity differs')
    p=run/d['capture']['path'];inputs.update([checked_input(p,d['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    md=a['pre_metadata'];mask=(md[...,0]==d['capture']['family_names'].index('swing_candidate_from_historical_r1'))&md[...,2].astype(bool)
    ids=np.asarray(d['capture']['active_indices'])[[0,1,3,4]];preq=a['pre_joint_pos'][...,ids];target=a['post_control'][...,28:32]
    delta=target-preq;sign=np.array([1,1,-1,1]);desired=(delta*sign>0).all(-1);clock=np.rint(a['post_state'][...,0]*100).astype(int)
    geometry=a['post_geometry'];anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m']);length=np.linalg.norm(geometry[...,:6].reshape(*geometry.shape[:-1],2,3)-anchors,axis=-1)
    groups=[]
    for lo,hi in [(1,4),(5,10),(11,100)]:
        m=mask&(clock>=lo)&(clock<=hi);found=m&desired
        groups.append({'clock_steps':[lo,hi],'n':int(m.sum()),'all4_local_direction_count':int(found.sum()),
            'each_leg_target_direction_fraction':(delta[m]*sign>0).mean(0).tolist() if m.any() else None,
            'delta_mean_rad':delta[m].mean(0).tolist() if m.any() else None,
            'desired_raw_advantage_mean':float(a['advantage_raw'][...,0][found].mean()) if found.any() else None})
    m=mask;std=a['sample'][m][:,[2,5]];physical=a['post_control'][m][:,18:24][:,[2,5]]
    result={'inputs_sha256':inputs,'checkpoint_sha256':s['source_sha256'],'phase_coverage':groups,
        'controlled_Swing_samples':int(m.sum()),'wheel_sample_clip_fraction':(abs(std)>1).mean(0).tolist(),
        'actual_wheel_target_std_all_states_rad_s':(physical.std(0)*100).tolist(),
        'minimum_leg_length_m':length[m].min(0).tolist(),'both_length_below030_count':int((length[m]<.3).all(1).sum()),
        'preframe_fullq_consistency_max_error':float(abs(delta-(s['action']['leg_scale_rad']*np.clip(a['sample'][...,[0,1,3,4]],-1,1)-a['pre_obs150'][...,9:13]/2))[m].max()),
        'capture_MiB':d['capture']['bytes']/1024**2,'state_unchanged':d['frozen_state_unchanged'],'simulation':0,'optimizer_updates':0,
        'limits':['localdirection is sufficient sampledgeometrypath,not necessaryforallrecovery',
            'randomcontrol std includesstate/episode variation,not isolatedwithinstate exploratory std',
            'fullpostjoint on doneexcluded for analysis; here length/control use pre-reset snapshots',
            '2.56s limitedcoverage,no capability/fullhold or uniquecriticfault claim']}
    publish(output,{'review.json':result},inputs);print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();review(a.run,a.output_dir)
