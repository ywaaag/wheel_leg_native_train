"""CPU first-episode leg target/torque/geometry alignment,identity-bound."""
import argparse,json
from pathlib import Path
import numpy as np
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,validate_rows
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def summarize(e,anchors):
    st=np.asarray(validate_rows(e['compact_trace_100hz'],'state'));c=np.asarray(validate_rows(e['control_diagnostics_100hz'],'control'));g=np.asarray(validate_rows(e['wheel_geometry_trace_100hz'],'geometry'))
    if not len(st) or len(st)!=len(c) or len(c)!=len(g):raise ValueError('Aligned complete traces required')
    active=(st[:,STATE['recovery_clock_s']]>0)&(st[:,STATE['initial_valid']]>0)&(st[:,STATE['previous_mode']]!=7)
    ids=np.flatnonzero(active);c=c[ids];g=g[ids];st=st[ids]
    leg=[0,1,3,4];q=c[:,:6][:,leg];dq=c[:,6:12][:,leg];target=c[:,28:32];raw=c[:,12:18][:,leg]
    requested=c[:,32:38][:,leg];physical=c[:,38:44][:,leg]
    length=np.linalg.norm(g[:,:6].reshape(-1,2,3)-anchors,axis=-1)
    firstloss=np.flatnonzero((st[:,10]<=2)|(st[:,11]<=2));firsttilt=np.flatnonzero(st[:,15]>.18)
    record={'env_id':e['env_id'],'family':e['family'],'first_target_rad':target[0].tolist(),'first_post_q_rad':q[0].tolist(),
        'first_target_minus_post_q_rad':(target[0]-q[0]).tolist(),'raw_action_clip_fraction':(abs(raw)>1).mean(0).tolist(),
        'joint_target_limit_clip_fraction':(abs(c[:,24:28]-target)>1e-7).mean(0).tolist(),
        'PD_requested_first_nm':requested[0].tolist(),'PD_physical_first_nm':physical[0].tolist(),
        'PD_limit_fraction':(abs(physical)>=40-1e-4).mean(0).tolist(),
        'q_range_rad':np.stack((q.min(0),q.max(0))).tolist(),'target_range_rad':np.stack((target.min(0),target.max(0))).tolist(),
        'pair_sum_left_right_q_range_rad':np.stack(((q[:,0]+q[:,1]).min(),(q[:,0]+q[:,1]).max(),(q[:,2]+q[:,3]).min(),(q[:,2]+q[:,3]).max())).tolist(),
        'pair_difference_left_right_q_range_rad':np.stack(((q[:,0]-q[:,1]).min(),(q[:,0]-q[:,1]).max(),(q[:,2]-q[:,3]).min(),(q[:,2]-q[:,3]).max())).tolist(),
        'minimum_length_m':length.min(0).tolist(),'first_contact_loss_clock_s':float(st[firstloss[0],0]) if len(firstloss) else None,
        'first_tilt_above018_clock_s':float(st[firsttilt[0],0]) if len(firsttilt) else None,
        'timeline_first100ms':[{'clock_s':float(st[i,0]),'q':q[i].tolist(),'target':target[i].tolist(),'requested_nm':requested[i].tolist(),
            'physical_nm':physical[i].tolist(),'length_m':length[i].tolist(),'tilt_rad':float(st[i,15]),'contact_n':st[i,10:12].tolist()} for i in range(len(st)) if st[i,0]<=.100001]}
    return record


def audit(run,output):
    run=Path(run).resolve();p=run/'source_eval/source_snapshot/spec.json';s=json.loads(p.read_text());inputs=dict([checked_input(p)]);anchors=np.asarray(s['recovery']['standing_task']['hip_anchors_root_m']);rows=[]
    for label,rel in [('source','source_eval/evaluation_source.json'),('new10','formal/evaluation_10_0_0.json'),('new25','formal/evaluation_25_0_0.json')]:
        p=run/rel;d=json.loads(p.read_text());inputs.update([checked_input(p)])
        if d.get('checkpoint'):inputs.update([checked_input(d['checkpoint'],d['checkpoint_sha256'])])
        groups=[d,*d['retained_evaluations']]
        rows.append({'candidate':label,'groups':[{'family':g['evaluation_family'],'per_env':[summarize(e,anchors) for e in g['per_env']]} for g in groups]})
    result={'inputs_sha256':inputs,'rows':rows,'simulation':0,'optimizer_steps':0,'limitations':[
        'policy-end actualq/velocity versus latestheld5ms PD; do not declare residual wiringfault',
        'event precedence is not causality; fullpassive/precontroljoint trajectory not present in newcheckpoint evaluation',
        'joint pair sum is descriptive nativeactive geometry,not virtualleg action mapping']}
    publish(output,{'audit.json':result},inputs);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=audit(a.run,a.output_dir)
    for item in r['rows']:
        print(item['candidate'])
        for g in item['groups']:print(g['family'],json.dumps({k:v for k,v in g['per_env'][0].items() if k!='timeline_first100ms'}))
