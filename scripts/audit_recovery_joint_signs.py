"""CPU named-coordinate wiring and measured random leg target coverage audit."""
import argparse,json
from pathlib import Path
import numpy as np
from pxr import Usd,UsdPhysics
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def audit(capture_run,random_run,output):
    capture_run=Path(capture_run).resolve();random_run=Path(random_run).resolve();inputs={}
    sp=capture_run/'source_snapshot/spec.json';s=json.loads(sp.read_text());inputs.update([checked_input(sp),checked_input(s['asset_path'],s['asset_sha256'])])
    order=s['action']['order'];leg=[0,1,3,4];records=[]
    stage=Usd.Stage.Open(s['asset_path'])
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.RevoluteJoint) and prim.GetName() in order:
            j=UsdPhysics.RevoluteJoint(prim);records.append({'name':prim.GetName(),'axis':j.GetAxisAttr().Get(),
                'body0':[str(x) for x in j.GetBody0Rel().GetTargets()],'body1':[str(x) for x in j.GetBody1Rel().GetTargets()],
                'localRot0_xyzw':[*j.GetLocalRot0Attr().Get().GetImaginary(),j.GetLocalRot0Attr().Get().GetReal()],
                'localRot1_xyzw':[*j.GetLocalRot1Attr().Get().GetImaginary(),j.GetLocalRot1Attr().Get().GetReal()],
                'limits_deg':[float(v) if np.isfinite(v) else None for v in [j.GetLowerLimitAttr().Get(),j.GetUpperLimitAttr().Get()]],'unbounded_limit_semantics':'null represents authored infinite wheel limit'})
    checks=[]
    for i in range(3):
        p=capture_run/f'evaluation_{i:02d}.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
        p=capture_run/d['input_capture']['path'];inputs.update([checked_input(p,d['input_capture']['sha256'])])
        meta=d['input_capture'];mapped=[meta['joint_names'][j] for j in meta['active_indices']]
        if mapped!=order:raise ValueError('Named joint order mismatch')
        with np.load(p) as z:a={k:z[k] for k in z.files}
        m=a['pre_active'].astype(bool)&~a['post_initializing'].astype(bool)
        q=a['pre_joint_pos'][...,meta['active_indices']];reference=a['pre_reference'];obs=a['pre_observation']
        frame_error=float(abs(obs[...,9:13][m]-(q[...,leg]-reference[...,leg])[m]*2).max())
        control=a['post_control'];expected=reference[...,leg]+np.clip(a['pre_mean'][...,leg],-1,1)*s['action']['leg_scale_rad']
        target_error=float(abs(control[...,24:28][m]-expected[m]).max())
        # Sameprestep predicted force versus heldpoststep force must not be compared as exact equality.
        checks.append({'family':d['evaluation_family'],'active_name_order':mapped,'q_frame_sign_scale_error':frame_error,
            'unlimited_leg_target_sign_scale_error':target_error,'control_count':int(m.sum())})
    p=random_run/'source_snapshot/spec.json';rs=json.loads(p.read_text());inputs.update([checked_input(p)])
    p=random_run/'evaluation_00.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
    p=random_run/d['capture']['path'];inputs.update([checked_input(p,d['capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    md=a['pre_metadata'];m=(md[...,0]==d['capture']['family_names'].index('swing_candidate_from_historical_r1'))&md[...,2].astype(bool)
    # preframe encodes(q-reference)*2; target encodes(reference+1.6clippedaction).
    # Subtracting cancelsreference; recover target-minus-preq without assumingreferencezero.
    delta=rs['action']['leg_scale_rad']*np.clip(a['sample'][...,leg],-1,1)-a['pre_obs150'][...,9:13]/2
    direction=np.array([1.,1.,-1.,1.]);signed=delta*direction
    desired=(signed>0).all(-1);clock=np.rint(a['post_state'][...,0]*100).astype(int)
    phase=[]
    for lo,hi in [(1,4),(5,10),(11,100)]:
        mask=m&(clock>=lo)&(clock<=hi);n=int(mask.sum());found=mask&desired
        phase.append({'clock_steps':[lo,hi],'samples':n,'all4_local_direction_count':int(found.sum()),
            'per_channel_desired_sign_fraction':(signed[mask]>0).mean(0).tolist() if n else None,
            'delta_target_minus_pre_q_mean_rad':delta[mask].mean(0).tolist() if n else None,
            'raw_advantage_mean_desired':float(a['advantage_raw'][...,0][found].mean()) if found.any() else None})
    result={'inputs_sha256':inputs,'USD_named_joints':records,'wiring_checks':checks,'random_coverage':phase,
        'direction_order':order,'local_leg_direction':[1,1,-1,1],'simulation':0,'optimizer_steps':0,
        'limits':['randomcapture is originalGaussian frozenB25,not currentboundedmean new25 stochastictrajectory',
            'localgeometry signs validnear savedSwingbranch; largeabsolute targets cannot be certified by sign alone',
            'directioncoincidence alone not reachable/adequate action or causalskill evidence',
            'no independent engine-appliedforce sign probe; q/target and USD axis agree but not exhaustivephysics certification']}
    publish(output,{'audit.json':result},inputs);print(json.dumps({'checks':checks,'coverage':phase},indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-run',type=Path,required=True);p.add_argument('--random-run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();audit(a.capture_run,a.random_run,a.output_dir)
