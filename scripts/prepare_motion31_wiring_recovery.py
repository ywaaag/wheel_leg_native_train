"""Publish one storage-preflight recovery, consume smoke50 without rerunning it."""
import argparse,copy,json,os
from pathlib import Path
from native_stand.students.data import sha
from native_stand.students.motion_wiring_recovery import verify,VERSION
from native_stand.students.requests import validate
from native_stand.command_v6.domain.experiment_naming import new_experiment_name
from native_stand.command_v6.tools.experiment_preparation import publish
ROOT=Path(__file__).resolve().parents[1]

def prepare(parent,*,write=False,kind='storage'):
 if kind=='partial-smoke':return prepare_partial(parent,write=write)
 if kind!='storage':raise ValueError('unknown Motion engineering recovery kind')
 parent=Path(parent).resolve();old=json.loads(parent.read_text());run=ROOT/'runs'/old['experiment']
 terminal=json.loads((run/'chain_terminal_report.json').read_text());name=new_experiment_name('motion31_parallel512_storage_recovery');folder=ROOT/'configs/experiments'/name
 inputs={str(p):sha(p) for p in [parent,parent.with_name('budget.json'),run/'chain_terminal_report.json']}
 for phase in ('source_eval','smoke'):
  for p in (run/phase).rglob('*'):
   if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.jsonl','.npz'):inputs[str(p)]=sha(p)
 elapsed=terminal['chain_wall_s'];remaining=old['budget']['chain_wall_s']-elapsed
 s=copy.deepcopy(old);s.update(experiment=name,authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'explicit user authorizes fixing blocked entry and continuing remaining original formal budget'})
 s['artifacts']['run_name']=name;s['motion_training'].update(spec_path=str(folder/'spec.json'),wiring_reuse={'version':VERSION,'parent_spec':str(parent),'parent_run':str(run),'inputs':inputs,'historical_smoke_updates':50,'historical_wall_s':elapsed,'original_online_limit':2050})
 # A new immutable task declaration carries the old consumption reference;
 # old incorrect ledger and historical reports remain unchanged.
 task={'version':'motion31_block_task_v1','formal_limit':2000,'source_sha256':s['source_sha256'],'automatic_next_block':False,'registry_dir':str(folder/'task_blocks'),'historical_consumption':{'smoke':50,'formal':0,'wall_s':elapsed,'parent_ledger':str(parent.with_name('budget.json')),'parent_ledger_sha256':sha(parent.with_name('budget.json'))}}
 from prepare_motion31_training import json_sha
 s['motion_training'].update(task_manifest=str(folder/'task_manifest.json'),task_manifest_sha256=json_sha(task))
 s['budget'].update(smoke_updates=0,formal_updates=2000,sample_limit=2000*65536,formal_samples=2000*65536,chain_wall_s=remaining,formal_wall_s=remaining)
 s['student_dependencies'].update(inputs);verify(s)
 errors=validate(s,motion_task_data=task)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'smoke':0,'formal':2000,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':2000,'historical_consumption_reference':task['historical_consumption']}
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'historical_smoke_updates':50,'formal_remaining':2000,'wall_remaining_s':remaining,'simulation':0,'ppo':0,'files_written':0}
 if write:
  claims=ROOT/'configs/experiments/.motion_wiring_recovery_claims';claims.mkdir(exist_ok=True)
  with (claims/(sha(parent)+'.json')).open('x') as f:json.dump({'destination':name,'parent_spec':str(parent)},f)
  from native_stand.students.motion_reward_audit import audit
  from native_stand.students import motion_tracking_reward
  reward_snapshot=audit(s['reward']);reward_snapshot.update(spec_sha256=json_sha(s),source_sha256=s['source_sha256'],reward_source_sha256=sha(Path(motion_tracking_reward.__file__)))
  publish(folder,{'spec.json':s,'budget.json':book,'task_manifest.json':task,'task_blocks/block_0001.json':{'index':1,'spec':str(folder/'spec.json'),'planned_spec_sha256':json_sha(s)},'preparation.json':report,'reward_snapshot.json':reward_snapshot},s['student_dependencies'],completion_marker=True);report['files_written']=8
 return report

def prepare_partial(parent,*,write=False):
 from native_stand.students.motion_wiring_recovery import verify_partial,PARTIAL_VERSION
 from native_stand.students.motion_reward_audit import audit
 from native_stand.students import motion_tracking_reward
 import hashlib
 json_sha=lambda v:hashlib.sha256((json.dumps(v,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
 parent=Path(parent).resolve();old=json.loads(parent.read_text());run=ROOT/'runs'/old['experiment']
 terminal=json.loads((run/'chain_terminal_report.json').read_text());name=new_experiment_name('motion31_wide_narrow_smoke_recovery');folder=ROOT/'configs/experiments'/name
 inputs={str(p):sha(p) for p in [parent,parent.with_name('budget.json'),run/'chain_terminal_report.json']}
 for phase in ('source_eval','smoke'):
  for p in (run/phase).rglob('*'):
   if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.jsonl','.npz'):inputs[str(p)]=sha(p)
 elapsed=terminal['chain_wall_s'];remaining=old['budget']['chain_wall_s']-elapsed
 s=copy.deepcopy(old);s.update(experiment=name,authorization={'status':'UNAUTHORIZED','hapi_session':os.environ['HAPI_SESSION_ID'],'user_scope':'explicit engineering recovery: remaining original inclusive2000; repeat remaining smoke, then formal'})
 s['artifacts']['run_name']=name;s['motion_training'].update(spec_path=str(folder/'spec.json'),partial_smoke_recovery={'version':PARTIAL_VERSION,'parent_spec':str(parent),'parent_run':str(run),'inputs':inputs,'historical_smoke_updates':1,'historical_wall_s':elapsed,'original_online_limit':2000})
 task={'version':'motion31_block_task_v1','formal_limit':2000,'source_sha256':s['source_sha256'],'automatic_next_block':False,'registry_dir':str(folder/'task_blocks'),'historical_consumption':{'smoke':1,'formal':0,'wall_s':elapsed,'parent_ledger':str(parent.with_name('budget.json')),'parent_ledger_sha256':sha(parent.with_name('budget.json'))}}
 s['motion_training'].update(task_manifest=str(folder/'task_manifest.json'),task_manifest_sha256=json_sha(task))
 s['budget'].update(smoke_updates=49,sample_limit=1999*s['ppo']['envs']*s['ppo']['steps_per_env'],chain_wall_s=remaining)
 s['student_dependencies'].update(inputs);verify_partial(s)
 errors=validate(s,motion_task_data=task)
 if errors:raise ValueError(errors)
 book={'authorization':'UNAUTHORIZED','experiment':name,'limits':{'source_eval':0,'smoke':49,'formal':1950,'evaluate':0,'play':0},'used':{'source_eval':0,'smoke':0,'formal':0,'evaluate':0,'play':0},'attempts':{},'source_eval_wall_used_s':0.,'total_online_PPO_limit':1999,'historical_consumption_reference':task['historical_consumption']}
 report={'spec':str(folder/'spec.json'),'run':str(ROOT/'runs'/name),'historical_smoke_updates':1,'smoke_remaining':49,'formal_remaining':1950,'online_remaining':1999,'original_online_limit':2000,'wall_remaining_s':remaining,'source_eval_reused':True,'wiring_reused':False,'simulation':0,'ppo':0,'files_written':0}
 if write:
  claims=ROOT/'configs/experiments/.motion_wiring_recovery_claims';claims.mkdir(exist_ok=True)
  with (claims/(sha(parent)+'.json')).open('x') as f:json.dump({'destination':name,'parent_spec':str(parent)},f)
  reward_snapshot=audit(s['reward']);reward_snapshot.update(spec_sha256=json_sha(s),source_sha256=s['source_sha256'],reward_source_sha256=sha(Path(motion_tracking_reward.__file__)))
  payloads={'spec.json':s,'budget.json':book,'task_manifest.json':task,'task_blocks/block_0001.json':{'index':1,'spec':str(folder/'spec.json'),'planned_spec_sha256':json_sha(s)},'preparation.json':report,'reward_snapshot.json':reward_snapshot}
  publish(folder,payloads,s['student_dependencies'],completion_marker=True);report['files_written']=len(payloads)+1
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-spec',required=True);p.add_argument('--kind',choices=('storage','partial-smoke'),default='storage');p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.parent_spec,write=a.write,kind=a.kind),indent=2))
