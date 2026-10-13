"""Read-only first-episode handoff audit; write a new CPU report directory."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from native_stand.command_v6.domain.trace_schema import STATE, CONTROL, POSTURE, WIDTHS, VERSION
from native_stand.recovery.motion_handoff import score
from native_stand.recovery.min_height import entry_mask, protocol


def audit(run, output):
    run, output = Path(run).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    terminal = json.loads((run/'terminal_report.json').read_text())
    settlement = json.loads((run/'monitor_exit.json').read_text())
    cases, hashes = [], {}
    for condition in terminal['conditions']:
        item = {'index': condition['index'], 'status': condition['status'],
                'condition': condition['condition'], 'per_env': []}
        if condition['status'] != 'COMPLETED':
            cases.append(item)
            continue
        path = run/condition['result']
        saved = json.loads(path.read_text())
        assert saved['field_schema']['state'] == VERSION
        trace = run/saved['trace']['path']
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[trace.name] = hashlib.sha256(trace.read_bytes()).hexdigest()
        assert hashes[trace.name] == saved['trace']['sha256']
        with np.load(trace) as arrays:
            for key, width in WIDTHS.items():
                assert arrays[key].shape[-1] == width
            for eid, previous in enumerate(saved['per_env']):
                mask = arrays['first_episode_valid'][:, eid]
                s = arrays['state'][mask, eid]
                p = arrays['posture'][mask, eid]
                control = arrays['controller'][mask, eid, 0]
                times = arrays['policy_time_s'][mask]
                result = score(torch.tensor(s), torch.tensor(p), torch.tensor(control == 2),
                               policy_time_s=torch.tensor(times, dtype=torch.float32),configuration=saved['protocol'])
                for key in ('accepted', 'hold_complete', 'entry_index', 'failed_checks'):
                    assert result[key] == previous[key], (condition['index'], eid, key)
                result.update(env=eid, initialization_valid=previous['initial_valid'],
                              switched=previous['actually_switched'],
                              last_physical_causes=arrays['termination_causes'][mask, eid][-1].tolist(),
                              last_motion_clock_s=float(arrays['motion_clock_s'][mask, eid, 0][-1]),
                              failed_stage=previous['failure_stage'])
                indices = np.flatnonzero(mask)
                result['phase_windows']={}
                motion_indices=np.flatnonzero(control==2)
                entry=result['entry_index']
                stages={'initialization':control==0,'Recovery_preparation':control==1,
                        'Motion_before_entry':(control==2)&(np.arange(len(s))< (entry+1 if entry is not None else len(s))),
                        'Motion_hold':(control==2)&(np.arange(len(s))>(entry if entry is not None else len(s)))}
                for name,selection in stages.items():
                    ix=np.flatnonzero(selection)
                    if not len(ix):continue
                    absolute=indices[ix]
                    delta=arrays['root_post'][absolute,eid,:3]-arrays['root_pre'][absolute,eid,:3]
                    result['phase_windows'][name]={'sample_indices':ix.tolist(),'intervals':len(ix),'duration_s':len(ix)*.01,
                        'world_net_displacement_m':delta.sum(0).tolist(),
                        'world_planar_path_m':float(np.linalg.norm(delta[:,:2],axis=1).sum()),
                        'native_forward_velocity_integral_m':float(s[ix,STATE['vx_mps']].sum()*.01),
                        'pitch_roll_start_end_rad':p[ix[[0,-1]],:2].tolist(),
                        'angular_velocity_world_start_end_rad_s':arrays['root_post'][absolute[[0,-1]],eid,10:13].tolist(),
                        'leg_length_start_end_m':p[ix[[0,-1]],2:4].tolist()}
                if len(motion_indices):
                    contacts=(s[:,[STATE['left_contact_n'],STATE['right_contact_n']]]>2).all(1)
                    flight=motion_indices[~contacts[motion_indices]]
                    landing=None
                    if len(flight):
                        later=motion_indices[(motion_indices>flight[0])&contacts[motion_indices]]
                        if len(later):landing=int(later[0])
                    result['contact_events']={'definition':'first dual>2N sample following first nondual Motion sample; force resultant, not normal load',
                        'first_nondual_motion_index':int(flight[0]) if len(flight) else None,'first_recontact_index':landing}
                    boundaries=[('Motion_before_first_loss',int(motion_indices[0]),int(flight[0]) if len(flight) else (entry+1 if entry is not None else len(s)))]
                    if len(flight):
                        boundaries.append(('Motion_nondual_to_recontact',int(flight[0]),landing if landing is not None else len(s)))
                    if landing is not None:
                        boundaries.append(('Motion_recontact_to_entry',landing,entry+1 if entry is not None else len(s)))
                    result['motion_contact_subwindows']={}
                    for name,start,stop in boundaries:
                        ix=indices[start:stop]
                        if not len(ix):continue
                        delta=arrays['root_post'][ix,eid,:3]-arrays['root_pre'][ix,eid,:3]
                        result['motion_contact_subwindows'][name]={'index_half_open':[start,stop],
                            'duration_s':len(ix)*.01,'world_net_displacement_m':delta.sum(0).tolist(),
                            'world_planar_path_m':float(np.linalg.norm(delta[:,:2],axis=1).sum()),
                            'native_forward_integral_m':float(s[start:stop,STATE['vx_mps']].sum()*.01),
                            'angular_speed_world_peak_rad_s':float(np.linalg.norm(arrays['root_post'][ix,eid,10:13],axis=1).max())}
                switch = np.flatnonzero(control == 2)
                if len(switch):
                    ii = int(switch[0]); absolute = int(indices[ii])
                    before = arrays['target_pre'][absolute, eid]
                    first = arrays['control'][absolute, eid]
                    target = np.r_[first[CONTROL['leg_target_after_limit']],
                                   first[CONTROL['clipped_action']][[2, 5]]*100]
                    root = arrays['root_pre'][absolute, eid]
                    result['switch'] = dict(policy_index=absolute,
                        recovery_intervals=int((control[:ii] == 1).sum()),
                        root_state_pre=root.tolist(), joint_q_pre=arrays['joint_q_pre'][absolute,eid].tolist(),
                        joint_dq_pre=arrays['joint_dq_pre'][absolute,eid].tolist(),
                        native_state_before=s[ii-1].tolist() if ii else None,
                        posture_before=p[ii-1].tolist() if ii else None,
                        wheel_geometry_after_first_motion_interval=arrays['geometry'][absolute,eid].tolist(),
                        physical_target_jump=(target-before).tolist(),
                        physical_target_before=before.tolist(), physical_target_first=target.tolist(),
                        motion_previous_outside_fraction=previous['switch_state']['motion_previous_outside_fraction'])
                    assert int((control[:ii] == 1).sum()) == round(condition['condition']['switch_s']/.01)
                    eligible = entry_mask(torch.tensor(s[:,STATE['height_m']]), torch.tensor(p[:,:2]),
                        torch.tensor(s[:,STATE['tilt_rad']]), torch.tensor(s[:,[STATE['left_contact_n'],STATE['right_contact_n']]]),
                        torch.tensor(s[:,STATE['clearance_m']]), torch.tensor(s[:,STATE['initial_valid']]>0), protocol()).numpy()
                    longest = current = 0
                    for value in eligible[ii:ii+200]:
                        current = current+1 if value else 0; longest = max(longest,current)
                    result['entry_dwell_max_within_2s'] = longest*.01
                if result['hold_complete']:
                    start, stop = result['hold_index_half_open']
                    hold, posture = s[start:stop], p[start:stop]
                    assert len(hold) == 1000 and (control[start:stop] == 2).all()
                    assert len(np.unique(hold[:,STATE['episode_id']])) == 1
                    result['hold'] = dict(samples=1000, duration_s=10.,
                        height_min_m=float(hold[:,STATE['height_m']].min()),
                        pitch_roll_mean_abs_rad=np.abs(posture[:,:2]).mean(0).tolist(),
                        pitch_roll_peak_abs_rad=np.abs(posture[:,:2]).max(0).tolist(),
                        tilt_peak_rad=float(hold[:,STATE['tilt_rad']].max()),
                        dual_contact_fraction=float((hold[:,[STATE['left_contact_n'],STATE['right_contact_n']]]>2).all(1).mean()),
                        closure_peak_m=float(hold[:,STATE['closure_m']].max()),
                        saturation_fraction=float(hold[:,STATE['saturated']].mean()),
                        displacement_world_m=(arrays['root_post'][indices[stop-1],eid,:3]-arrays['root_pre'][indices[start],eid,:3]).tolist(),
                        channel_applied_limit_fraction=(np.abs(arrays['control'][indices[start:stop],eid,CONTROL['applied_torque']])>=np.array([40,40,5.5,40,40,5.5])-1e-4).mean(0).tolist())
                item['per_env'].append(result)
        item['counts'] = {key: sum(bool(x.get(key)) for x in item['per_env']) for key in
                          ('initialization_valid', 'switched', 'hold_complete', 'accepted', 'strict_vx_0p02_pass')}
        item['counts']['entry_confirmed'] = sum(x['entry_index'] is not None for x in item['per_env'])
        cases.append(item)
    output.mkdir(parents=True)
    report = dict(run=str(run), protocol=VERSION, cases=cases, inputs_sha256=hashes,
                  terminal=terminal, settlement=settlement,
                  output_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),
                  offline_optimizer=0, online_PPO=0, independent_rescore_matches=True)
    (output/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit(args.run,args.output)
    print(json.dumps({'cases':len(result['cases']),'rescore_matches':True,
                      'output_bytes':result['output_bytes']},ensure_ascii=False))
