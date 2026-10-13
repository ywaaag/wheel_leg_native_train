"""Manual full-resume checks; copied into the experiment bundle before training."""
import json
from pathlib import Path

def verify_resume(info,spec,cp,checkpoint):
 from .data import sha
 from .manual_parameters import SETTINGS,REWARD_SHA
 from .manual_support import RECIPE,REWARD
 from native_stand.command_v6.tools.execution_identity import identity
 from native_stand.command_v6.wiring import validate_persisted_certificate
 checkpoint=Path(checkpoint).resolve();phase=checkpoint.parent
 if phase!=Path(info['run']).resolve()/'formal':raise ValueError('resume only from this manual formal checkpoint')
 terminal=json.loads((phase/'terminal_report.json').read_text());chain=json.loads((Path(info['run'])/'chain_terminal_report.json').read_text())
 if terminal.get('status') not in ('COMPLETED','STOPPED_BOUNDED') or terminal.get('failure') or chain.get('status') not in ('COMPLETED','STOPPED_BOUNDED') or chain.get('failure'):raise ValueError('failed or unsettled run cannot be resumed as normal continuation')
 if cp.get('course_resume_version')!='student_full_training_resume_v1' or cp.get('recipe_version')!=RECIPE or cp.get('interface_version')!='multiskill_mcu_v2' or not cp.get('fixed_std'):raise ValueError('not a full manual training checkpoint')
 if cp.get('training_recipe')!=spec['student_training'] or cp.get('asset_sha256')!=spec['asset_sha256'] or cp.get('spec_sha256')!=sha(phase/'source_snapshot/spec.json'):raise ValueError('resume checkpoint/spec/asset identity differs')
 for k in ('critic','optimizer','training_rng','cumulative_update','recipe_updates','course_state','certified_capabilities'):
  if k not in cp:raise ValueError('full resume missing '+k)
 if cp['training_recipe']['reward'].get('manual_implementation_sha256')!=REWARD_SHA:raise ValueError('reward changed; start a new Actor-only experiment')
 if cp.get('source_code_sha256')!=identity(spec)['location_independent_modules_sha256']:raise ValueError('execution code changed; full resume forbidden')
 task=json.loads(Path(info['task_manifest']).read_text())
 if task['manual_experiment']['settings']!=SETTINGS:raise ValueError('hyperparameters changed; new experiment required')
 smoke=spec['recovery_course'].get('smoke_evidence') if spec['recovery_course']['resume'] else {'folder':str(Path(info['run'])/'smoke')}
 folder=Path(smoke['folder']);previous=json.loads((folder/'source_snapshot/spec.json').read_text())
 if validate_persisted_certificate(folder,previous)['status']!='PASSED':raise ValueError('original public smoke certificate missing or invalid')
 return {'folder':str(folder),'sha256':sha(folder/'wiring_certificate.json')}
