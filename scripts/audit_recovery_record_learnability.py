"""CPU-only attribution of record reward and clipped action aliases; no learning."""
import argparse,itertools,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,validate_rows
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def factors(centers,anchors,gravity):
    v=centers-anchors;l=np.linalg.norm(v,axis=-1)
    return (l,v/l[:,None],gravity/np.linalg.norm(gravity))


def score(f):
    l,u,g=f
    return float(np.mean(np.exp(-((l-.15)/.225)**2)*(1+np.clip(u@g,-1,1))/2))


def attribution(old,new):
    # Exact Shapley decomposition of a measured geometric change,not causal dynamics.
    parts=np.zeros(3)
    for order in itertools.permutations(range(3)):
        state=list(old);before=score(state)
        for i in order:
            state[i]=new[i];after=score(state);parts[i]+=(after-before)/6;before=after
    return parts


def audit(capture_run,training_run,output):
    capture_run=Path(capture_run).resolve();training_run=Path(training_run).resolve()
    sp=capture_run/'source_snapshot/spec.json';s=json.loads(sp.read_text());inputs=dict([checked_input(sp)])
    anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m'])
    inputs.update([checked_input(s['asset_path'],s['asset_sha256'])])
    from native_stand.recovery.asset_poses import AssetPoses
    asset=AssetPoses(s['asset_path'])
    p=capture_run/'evaluation_00.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
    if d['checkpoint_sha256']!=s['source_sha256']:raise ValueError('Unexpected source identity')
    p=capture_run/d['input_capture']['path'];inputs.update([checked_input(p,d['input_capture']['sha256'])])
    with np.load(p) as z:a={k:z[k] for k in z.files}
    events=[];returns=[]
    reward_idx=d['input_capture']['reward_names'].index('support_record_progress')
    for env,e in enumerate(d['per_env']):
        ids=np.flatnonzero(a['pre_active'][:,env]);g=np.asarray(validate_rows(e['wheel_geometry_trace_100hz'],'geometry'))
        st=np.asarray(validate_rows(e['compact_trace_100hz'],'state'));x=a['support_record_transition'][ids,env]
        first=int(np.flatnonzero(x[:,5]>0)[0]);idx=ids[first]
        pose=asset.forward(dict(zip(d['input_capture']['joint_names'],a['pre_joint_pos'][idx,env].tolist())))
        centers=np.stack([pose[side+'_wheel'][:3,3] for side in ('left','right')])
        gravity=Rotation.from_quat(a['pre_root'][idx,env,3:7]).inv().apply([0,0,-1])
        best=factors(centers,anchors,gravity)
        baseline_error=abs(score(best)-float(x[first,0]))
        for j in range(first,len(ids)):
            post=factors(g[j,:6].reshape(2,3),anchors,g[j,6:9])
            if x[j,5] and x[j,2]>x[j,1]:
                pieces=attribution(best,post)
                if x[j,4]>0:
                    events.append({'env_id':env,'policy_index':int(ids[j]),'recovery_clock_s':float(st[j,STATE['recovery_clock_s']]),
                        'reward':float(x[j,4]),'deltaQ_parts_length_leg_direction_body_rotation':pieces.tolist(),
                        'sum_error':abs(float(pieces.sum())-(score(post)-score(best))),
                        'tilt_rad':float(st[j,STATE['tilt_rad']]),'leg_length_m':post[0].tolist(),
                        'leg_target_after_limit_rad':a['post_control'][ids[j],env,28:32].tolist()})
                best=post
        controlled=x[:,5].astype(bool);base=a['post_reward_total'][ids,env]-a['post_reward_weighted_dt'][ids,env,reward_idx]
        bonus=a['post_reward_weighted_dt'][ids,env,reward_idx];used=np.flatnonzero(controlled)
        discount=.99**np.arange(len(used))
        returns.append({'env_id':env,'baseline_FK_quality_error':baseline_error,
            'original_discounted_return':float(base[used]@discount),'added_discounted_return':float(bonus[used]@discount),
            'added_return':float(bonus[used].sum()),'controlled_steps':len(used),
            'terminal_total_reward':float(a['post_reward_total'][ids[-1],env])})
    candidates=[]
    for label,rel in [('source','source_eval/evaluation_source.json'),('new10','formal/evaluation_10_0_0.json'),('new25','formal/evaluation_25_0_0.json')]:
        p=training_run/rel;raw=json.loads(p.read_text());inputs.update([checked_input(p)])
        if raw.get('checkpoint'):inputs.update([checked_input(raw['checkpoint'],raw['checkpoint_sha256'])])
        per=[]
        for e in raw['per_env']:
            st=np.asarray(validate_rows(e['compact_trace_100hz'],'state'));c=np.asarray(validate_rows(e['control_diagnostics_100hz'],'control'))
            if len(st)!=len(c):raise ValueError('Trace alignment differs')
            valid=(st[:,STATE['recovery_clock_s']]>0)&(st[:,STATE['initial_valid']]>0)&(st[:,STATE['previous_mode']]!=7)
            c=c[valid];v=st[valid];mean=c[:,12:18][:,[2,5]];clipped=c[:,18:24][:,[2,5]]
            per.append({'env_id':e['env_id'],'controlled_samples':len(c),'raw_wheel_range':np.stack((mean.min(0),mean.max(0))).tolist(),
                'clipped_wheel_unique_pairs':np.unique(np.round(clipped,7),axis=0).tolist(),
                'leg_raw_clip_fraction':np.mean(abs(c[:,12:18][:,[0,1,3,4]])>1,axis=0).tolist(),
                'first_leg_target_rad':c[0,28:32].tolist(),'last_leg_target_rad':c[-1,28:32].tolist(),
                'first_actual_leg_q_rad':c[0,:6][[0,1,3,4]].tolist(),'last_actual_leg_q_rad':c[-1,:6][[0,1,3,4]].tolist(),
                'terminal_tilt_rad':float(v[-1,STATE['tilt_rad']])})
        candidates.append({'candidate':label,'checkpoint_sha256':raw['checkpoint_sha256'],'per_env':per})
    sums=np.sum([e['deltaQ_parts_length_leg_direction_body_rotation'] for e in events],axis=0)
    result={'inputs_sha256':inputs,'events':events,'attribution_sum':sums.tolist(),'returns':returns,'candidates':candidates,
        'simulation':0,'optimizer_steps':0,'limitations':['Shapley is geometric accounting,not causal attribution or PPO gradient.',
        'Original return includes failure reward; positive bonus cannot be compared as percentage of a negative net return.',
        'Frozen deterministic control alias does not imply PPO policy gradient zero; random train detailed return/advantage/critic not captured.',
        'Exactrewardevents use wiring PPO0 frozenB25; candidate trajectories lack perstep reward and pre150D,not claimed replay.']}
    publish(output,{'audit.json':result},inputs)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-run',type=Path,required=True);p.add_argument('--training-run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();r=audit(a.capture_run,a.training_run,a.output_dir);print(json.dumps({'attribution_sum':r['attribution_sum'],'return_env0':r['returns'][0],'events_env0':[e for e in r['events'] if e['env_id']==0],'candidate_env0':[(e['candidate'],e['per_env'][0]) for e in r['candidates']]},indent=2))
