"""One settled storage-preflight recovery; reuse real wiring, not capability gates."""
import copy,json
from pathlib import Path
from .data import sha
VERSION='motion31_preformal_storage_recovery_v1'
PARTIAL_VERSION='motion31_partial_smoke_diagnostic_recovery_v1'

def verify_partial(spec):
 """Reuse only complete source evidence; a fresh real smoke certificate is still required."""
 c=spec['motion_training']['partial_smoke_recovery']
 fields={'version','parent_spec','parent_run','inputs','historical_smoke_updates','historical_wall_s','original_online_limit'}
 if set(c)!=fields or c['version']!=PARTIAL_VERSION:raise ValueError('partial Motion recovery schema differs')
 parent=Path(c['parent_spec']);run=Path(c['parent_run']);old=json.loads(parent.read_text());book=json.loads(parent.with_name('budget.json').read_text())
 if old.get('motion_training',{}).get('partial_smoke_recovery') or old.get('motion_training',{}).get('wiring_reuse'):raise ValueError('partial recovery cannot become an automatic retry chain')
 for path,digest in c['inputs'].items():
  if sha(path)!=digest:raise ValueError('partial recovery evidence SHA differs: '+path)
 chain=json.loads((run/'chain_terminal_report.json').read_text());terminal=json.loads((run/'smoke/terminal_report.json').read_text())
 if chain['status']!='FAILED' or terminal['status']!='FAILED' or terminal.get('failure',{}).get('exception')!="AttributeError(\"'function' object has no attribute 'items'\")":raise ValueError('partial recovery requires the known diagnostic name-shadow fault')
 if (run/'formal').exists() or book['used']['formal']!=0 or any(a['phase']=='formal' or a['status']=='RUNNING' for a in book['attempts'].values()):raise ValueError('partial recovery requires settled preformal failure')
 metrics=[json.loads(line) for line in (run/'smoke/metrics.jsonl').read_text().splitlines()]
 actual=book['used']['smoke']
 if actual!=1 or len(metrics)!=actual or [r['update'] for r in metrics]!=[1] or metrics[0]['actor_changed_this_update'] or not metrics[0]['critic_changed_this_update'] or not metrics[0]['actor_update_scope']['critic_warmup']:raise ValueError('partial recovery real optimizer evidence differs')
 if c['historical_smoke_updates']!=actual or c['original_online_limit']!=2000 or old['budget']['smoke_updates']+old['budget']['formal_updates']!=2000:raise ValueError('partial recovery original inclusive budget differs')
 if spec['budget']['smoke_updates']!=old['budget']['smoke_updates']-actual or spec['budget']['formal_updates']!=old['budget']['formal_updates'] or actual+spec['budget']['smoke_updates']+spec['budget']['formal_updates']!=2000:raise ValueError('partial recovery cannot reset or enlarge online budget')
 if abs(c['historical_wall_s']-chain['chain_wall_s'])>1e-6 or spec['budget']['chain_wall_s']+c['historical_wall_s']>old['budget']['chain_wall_s']+1e-6:raise ValueError('partial recovery wall reset prohibited')
 behavior=('source_checkpoint','source_sha256','asset_path','asset_sha256','student_interface','observation','history','action','control','ground','termination','ppo','reward','curriculum','motion_assessment','student_training','student_evaluation','recovery','seed','performance','device')
 if any(spec[k]!=old[k] for k in behavior):raise ValueError('partial recovery changes frozen learning behavior')
 required=[parent,parent.with_name('budget.json'),run/'chain_terminal_report.json',run/'smoke/terminal_report.json',run/'smoke/metrics.jsonl',run/'source_eval/candidate_registry.json',run/'source_eval/terminal_report.json',run/'source_eval/manifest.json',run/'source_eval/source_snapshot/spec.json']
 if any(str(p) not in c['inputs'] for p in required):raise ValueError('partial recovery required identity evidence missing')
 folder=run/'source_eval';source=json.loads((folder/'terminal_report.json').read_text());manifest=json.loads((folder/'manifest.json').read_text())
 if source['status']!='COMPLETED' or source.get('failure') or source['actual_updates']!=0 or len(source['evaluations'])!=len(old['student_evaluation']['cases']):raise ValueError('partial recovery source assessment incomplete')
 if manifest['spec_sha256']!=sha(folder/'source_snapshot/spec.json') or manifest['source_sha256']!=old['source_sha256'] or manifest['asset_sha256']!=old['asset_sha256']:raise ValueError('partial source manifest identity differs')
 if json.loads((folder/'source_snapshot/spec.json').read_text())!=old:raise ValueError('partial source frozen spec differs')
 for expected,record in zip(old['student_evaluation']['cases'],source['evaluations']):
  path=folder/record['path'];raw=json.loads(path.read_text());trace=folder/raw['trace']['path']
  if any(str(p) not in c['inputs'] for p in (path,trace)) or sha(path)!=record['sha256'] or sha(trace)!=raw['trace']['sha256'] or raw['protocol']!=old['motion_assessment'] or raw['checkpoint_sha256']!=old['source_sha256'] or raw['asset_sha256']!=old['asset_sha256'] or raw['spec_sha256']!=manifest['spec_sha256'] or raw['case']['command']!=expected['command'] or len(raw['per_env'])!=8:raise ValueError('partial source protocol/checkpoint/trace differs')
  if [r.get('env') for r in raw['per_env']]!=list(range(8)) or any(not r.get('survival_passed') or r.get('controlled_seconds')!=30 for r in raw['per_env']):raise ValueError('partial source complete first-episode evidence missing')
 claim=parent.parent.parent/'.motion_wiring_recovery_claims'/(sha(parent)+'.json')
 if claim.exists() and json.loads(claim.read_text())['destination']!=spec['experiment']:raise ValueError('partial recovery already claimed')
 return {'status':'VERIFIED_SOURCE_ONLY','historical_smoke_updates':actual,'remaining_smoke_updates':spec['budget']['smoke_updates'],'remaining_formal_updates':spec['budget']['formal_updates'],'wiring_passed':False,'capability_accepted':False}

def verify(spec):
 c=spec['motion_training']['wiring_reuse']
 if set(c)!={'version','parent_spec','parent_run','inputs','historical_smoke_updates','historical_wall_s','original_online_limit'} or c['version']!=VERSION:raise ValueError('Motion wiring recovery schema differs')
 for path,digest in c['inputs'].items():
  if sha(path)!=digest:raise ValueError('Motion wiring recovery evidence SHA differs: '+path)
 parent=Path(c['parent_spec']);run=Path(c['parent_run']);old=json.loads(parent.read_text());book=json.loads(parent.with_name('budget.json').read_text())
 chain=json.loads((run/'chain_terminal_report.json').read_text())
 if chain['status']!='FAILED' or chain['failure']!="ValueError('insufficient output storage before reserve')" or (run/'formal').exists() or any(a['phase']=='formal' or a['status']=='RUNNING' for a in book['attempts'].values()):raise ValueError('unsupported Motion recovery; requires settled preformal storage fault')
 from native_stand.command_v6.wiring import validate_persisted_certificate
 if validate_persisted_certificate(run/'smoke',old)['status']!='PASSED':raise ValueError('real original Motion wiring certificate not valid')
 terminal=json.loads((run/'smoke/terminal_report.json').read_text());progress=json.loads((run/'smoke/progress.json').read_text())
 metrics=[json.loads(line) for line in (run/'smoke/metrics.jsonl').read_text().splitlines()]
 actual=terminal['actual_updates']
 if actual!=progress['actual_updates'] or actual!=50 or len(metrics)!=actual or [r['update'] for r in metrics]!=list(range(1,actual+1)) or c['historical_smoke_updates']!=actual:raise ValueError('historical real Motion consumption differs')
 if c['original_online_limit']!=2050 or spec['budget']['smoke_updates']!=0 or spec['budget']['formal_updates']!=2000 or c['historical_smoke_updates']+spec['budget']['formal_updates']!=2050:raise ValueError('Motion recovery cannot enlarge or repeat budget')
 if abs(c['historical_wall_s']-chain['chain_wall_s'])>1e-6 or spec['budget']['chain_wall_s']+c['historical_wall_s']>old['budget']['chain_wall_s']+1e-6:raise ValueError('Motion recovery wall budget reset prohibited')
 def behavior(s):
  # Only declaration, remaining execution budget and evidence references change.
  return {k:s[k] for k in ('source_checkpoint','source_sha256','asset_path','asset_sha256','student_interface','observation','history','action','control','ground','termination','ppo','reward','curriculum','motion_assessment','student_training','student_evaluation','recovery','seed','performance','device')}
 if behavior(spec)!=behavior(old):raise ValueError('Motion recovery modifies frozen training behavior')
 required=[parent,parent.with_name('budget.json'),run/'chain_terminal_report.json',run/'source_eval/candidate_registry.json',run/'smoke/wiring_certificate.json',run/'smoke/metrics.jsonl',run/'smoke/terminal_report.json',run/'smoke/progress.json']
 if any(str(p) not in c['inputs'] for p in required):raise ValueError('Motion recovery required evidence not bound')
 cases=old['student_evaluation']['cases']
 for folder in (run/'source_eval',run/'smoke'):
  t=json.loads((folder/'terminal_report.json').read_text())
  if t['status']!='COMPLETED' or t.get('failure') or len(t['evaluations'])!=len(cases):raise ValueError('Motion original source/smoke incomplete')
  for expected,record in zip(cases,t['evaluations']):
   p=folder/record['path'];raw=json.loads(p.read_text());trace=folder/raw['trace']['path']
   if str(p) not in c['inputs'] or str(trace) not in c['inputs'] or sha(p)!=record['sha256'] or sha(trace)!=raw['trace']['sha256'] or raw['protocol']!=old['motion_assessment'] or len(raw['per_env'])!=8 or raw['case']['command']!=expected['command']:raise ValueError('Motion reuse raw protocol/env/trace evidence differs')
 claim=parent.parent.parent/'.motion_wiring_recovery_claims'/(sha(parent)+'.json')
 if claim.exists() and json.loads(claim.read_text())['destination']!=spec['experiment']:raise ValueError('Motion original wiring already claimed by another recovery')
 return {'status':'VERIFIED','historical_smoke_updates':actual,'historical_ledger_discrepancy':book['used']['smoke']!=actual,'remaining_formal_updates':2000,'capability_accepted':False}
