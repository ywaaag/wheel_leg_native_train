"""Offline geometric potential and absorbing-terminal audit on frozen B25 data."""
import argparse
import json
from pathlib import Path
import torch
from native_stand.command_v6.domain.trace_schema import validate_rows,STATE
from native_stand.recovery.support_geometry_proposal import geometry,potential,shaping
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish

def audit(run,output):
    run=Path(run).resolve();sp=run/'source_snapshot/spec.json';spec=json.loads(sp.read_text())
    inputs=dict([checked_input(sp)]);groups=[];anchors=torch.tensor(spec['recovery']['standing_task']['hip_anchors_root_m'],dtype=torch.float64)
    for i in range(3):
        path=run/f'evaluation_{i:02d}.json';inputs.update([checked_input(path)])
        data=json.loads(path.read_text());rows=[]
        if data['checkpoint_sha256']!=spec['source_sha256'] or data['asset_sha256']!=spec['asset_sha256']:
            raise ValueError('Source identity differs')
        for e in data['per_env']:
            state=torch.tensor(validate_rows(e['compact_trace_100hz'],'state'),dtype=torch.float64)
            geo=torch.tensor(validate_rows(e['wheel_geometry_trace_100hz'],'geometry'),dtype=torch.float64)
            if len(state)!=len(geo):raise ValueError('Misaligned geometry')
            # Trace v1 named field boundary: centers xyz left/right,gravityxyz.
            geom=geometry(geo[:,:6].reshape(-1,2,3),anchors,geo[:,6:9])
            control=(state[:,STATE['recovery_clock_s']]>0)&state[:,29].bool()&(state[:,32]!=7)
            idx=control.nonzero().flatten()
            if not len(idx):raise ValueError('No valid controlled trajectory')
            entered=e['entry_confirmation_index']
            eligible=control.clone() if i==0 else torch.zeros_like(control)
            if entered is not None:eligible[entered+1:]=False
            phi=potential(geom['cost'],state[:,STATE['height_m']],eligible)
            # End-of-policy-step geometry: differences cover next transitions.
            # No exact pre-first-physics geometry is available in this trace.
            p=phi[idx];terminal=torch.zeros(len(p)-1,dtype=torch.bool)
            terminal[-1]=bool(e['episode_result']['terminated'])
            differences=shaping(p[:-1],p[1:],absorbing_terminal=terminal)
            discount=.99**torch.arange(len(differences),dtype=torch.float64)
            rows.append({'env_id':e['env_id'],'first_control_s':float(state[idx[0],0]),
                'length_initial_m':geom['length_m'][idx[0]].tolist(),'length_final_m':geom['length_m'][idx[-1]].tolist(),
                'length_min_m':geom['length_m'][idx].amin(0).tolist(),
                'down_angle_initial_rad':geom['down_angle_rad'][idx[0]].tolist(),
                'down_angle_final_rad':geom['down_angle_rad'][idx[-1]].tolist(),
                'phi_first':float(p[0]),'phi_last_before_terminal':float(p[-1]),
                'cost_first':float(geom['cost'][idx[0]]),'cost_last':float(geom['cost'][idx[-1]]),
                'terminal_release_beta1':float(differences[-1]),
                'discounted_shaping_sum_beta1':float((differences*discount).sum()),
                'expected_absorbing_constant_minus_phi0':float(-p[0]),
                'telescoping_error':float(abs((differences*discount).sum()+p[0])),
                'nonterminal_sum_beta1':float(differences[:-1].sum()),
                'scales':[{'beta':b,'terminal_release':float(b*differences[-1]),
                    'discounted_sum':float(b*(differences*discount).sum())} for b in (.01,.03,.1,.3)],
                'terminated':bool(e['episode_result']['terminated']),
                'scope':'post-state adjacent intervals only; omitted first input transition; no reward history modification'})
        groups.append({'family':data['evaluation_family'],'rows':rows})
    report={'inputs_sha256':inputs,'groups':groups,'simulation':0,'optimizer':0,
        'decision':'Strict PBRS from fixed initial potential and absorbing zero endpoint adds constant full discounted return across success/failure paths. It may affect finite-sample critic conditioning but supplies no extra optimal objective preference for contraction; do not proceed to PPO on this rationale alone.',
        'next_proposal':'Separately declare bounded low-height geometry target cost (changes reward objective) if user approves; calibrate no-motion vs contraction vs unsafe pivot,oldgroup masks and terminal costs. Do not silently replace PBRS with positive-only progress.'}
    publish(output,{'audit.json':report},inputs);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();d=audit(a.run,a.output_dir);print(json.dumps(d,indent=2))
