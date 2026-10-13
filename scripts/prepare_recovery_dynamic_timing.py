"""CPU validate exact overlapped nativejoint schedules; publish nonrunnable plan."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.recovery.asset_poses import AssetPoses
from native_stand.recovery.dynamic_diagnostic import target,encode_native,LEG_ORDER,VERSION
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def prepare(spec_path,output):
    p=Path(spec_path).resolve();s=json.loads(p.read_text());inputs=dict([checked_input(p)])
    library=Path(s['recovery']['pose_library']);inputs.update([checked_input(library,s['recovery']['pose_library_sha256']),checked_input(s['asset_path'],s['asset_sha256'])])
    pose=next(p for p in json.loads(library.read_text())['poses'] if p['family']=='swing_candidate_from_historical_r1' and p['split']=='train')
    asset=AssetPoses(s['asset_path']);limits={j['name']:j['limits'] for j in asset.joints};initial=np.array([pose['joint_pos'][n] for n in LEG_ORDER]);anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m'])
    rotation=np.eye(4);rotation[:3,:3]=Rotation.from_quat(pose['root_quaternion_xyzw']).as_matrix();rows=[]
    for duration in [.12,.24]:
        for delay in [0.,.04,.08]:
            times=np.arange(round((duration+delay+.1)/.001)+1)*.001
            targets=np.stack([target(initial,t,contraction_rad=.3,rotation_rad=.2,duration_s=duration,contraction_delay_s=delay) for t in times])
            # CPU geometry at actualpolicy command timestamps,plus finalendpoint.
            indices=sorted(set(list(range(0,len(times),10))+[len(times)-1]));q=dict(pose['joint_pos']);trace=[];error=None
            for index in indices:
                qt=targets[index]
                try:encode_native(qt,np.zeros(4))
                except ValueError as e:error=str(e);break
                q,residual=asset.solve(dict(zip(LEG_ORDER,qt)),q)
                violation=[n for n,v in q.items() if n in limits and not limits[n][0]-1e-8<=v<=limits[n][1]+1e-8]
                b=asset.forward(q);wheel=np.stack([b[side+'_wheel'][:3,3] for side in ('left','right')]);length=np.linalg.norm(wheel-anchors,axis=-1)
                support=asset.support(q,rotation);gap=min(pose['root_height_m']+p['lowest_z_root'] for p in support)
                trace.append({'time_s':float(times[index]),'qtarget_rad':qt.tolist(),'length_m':length.tolist(),
                    'closure_max_m':float(max(residual)),'fixed_root_plane_min_gap_m':float(gap)})
                if max(residual)>1e-4 or violation:error='closure/jointlimit invalid';break
            velocity=np.diff(targets,axis=0)/.001;accel=np.diff(velocity,axis=0)/.001
            rows.append({'id':f't{round(duration*1000)}_delay{round(delay*1000)}','duration_s':duration,'contraction_delay_s':delay,
                'contraction_rad':.3,'rotation_rad':.2,'geometry_command_samples_valid':error is None,'failure':error,
                'target_speed_peak_rad_s':abs(velocity).max(0).tolist(),'target_accel_peak_rad_s2':abs(accel).max(0).tolist(),
                'samples':trace,'root_motion_needed':any(p['fixed_root_plane_min_gap_m']<-.001 for p in trace)})
    result={'version':VERSION,'inputs_sha256':inputs,'candidates':rows,'runnable':False,'runtime_authorized':False,
        'PPO':0,'simulation':0,'diagnostic_contract':{'initial':'savedSwingfullstate,existingpassivesettlevalidation',
            'schedule_clock_origin':'firstcontrolledtransition aftervalidinit,neverwallclock','action_origin':'explicit_diagnostic',
            'legs':'override4 explicitnativepositiontargets onlyduringdiagnostic','wheels':'same frozenboundedmeanactor targets,no hiddenzero/brake',
            'after_schedule':'holdfinallegtarget for.1sec thenstoptrial,no automaticpolicyhandover',
            'bounds':'6trials,3secondsmaxeachincludinginit,900wallinclcleanup,128MiB detailedcap;UNAUTHORIZED',
            'early_exit':['nonfinite','closure>.005m','originaltiltfailure','targetoutsideenvelope','initializationinvalid','wall/storageceiling'],
            'measurements':'named1mscontactsandfullstate;5msPDtorques;100Hzcommandandactionorigin',
            'preconditions_unresolved':['runtimeadapterandcontactproducer','actualreference/sensorsemantics','substepcapturevalidated','independentauthorization']},
        'limits':['quintic targetvelocity not actualjointvelocity; no effort feasibility guarantee',
          'geometry at commandtimestamps does not validate inertia/passivebranchcontact/selfcollision',
          'endpoint.297m length not DrawBack; no successfuldynamictrajectory or full recovery claim']}
    publish(output,{'timing_plan.json':result},inputs);print(json.dumps([{k:v for k,v in x.items() if k!='samples'} for x in rows],indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();prepare(a.spec,a.output_dir)
