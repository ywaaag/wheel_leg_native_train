"""Explicit forward-only curriculum, v3 training recipe; parking diagnostic only."""
import copy
VERSION='motion31_forward_progression_v1'
ASSESSMENT='motion31_forward_capability_v1'
TARGETS=(2.,3.,4.)

def configuration():
 return {'version':VERSION,'targets':list(TARGETS),'envs':512,'zero_slots':128,'old_slots':192,'new_slots':192,
  'formal_updates_max':1995,'smoke_updates_max':5,'stage_updates_max':1500,'evaluation_every':250,'confirmations':2,
  'source_capabilities':[[0.,0.],[.5,0.],[1.,0.],[1.5,0.]],'parking':'diagnostic only; original training schedule retained',
  'scope':'forward only, no reverse/yaw; single evaluation seed, not final multi-seed certification'}

def commands(stage):
 if type(stage) is not int or stage not in range(3):raise ValueError('invalid forward stage')
 return configuration()['source_capabilities']+[[v,0.] for v in TARGETS[:stage+1]]

def stage_config(stage,envs=512):
 if envs not in (64,512):raise ValueError('forward64/512 only')
 values=commands(stage);unit=envs//64;old=len(values)-2
 counts=[16*unit]+[(24*unit)//old+(i<(24*unit)%old) for i in range(old)]+[24*unit]
 return {'id':stage,'name':('F2','F3','F4')[stage],'commands':values,'weights':[n/envs for n in counts],
  'sampling_mode':'fixed_slots','sampling_slots':[i for i,n in enumerate(counts) for _ in range(n)],'enforce_whitelist':True,'slot_counts':counts}

def protocol():
 from .motion_guard import protocol as absolute
 p=absolute();p.update(version=ASSESSMENT,parking_required=False,parking_scope='diagnostic only; not precise stopping',
  forward_scope='zero and positive straight commands only; original full30s/hold10..18s',
  acceptance_note='original tracking MAE<=.3 and gain .8..1.2; final4mps mean3.6..4.4 plus sustained rule; no precision drift gate')
 return p

def assess(result):
 r=copy.deepcopy(result);r['version']=ASSESSMENT
 r.setdefault('diagnostic_checks',{})['parking']=r['checks'].pop('parking',None)
 r['accepted']=all(r['checks'].values());r['failed_checks']=[k for k,v in r['checks'].items() if not v]
 return r

def cases(spec,stage):
 template=spec['student_evaluation']['cases'][0]
 return [{**template,'case_id':f'forward_{stage}_command_{i}','command':v+[.34]} for i,v in enumerate(commands(stage))]

def effective_spec(spec,stage):
 s=copy.deepcopy(spec);s['motion_training']['stage']=stage;s['student_training']['stage']=stage;s['student_training']['course_stage']=stage
 s['curriculum']['stages']=[stage_config(stage,s['ppo']['envs'])];s['student_evaluation']['cases']=cases(s,stage)
 return s

def advance(state,candidate):
 stage=state['stage'];update=candidate['update']
 if candidate.get('stage')!=stage or update<=state.get('last_evaluation_update',-1):raise ValueError('forward stage/update differs')
 records=candidate.get('evaluations',[])
 complete=candidate.get('complete_matrix') is True and len(records)==len(commands(stage))
 if complete:
  complete=all(r.get('case',{}).get('command')==v+[.34] and len(r.get('per_env',[]))==8 and len({e.get('env',e.get('env_id')) for e in r['per_env']})==8 and all(e.get('accepted') is True for e in r['per_env']) for r,v in zip(records,commands(stage)))
 streak=state.get('consecutive_passes',0)+1 if complete else 0;passed=streak>=2
 out={**state,'last_evaluation_update':update,'consecutive_passes':streak}
 if passed:out['accepted_by_stage']={**state.get('accepted_by_stage',{}),str(stage):{'checkpoint':candidate['checkpoint'],'sha256':candidate['sha256'],'update':update,'evaluations':[{'path':r['path'],'sha256':r['sha256']} for r in records]}}
 if passed and stage<2:out.update(stage=stage+1,stage_started_update=update,consecutive_passes=0)
 return out,{'stage_passed':passed,'advanced':passed and stage<2,'all_stages_passed':passed and stage==2,'complete_matrix_passed':complete}

def choose(candidates,accepted_by_stage):
 from .motion_course import choose as base
 r=base(candidates,{})
 stage=r['current_stage'];passed=accepted_by_stage.get(str(stage))
 accepted=next((c for c in candidates if stage==2 and passed and c.get('sha256')==passed['sha256'] and c.get('stage')==stage),None)
 r.update(accepted_candidate=accepted,accepted_by_stage=accepted_by_stage,final_multi_seed_certified=False,capability_scope='forward only; no reverse/yaw certification')
 return r

from .motion_course import extend_mixture
