"""Read-only measured trajectory reward counterfactual; no physics or PPO."""
import argparse,json
from pathlib import Path
import torch
from native_stand.recovery.drawback_guidance_proposal import quality,dense_reward
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.command_v6.domain.trace_schema import validate_rows,STATE,PHASE_CODES


def audit(run,output):
    run=Path(run);inputs={}
    def load(p):
        k,h=checked_input(p);inputs[k]=h;return json.loads(Path(k).read_text())
    spec=load(run/'source_eval/source_snapshot/spec.json');d=load(run/'source_eval/evaluation_source.json')
    if d['spec_sha256']!=inputs[str((run/'source_eval/source_snapshot/spec.json').resolve())]:raise ValueError('Spec identity conflict')
    cp,sha=checked_input(spec['source_checkpoint'],spec['source_sha256']);inputs[cp]=sha
    if d['checkpoint_sha256']!=sha:raise ValueError('Source checkpoint differs')
    ref=next(g for g in d['retained_evaluations'] if g['per_env'][0]['family']=='drawback_manual0001')['per_env'][0]
    validate_rows(ref['wheel_geometry_trace_100hz'],'geometry');target=torch.tensor(ref['wheel_geometry_trace_100hz'][0][:6]).reshape(2,3)
    # Native lateral=root X. Average mirrored real DrawBack centers to avoid encoding saved-pose asymmetry.
    target[0,0]=(target[0,0]-target[1,0])/2;target[1,0]=-target[0,0];target[:,1:]=target[:,1:].mean(0)
    rows=[]
    for group in [d]+d['retained_evaluations']:
        for e in group['per_env']:
            validate_rows(e['wheel_geometry_trace_100hz'],'geometry');validate_rows(e['compact_trace_100hz'],'state')
            geo=torch.tensor(e['wheel_geometry_trace_100hz']);state=torch.tensor(e['compact_trace_100hz']);q=quality(geo[:,:6].reshape(-1,2,3),geo[:,9:13],target)
            active=(state[:,0]>0)&(state[:,32]!=PHASE_CODES['initializing'])&state[:,29].bool();failed=state[:,3].bool()|state[:,4].bool()
            # Candidate only: current-family Swing pre-entry; existing old-group rewards unchanged.
            eligible=active & (state[:,1]==0) & (e['family']=='swing_candidate_from_historical_r1')
            idx=torch.where(active)[0]
            rows.append({'family':e['family'],'env_id':e['env_id'],'position_quality_first_last':[float(q['position_quality'][i]) for i in (idx[0],idx[-1])],
                'mirror_quality_first_last':[float(q['mirror_quality'][i]) for i in (idx[0],idx[-1])],
                'mirror_error_abs_peak_rad':q['mirror_error_rad'][active].abs().amax(0).tolist(),
                'counterfactual_return_weight1_per_s':float(dense_reward(q['quality'],eligible,failed).sum()),'failed_step_reward':float(dense_reward(q['quality'],eligible,failed)[failed].sum())})
    idealq=torch.tensor([-.0234,1.4318,.0234,1.4318]);cases={}
    for name,w,qj in [('target_symmetric',target,idealq),('one_wheel_15cm_away',target+torch.tensor([[0.,0.,0.],[0.,0.,.15]]),idealq),('target_joint_asymmetric',target,idealq+torch.tensor([.15,0.,0.,0.]))]:
        v=quality(w,qj,target);cases[name]={k:float(v[k]) for k in ('quality','position_quality','mirror_quality')}
    result={'target_root_m':target.tolist(),'position_width_m':.25,'mirror_width_rad':.10,'weight_per_s_candidates':[1.,3.,10.],
        'rows':rows,'scenarios':cases,'simulation':0,'optimizer_steps':0,'runnable':False,'strict_symmetry_guarantee':False,
        'unresolved':['Instantaneous positive quality can reward dwelling near DrawBack; handoff event/version not implemented',
        'Failed-step zero does not cancel earlier hovering/flight reward; root geometry does not certify support or dynamics',
        'Reward cannot force exact mirrored sampled actions or physical states',
        'Widths and weights are CPU proposal only; no runtime declaration or budget authorized',
        'This changes task preferences and is not PBRS or a certified Lyapunov function']}
    publish(output,{'audit.json':result},inputs,completion_marker=True);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=audit(a.run,a.output_dir);print(json.dumps(r,indent=2))
