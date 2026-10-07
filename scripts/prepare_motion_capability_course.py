"""Generate the authorized capability-first motion spec and independent ledger."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = json.loads((root / 'configs/experiments/motion_forward_cohort_20261006/spec.json').read_text())
spec = base
spec['experiment'] = 'motion_capability_course_20261006'
spec['version'] = 6
spec['source_checkpoint'] = str(root / 'runs/motion_forward_cohort_20261006/formal/model_update_25.pt')
spec['source_sha256'] = 'bacd31f34a1e3917afa8e5dd9648bb5985c023dd0bc9ffd6a96ad1e1eed6fbad'
spec['source_update'] = 25
spec['source_spec_sha256'] = '577a7a7e181ad3a2b17ba9e555e0ed1cee6b182ce40f7fedce7fc698ab48bf73'
spec['seed'] = 20261006
course = spec['curriculum']
course.update(active_stage=1, minimum_zero_fraction=.2, episode_length_s=31., schedule_s=[1.,2.,24.,2.])
course['task_progression'] = dict(initial_stage=1,max_enabled_stage=8,
    consecutive_confirmations=1,standing_regression_confirmations=2,
    learned_regression_confirmations=2,
    confirmation_spacing_updates=250,merge_nearby_updates=0,
    max_updates_per_stage=1500,blocked_reason='linear then yaw capability course')

def stage(index, kind, target):
    current = [[target,0],[-target,0]] if kind=='L' else [[0,target],[0,-target]]
    if kind=='L':
        previous = [[sign*speed,0] for speed in (.5,1.,2.,3.) if speed<target for sign in (1,-1)]
        commands = [[0,0]]+previous+current
        weights = [.2]+[.2/len(previous)]*len(previous)+[.3,.3]
    else:
        linear = [[sign*speed,0] for speed in (.5,1.,2.,3.,4.) for sign in (1,-1)]
        previous = [[0,sign*speed] for speed in (1.,2.,3.) if speed<target for sign in (1,-1)]
        commands = [[0,0]]+linear+previous+current
        weights = [.2]+[.3/len(linear)]*len(linear)+[.1/len(previous)]*len(previous)+[.2,.2] if previous else [.2]+[.3/len(linear)]*len(linear)+[.25,.25]
    return dict(id=index,name=f'{kind}{int(target)}',commands=commands,weights=weights,
        boundary=current,command_mode='fixed',schedule_s=[1.,2.,24.,2.],episode_length_s=31.)

course['stages'] = [dict(id=0,name='L0',commands=[[0,0]],weights=[1.],boundary=[[0,0]],
    command_mode='fixed',schedule_s=[1.,2.,24.,2.],episode_length_s=31.)]
course['stages'] += [stage(i,'L',v) for i,v in enumerate((1.,2.,3.,4.),1)]
course['stages'] += [stage(i,'Y',v) for i,v in enumerate((1.,2.,3.,4.),5)]
spec['evaluation'].update(protocol_identity='capability_v2',seconds=30.,light_seconds=4.,
    evaluation_schedule_s=[2.,8.,8.,8.],
    steady_window_s=[10.,18.],motion_window_s=[10.,18.],full_every_updates=250,
    checkpoint_every_updates=100,light_every_updates=0,standing_height_m=[.34,.46],
    dual_contact_min=.95,peak_tilt_max_rad=.5,saturation_fraction_max=.5,
    yaw_drift_max_m=100.,yaw_excursion_max_m=100.,full_at_final=True)
spec['reward']['stage_linear_denominators']={str(i):float(v) for i,v in
    enumerate((.01,1.,4.,9.,16.,16.,16.,16.,16.))}
spec['reward']['stage_yaw_denominators']={str(i):float(v) for i,v in
    enumerate((.09,.09,.09,.09,.09,1.,4.,9.,16.))}
spec['budget'].update(source_eval_wall_s=300,smoke_updates=10,formal_updates=6000,
    smoke_wall_s=1800,formal_wall_s=64800,sample_limit=49152000,formal_samples=49152000)
spec['safety_stop_commands'] = []
spec['authorization_note'] = '2026-10-06 capability course, GPU1; smoke<=10, formal<=6000, total wall<=18h'
out = root / 'configs/experiments/motion_capability_course_20261006'
out.mkdir(parents=True,exist_ok=False)
(out/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
if not (out/'budget.json').exists():
    (out/'budget.json').write_text(json.dumps(dict(authorization='AUTHORIZED',
        limits=dict(source_eval=1,smoke=10,formal=6000,evaluate=0,play=0),
        used=dict(source_eval=0,smoke=0,formal=0,evaluate=0,play=0),attempts={},
        source_eval_wall_used_s=0.),indent=2)+'\n')
print(json.dumps(dict(spec=str(out/'spec.json'),sha256=hashlib.sha256((out/'spec.json').read_bytes()).hexdigest(),
    stages=[(s['id'],s['name'],len(s['commands'])) for s in course['stages']])))
