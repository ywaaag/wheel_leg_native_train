"""CPU full-return comparisons of geometric target candidates, no simulation."""
import json
from pathlib import Path
import torch
from native_stand.recovery.support_geometry_proposal import geometry,target_terms
from native_stand.command_v6.domain.trace_schema import STATE,validate_rows
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def discounted(r):return float((r*.99**torch.arange(len(r),dtype=r.dtype)).sum())

def audit(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';s=json.loads(sp.read_text())
    inputs=dict([checked_input(sp)]);actual=[]
    anchors=torch.tensor(s['recovery']['standing_task']['hip_anchors_root_m'],dtype=torch.float64)
    for i in range(3):
        p=run/f'evaluation_{i:02d}.json';d=json.loads(p.read_text());inputs.update([checked_input(p)])
        raw=run/d['input_capture']['path'];inputs.update([checked_input(raw,d['input_capture']['sha256'])])
        import numpy as np
        with np.load(raw) as z:
            valid=z['pre_active'].astype(bool)&~z['post_initializing'].astype(bool)
            rewards=z['post_reward_total'].copy();lift=z['post_reward_weighted_dt'][:,:,d['input_capture']['reward_names'].index('lift')].copy()
        for e in d['per_env']:
            state=torch.tensor(validate_rows(e['compact_trace_100hz'],'state'),dtype=torch.float64)
            g=torch.tensor(validate_rows(e['wheel_geometry_trace_100hz'],'geometry'),dtype=torch.float64)
            geom=geometry(g[:,:6].reshape(-1,2,3),anchors,g[:,6:9])
            mask=torch.tensor(valid[:len(state),e['env_id']]);eligible=mask.clone() if i==0 else torch.zeros_like(mask)
            if e['entry_confirmation_index'] is not None:eligible[e['entry_confirmation_index']+1:]=False
            base=torch.tensor(rewards[:len(state),e['env_id']],dtype=torch.float64)
            l=torch.tensor(lift[:len(state),e['env_id']],dtype=torch.float64)
            terms=target_terms(geom['length_m'],torch.cos(geom['down_angle_rad']),state[:,STATE['height_m']],eligible)
            actual.append({'family':d['evaluation_family'],'env_id':e['env_id'],
                'base_discounted_return_including_initialization_clock':discounted(base),
                'controlled_lift_sum':float(l[mask].sum()),
                'cost_sum_w03':float(terms['negative_cost'].sum()),'bonus_sum_w03':float(terms['positive_quality'].sum()),
                'cost_discounted_w03':discounted(terms['negative_cost']),
                'bonus_discounted_w03':discounted(terms['positive_quality']),
                'quality_peak':float(terms['quality'][mask].max()),
                'gate_escape_high_without_entry_samples':int(((state[:,6]>=.30)&eligible).sum())})
    # These are labeled abstract scenario fixtures,not physically feasible USD
    # rollouts. Base reward rates explicitly chosen for boundary stress only.
    scenarios=[]
    cases=[('stationary_long',100,.375,.28,.18,1.0,False),
        ('early_failure_long',30,.375,.28,.18,1.0,False),
        ('short_down_stall',100,.15,1.,.18,1.,False),
        ('single_side_short',100,.15,1.,.18,1.,False),
        ('short_up',100,.15,-1.,.18,1.,False),
        ('unsafe_high_escape',100,.375,.28,.34,1.,False),
        ('safe_support_then_stand',1100,.15,1.,.18,5.,True)]
    for name,n,length,cos,height,base_per_s,success in cases:
        h=torch.full((n,),height,dtype=torch.float64);L=torch.full((n,2),length,dtype=torch.float64)
        c=torch.full_like(L,cos);eligible=torch.ones(n,dtype=torch.bool)
        if name=='single_side_short':L[:,1]=.375
        if success:h[40:]=.42;eligible[40:]=False
        if name=='safe_support_then_stand':
            # Same start:0.375m and poor downward orientation,then improve.
            L[:30]=torch.linspace(.375,.15,30)[:,None];c[:30]=torch.linspace(.28,1.,30)[:,None]
        base=torch.full((n,),base_per_s*.01,dtype=torch.float64);base[-1]+=10 if success else -1
        for w in (.1,.3,1.):
            t=target_terms(L,c,h,eligible,weight_per_s=w)
            scenarios.append({'scenario':name,'steps':n,'weight_per_s':w,'base_return':discounted(base),
                'negative_cost_return':discounted(base+t['negative_cost']),
                'positive_bonus_return':discounted(base+t['positive_quality']),
                'bonus_peak':float(t['positive_quality'].max()),'cost_sum':float(t['negative_cost'].sum()),
                'bonus_sum':float(t['positive_quality'].sum())})
    data={'inputs_sha256':inputs,'actual':actual,'abstract_scenarios':scenarios,'simulation':0,'optimizer':0,
        'decision':'Negative geometry cost rejected as first runtime candidate: savedgate creates cost relief by highstate without geometry improvement; additional cumulative negative cost can amplify early-failure preference. Positive bounded bilateralquality avoids those incremental-negative-cost incentives but creates short-support residence incentive. Neither passed a guarantee of correct full-task preference.',
        'next_candidate_for_review':{'version':'swing_low_support_quality_proposal_v1','weight_per_s':.3,'dt':.01,
            'runnable':False,'approval_required':'Explicitly accept changed objective and residence tradeoff before schema/runtime/newexperiment publication',
            'mask':'Swing controlled pre-entry only','geometry_scales_m':[.15,.375],'height_gate_m':[.22,.30],
            'source':'certifiedB25','mean_auxiliary_enabled':False,
            'scope':'Bounded target bonus,notPBRS; no automatic success/stability/observability guarantee'}}
    publish(output,{'audit.json':data},inputs);return data

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();d=audit(a.run,a.output_dir);print(json.dumps({'decision':d['decision'],'scenarios':d['abstract_scenarios'],'candidate':d['next_candidate_for_review']},indent=2))
