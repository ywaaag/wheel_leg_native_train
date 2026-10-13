"""Once-completed migration review: probability mean replay and full retained gates."""
import argparse,json
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def review(run,output):
    run=Path(run).resolve();p=run/'source_snapshot/spec.json';s=json.loads(p.read_text());inputs=dict([checked_input(p)])
    p=run/'terminal_report.json';t=json.loads(p.read_text());inputs.update([checked_input(p)])
    if t['status']!='COMPLETED':raise ValueError('Incomplete migration evaluation')
    inputs.update([checked_input(s['source_checkpoint'],s['source_sha256'])]);saved=torch.load(s['source_checkpoint'],map_location='cpu',weights_only=False)
    obs=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);actor=model(obs,actor=True,spec=s)
    actor.load_state_dict(saved['actor'],strict=True);actor.eval();base=dict(s);base.pop('action_distribution');original=model(obs,actor=True,spec=base);original.load_state_dict(saved['actor'],strict=True);original.eval()
    rows=[]
    for item in t['completed']:
        p=run/item['path'];d=json.loads(p.read_text());inputs.update([checked_input(p)])
        if d['checkpoint_sha256']!=s['source_sha256']:raise ValueError('Checkpoint differs')
        p=run/d['input_capture']['path'];inputs.update([checked_input(p,d['input_capture']['sha256'])])
        with np.load(p) as z:a={k:z[k] for k in z.files}
        valid=a['pre_active'].astype(bool);v=torch.tensor(a['pre_observation'][valid]);td=TensorDict({'policy':v[:,:25],'history':v[:,25:]},batch_size=[len(v)])
        threads=torch.get_num_threads();torch.set_num_threads(1)
        try:
            with torch.inference_mode():pred=actor(td).numpy();before=original(td).numpy()
        finally:torch.set_num_threads(threads)
        target=before.copy();target[:,[2,5]]=np.tanh(target[:,[2,5]])
        runtime=a['pre_mean'][valid];controlled=valid&~a['post_initializing'].astype(bool);means=a['pre_mean'][controlled];std=a['distribution_std'][controlled]
        # Independent quadrature expected physical stochastic exploration on actual migrated states.
        from numpy.polynomial.hermite import hermgauss
        nodes,w=hermgauss(64);w=w/np.sqrt(np.pi);x=means[:,[2,5],None]+np.sqrt(2)*std[:,[2,5],None]*nodes
        clipped=np.clip(x,-1,1);avg=clipped@w;var=np.maximum((clipped*clipped)@w-avg*avg,0)
        rows.append({'family':d['evaluation_family'],'passed_envs':d['passed_envs'],'accepted':d['accepted'],
            'runtime_mean_replay_max_error':float(abs(pred-runtime).max()),'wheel_transform_replay_error':float(abs(pred-target).max()),
            'std_source_error':float(abs(a['distribution_std']-saved['actor']['distribution.std_param'].numpy()).max()),
            'expected_within_state_wheel_std_rad_s':(np.sqrt(var).mean(0)*100).tolist(),
            'mean_wheel_action_range':np.stack((means[:,[2,5]].min(0),means[:,[2,5]].max(0))).tolist(),
            'mean_peak_height_m':float(np.mean([e['height_peak_m'] for e in d['per_env']])),
            'mean_duration_s':float(np.mean([e['continuous_s'] for e in d['per_env']])),
            'entry_count':sum(e['entry_confirmation_index'] is not None for e in d['per_env']),
            'per_env':[{'env_id':e['env_id'],'initial_valid':e['initial_valid'],'failed_checks':e['standing_failed_checks'],
                'hold_observed_s':e['post_rise_observed_s'],'hold_complete':e['hold_window_complete'],'termination':e['termination_reason']} for e in d['per_env']]})
    result={'inputs_sha256':inputs,'rows':rows,'old_groups_preserved':all(x['accepted'] for x in rows if x['family']!='swing_candidate_from_historical_r1'),
        'simulation':0,'optimizer_updates':0,'limitations':['expected stochastic std on actual deterministic candidate states,not randomruntime measurement','same weights/newdistribution is behavior intervention,not newlearnedcheckpoint']}
    publish(output,{'review.json':result},inputs);print(json.dumps(rows,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();review(a.run,a.output_dir)
