"""Fresh bounded PPO0 student100->Motion local teaching probe; never launch."""
import argparse,copy,json,hashlib
from pathlib import Path
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish,checked_input,differences
from native_stand.students.requests import validate,evaluation_recovery
from native_stand.students.model import load
from native_stand.students.handoff_probe import VERSION,KIND
from native_stand.recovery.handoff_protocol import declaration,duration

def prepare(parent,checkpoint,*,write=False):
 root=Path(__file__).resolve().parents[1];parent=Path(parent).resolve();checkpoint=Path(checkpoint).resolve();original=json.loads(parent.read_text());s=copy.deepcopy(original);inputs=dict([checked_input(parent),checked_input(checkpoint)])
 actor,cp=load(checkpoint,'RecoveryStudent')
 if cp['interface_version']!='multiskill_mcu_v2' or cp.get('recipe_version')!='student_recovery_ppo_lift_rate_v3':raise ValueError('probe source must be exact v3 student candidate')
 if cp['spec_sha256']!=inputs[str(parent)]:raise ValueError('student checkpoint parent spec differs')
 for path,expected in original['student_dependencies'].items():inputs.update([checked_input(path,expected)])
 name=new_experiment_name('student100_motion_b250_local_probe_resetfix_ppo0');folder=root/'configs/experiments'/name
 s.update(experiment=name,source_checkpoint=str(checkpoint),source_sha256=inputs[str(checkpoint)],evaluation_only=True,restore_source_rng=False,restore_recovery_curriculum=False,authorization={'status':'UNAUTHORIZED','hapi_session':None,'user_scope':'local student Motion teaching probe preparation only'},resources={'mode':'exclusive','sharing_authorized':False},notifications={'enabled':False})
 s.pop('student_training',None);s.pop('wiring_smoke',None)
 s['artifacts']['run_name']=name
 cases=[]
 normal=next(r for r in json.load(open(root/'configs/experiments/2026_10_11-11_36__mcu_v2_student_independent_ppo0/spec.json'))['student_evaluation']['cases'] if r['kind']=='teacher_normal')
 cases.append(copy.deepcopy(normal))
 teacher=s['student_teachers'][0];cases.append({'case_id':'frozen_original_combination','kind':'teacher_combination','checkpoint':teacher['checkpoint'],'sha256':teacher['sha256'],'family':'swing_candidate_from_historical_r1','seed':20261010,'yaw_rad':0.,'seconds':13.52,'role':'RecoveryStudent'})
 # Explicit fixed conditions selected around observed h.30 / crest / fall, not an online trigger.
 for switch in [.30,.40,.45,.50,.55,.60,.65]:
  cases.append({'case_id':f'student100_prefix_{round(switch*100):03d}','kind':KIND,'checkpoint':str(checkpoint),'sha256':inputs[str(checkpoint)],'family':'swing_candidate_from_historical_r1','seed':20261010,'yaw_rad':0.,'seconds':duration(switch,s['recovery']['initialization']['settle_max_s']),'role':'RecoveryStudent','switch_s':switch})
 s['student_evaluation']={'version':VERSION,'cases':cases,'max_output_bytes':512*2**20,'handoff_protocol':declaration()}
 seconds=max(r['seconds'] for r in cases);s['recovery']['fsm']['timeout_s']=seconds;s['curriculum']['episode_length_s']=seconds
 s['budget'].update(smoke_updates=0,formal_updates=0,source_eval_updates=0,sample_limit=0,evaluation_wall_s=1800,chain_wall_s=1800,source_eval_wall_s=0,smoke_wall_s=0,formal_wall_s=0)
 s['evaluation'].update(seconds=seconds,run_final_durability=False);s['evaluation_requests']=[]
 libpath=Path(s['recovery']['pose_library']);inputs.update([checked_input(libpath,s['recovery']['pose_library_sha256'])]);lib=json.loads(libpath.read_text())
 normalposes=[p for p in lib['poses'] if p['family']=='motion_native_normal' and p['split']=='holdout'];assert normalposes and all(p['initialization_control']=='direct_zero_reset' for p in normalposes)
 normalprovenance=normalposes[0]['normal_initialization_provenance'];inputs.update([checked_input(normalprovenance['path'],normalprovenance['sha256'])])
 for row in cases:evaluation_recovery(s['recovery'],lib['poses'],row['family'])
 encoded=(json.dumps(lib,indent=2)+'\n').encode();s['recovery']['pose_library']=str(folder/'poses.json');s['recovery']['pose_library_sha256']=hashlib.sha256(encoded).hexdigest()
 for row in cases:inputs.update([checked_input(row['checkpoint'],row['sha256'])])
 s['student_dependencies']=inputs
 errors=validate(s)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'evaluate':1,'smoke':0,'formal':0},'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},'sample_limit':0,'source_eval_wall_used_s':0.,'hapi_session':None}
 report={'spec':str(folder/'spec.json'),'ledger':str(folder/'budget.json'),'experiment':name,'status':'UNAUTHORIZED_NOT_RUN','PPO':0,'offline_optimizer':0,'conditions':len(cases),'score_episodes':len(cases)*8,'simulated_envs':64,'scored_envs':8,'wall_s':1800,'storage_bytes':512*2**20,'student_checkpoint_sha256':inputs[str(checkpoint)],'source_parent_spec_sha256':inputs[str(parent)],'normal_initialization':normalprovenance,'case_ids':[r['case_id'] for r in cases],'effective_changes':differences(original,s),'runtime':'CPU adapter implemented, physics unverified','success_meaning':'Motion local teaching region; never student independent success'}
 if write:publish(folder,{'spec.json':s,'budget.json':book,'preparation.json':report},inputs,completion_marker=True,serialized_files={'poses.json':(encoded,s['recovery']['pose_library_sha256'])})
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--parent-spec',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.parent_spec,a.checkpoint,write=a.write),indent=2))
