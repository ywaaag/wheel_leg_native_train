"""Read-only settled predecessor consumption, no credit or reserve mutation."""
import json
from pathlib import Path
from .data import sha
VERSION='motion31_quality_consumption_v1'

def known_zero_ppo_source_fault(source_terminal):
 failure=source_terminal.get('failure') or {}
 if source_terminal.get('status')!='FAILED' or source_terminal.get('actual_updates')!=0:return False
 if failure.get('exception')=="NameError(\"name 'spec' is not defined\")":return True
 return (failure.get('exception','').startswith("RuntimeError('Inplace update to inference tensor outside InferenceMode is not allowed.")
  and 'motion_quality.py' in failure.get('traceback','') and 'self.ticks[ids]=0' in failure.get('traceback',''))

def consumption(parent_spec):
 parent=Path(parent_spec).resolve();old=json.loads(parent.read_text());bookpath=parent.with_name('budget.json');book=json.loads(bookpath.read_text())
 prior=old['motion_training'].get('prior_consumption')
 if prior:verify(old)
 else:
  from .motion_wiring_recovery import verify_partial
  verify_partial(old)
 run=parent.parents[2].parent/'runs'/old['experiment'];terminal_path=run/'chain_terminal_report.json';terminal=json.loads(terminal_path.read_text())
 if any(r['status']=='RUNNING' for r in book['attempts'].values()):raise ValueError('quality predecessor must be settled')
 user_stopped=terminal['status']=='STOPPED_BOUNDED' and any(r.get('terminal',{}).get('stop_kind')=='user_signal' for r in terminal['phase_results'])
 source_terminal=json.loads((run/'source_eval/terminal_report.json').read_text()) if (run/'source_eval/terminal_report.json').exists() else {}
 known_source_fault=bool(prior and terminal['status']=='FAILED' and book['used']['smoke']==book['used']['formal']==0 and known_zero_ppo_source_fault(source_terminal))
 if not user_stopped and not known_source_fault:raise ValueError('quality predecessor requires explicit user stop or exact zero-PPO protocol interface fault')
 historical=prior or old['motion_training']['partial_smoke_recovery']
 historical_updates=historical['historical_online_updates'] if prior else historical['historical_smoke_updates']
 used=historical_updates+book['used']['smoke']+book['used']['formal']
 wall=terminal['chain_wall_including_parent_s']
 if used!=terminal['online_updates_including_parent'] or used>=historical['original_online_limit']:raise ValueError('quality predecessor inclusive updates exhausted/conflicting')
 return {'version':VERSION,'parent_spec':str(parent),'parent_spec_sha256':sha(parent),'parent_ledger':str(bookpath),'parent_ledger_sha256':sha(bookpath),
  'parent_terminal':str(terminal_path),'parent_terminal_sha256':sha(terminal_path),'historical_online_updates':used,'historical_wall_s':wall,
  'original_online_limit':historical['original_online_limit'],'original_chain_wall_s':64800}

def verify(spec):
 c=spec['motion_training']['prior_consumption']
 if c!=consumption(c['parent_spec']):raise ValueError('quality historical consumption identity differs')
 if c['historical_online_updates']+spec['budget']['smoke_updates']+spec['budget']['formal_updates']>c['original_online_limit']:raise ValueError('quality total online budget reset')
 if c['historical_wall_s']+spec['budget']['chain_wall_s']>c['original_chain_wall_s']+1e-6:raise ValueError('quality chain wall reset')
 claim=Path(c['parent_spec']).parent.parent/'.motion_quality_consumption_claims'/(c['parent_spec_sha256']+'.json')
 if claim.exists() and json.loads(claim.read_text())['destination']!=spec['experiment']:raise ValueError('quality predecessor consumption already claimed')
 return c
