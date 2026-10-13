"""Offline two independent proposal costs on actual B25 recorded trajectories."""
import json
from pathlib import Path
import numpy as np
import torch
from native_stand.recovery.proposal_costs import wheel_mean_excess,low_height_wheel_effort
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def calibrate(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';spec=json.loads(sp.read_text())
    inputs=dict([checked_input(sp)]);groups=[]
    for i in range(3):
        path=run/f'evaluation_{i:02d}.json';inputs.update([checked_input(path)]);d=json.loads(path.read_text())
        raw=run/d['input_capture']['path'];inputs.update([checked_input(raw,d['input_capture']['sha256'])])
        with np.load(raw,allow_pickle=False) as z:a={k:z[k] for k in z.files}
        valid=a['pre_active'].astype(bool)&~a['post_initializing'].astype(bool)
        h=torch.from_numpy(a['post_state'][:,:,6]);effort=torch.from_numpy(a['post_control'][:,:,38:44])
        physical_cost=low_height_wheel_effort(h,effort).numpy()
        eligible=valid.copy()
        if d['evaluation_family']!='swing_candidate_from_historical_r1':eligible[:]=False
        for env,e in enumerate(d['per_env']):
            entry=e.get('entry_confirmation_index')
            if entry is not None:eligible[entry+1:,env]=False
        mean=torch.from_numpy(a['pre_mean']).clone().requires_grad_(True)
        term=wheel_mean_excess(mean,torch.from_numpy(eligible))
        loss=.001*term[torch.from_numpy(valid)].mean();loss.backward()
        raw_reward=a['post_reward_weighted_dt'][valid].sum(-1)
        new_reward=-.1*.01*physical_cost[valid]
        groups.append({'family':d['evaluation_family'],'controlled_count':int(valid.sum()),
            'mean_excess_auxiliary':{'coefficient':.001,'margin':.9,'raw_mean':float(term.detach()[valid].mean()),
                'weighted_loss_per_controlled_sample':float(loss.detach()),
                'mean_output_gradient_abs_max':float(mean.grad.abs().max()),
                'eligible_count':int(eligible.sum()),'old_group_loss_exactly_zero':bool(not eligible.any())},
            'low_wheel_effort_reward':{'weight_per_second':-.1,'policy_dt_s':.01,
                'added_cost_mean_per_second':float(new_reward.mean()/.01),
                'added_cost_per_episode':float(new_reward.sum()/8),
                'original_continuous_reward_per_episode':float(raw_reward.sum()/8),
                'added_cost_vs_positive_lift_sum':float(abs(new_reward.sum())/max(1e-12,a['post_reward_weighted_dt'][valid,d['input_capture']['reward_names'].index('lift')].sum())),
                'sample_gate_nonzero_fraction':float((physical_cost[valid]>0).mean())}})
    data={'inputs_sha256':inputs,'groups':groups,'simulation':0,'optimizer_steps':0,
        'scope':'CPU proposal costs and output gradients only; no actor modification, no critic/PPO gradient replay, no policy-invariance/stability guarantees',
        'independent_proposals':{
            'mean_excess':{'source':spec['source_checkpoint'],'variable':'Swing pre-entry wheel mean-only auxiliary loss',
                'preserve':'std/Adam/reward/control/observation/sampling/assessment unchanged',
                'runnable':False,'missing':'actual trainer optimizer hook,mask semantics,wiring tests,new declaration and runtime budget'},
            'low_wheel_effort':{'source':spec['source_checkpoint'],'variable':'one bounded low-height physical wheel effort reward term',
                'preserve':'actor/critic/Adam/std/control/observation/sampling/assessment unchanged',
                'runnable':False,'missing':'reward schema+domain+runtime connection,independent tests,new declaration and runtime budget'}}}
    publish(output,{'calibration.json':data},inputs);return data

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();print(json.dumps(calibrate(a.run,a.output_dir),indent=2))
