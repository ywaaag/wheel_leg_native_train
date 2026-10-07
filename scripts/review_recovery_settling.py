"""Offline gate audit of saved 39-column Recovery traces; no Isaac/PPO.

Full linear/angular velocity vectors are absent in this trace format. Horizontal
speed and abs(yaw) provide necessary conditions only, never full gate acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation


def longest(mask, dt=.01):
    best=current=0
    for value in mask:
        current=current+1 if value else 0
        best=max(best,current)
    return best*dt


def review_episode(episode, config):
    trace=np.asarray(episode['compact_trace_100hz'],dtype=float)
    if trace.ndim!=2 or trace.shape[1]!=39 or not np.isfinite(trace).all():
        raise ValueError('Invalid 39-column finite trace')
    dt=.01
    h=trace[:,6]; speed=np.linalg.norm(trace[:,7:9],axis=1); yaw=np.abs(trace[:,9])
    gates={'height':(h>=config['height_m'][0])&(h<=config['height_m'][1]),
        'tilt':trace[:,15]<=config['tilt_max_rad'],
        'horizontal_speed_necessary':speed<=config['linear_speed_max_mps'],
        'yaw_speed_necessary':yaw<=config['angular_speed_max_rad_s'],
        'dual_contact':(trace[:,10:12]>config['dual_contact_min_n']).all(1),
        'chassis_clearance':trace[:,13]>=config['chassis_clearance_min_m']}
    all_known=np.logical_and.reduce(list(gates.values()))
    result={'env_id':episode['env_id'],'pose_id':episode['pose_id'],
        'success_recorded':episode['success'],'termination_reason':episode['termination_reason'],
        'runtime_fault':episode['runtime_fault'],'samples':len(trace),
        'known_gate_pass_fraction':{k:float(v.mean()) for k,v in gates.items()},
        'known_gate_longest_s':{k:longest(v,dt) for k,v in gates.items()},
        'all_known_longest_s':longest(all_known,dt),
        'exact_all_gates':'UNKNOWN: vz and angular x/y not saved',
        'windows':{}}
    for name,mask in [('whole',np.ones(len(trace),dtype=bool)),('late',trace[:,0]>=max(0.,trace[-1,0]-2.))]:
        a=trace[mask]
        gravity=Rotation.from_quat(a[:,22:26]).inv().apply(np.tile([0.,0.,-1.],(len(a),1)))
        pitch=np.arctan2(gravity[:,2],-gravity[:,1])
        roll=np.arctan2(-gravity[:,0],np.linalg.norm(gravity[:,1:3],axis=1))
        result['windows'][name]={'samples':len(a),'height_mean_m':float(a[:,6].mean()),
            'vx_abs_mean_mps':float(np.abs(a[:,7]).mean()),'yaw_abs_mean_rad_s':float(np.abs(a[:,9]).mean()),
            'tilt_mean_rad':float(a[:,15].mean()),
            'pitch_abs_mean_rad':float(np.abs(pitch).mean()),
            'roll_abs_mean_rad':float(np.abs(roll).mean()),
            'net_displacement_m':float(np.linalg.norm(a[-1,19:21]-a[0,19:21]))}
    control=episode.get('terminal_control_pre_reset')
    if control is not None:
        c=np.asarray(control)
        if c.shape!=(54,): raise ValueError('Unknown terminal control schema')
        result['terminal_control']={'active_q':c[:6].tolist(),'active_qdot':c[6:12].tolist(),
            'raw_action':c[12:18].tolist(),'clipped_action':c[18:24].tolist(),
            'wheel_targets_rad_s':(c[[20,23]]*100.).tolist(),
            'requested_effort_nm':c[32:38].tolist(),'clipped_effort_nm':c[38:44].tolist(),
            'applied_effort_nm':c[44:50].tolist(),
            'scope':'terminal instant only; target inferred from executed action and frozen100rad/s scale'}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    spec_path=a.run/'source_snapshot/spec.json'
    spec=json.loads(spec_path.read_text())
    result={'run':str(a.run.resolve()),'spec_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        'protocol':spec['recovery']['autonomous_stability'],'required_stable_s':spec['recovery']['fsm']['verify_s'],
        'ppo_updates':0,'simulation_seconds':0,'evaluations':[]}
    result['reward_weights']=spec['reward']
    result['settling_reward']=spec['recovery']['settling_reward']
    result['trace_limitations']=['Full vz and angular x/y absent; reconstructed gates are necessary conditions only.',
        'Control targets/torques available at terminal only; no full control trajectory.',
        'Force threshold contact and policy-sampled saturation do not certify all physics/PD substeps.']
    for path in sorted(a.run.glob('evaluation_*_0_0.json')):
        data=json.loads(path.read_text())
        rows=[review_episode(e,result['protocol']) for e in data['per_env']]
        result['evaluations'].append({'path':str(path.resolve()),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'per_env':rows})
    with a.output.open('x') as stream: json.dump(result,stream,indent=2)
    print(json.dumps([{'evaluation':Path(e['path']).name,'per_env':[
        {'env':r['env_id'],'gate_pass':r['known_gate_pass_fraction'],
         'all_known_longest_s':r['all_known_longest_s'],'late':r['windows']['late'],
         'wheel_targets':r.get('terminal_control',{}).get('wheel_targets_rad_s')} for r in e['per_env']]}
        for e in result['evaluations']],indent=2))


if __name__=='__main__': main()
