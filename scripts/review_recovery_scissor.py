"""Offline sampled physical USD closure geometry and wheel delta-cost replay."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from native_stand.recovery.asset_poses import AssetPoses


def main(run, output):
    if output.exists():raise FileExistsError(output)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text())
    library=Path(s['recovery']['pose_library']);asset_path=Path(s['asset_path'])
    if sha(asset_path)!=s['asset_sha256']:raise ValueError('asset SHA differs')
    lib=json.loads(library.read_text());asset=AssetPoses(asset_path)
    inputs={str(p):sha(p) for p in [sp,library,asset_path]};results=[]
    for u in (50,100):
        p=run/f'evaluation_{u}_0_0.json';inputs[str(p)]=sha(p);d=json.loads(p.read_text())
        e=d['per_env'][0];c=np.asarray(e['control_diagnostics_100hz'],float)
        initial=next(p for p in lib['poses'] if p['pose_id']==e['pose_id'])['joint_pos']
        samples=[]
        for i in (780,1067,1500,2000,2299):
            names=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')
            q,error=asset.solve(dict(zip(names,c[i,[0,1,3,4]])),initial)
            b=asset.forward(q)
            samples.append({'policy_time_s':(i+1)*.01,
                'root_local_forward_wheel_offset_m':float(abs(b['left_wheel'][2,3]-b['right_wheel'][2,3])),
                'offline_closure_max_m':float(max(error))})
        delta=np.diff(c[:,18:24],axis=0)[-499:]
        wheels=delta[:,[2,5]]
        results.append({'update':u,'env_id':0,'sampled_geometry':samples,
            'last5s_wheel_target_step_rms_rad_s':np.sqrt(np.mean((wheels*100)**2,axis=0)).tolist(),
            'last5s_wheel_delta_reward_per_second':float(s['reward']['action_delta']*np.mean((wheels**2).sum(1)/6)),
            'last5s_wheel_delta_reward_per_policy_step':float(s['reward']['action_delta']*np.mean((wheels**2).sum(1)/6)*.01)})
    result={'inputs_sha256':inputs,'results':results,'simulation':0,'PPO':0,
        'scope':'env0 sampled USD closure reconstruction, root-local forward=-Z; not runtime world-horizontal/contact geometry',
        'limitations':['Closure solution branch initialized from captured pose; runtime passive joints missing',
            'Five samples in one environment do not certify all geometry or causal stability',
            'Wheel-only normalized delta contribution; excludes other costs and PPO gradients']}
    for p,h in inputs.items():
        if sha(Path(p))!=h:raise ValueError('input changed')
    output.mkdir(parents=True)
    with (output/'review.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();main(a.run.resolve(),a.output_dir.resolve())
