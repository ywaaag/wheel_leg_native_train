"""CPU counterfactual coefficient audit; no simulator/PPO or checkpoint export."""
import contextlib
import copy
import io
import json
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.recovery.mean_auxiliary import MeanAuxiliary,declaration
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish


def audit(run,training,output):
    run=Path(run).resolve();training=Path(training).resolve();output=Path(output).resolve()
    spec_path=run/'source_snapshot/spec.json';spec=json.loads(spec_path.read_text())
    saved_path=Path(spec['source_checkpoint']);inputs=dict([checked_input(spec_path),checked_input(saved_path,spec['source_sha256']),
        checked_input(training/'metrics.jsonl'),checked_input(training/'source_snapshot/spec.json')])
    saved=torch.load(saved_path,map_location='cpu',weights_only=False)
    batches={};family_names=[]
    for i in range(3):
        p=run/f'evaluation_{i:02d}.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
        raw=run/d['input_capture']['path'];inputs.update([checked_input(raw,d['input_capture']['sha256'])])
        if d['checkpoint_sha256']!=spec['source_sha256']:raise ValueError('Source capture identity differs')
        with np.load(raw) as a:
            mask=a['pre_active'].astype(bool)&~a['post_initializing'].astype(bool)
            # Same first0.30 recovery window for old/new initial states, not long
            # steady samples that could hide initial transient output drift.
            mask &= a['pre_metadata'][:,:,4]<=.30+1e-6
            batches[d['evaluation_family']]=torch.from_numpy(a['pre_observation'][mask]).clone()
        family_names.append(d['evaluation_family'])
    metrics=[json.loads(x) for x in (training/'metrics.jsonl').read_text().splitlines()]
    eligible=sum(x['wheel_mean_auxiliary']['eligible_count'] for x in metrics)
    denominator=sum(x['wheel_mean_auxiliary']['controlled_denominator'] for x in metrics)
    mass=eligible/denominator
    ratios=[x['wheel_mean_auxiliary']['first_step']['weighted_aux_actor_norm']/
        max(1e-12,x['wheel_mean_auxiliary']['first_step']['incoming_PPO_entropy_actor_norm_after_clip']) for x in metrics]
    rng=torch.get_rng_state().clone();rows=[];baseline=None
    try:
        for coefficient in (0.,.001,.01,.03,.1):
            with contextlib.redirect_stdout(io.StringIO()):
                dummy=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1])
                actor=model(dummy,actor=True,spec=spec);critic=model(dummy,actor=False,spec=spec)
            actor.load_state_dict(saved['actor'],strict=True);critic.load_state_dict(saved['critic'],strict=True)
            for role,network in [('actor',actor),('critic',critic)]:
                if saved['parameter_names'][role]!=list(dict(network.named_parameters())):raise ValueError('Adam name mapping differs')
            opt=torch.optim.Adam([*actor.parameters(),*critic.parameters()],lr=spec['ppo']['learning_rate'])
            opt.load_state_dict(copy.deepcopy(saved['optimizer']))
            actor.eval();cfg=declaration();cfg['coefficient']=coefficient
            aux=MeanAuxiliary(actor,cfg,max_grad_norm=1.)
            x=batches[family_names[0]]
            aux.batch=x.clone();aux.eligible_count=len(x)
            # Ratio proxy preserves measured eligibility mass; explicitly NOT
            # reconstructed on-policy rollout or actual PPO gradient.
            aux.denominator=round(len(x)/mass)
            def evaluate():
                with torch.no_grad():return {f:actor(TensorDict({'policy':z[:,:25],'history':z[:,25:]},batch_size=[len(z)])).clone()
                    for f,z in batches.items()}
            before=evaluate();before_actor=copy.deepcopy(actor.state_dict());before_critic=copy.deepcopy(critic.state_dict())
            # Zero incoming actor gradients allow Adam's inherited moments to
            # decay and move parameters. A coefficient0 control isolates this.
            for p in actor.parameters():p.grad=torch.zeros_like(p)
            for p in critic.parameters():p.grad=None
            aux.before_step(opt,(),{})
            opt.step()  # Exactly one CPU counterfactual Adam step, NOT PPO.
            after=evaluate()
            if baseline is None:baseline={f:z.clone() for f,z in after.items()}
            groups=[]
            for f in batches:
                change=after[f]-before[f];isolated=after[f]-baseline[f]
                groups.append({'family':f,'sample_count':len(batches[f]),
                    'mean_output_before_by_channel':before[f].mean(0).tolist(),
                    'mean_output_delta_after_one_CPU_Adam_step':change.mean(0).tolist(),
                    'max_abs_output_delta':float(change.abs().max()),
                    'mean_delta_vs_zero_coefficient_Adam_control':isolated.mean(0).tolist(),
                    'max_abs_delta_vs_Adam_control':float(isolated.abs().max()),
                    'wheel_clip_fraction_before':(before[f][:,[2,5]].abs()>1).float().mean(0).tolist(),
                    'wheel_clip_fraction_after':(after[f][:,[2,5]].abs()>1).float().mean(0).tolist()})
            row={'coefficient':coefficient,'hook':aux.summary(),'groups':groups,
                'critic_unchanged':all(torch.equal(v,critic.state_dict()[k]) for k,v in before_critic.items()),
                'std_parameter_delta':(actor.state_dict()['distribution.std_param']-before_actor['distribution.std_param']).tolist(),
                'actor_parameter_max_delta':max(float((v-actor.state_dict()[k]).abs().max()) for k,v in before_actor.items()),
                'estimated_real_training_aux_incoming_clipped_norm_ratio':sum(ratios)/len(ratios)*coefficient/.001}
            rows.append(row)
    finally:torch.set_rng_state(rng)
    result={'inputs_sha256':inputs,'cases':rows,'recorded_eligible_mass':mass,
        'simulation':0,'online_PPO':0,'offline_counterfactual_Adam_steps':len(rows),'exported_checkpoints':0,
        'scope':'Identical frozenB25 each candidate; first0.30s deterministic savedinputs; zero incoming actor gradient; inherited Adam; oneCPUstep each. Eligibility denominator proxy from prior formal. No actual PPO gradient/direction/minibatch/storage replay; projected norm ratios only linear scaling estimates,not convergence evidence.',
        'proposal':{'coefficient':.03,'reason':'30x previous coefficient estimates ~9.47% of incoming already-clipped actor norm; bounded first candidate,not proven optimum',
            'runtime_authorized':False,'runtime_budget_proposal':{'source_wall_s':900,'smoke_updates':10,'smoke_wall_s':900,'formal_updates':25,'formal_wall_s':3600,
                'formal_full_evaluations':[10,25],'inclusive_updates':35,'sample_limit':286720,'chain_wall_s':5460},
            'preserve':'sourceB25,std/Adam,reward,obs,physics,26/25/13sampling; only fixed auxiliary coefficient changes'}}
    publish(output,{'audit.json':result},inputs);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-run',type=Path,required=True)
    p.add_argument('--training-run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    print(json.dumps(audit(a.capture_run,a.training_run,a.output_dir),indent=2))
