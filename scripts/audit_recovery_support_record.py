"""Offline smooth geometric record proposal on actual first episodes."""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from native_stand.recovery.support_geometry_proposal import geometry
from native_stand.recovery.support_record_proposal import quality,record_step
from native_stand.command_v6.domain.trace_schema import STATE,validate_rows
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def audit(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text())
    inputs=dict([checked_input(sp)]);rows=[]
    anchors=torch.tensor(s['recovery']['standing_task']['hip_anchors_root_m'],dtype=torch.float64)
    for i in range(3):
        p=run/f'evaluation_{i:02d}.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
        if d['checkpoint_sha256']!=s['source_sha256']:raise ValueError('Wrong source')
        raw=run/d['input_capture']['path'];inputs.update([checked_input(raw,d['input_capture']['sha256'])])
        with np.load(raw) as z:original=z['post_reward_total'].copy()
        for e in d['per_env']:
            state=torch.tensor(validate_rows(e['compact_trace_100hz'],'state'),dtype=torch.float64)
            g=torch.tensor(validate_rows(e['wheel_geometry_trace_100hz'],'geometry'),dtype=torch.float64)
            geo=geometry(g[:,:6].reshape(-1,2,3),anchors,g[:,6:9])
            q=quality(geo['length_m'],torch.cos(geo['down_angle_rad']))
            active=(state[:,STATE['recovery_clock_s']]>0)&state[:,STATE['initial_valid']].bool()&(state[:,STATE['previous_mode']]!=7)
            ids=active.nonzero().flatten();values=q['quality'][ids]
            eligible=torch.ones_like(values,dtype=torch.bool) if i==0 else torch.zeros_like(values,dtype=torch.bool)
            if e['entry_confirmation_index'] is not None:eligible[ids>e['entry_confirmation_index']]=False
            best=values[0:1].clone();rewards=torch.zeros_like(values)
            for j in range(1,len(values)):
                failure=bool(state[ids[j],STATE['task_failed']] or state[ids[j],STATE['runtime_fault']])
                r,best=record_step(values[j:j+1],best,eligible=eligible[j:j+1],failed=torch.tensor([failure]),beta=.3)
                rewards[j]=r[0]
            base=torch.tensor(original[:len(state),e['env_id']],dtype=torch.float64)[ids]
            rows.append({'family':d['evaluation_family'],'env_id':e['env_id'],
                'quality_initial':float(values[0]),'quality_peak':float(values.max()),'quality_final':float(values[-1]),
                'reward_sum_beta03':float(rewards.sum()),'discounted_added_reward':float((rewards*.99**torch.arange(len(rewards))).sum()),
                'nonzero_reward_samples':int((rewards>0).sum()),'peak_side_quality':q['side'][ids].amax(0).tolist(),
                'discounted_base_controlled_return':float((base*.99**torch.arange(len(base))).sum()),
                'scope':'First post-control geometry as baseline; missing pre-first-control geometry,omitfirsttransition'} )
    scenarios=[]
    for name,values,failed in [('stall',[.235]*100,False),('improve_then_stall',[.235,.3,.4]+[.4]*97,False),
        ('oscillate',[.235,.3,.235,.3]*25,False),('same_geometry_high',[.235]*100,False),
        ('terminal_spike',[.235,.235,.9],True),('early_fail',[.235]*30,True),
        ('fully_improve',[.235,.4,.6,.8,1.],False)]:
        best=torch.tensor([values[0]],dtype=torch.float64);total=0.;disc=0.
        for j,v in enumerate(values[1:],1):
            r,best=record_step(torch.tensor([v],dtype=torch.float64),best,eligible=torch.tensor([True]),
                failed=torch.tensor([failed and j==len(values)-1]),beta=.3)
            total+=r.item();disc+=.99**j*r.item()
        scenarios.append({'name':name,'reward_sum':total,'discounted_added_reward':disc})
    result={'inputs_sha256':inputs,'actual':rows,'synthetic_quality_sequences':scenarios,
        'fixed_proposal':{'beta_per_episode':.3,'short_m':.15,'width_m':.225,'length_direction':'wide Gaussian times (1+cosdown)/2,average two sides',
            'reward':'beta*new episode quality record gain; no dt/no absorbing release/no heightgate; stopafterfirstentry',
            'runtime_wired':False,'source':'RecoveryB25','meanaux':False},
        'limitations':['Stateful best-quality reward not observed by current150D: possible hidden reward-state/critic aliasing requires review before runtime.',
            'Average permits one-sided progress; rawgeometry/safety and bilateral terminal gates required,not new asymmetry penalty.',
            'Earned progress remains onlaterfailure; atmost.3 episodebudget is not proof of correct fulltaskpreferences.',
            'Smoothquality slope on oldtrajectory doesnot establish accessible successfulactions; no newphysics evidence.',
            'Pastpost-control baseline differs from proposed initialization-completion baseline; runtime must capture exactprecontrol'],
        'simulation':0,'optimizer':0}
    publish(output,{'audit.json':result},inputs);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();d=audit(a.run,a.output_dir);print(json.dumps({'actual':d['actual'][:8],'synthetic':d['synthetic_quality_sequences']},indent=2))
