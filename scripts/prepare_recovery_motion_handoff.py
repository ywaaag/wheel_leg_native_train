"""Identity-bound finite-time handoff CPU preparation; runtime not authorized."""
import argparse,json,hashlib
from pathlib import Path
import torch
from tensordict import TensorDict
from native_stand.command_v6.tools.experiment_preparation import checked_input,publish
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.model_factory import model
from native_stand.recovery.motion_handoff import scan_conditions


def prepare(output):
    root=Path.cwd();inputs={}
    def bind(p,sha=None):
        path,h=checked_input(root/p if not Path(p).is_absolute() else p,sha);inputs[path]=h;return Path(path)
    motion=bind('runs/motion_cohort_width_ab_20261006/B/formal/model_update_250.pt','5d3389d5b8e33b7915d12d21308702f3105248485741b27ec91d0aaf4b90b89e');mp=bind('runs/motion_cohort_width_ab_20261006/B/formal/source_snapshot/spec.json');ms=json.loads(mp.read_text())
    recp=bind('runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/source_snapshot/spec.json');rs=json.loads(recp.read_text());asset=bind(rs['asset_path'],rs['asset_sha256']);pose=bind(rs['recovery']['pose_library'],rs['recovery']['pose_library_sha256'])
    original_library=bind('configs/experiments/2026_10_9-10_58__recovery_swing_bounded_mean_from_b25/poses.json');library=json.loads(original_library.read_text());normal=[p for p in library['poses'] if p['family']=='R0' and p['split']=='holdout' and p['offline_valid']]
    if not normal:raise ValueError('Explicit normal baseline pose missing')
    checkpoints={'B_init':bind('isolated/recovery_swing_leg_initialization_qualified_20261010/initialization_candidate.pt'),**{f'B{u}':bind(f'runs/2026_10_10-14_23__recovery_swing_controlled_actor_b/formal/model_update_{u}.pt') for u in (25,50,100)}}
    rng=torch.get_rng_state().clone()
    try:
        dummy=TensorDict({'policy':torch.zeros(1,25),'history':torch.zeros(1,125)},batch_size=[1]);identities={}
        for label,cp,spec in [('Motion_B250',motion,ms)]+[(label,cp,rs) for label,cp in checkpoints.items()]:
            saved=torch.load(cp,map_location='cpu',weights_only=False);actor=model(dummy,actor=True,spec=spec);actor.load_state_dict(saved['actor'],strict=True)
            if label=='Motion_B250' and saved['spec_sha256']!=inputs[str(mp)]:raise ValueError('Motion parent identity conflict')
            identities[label]={'path':str(cp),'sha256':inputs[str(cp)],'actor_parameters':sum(p.numel() for p in actor.parameters()),'std':actor.distribution.std_param.detach().tolist(),'parent_spec_sha256':saved['spec_sha256']}
    finally:torch.set_rng_state(rng)
    for key in ('physics_dt_s','pd_dt_s','policy_dt_s','leg_kp','leg_kd','wheel_kv','effort_limits_nm','closure_fault_m'):
        if ms['control'][key]!=rs['control'][key]:raise ValueError('Physical PD contract conflict '+key)
    cases=scan_conditions(list(checkpoints));name=new_experiment_name('recovery_motion_b250_handoff_ppo0')
    result={'experiment':name,'status':'CPU_CONTRACT_READY_RUNTIME_ADAPTER_PENDING','runnable':False,'authorization':'UNAUTHORIZED','PPO':0,'optimizer_steps':0,'asset':{'path':str(asset),'sha256':inputs[str(asset)]},'models':identities,'normal_baseline_pose_id':normal[0]['pose_id'],'normal_baseline_pose_source':str(original_library),'cases':cases,'scored_envs_per_case':8,'total_episodes':176,'wall_s':3600,'storage_max_bytes':1073741824,'speed_protocol_source':{'path':str(mp),'sha256':inputs[str(mp)],'vx_mean_abs_max':ms['evaluation']['vx_error_max_mps'],'vy_mean_abs_max':ms['evaluation']['vy_abs_max_mps'],'yaw_mean_abs_max':ms['evaluation']['yaw_error_max_rad_s']},'protocol':{'version':'recovery_motion_zero_handoff_v1','settle_deadline_after_switch_s':2.,'entry_dwell_s':.2,'minimum_height_m':.30,'hold_s':10.,'window':'first_confirmed_entry_then_next1000samples','direct_switch':True,'normal_baseline_failure_stops_scan':True,'failure_before_switch_stays_in_denominator':True,'reset_at_switch':False,'Motion_command':[0.,0.,.4],'history':'Motion maintained throughout prefix; no refill at handoff','previous_action':'physical executed targets separately encoded .5/100 and1.6/100; clipped loss logged'},'required_runtime_evidence':['controller eachstep','physical state full joints q/dq/contacts','dual histories frames and physical previous-action information loss','prepostswitch physical target jump','actual held PD torques/channel limits','settle/hold/failedstage'],'unimplemented':['Public supervisor PPO0 request adapter and runtime same-environment physical handoff','Per-case first-episode/no-reset-at-handoff execution and baseline early stop','Atomic compressed trace storage cap and supervisor ledger settlement for custom protocol'],'limitations':['R0 saved baseline pose runtime acceptance on knee-stop asset not yet reverified','No switched state tested; static state or critic value cannot establish basin','CPU scoring speed thresholds refer frozen B250 zero gate; new protocol differs from30s Motion command schedule']}
    publish(output,{'preparation.json':result},inputs,completion_marker=True);print(json.dumps({'status':result['status'],'models':identities,'cases':len(cases),'PPO':0},indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();prepare(a.output_dir)
