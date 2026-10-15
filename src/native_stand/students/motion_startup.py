"""Explicit minimal startup: exact source proof reuse, actual short wiring only."""
import json
from pathlib import Path
from .data import sha
VERSION='motion31_minimal_startup_v1'
SMOKE_VERSION='motion31_wiring5_no_capability_eval_v2'

def source_protocol(spec):
 if spec.get('student_training',{}).get('course_version')=='motion31_forward_progression_v1':
  from .motion_guard import protocol
  return protocol()
 return spec['motion_assessment']

def source_rows(spec,rows):
 if spec.get('student_training',{}).get('course_version')=='motion31_forward_progression_v1':
  from .motion_forward_course import assess
  return [assess(r) for r in rows]
 return rows

def smoke_profile():
 from .motion_training import short_wiring
 p=short_wiring();p.update(version=SMOKE_VERSION,scope='actual5 PPO wiring; no independent capability evaluation',
  mandatory=['actual_actor_update','actual_critic_update','nonzero_reward','all_cohort_hold_samples','checkpoint_roundtrip','runtime_control_readback','command_observation_readback'])
 return p

def build(spec,evidence_runs):
 """Freeze matching raw JSON/SHA references; missing endpoints remain new requests."""
 selected={};protocol=source_protocol(spec);key=lambda row:json.dumps({k:row[k] for k in ('command','seed','family','yaw_rad','seconds')},sort_keys=True)
 expected={key(row):row for row in spec['student_evaluation']['cases']}
 for directory in evidence_runs:
  folder=Path(directory).resolve();snapshot=folder/'source_snapshot/spec.json'
  if not snapshot.is_file():continue
  before=json.loads(snapshot.read_text())
  if any(before.get(k)!=spec.get(k) for k in ('action','control','ground','observation','history','student_interface')):continue
  for p in sorted(folder.glob('evaluation_*.json')):
   raw=json.loads(p.read_text())
   if not isinstance(raw,dict) or not isinstance(raw.get('case'),dict):continue
   try:k=key(raw['case'])
   except KeyError:continue
   if k not in expected or k in selected:continue
   if (raw.get('checkpoint_sha256')!=spec['source_sha256'] or raw.get('asset_sha256')!=spec['asset_sha256'] or raw.get('protocol')!=protocol
       or raw.get('spec_sha256')!=sha(snapshot) or len(raw.get('per_env',[]))!=8 or raw.get('model_unchanged') is not True):continue
   rows=raw['per_env']
   if len({r.get('env',r.get('env_id')) for r in rows})!=8 or any('runtime_fault' in r.get('quality_termination_causes',[]) for r in rows):continue
   # Trace SHA is verified once at publication. Runtime rechecks the frozen raw
   # identity and presence; its content digest remains bound in the raw JSON.
   trace=folder/raw.get('trace',{}).get('path','')
   if trace.parent!=folder or not trace.is_file() or sha(trace)!=raw['trace'].get('sha256'):continue
   selected[k]={'case_key':k,'raw_path':str(p),'raw_sha256':sha(p),'source_spec':str(snapshot),'source_spec_sha256':sha(snapshot),
    'trace_path':str(trace),'trace_sha256':raw['trace']['sha256']}
 return {'version':VERSION,'source_policy':'reuse_exact_source_evidence_then_evaluate_only_missing_endpoints','smoke_policy':SMOKE_VERSION,
  'references':[selected[k] for k in expected if k in selected],
  'missing_commands':[row['command'] for k,row in expected.items() if k not in selected],
  'source_evaluation_is_not_wiring':True,'no_capability_prerequisite_for_smoke':True}

def resolve(spec):
 c=spec['motion_startup']
 if c.get('version')!=VERSION or c.get('smoke_policy')!=SMOKE_VERSION or spec['student_training'].get('smoke_wiring')!=smoke_profile():raise ValueError('minimal startup version/profile differs')
 expected={json.dumps({k:row[k] for k in ('command','seed','family','yaw_rad','seconds')},sort_keys=True):row for row in spec['student_evaluation']['cases']}
 result={}
 for reference in c['references']:
  k=reference['case_key'];path=Path(reference['raw_path']);snapshot=Path(reference['source_spec']);trace=Path(reference['trace_path'])
  if k not in expected or k in result or sha(path)!=reference['raw_sha256'] or sha(snapshot)!=reference['source_spec_sha256'] or not trace.is_file():raise ValueError('source reuse identity/duplicate differs')
  raw=json.loads(path.read_text());before=json.loads(snapshot.read_text())
  if any(before.get(field)!=spec.get(field) for field in ('action','control','ground','observation','history','student_interface')):raise ValueError('source physical/IO identity differs')
  actual_key=json.dumps({field:raw['case'][field] for field in ('command','seed','family','yaw_rad','seconds')},sort_keys=True)
  if (actual_key!=k or raw.get('checkpoint_sha256')!=spec['source_sha256'] or raw.get('asset_sha256')!=spec['asset_sha256'] or raw.get('protocol')!=source_protocol(spec)
      or raw.get('spec_sha256')!=reference['source_spec_sha256'] or raw.get('trace',{}).get('sha256')!=reference['trace_sha256'] or len(raw.get('per_env',[]))!=8 or raw.get('model_unchanged') is not True):raise ValueError('source evidence semantics differ')
  result[k]={'case':raw['case'],'path':str(path),'sha256':reference['raw_sha256'],'per_env':source_rows(spec,raw['per_env']),'derived_assessment':spec['motion_assessment'],'reused':True,'reuse_reference':reference}
 missing=[row for k,row in expected.items() if k not in result]
 if [r['command'] for r in missing]!=c['missing_commands']:raise ValueError('source missing-endpoint plan differs')
 return result,missing

def merge(spec,reused,new_records):
 key=lambda row:json.dumps({k:row[k] for k in ('command','seed','family','yaw_rad','seconds')},sort_keys=True)
 records={**reused}
 for row in new_records:
  k=key(row['case'])
  if k in records:raise ValueError('duplicate evaluated/reused source proof')
  records[k]=row
 if len(records)!=len(spec['student_evaluation']['cases']):raise ValueError('source proof matrix incomplete')
 return [records[key(row)] for row in spec['student_evaluation']['cases']]
