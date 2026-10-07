"""Read immutable motion evidence; independently compare Gaussian kernels on CPU."""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runs/motion_forward_cohort_20261006/formal'
RUN = ROOT / 'runs/motion_capability_course_20261006/formal'
OUT = ROOT / 'isolated/root_cause_audit_20261006/CAPABILITY_RECIPE_AUDIT_20261006.json'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kernel(vx, vy, yaw, command_vx, command_yaw, linear_d, yaw_d):
    error = vx - command_vx
    raw = math.exp(-(error*error+vy*vy)/linear_d
                   -(yaw-command_yaw)**2/yaw_d)
    return raw, -2*error/linear_d*raw


def main():
    source_spec = read(SOURCE/'source_snapshot/spec.json')
    spec = read(RUN/'source_snapshot/spec.json')
    manifest = read(RUN/'manifest.json')
    source_manifest = read(SOURCE/'manifest.json')
    snapshot_hashes = manifest['source_snapshot_sha256']
    snapshot_check = {name: sha(RUN/'source_snapshot'/name)==digest
                      for name,digest in snapshot_hashes.items()}
    if not all(snapshot_check.values()):
        raise ValueError('immutable formal snapshot identity differs')
    if sha(SOURCE/'model_update_25.pt') != spec['source_sha256']:
        raise ValueError('source checkpoint SHA differs')
    old_d = source_spec['reward']['linear_error_denominator']
    new_d = spec['reward']['stage_linear_denominators']['1']
    yaw_d = spec['reward']['stage_yaw_denominators']['1']
    metrics = [json.loads(line) for line in (RUN/'metrics.jsonl').read_text().splitlines()]
    commands = spec['curriculum']['stages'][1]['commands']
    totals = [sum(m['task_metrics'][i]['samples'] for m in metrics) for i in range(len(commands))]
    windows = []
    for start,end in ((1,100),(101,250),(251,500)):
        subset = [m for m in metrics if start<=m['update']<=end]
        cohort = []
        for i,command in enumerate(commands):
            count = sum(m['task_metrics'][i]['samples'] for m in subset)
            cohort.append(dict(command=command,samples=count,means={
                field:sum(m['task_metrics'][i]['samples']*m['task_metrics'][i]['means'][field]
                          for m in subset if m['task_metrics'][i]['samples'])/count
                for field in ('vx_mps','vx_error_abs_mps','saturation','action_clip_fraction','dual_contact')}))
        windows.append(dict(updates=[start,end],cohorts=cohort,
                            global_raw_tracking=mean(m['rollout']['raw_mean']['velocity_tracking'] for m in subset)))
    evaluations = []
    for update in (250,500):
        for command in commands:
            label = f'evaluation_{update}_{command[0]}_{command[1]}.json'
            data = read(RUN/label)
            per_env = []
            for row,gate in zip(data['per_env'],data['capability_gate']['per_env']):
                trace = row['trace']
                hold = [x for i,x in enumerate(trace) if 10<=(i+1)*data['dt']<=18]
                kernels = {str(d):[kernel(x[3],x[4],x[5],x[6],x[7],d,yaw_d) for x in hold]
                           for d in (old_d,new_d)}
                per_env.append(dict(env_id=row['env_id'],outcome=row['outcome'],
                    failed_checks=gate['failed_checks'],
                    metrics={key:row.get(key) for key in ('mean_vx_mps','mean_abs_vx_error_mps',
                        'hold_direction_fraction','hold_signed_mean','hold_70pct_fraction',
                        'horizontal_speed_p95_mps','net_drift_m','dual_contact_fraction',
                        'peak_tilt_rad','closure_max_m','saturation_fraction')},
                    tracking_counterfactual={key:dict(raw_mean=mean(v[0] for v in values),
                        weighted_dt_mean=mean(v[0] for v in values)*8*.01,
                        abs_d_raw_d_vx_mean=mean(abs(v[1]) for v in values))
                        for key,values in kernels.items()}))
            evaluations.append(dict(update=update,command=command,path=str(RUN/label),
                sha256=sha(RUN/label),passed_envs=data['capability_gate']['passed_envs'],per_env=per_env))
    timeout_events = [dict(update=m['update'],timeouts=sum(
        c['samples']*c['means']['timeout'] for c in m['task_metrics'] if c['samples']))
        for m in metrics if any(c['samples'] and c['means']['timeout'] for c in m['task_metrics'])]
    paths = [SOURCE/'model_update_25.pt',SOURCE/'source_snapshot/spec.json',
        SOURCE/'source_snapshot/domain_reward.py',RUN/'source_snapshot/spec.json',
        RUN/'source_snapshot/train.py',RUN/'source_snapshot/runtime_env.py',
        RUN/'source_snapshot/domain_reward.py',RUN/'metrics.jsonl',RUN/'terminal_report.json',
        ROOT/'scripts/prepare_motion_capability_course.py',Path(__file__)]
    result = dict(source_checkpoint=str(paths[0]),source_sha256=sha(paths[0]),
        source_spec_matches_checkpoint=sha(paths[1])==spec['source_spec_sha256'],
        source_manifest_spec_matches=source_manifest['spec_sha256']==sha(paths[1]),
        formal_manifest_spec_matches=manifest['spec_sha256']==sha(RUN/'source_snapshot/spec.json'),
        formal_snapshot_checks=snapshot_check,identities={str(p):sha(p) for p in paths},
        unchanged_contract={k:source_spec[k]==spec[k] for k in
                            ('action','control','ground','termination','observation','history','ppo')},
        actual_kernel=dict(source_linear_d=old_d,formal_linear_d=new_d,yaw_d=yaw_d,
            weight=8,policy_dt=.01,formula='exp(-((vx-cvx)^2+vy^2)/dv-(yaw-cyaw)^2/dyaw)',
            separate_tracking_fields_ignored=True),
        scheduled_denominators=spec['reward']['stage_linear_denominators'],
        sample_totals=[dict(command=c,samples=n,fraction=n/sum(totals)) for c,n in zip(commands,totals)],
        source_training=dict(schedule_s=source_spec['curriculum']['schedule_s'],
            episode_s=source_spec['curriculum']['episode_length_s'],
            nominal_weights=source_spec['curriculum']['stages'][1]['weights']),
        formal_training=dict(schedule_s=spec['curriculum']['schedule_s'],
            episode_s=spec['curriculum']['episode_length_s'],
            nominal_hold_fraction=24/31,measured_hold_fraction='UNKNOWN: episode age not captured'),
        timeout_events=timeout_events,training_windows=windows,evaluations=evaluations,
        terminal=read(RUN/'terminal_report.json'),
        causal_limit='Kernel replay holds state fixed; no PPO or physics replay, no causal A/B.',
        online_updates_added=0,gpu_wall_added_s=0)
    with OUT.open('x') as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
    print(str(OUT))
    print('source/formal linear denominator:',old_d,new_d)
    print('snapshot identities:',all(snapshot_check.values()))
    for evaluation in evaluations:
        rows=evaluation['per_env']
        print(evaluation['update'],evaluation['command'],evaluation['passed_envs'],
              {d:round(mean(r['tracking_counterfactual'][str(d)]['raw_mean'] for r in rows),6)
               for d in (old_d,new_d)})


if __name__ == '__main__':
    main()
