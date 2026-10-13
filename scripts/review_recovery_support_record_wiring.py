"""Once-terminal readback of reward record, actual geometry and unchanged actor."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import torch
from native_stand.recovery.support_geometry_proposal import geometry
from native_stand.recovery.support_record_proposal import quality
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def review(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';spec=json.loads(sp.read_text())
    t=json.loads((run/'terminal_report.json').read_text());inputs=dict(checked_input(p) for p in (sp,run/'terminal_report.json'))
    groups=[];anchors=torch.tensor(spec['recovery']['standing_task']['hip_anchors_root_m'],dtype=torch.float64)
    from native_stand.recovery.asset_poses import AssetPoses
    asset=AssetPoses(spec['asset_path'])
    for item in t['completed']:
        p=run/item['path'];d=json.loads(p.read_text());inputs.update([checked_input(p)])
        raw=run/d['input_capture']['path'];inputs.update([checked_input(raw,d['input_capture']['sha256'])])
        if d['checkpoint_sha256']!=spec['source_sha256']:raise ValueError('Actor identity differs')
        with np.load(raw) as z:a={k:z[k] for k in z.files}
        x=a['support_record_transition'];valid=a['pre_active'].astype(bool)
        active=valid&~a['post_initializing'].astype(bool)
        reward=a['post_reward_weighted_dt'][:,:,d['input_capture']['reward_names'].index('support_record_progress')]
        expected=.3*np.maximum(x[:,:,2]-x[:,:,1],0)*x[:,:,5]*(1-x[:,:,6])
        control=a['post_control'];joint=a['pre_joint_pos'][:,:,d['input_capture']['active_indices']]
        # True precontrol geometry reconstructed from captured active joints on
        # the published closed-chain branch,not assumed post-firstcontrol pose.
        # Instead baseline audit uses same before() snapshot and exactfirsteligible
        # relation; independently re-evaluate postgeometry from rawgeom trace.
        rows=[]
        for env,e in enumerate(d['per_env']):
            indices=np.flatnonzero(valid[:,env]);record=x[indices,env];first=np.flatnonzero(record[:,5]>0)
            g=torch.tensor(e['wheel_geometry_trace_100hz'],dtype=torch.float64)
            gg=geometry(g[:,:6].reshape(-1,2,3),anchors,g[:,6:9]);q=quality(gg['length_m'],torch.cos(gg['down_angle_rad']))['quality'].numpy()
            post_error=float(abs(q-record[:,2]).max())
            baseline_error=None
            if len(first):
                index=indices[first[0]]
                authored=asset.forward(dict(zip(d['input_capture']['joint_names'],a['pre_joint_pos'][index,env].tolist())))
                centers=torch.tensor(np.stack([authored[side+'_wheel'][:3,3] for side in ('left','right')])[None],dtype=torch.float64)
                gravity=torch.tensor(Rotation.from_quat(a['pre_root'][index,env,3:7]).inv().apply([0.,0.,-1.])[None],dtype=torch.float64)
                pregeo=geometry(centers,anchors,gravity)
                preq=quality(pregeo['length_m'],torch.cos(pregeo['down_angle_rad']))['quality'].item()
                baseline_error=float(abs(preq-record[first[0],0]))
            rows.append({'env_id':env,'initial_valid':e['initial_valid'],'passed':e['success'],
                'baseline_at_first_eligible':float(record[first[0],0]) if len(first) else None,
                'first_best_equals_prequality':bool(abs(record[first[0],1]-record[first[0],0])<1e-7) if len(first) else None,
                'baseline_pre_fulljoint_USD_FK_quality_error':baseline_error,
                'reward_sum':float(reward[indices,env].sum()),'nonzero_reward_steps':int((reward[indices,env]>0).sum()),
                'maximum_budget':float(.3*(1-record[first[0],0])) if len(first) else 0.,
                'post_geometry_quality_max_error':post_error,
                'within_episode_record_non_decreasing':bool((np.diff(record[first[0]:,3])>=-1e-7).all()) if len(first) else None,
                'failure_steps_reward_zero':bool((reward[indices,env][record[:,6]>0]==0).all()),
                'episode_ids_unique':np.unique(a['pre_metadata'][indices,env,1]).tolist(),
                'first_control_pre_mean':a['pre_mean'][indices[np.flatnonzero(active[indices,env])[0]],env].tolist()})
        checks={'reward_formula_max_error':float(abs(reward[valid]-expected[valid]).max()),
            'raw_reward_weight_max_error':float(abs(.3*a['post_reward_raw'][:,:,d['input_capture']['reward_names'].index('support_record_progress')][valid]-reward[valid]).max()),
            'initialization_reward_zero':bool((reward[valid&~active]==0).all()),
            'failure_reward_zero':all(r['failure_steps_reward_zero'] for r in rows),
            'all_budget_within_cap':all(r['reward_sum']<=r['maximum_budget']+1e-6 for r in rows),
            'post_geometry_matches':max(r['post_geometry_quality_max_error'] for r in rows)<1e-5}
        checks['baseline_exact_readback']=all(r['first_best_equals_prequality'] and
            r['baseline_pre_fulljoint_USD_FK_quality_error']<1e-4 for r in rows) if d['evaluation_family']=='swing_candidate_from_historical_r1' else all(r['baseline_at_first_eligible'] is None for r in rows)
        checks['old_family_reward_zero']=d['evaluation_family']=='swing_candidate_from_historical_r1' or all(r['reward_sum']==0 for r in rows)
        groups.append({'family':d['evaluation_family'],'passed_envs':d['passed_envs'],'checks':checks,'rows':rows})
    result={'inputs_sha256':inputs,'status':t['status'],'groups':groups,'simulation_performed_in_review':0,'PPO':0,
        'wiring_pass':len(groups)==3 and all(g['checks']['reward_formula_max_error']<1e-6 and g['checks']['initialization_reward_zero'] and
            g['checks']['raw_reward_weight_max_error']<1e-6 and g['checks']['old_family_reward_zero'] and g['checks']['failure_reward_zero'] and g['checks']['all_budget_within_cap'] and g['checks']['post_geometry_matches'] and g['checks']['baseline_exact_readback'] for g in groups),
        'scope':'Deterministic frozenactor reward readback; no learning/effect claim; exact baseline uses runtimeprecontrol snapshot'}
    publish(output,{'review.json':result},inputs);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();d=review(a.run,a.output_dir);print(json.dumps(d,indent=2))
