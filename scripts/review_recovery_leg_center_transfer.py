"""CPU fixed-observation actor transfer and measured first hold-loss alignment."""
import argparse,json,copy
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.command_v6.tools.evaluation_storage import read
from native_stand.command_v6.domain.trace_schema import STATE,CONTROL,POSTURE,validate_rows
from native_stand.recovery.standing import longitudinal_geometry


def review(rollout,a_run,b_run,output):
    inputs={}
    def bind(p,expected=None):
        key,sha=checked_input(p,expected);inputs[key]=sha;return Path(key)
    rollout=Path(rollout);meta=json.loads(bind(rollout/'evaluation_00.json').read_text())
    if not meta['frozen_state_unchanged']:raise ValueError('Rollout not frozen')
    with np.load(bind(rollout/meta['capture']['path'],meta['capture']['sha256'])) as z:
        x=z['pre_obs150'].reshape(-1,150).copy();md=z['pre_metadata'].reshape(-1,4).copy();state=z['post_state'].reshape(-1,39).copy()
    clock=np.maximum(state[:,0]-.01,0);families=meta['capture']['family_names']
    groups={f:(md[:,0]==i)&md[:,2].astype(bool) for i,f in enumerate(families)}
    groups['Swing_pre100ms_inferred']=groups['swing_candidate_from_historical_r1']&(clock<.1-1e-7)&(md[:,3]<0)&~(state[:,3].astype(bool)|state[:,4].astype(bool))
    dummy=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);obs=torch.from_numpy(x)
    cases=[];events=[];base=None;oldrng=torch.get_rng_state().clone();threads=torch.get_num_threads();torch.set_num_threads(1)
    try:
        for label,run,update in [('source',Path(a_run),None),('A10',Path(a_run),10),('A25',Path(a_run),25),('B10',Path(b_run),10),('B25',Path(b_run),25)]:
            sp=bind(run/('source_eval' if update is None else 'formal')/'source_snapshot/spec.json');spec=json.loads(sp.read_text())
            cp=bind(spec['source_checkpoint'],spec['source_sha256']) if update is None else bind(run/f'formal/model_update_{update}.pt')
            saved=torch.load(cp,map_location='cpu',weights_only=False);actor=model(dummy,actor=True,spec=spec);actor.load_state_dict(saved['actor'],strict=True);actor.eval();before=copy.deepcopy(actor.state_dict())
            with torch.no_grad():
                mu=actor(TensorDict({'policy':obs[:,:25],'history':obs[:,25:]},batch_size=[len(obs)]),stochastic_output=False).numpy()
            if not all(torch.equal(v,actor.state_dict()[k]) for k,v in before.items()):raise ValueError('Actor changed')
            if base is None:base=mu.copy()
            error=spec['action']['leg_scale_rad']*mu[:,[0,1,3,4]]-x[:,9:13]/2
            executed=spec['action']['leg_scale_rad']*np.clip(mu[:,[0,1,3,4]],-1,1)-x[:,9:13]/2
            rows={}
            for family,mask in groups.items():
                if not mask.any():raise ValueError('Empty family')
                e=error[mask];de=executed[mask];shift=(mu-base)[mask]
                rows[family]={'samples':int(mask.sum()),'mean_raw_target_error_rad':e.mean(0).tolist(),'abs_raw_error_mean_rad':abs(e).mean(0).tolist(),'mean_clipped_target_error_rad':de.mean(0).tolist(),'raw_leg_clip_fraction':(abs(mu[mask][:,[0,1,3,4]])>1).mean(0).tolist(),'all_four_local_shortening_direction_fraction':float(((de*np.array([1,1,-1,1]))>0).all(1).mean()),'aux_unit_loss_mean':float(np.maximum(abs(e)-.15,0).__pow__(2).mean()),'mean_output_shift_from_source':shift.mean(0).tolist(),'peak_abs_output_shift_from_source':abs(shift).max(0).tolist()}
            cases.append({'model':label,'checkpoint':str(cp),'groups':rows})
            if update is None:continue
            ep=bind(run/f'formal/evaluation_{update}_0_0.json');d=read(ep)
            if d['checkpoint_sha256']!=inputs[str(cp)] or d['spec_sha256']!=inputs[str(sp)]:raise ValueError('Evaluation identity differs')
            for g in d['retained_evaluations']:
                for row in g['per_env']:
                    for key,kind in [('compact_trace_100hz','state'),('posture_trace_100hz','posture'),('control_diagnostics_100hz','control'),('wheel_geometry_trace_100hz','geometry')]:validate_rows(row[key],kind)
                    s,p,c,geo=[np.asarray(row[k]) for k in ('compact_trace_100hz','posture_trace_100hz','control_diagnostics_100hz','wheel_geometry_trace_100hz')]
                    if len(set(map(len,(s,p,c,geo))))!=1 or len(np.unique(s[:,STATE['episode_id']]))!=1:raise ValueError('Trace alignment conflict')
                    start=row['entry_confirmation_index']+1;stop=start+1000
                    if stop>len(s):raise ValueError('Incomplete hold')
                    ids=np.flatnonzero((s[start:stop,[10,11]]<=2).any(1))+start
                    offset=longitudinal_geometry(torch.as_tensor(geo[:,:6].reshape(-1,2,3)),torch.as_tensor(geo[:,6:9])).numpy()
                    def at(i):
                        return {'index':int(i),'recovery_s':float(s[i,0]),'roll_rad':float(p[i,1]),'offset_m':float(offset[i]),'contact_n':s[i,[10,11]].tolist(),'leg_q_rad':c[i,[0,1,3,4]].tolist(),'leg_target_rad':c[i,CONTROL['leg_target_after_limit']].tolist(),'wheel_target_rad_s':(c[i,[20,23]]*spec['action']['wheel_scale_rad_s']).tolist(),'applied_nm':c[i,CONTROL['applied_torque']].tolist()}
                    event={'model':label,'family':row['family'],'env_id':row['env_id'],'hold_start_index':start,'first_hold_loss':None,'loss_samples':len(ids)}
                    if len(ids):
                        i=int(ids[0]);event.update(first_hold_loss=at(i),preceding_100ms=[at(j) for j in range(max(start,i-10),i)],offset_over4cm_first_index=next((j for j in range(start,i+1) if abs(offset[j])>.04),None),roll_over0p1_first_index=next((j for j in range(start,i+1) if abs(p[j,1])>.1),None))
                    events.append(event)
    finally:torch.set_num_threads(threads);torch.set_rng_state(oldrng)
    result={'fixed_input_source':str(rollout),'models':cases,'hold_events':events,'simulation':0,'optimizer_steps':0,'actor_unchanged':True,'limitations':['Fixed inputs from source random rollout, not updated-model on-policy occupancy','Early preclock inferred postclock minus 10ms, not new runtime mask certification','Local shortening signs are a sufficient local path, not a necessary recovery condition','100Hz held torques, not full substep impulse; temporal ordering is not causal proof','No dynamic Swing success demonstration']}
    publish(output,{'review.json':result},inputs,completion_marker=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rollout','a-run','b-run','output-dir'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();r=review(a.rollout,a.a_run,a.b_run,a.output_dir);print(json.dumps({'models':[{'model':m['model'],'early':m['groups']['Swing_pre100ms_inferred']} for m in r['models']],'hold_event_counts':{m:sum(e['first_hold_loss'] is not None for e in r['hold_events'] if e['model']==m) for m in ('A10','A25','B10','B25')}},indent=2))
