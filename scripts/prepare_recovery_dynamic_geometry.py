"""CPU finite nativejoint path candidates for explicit dynamic diagnostic design."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

NAMES=['left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch']


def prepare(spec_path,output):
    sp=Path(spec_path).resolve();s=json.loads(sp.read_text());inputs=dict([checked_input(sp)])
    lib=Path(s['recovery']['pose_library']);inputs.update([checked_input(lib,s['recovery']['pose_library_sha256']),checked_input(s['asset_path'],s['asset_sha256'])])
    poses=json.loads(lib.read_text())['poses'];start=next(p for p in poses if p['family']=='swing_candidate_from_historical_r1' and p['split']=='train')
    asset=AssetPoses(s['asset_path']);limits={j['name']:j['limits'] for j in asset.joints};anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m'])
    rotation=np.eye(4);rotation[:3,:3]=Rotation.from_quat(start['root_quaternion_xyzw']).as_matrix()
    paths=[]
    for contraction in [.15,.3,.6]:
        for rotation_offset in [-.2,0,.2]:
            q=dict(start['joint_pos']);rows=[];rejection=None
            for fraction in np.linspace(0,1,31):
                a=fraction*contraction;b=fraction*rotation_offset
                active={n:start['joint_pos'][n]+v for n,v in zip(NAMES,[a-b,a+b,-a+b,a+b])}
                # Currentreference is0 for this pose recipe; verify rather than silently widening output range.
                if any(abs(v)>1.6+1e-7 or not limits[n][0]<=v<=limits[n][1] for n,v in active.items()):
                    rejection='native active/action position envelope exceeded';break
                previous=dict(q);q,error=asset.solve(active,q);closure=float(max(error));violations=[n for n,v in q.items() if n in limits and not limits[n][0]-1e-8<=v<=limits[n][1]+1e-8]
                body=asset.forward(q);w=np.stack([body[side+'_wheel'][:3,3] for side in ['left','right']]);v=w-anchors
                gravity=rotation[:3,:3].T@np.array([0,0,-1]);cos=(v@gravity)/np.linalg.norm(v,axis=-1)
                support=asset.support(q,rotation);gap=min(start['root_height_m']+x['lowest_z_root'] for x in support)
                rows.append({'fraction':float(fraction),'active_q_rad':[q[n] for n in NAMES],'length_m':np.linalg.norm(v,axis=-1).tolist(),
                    'down_cosine':cos.tolist(),'closure_max_m':closure,'fixed_root_ideal_plane_min_gap_m':float(gap),
                    'passive_increment_max_rad':max(abs(q[n]-previous[n]) for n in q if n not in NAMES)})
                if closure>1e-4 or violations:rejection='closure or joint limit invalid';break
            paths.append({'contraction_offset_rad':contraction,'rotation_offset_rad':rotation_offset,'closed_path':rejection is None,
                'rejection':rejection,'path':rows,'fixed_root_plane_requires_motion':any(x['fixed_root_ideal_plane_min_gap_m']<-.001 for x in rows)})
    result={'inputs_sha256':inputs,'paths':paths,'runtime_authorized':False,'runnable':False,'simulation':0,'optimizer_steps':0,
        'scope':'Geometry paths,not motorcontrol,successfulSwingtrajectory,reset certificate or dynamicrecovery',
        'diagnostic_request_draft':{'candidate_count_cap':6,'episode_simulated_seconds_cap':3,'wall_seconds_cap':900,'PPO_updates':0,
            'detailed_storage_MiB_cap':128,'proposed_device':'shared physicalGPU0,existingUUID; reverifybefore reserve',
            'reference_schedule':'unset until geometry endpoints and actuator envelopes reviewed',
            'required_fields':['pre/post fulljoint root pose velocity','native targets/raw action/reference','5ms PD requested/clipped/applied torque',
                '1ms or explicitly bounded contact impulse by named supportcollider','wheelcenters closure','episode/reset/initialvalid/actionorigin/override mask'],
            'limitations':['No fullselfcollision or dynamics','reference0 envelope assumption requires real readback before runtime',
            'diagnosticactions require explicitauthorization and isolatedadapter; not regularpolicy or hiddencontrol',
            'short localpaths do not necessarily reachDrawBack or produce upwardforce; handoverdisabled until verifiedfullstatecondition']}}
    publish(output,{'geometry_candidates.json':result},inputs)
    print(json.dumps([{'a':x['contraction_offset_rad'],'b':x['rotation_offset_rad'],'closed':x['closed_path'],'requiresrootmotion':x['fixed_root_plane_requires_motion'],'endpoint':x['path'][-1] if x['path'] else None} for x in paths],indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();prepare(a.spec,a.output_dir)
