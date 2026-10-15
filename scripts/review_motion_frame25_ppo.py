"""Read-only review of completed frame25 PPO evaluations; no simulation."""
import argparse,json,hashlib,collections
from pathlib import Path

def review(run,output):
 run=Path(run).resolve();output=Path(output).resolve()
 if output.exists():raise FileExistsError(output)
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 inputs={}
 def read(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
 terminal=read(run/'chain_terminal_report.json')
 if terminal['status'] not in ('COMPLETED','FAILED','STOPPED_BOUNDED'):raise ValueError('finished chain required')
 spec=read(run/'formal/source_snapshot/spec.json');source=Path(spec['source_checkpoint']);assert sha(source)==spec['source_sha256']
 registry=read(run/'formal/candidate_registry.json');rows=[]
 paths=[('source',0,run/'source_eval/evaluation_source.json',source,spec['source_sha256'])]+[('formal',r['update'],run/'formal'/r['evaluation'],Path(r['checkpoint']),r['checkpoint_sha256']) for r in registry if r['kind']=='full']
 for phase,u,p,cp,digest in paths:
  assert sha(cp)==digest;inputs[str(cp)]=digest;d=read(p);assert d['checkpoint_sha256']==digest
  if phase=='formal':assert next(r['evaluation_sha256'] for r in registry if r['update']==u)==sha(p)
  es=d['per_env'];gate=d['capability_gate'];assert len(es)==8 and gate['scored_envs']==8 and d['effective_protocol']['gate_identity']=='motion_standing034_v1'
  avg=lambda k:None if any(e.get(k) is None for e in es) else sum(e[k] for e in es)/8
  rows.append({'phase':phase,'update':u,'checkpoint':str(cp),'sha256':digest,'passed':gate['passed_envs'],'completed_hold_windows':sum(bool(e.get('window_time_axis',{}).get('complete')) for e in es),'minimum_first_episode_s':min(e['continuous_s'] for e in es),'mean_first_episode_s':avg('continuous_s'),'contact_fraction':avg('dual_contact_fraction'),'saturation_fraction':avg('saturation_fraction'),'peak_tilt_rad':max(e['peak_tilt_rad'] for e in es),'mean_height_m':avg('height_steady_mean_m'),'vx_MAE_mps':avg('mean_abs_vx_error_mps'),'termination_counts':dict(collections.Counter(e['termination_reason'] for e in es)),'failed_checks':dict(collections.Counter(k for e in gate['per_env'] for k in e['failed_checks'])),'per_env':[{k:e.get(k) for k in ['env_id','outcome','termination_reason','continuous_s','height_min_m','peak_tilt_rad','saturation_fraction']} for e in es]})
 best=max(rows,key=lambda r:(r['passed'],r['completed_hold_windows'],r['minimum_first_episode_s'],r['mean_first_episode_s'],-r['update']))
 metrics=[json.loads(x) for x in (run/'formal/metrics.jsonl').read_text().splitlines()]
 result={'status':terminal['status'],'rows':rows,'best_diagnostic_candidate':best,'selection_scope':'full protocol passed count, complete windows, minimum then mean first-episode survival; survival-only choice is not accepted','accepted':best['passed']==8,'formal_actor_samples':sum((x.get('frame25_ppo_control') or {}).get('effective_actor_update_samples',0) for x in metrics),'formal_actor_optimizer_steps':sum((x.get('frame25_ppo_control') or {}).get('actor_optimizer_steps',0) for x in metrics),'chain_wall_s':terminal['chain_wall_s'],'used':terminal['budget']['used'],'inputs':inputs,'simulation':0,'offline_optimizer_updates':0,'source_unchanged':sha(source)==spec['source_sha256']}
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','accepted','formal_actor_samples','formal_actor_optimizer_steps','chain_wall_s','used']},indent=2));print('best',best['update'],best['minimum_first_episode_s'],best['mean_first_episode_s'])
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();review(a.run,a.output)
