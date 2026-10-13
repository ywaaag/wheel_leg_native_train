"""CPU authoredUSD continuation scans; not runtime reset or dynamic reachability."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

NAMES=['left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch']

def audit(spec_path,output):
    p=Path(spec_path).resolve();s=json.loads(p.read_text());inputs=dict([checked_input(p)])
    lib=Path(s['recovery']['pose_library']);inputs.update([checked_input(lib,s['recovery']['pose_library_sha256']),checked_input(s['asset_path'],s['asset_sha256'])])
    poses=json.loads(lib.read_text())['poses'];swing=next(x for x in poses if x['family']=='swing_candidate_from_historical_r1' and x['split']=='train')
    drawback=next(x for x in poses if x['family']=='drawback_manual0001' and x['split']=='train')
    asset=AssetPoses(s['asset_path']);anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m']);limits={j['name']:j['limits'] for j in asset.joints}
    rotation=np.eye(4);rotation[:3,:3]=Rotation.from_quat(swing['root_quaternion_xyzw']).as_matrix()
    def measure(q,error):
        bodies=asset.forward(q);wheel=np.stack([bodies[x+'_wheel'][:3,3] for x in ['left','right']]);v=wheel-anchors
        support=asset.support(q,rotation);gap=min(swing['root_height_m']+x['lowest_z_root'] for x in support)
        return {'length_m':np.linalg.norm(v,axis=-1).tolist(),'wheel_centers_root_m':wheel.tolist(),
            'closure_max_m':float(max(error)),'joint_limit_violations':[n for n,v in q.items() if n in limits and not limits[n][0]-1e-8<=v<=limits[n][1]+1e-8],
            'fixed_root_min_ideal_plane_gap_m':float(gap),'active_q_rad':[q[n] for n in NAMES]}
    start=swing['joint_pos'];baseline=measure(start,np.linalg.norm(asset.residual(start).reshape(-1,3),axis=1))
    scans=[]
    for channel in range(4):
        for sign in [-1,1]:
            q=dict(start);path=[]
            for step in range(1,7):
                offset=sign*.025*step;active={n:start[n] for n in NAMES};active[NAMES[channel]]+=offset
                if not limits[NAMES[channel]][0]<=active[NAMES[channel]]<=limits[NAMES[channel]][1]:break
                q,error=asset.solve(active,q);row=measure(q,error);row['offset_rad']=offset;path.append(row)
                if row['closure_max_m']>1e-4 or row['joint_limit_violations']:break
            scans.append({'channel':NAMES[channel],'sign':sign,'path':path})
    # Bounded twojoint combinations per side,continuation from authoredbranch.
    pairs=[]
    for side,channels in [('left',[0,1]),('right',[2,3])]:
        for a in [-.1,-.05,0,.05,.1]:
            for b in [-.1,-.05,0,.05,.1]:
                q=dict(start);last=None
                for t in np.linspace(.2,1.,5):
                    active={n:start[n] for n in NAMES};active[NAMES[channels[0]]]+=a*t;active[NAMES[channels[1]]]+=b*t
                    if any(not limits[n][0]<=v<=limits[n][1] for n,v in active.items()):last=None;break
                    q,error=asset.solve(active,q);last=measure(q,error)
                    if last['closure_max_m']>1e-4 or last['joint_limit_violations']:break
                if last:pairs.append({'side':side,'offset_rad':[a,b],'endpoint':last})
    valid=[x for x in pairs if x['endpoint']['closure_max_m']<=1e-4 and not x['endpoint']['joint_limit_violations']]
    best={side:min([x for x in valid if x['side']==side],key=lambda x:x['endpoint']['length_m'][i]) for i,side in enumerate(['left','right'])}
    q=dict(start);bilateral=[]
    for offset in np.linspace(0,.15,16):
        active={n:start[n]+offset*sign for n,sign in zip(NAMES,[1,1,-1,1])}
        previous=dict(q);q,error=asset.solve(active,q);row=measure(q,error)
        row.update(offset_rad=float(offset),passive_increment_peak_rad=max(abs(q[n]-previous[n]) for n in q if n not in NAMES))
        bilateral.append(row)
        if row['closure_max_m']>1e-4 or row['joint_limit_violations']:break
    result={'inputs_sha256':inputs,'baseline':baseline,'drawback_saved':measure(drawback['joint_pos'],np.linalg.norm(asset.residual(drawback['joint_pos']).reshape(-1,3),axis=1)),
        'single_channel_continuations':scans,'pair_endpoints':pairs,'best_local':best,'bilateral_continuation':bilateral,'simulation':0,'optimizer_steps':0,
        'limits':['Fixed authoredroot plane gap is geometric obstacle check,not reject dynamiclift paths or reset approval',
            'No selfcollision pair detection; ideal collider lows do not certify collisionfree path',
            'Passive leastsquarescontinuation may lose/jump branch; closure/limits checked,not physical dynamicbranch certification',
            'Local ±.1/.15rad search not fullSwing-to-DrawBack trajectory or global impossibility test']}
    publish(output,{'audit.json':result},inputs);print(json.dumps({'baseline':baseline,'best_local':best},indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.spec,a.output_dir)
