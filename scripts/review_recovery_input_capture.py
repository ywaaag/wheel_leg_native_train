"""Offline real150D input/physical/action/reward review; never launches physics."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.special import ndtr
import torch
from tensordict import TensorDict
from native_stand.command_v6.domain.observation_diagnostics import summarize
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.command_v6.domain.contract import frame


def review(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';terminal_path=run/'terminal_report.json'
    s=json.loads(sp.read_text());terminal=json.loads(terminal_path.read_text())
    if terminal['status'] not in ('COMPLETED','STOPPED_BOUNDED','FAILED'):raise ValueError('Terminal run required')
    inputs=dict(checked_input(p) for p in (sp,terminal_path,run/'manifest.json'))
    inputs.update([checked_input(s['source_checkpoint'],s['source_sha256'])])
    saved=torch.load(s['source_checkpoint'],map_location='cpu',weights_only=False)
    from native_stand.command_v6.tools.model_factory import model
    with contextlib.redirect_stdout(io.StringIO()):
        actor=model(TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]),actor=True,spec=s)
    actor.load_state_dict(saved['actor'],strict=True);actor.eval()
    groups=[]
    for item in terminal['completed']:
        path=run/item['path'];inputs.update([checked_input(path)])
        d=json.loads(path.read_text());capture=d.get('input_capture')
        if (d.get('spec_sha256')!=inputs[str(sp)] or d.get('checkpoint_sha256')!=s['source_sha256'] or
                d.get('asset_sha256')!=s['asset_sha256']):raise ValueError('Capture result identity differs')
        if capture is None:raise ValueError('Declared actual input capture missing')
        raw=run/capture['path'];inputs.update([checked_input(raw,capture['sha256'])])
        with np.load(raw,allow_pickle=False) as archive:a={k:archive[k] for k in archive.files}
        valid=a['pre_active'].astype(bool);controlled=valid&~a['post_initializing'].astype(bool)
        pre=a['pre_metadata'];obs=a['pre_observation'];root=a['pre_root'];idx=capture['active_indices']
        shape=obs.shape[:2]
        angular=np.empty((*shape,3));gravity=np.empty_like(angular)
        for i in range(shape[1]):
            rotation=Rotation.from_quat(root[:,i,3:7])
            angular[:,i]=rotation.inv().apply(root[:,i,10:13]);gravity[:,i]=rotation.inv().apply(np.tile([0.,0.,-1.],(shape[0],1)))
        expected=frame(torch.tensor(angular,dtype=torch.float32).flatten(0,1),
            torch.tensor(gravity,dtype=torch.float32).flatten(0,1),
            torch.from_numpy(a['pre_command']).flatten(0,1),
            torch.from_numpy(a['pre_joint_pos'][:,:,idx]).flatten(0,1),
            torch.from_numpy(a['pre_joint_vel'][:,:,idx]).flatten(0,1),
            torch.from_numpy(a['pre_previous_action']).flatten(0,1),
            torch.from_numpy(a['pre_reference']).flatten(0,1)).numpy().reshape(*shape,25)
        errors=abs(expected-obs[:,:,:25]);latest=abs(obs[:,:,:25]-obs[:,:,125:150])
        shiftmask=valid[1:]&valid[:-1]&(pre[1:,:,1]==pre[:-1,:,1])
        shifterror=abs(obs[1:,:,25:125]-obs[:-1,:,50:150])
        predicted=[]
        with torch.inference_mode():
            x=torch.from_numpy(obs[valid])
            for batch in x.split(1024):
                predicted.append(actor(TensorDict({'policy':batch[:,:25],'history':batch[:,25:]},batch_size=[len(batch)])).numpy())
        replay=np.concatenate(predicted) if predicted else np.empty((0,6))
        mean=a['pre_mean'];std=a['distribution_std']
        clip_probability=ndtr((-1.-mean)/std)+ndtr((mean-1.)/std)
        phases=np.zeros(shape,dtype=np.int64)
        for env,e in enumerate(d['per_env']):
            entry=e.get('entry_confirmation_index')
            if entry is not None:
                elapsed=(np.arange(shape[0])-entry-1)*s['control']['policy_dt_s']
                phases[:,env]=np.where(elapsed>=5,3,np.where(elapsed>=2,2,np.where(elapsed>=0,1,0)))
        summaries=[]
        for phase,name in enumerate(('pre_entry','hold_0_2','hold_2_5','hold_5_10')):
            mask=controlled&(phases==phase);positions=np.argwhere(mask)
            ids=[(int(env),int(pre[t,env,1])) for t,env in positions]
            stat=summarize(torch.from_numpy(obs[mask]),episode_ids=ids)
            rewards={}
            for j,term in enumerate(capture['reward_names']):
                values=a['post_reward_weighted_dt'][mask,j];rawvalues=a['post_reward_raw'][mask,j]
                rewards[term]={'raw_mean':float(rawvalues.mean()) if len(values) else None,
                    'weighted_dt_sum':float(values.sum()),'weighted_per_second_mean':float(values.mean()/.01) if len(values) else None,
                    'raw_nonzero_fraction':float((rawvalues!=0).mean()) if len(values) else None}
            summaries.append({'phase':name,'observation':stat,
                'gaussian_clip_probability_mean_by_channel':clip_probability[mask].mean(0).tolist() if mask.any() else None,
                'deterministic_mean_outside_unit_fraction':(abs(mean[mask])>1).mean(0).tolist() if mask.any() else None,
                'mean_min':mean[mask].min(0).tolist() if mask.any() else None,'mean_max':mean[mask].max(0).tolist() if mask.any() else None,
                'actual_executed_clip_difference_max':float(abs(np.clip(mean[mask],-1,1)-a['post_control'][mask,18:24]).max()) if mask.any() else None,
                'rewards':rewards,'reward_total_sum':float(a['post_reward_total'][mask].sum()),
                'once_event_reward_residual_sum':float((a['post_reward_total'][mask]-a['post_reward_weighted_dt'][mask].sum(-1)).sum())})
            # Gate duty is formula readback on recorded post heights, separate
            # from actual raw nonzero counts (a gated state can have zero cost).
            height=a['post_state'][mask,6]
            summaries[-1]['height_gate_recomputed_from_frozen_spec']={
                k:{'start_m':lo,'full_m':hi,'positive_fraction':float((height>lo).mean()) if len(height) else None,
                   'full_fraction':float((height>=hi).mean()) if len(height) else None}
                for k,lo,hi in [('pitch_level',s['reward']['pitch_level_start_m'],s['reward']['pitch_level_full_m']),
                    ('roll_level',s['reward']['roll_level_start_m'],s['reward']['roll_level_full_m']),
                    ('vertical_and_level_angular',s['recovery']['standing_task']['reward']['gate_start_m'],
                        s['recovery']['standing_task']['reward']['gate_full_m'])]}
        # Each comparison uses same policy step and phase, not variance of all
        # episodes pooled; repeated deterministic states may correctly agree.
        aligned=[]
        for phase in range(4):
            moments=[]
            for t in range(shape[0]):
                mask=controlled[t]&(phases[t]==phase)
                if mask.sum()>1:moments.append(obs[t,mask].var(0))
            aligned.append({'phase':phase,'common_step_bins':len(moments),
                'mean_within_step_environment_variance':np.mean(moments,axis=0).tolist() if moments else None})
        wiring={'recomputed_scaled_frame_max_abs_error_by_dimension':errors[valid].max(0).tolist(),
            'recomputed_scaled_frame_max_abs_error':float(errors[valid].max()),
            'history_latest_vs_current_max_abs_error':float(latest[valid].max()),
            'history_shift_within_episode_max_abs_error':float(shifterror[shiftmask].max()) if shiftmask.any() else None,
            'checkpoint_forward_replay_max_abs_error':float(abs(replay-mean[valid]).max()) if len(replay) else None}
        groups.append({'family':d['evaluation_family'],'passed_envs':d['passed_envs'],
            'first_episode_valid_rows':int(valid.sum()),'controlled_rows':int(controlled.sum()),
            'initialization_rows':int((valid&~controlled).sum()),'wiring':wiring,
            'phases':summaries,'aligned_environment_variance':aligned,
            'first_control':[{ 'env_id':env,'pre_mean':mean[np.flatnonzero(controlled[:,env])[0],env].tolist(),
                'std':std[np.flatnonzero(controlled[:,env])[0],env].tolist(),
                'clip_probability':clip_probability[np.flatnonzero(controlled[:,env])[0],env].tolist()}
                for env in range(shape[1]) if controlled[:,env].any()]})
    report={'status':terminal['status'],'inputs_sha256':inputs,'source_sha256':s['source_sha256'],'groups':groups,
        'PPO':0,'limits':'Real scaled observations; variance/near-constant flags are excitation evidence,not observability or causal proof. Analytic Gaussian probabilities are not sampled trajectories. Actor replay is CPU forward,no optimizer. No critic/GAE/update interference evidence.',
        'clock_scope':'pre-action inputs; reward/post-state from same transition before reset; initialization excluded from controlled phase statistics'}
    publish(output,{'review.json':report},inputs);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();d=review(a.run,a.output_dir);print(json.dumps({'status':d['status'],'groups':[
        {'family':g['family'],'controlled_rows':g['controlled_rows'],'wiring':g['wiring'],'first_control':g['first_control'][:1]} for g in d['groups']]},indent=2))
