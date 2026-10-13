"""Deterministic constrained last-layer calibration, no simulator or PPO."""
import argparse,json,copy,hashlib
from pathlib import Path
import numpy as np
import torch
from scipy.optimize import minimize,LinearConstraint
from scipy.special import ndtr
from tensordict import TensorDict
from native_stand.command_v6.tools.model_factory import model
from native_stand.command_v6.tools.experiment_preparation import checked_input


def prepare(run,checkpoint,parent,output):
    output=Path(output);output.mkdir(exist_ok=False);inputs={}
    def bind(p,expected=None):
        k,h=checked_input(p,expected);inputs[k]=h;return Path(k)
    sp=bind(parent);spec=json.loads(sp.read_text());cp=bind(checkpoint,'34be4427f70ea71b5be056da3e65d554b23dcb826e539e7ce65aadff69118a1c');saved=torch.load(cp,map_location='cpu',weights_only=False)
    assert saved['spec_sha256']==inputs[str(sp)]
    meta=json.loads(bind(Path(run)/'evaluation_00.json').read_text());assert meta['checkpoint_sha256']==inputs[str(cp)]
    with np.load(bind(Path(run)/meta['capture']['path'],meta['capture']['sha256'])) as z:a={k:z[k].copy() for k in z.files}
    columns=meta['capture']['pre_metadata_columns'];md=a['pre_metadata'].reshape(-1,len(columns));families=meta['capture']['family_names'];state=a['post_state'].reshape(-1,39);x=a['pre_obs150'].reshape(-1,150);fullq=a['pre_joint_pos'].reshape(-1,a['pre_joint_pos'].shape[-1])
    names=meta['capture']['joint_names'];legnames=['left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch'];ids=[names.index(n) for n in legnames];q=fullq[:,ids]
    ctrl=md[:,columns.index('controlled')].astype(bool);entry=md[:,columns.index('entry_time')];clock=np.maximum(state[:,0]-.01,0);family=md[:,columns.index('family_code')]
    early=ctrl&(family==families.index('swing_candidate_from_historical_r1'))&(clock<=.03+1e-6)&(entry<0)&~(state[:,3].astype(bool)|state[:,4].astype(bool))
    anchors=ctrl&(family!=families.index('swing_candidate_from_historical_r1'))&(entry>=0)
    # Episode groups are env+episode; no adjacent-frame random split.
    env=np.broadcast_to(np.arange(a['pre_metadata'].shape[2]),a['pre_metadata'].shape[:3]).reshape(-1);ep=md[:,columns.index('episode_id')].astype(int)
    group=env*100000+ep;unique=np.unique(group[early]);holdgroups=unique[::5];train=early&~np.isin(group,holdgroups);hold=early&np.isin(group,holdgroups)
    rng=torch.get_rng_state().clone();threads=torch.get_num_threads();torch.set_num_threads(1)
    try:
        dummy=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);actor=model(dummy,actor=True,spec=spec);actor.load_state_dict(saved['actor']);actor.eval()
        with torch.no_grad():features=torch.nn.Sequential(*list(actor.mlp)[:-1])(torch.tensor(x)).numpy().astype(np.float64);base=actor(TensorDict({'policy':torch.tensor(x[:,:25]),'history':torch.tensor(x[:,25:])},batch_size=[len(x)]),stochastic_output=False).numpy()
        H=np.c_[features,np.ones(len(x))];target=(q+np.array([.1,.1,-.1,.1])-(q-x[:,9:13]/2))/1.6
        # Keep all early states constrained, holdout reporting remains episode-grouped.
        hs=H[train];ha=H[anchors];old=base[train][:,[0,1,3,4]];residual=target[train]-old
        changes=[];solvers=[]
        for j in range(4):
            hc=hs;rc=residual[:,j];constraint=LinearConstraint(hc,rc-.02999/1.6,rc+.02999/1.6)
            A=ha.T@ha/max(len(ha),1)
            result=minimize(lambda v:.5*float(v@v),np.zeros(H.shape[1]),jac=lambda v:v,
                constraints=[constraint,{'type':'ineq','fun':lambda v,A=A:(.04999/1.6)**2-float(v@A@v),'jac':lambda v,A=A:-2*A@v}],
                method='SLSQP',options={'ftol':1e-11,'maxiter':800,'disp':False})
            changes.append(result.x);solvers.append({'success':bool(result.success),'message':result.message,'iterations':result.nit})
        delta=np.stack(changes);new=copy.deepcopy(saved);weight=new['actor']['mlp.6.weight'];bias=new['actor']['mlp.6.bias']
        for j,row in enumerate((0,1,3,4)):weight[row]+=torch.tensor(delta[j,:-1],dtype=weight.dtype);bias[row]+=float(delta[j,-1])
        actor.load_state_dict(new['actor'])
        with torch.no_grad():after=actor(TensorDict({'policy':torch.tensor(x[:,:25]),'history':torch.tensor(x[:,25:])},batch_size=[len(x)]),stochastic_output=False).numpy()
        predicted=base[:,[0,1,3,4]]+H@delta.T
        print('LINEAR_REPLAY',float(abs(predicted-after[:,[0,1,3,4]]).max()),flush=True)
        calibration=float(abs(1.6*(after[train][:,[0,1,3,4]]-target[train])).max());anchor=float(np.sqrt(np.mean((1.6*(after[anchors][:,[0,1,3,4]]-base[anchors][:,[0,1,3,4]]))**2))) if anchors.any() else None
        std=saved['actor']['distribution.std_param'].numpy();boundary=x[:,9:13]/2/1.6;prob=ndtr((after[:,[0,1,3,4]]-boundary)*np.array([1,1,-1,1])/std[[0,1,3,4]])
        feasible=all(s['success'] for s in solvers) and calibration<=.03 and anchor is not None and anchor<=.05
        report={'status':'QUALIFIED' if feasible else 'INFEASIBLE_OR_NOT_CONVERGED','inputs_sha256':inputs,'source_checkpoint_sha256':inputs[str(cp)],'calibration_samples':int(train.sum()),'holdout_samples':int(hold.sum()),'anchor_samples':int(anchors.sum()),'calibration_episode_groups':len(np.unique(group[train])),'holdout_episode_groups':len(holdgroups),'calibration_max_error_rad':calibration,'holdout_max_error_rad':float(abs(1.6*(after[hold][:,[0,1,3,4]]-target[hold])).max()),'anchor_rms_change_rad':anchor,'solver':solvers,'early_four_direction_probability':float(prob[early].prod(1).mean()),'early_clip_probability':(ndtr((-1-after[early])/std)+1-ndtr((1-after[early])/std)).mean(0).tolist(),'early_mean_max_abs':abs(after[early]).max(0).tolist(),'optimizer_steps':0,'online_PPO':0,'changed_parameters':['actor.mlp.6.weight rows0,1,3,4','actor.mlp.6.bias rows0,1,3,4'],'limitations':['Preclock inferred postclock-dt; full pre-joint and pre metadata read directly','This is local geometric direction prior, not successful recovery demonstration','Group holdout is from same source random rollout, not independent initial distribution']}
        if feasible:
            new['initialization_candidate']={'version':'recovery_leg_output_calibration_v1','source_checkpoint':str(cp),'source_sha256':inputs[str(cp)],'parent_spec_sha256':inputs[str(sp)],'trained':False,'calibration_max_error_rad':calibration,'anchor_rms_change_rad':anchor}
            targetpath=output/'initialization_candidate.pt';torch.save(new,targetpath);report['candidate']=str(targetpath.resolve());report['candidate_sha256']=hashlib.sha256(targetpath.read_bytes()).hexdigest()
        (output/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
    finally:torch.set_rng_state(rng);torch.set_num_threads(threads)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('run','checkpoint','parent-spec','output-dir'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prepare(a.run,a.checkpoint,a.parent_spec,a.output_dir)
