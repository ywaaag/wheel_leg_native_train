"""One-shot immutable terminal/event audit; no report rewrite, polling or notification."""
import argparse
import json
from pathlib import Path
from .experiment_preparation import checked_input,publish
from ..domain.time_axis import sustained_events


def audit(run,ledger=None):
    run=Path(run).resolve();inputs={};missing=[]
    def read(path):
        if not path.is_file():missing.append(str(path));return {}
        inputs.update([checked_input(path)]);return json.loads(path.read_text())
    manifest=read(run/'manifest.json');terminal=read(run/'terminal_report.json');progress=read(run/'progress.json')
    spec=read(run/'source_snapshot/spec.json')
    dt=spec.get('control',{}).get('policy_dt_s',.01)
    from ..domain.trace_schema import validate_rows,STATE,CONTROL
    book=read(Path(ledger).resolve()) if ledger else {}
    attempt=book.get('attempts',{}).get(manifest.get('attempt_id'),{})
    cases=[]
    for path in sorted(run.glob('evaluation*.json')):
        read(path) # bind JSON receipt identity
        from .evaluation_storage import read as read_evaluation
        result=read_evaluation(path);envs=[]
        archive=result.get('numeric_trace_storage')
        if archive:inputs.update([checked_input(path.parent/archive['path'],archive['sha256'])])
        for row in result.get('per_env',[]):
            trace=row.get('compact_trace_100hz');control=row.get('control_diagnostics_100hz')
            if trace:validate_rows(trace,'state')
            contact=sustained_events([not (v[STATE['left_contact_n']]>2 and v[STATE['right_contact_n']]>2) for v in trace],dt=dt) if trace else None
            channels=None
            if control:
                limits=[40,40,5.5,40,40,5.5]
                validate_rows(control,'control')
                channels=[{'channel':i,'fraction':sum(abs(v[CONTROL['physical_clipped_torque'].start+i])>=limit-1e-4 for v in control)/len(control),
                    'field':'physical_clipped_torque','scope':'latest held PD request, not every PD step engine torque'} for i,limit in enumerate(limits)]
            envs.append({'env_id':row.get('env_id'),'family':row.get('family',result.get('evaluation_family')),
                'success':row.get('success'),'failed_checks':row.get('standing_failed_checks',row.get('failed_checks')),
                'hold_window_complete':row.get('hold_window_complete',row.get('continuous_window_completed')),
                'hold_prefix_s':row.get('diagnostic_hold_prefix_s'),'contact_loss_events':contact,
                'contact_loss_longest_s':max((v['duration_s'] for v in contact),default=0.) if contact is not None else None,
                'torque_limit_channels_policy_rate':channels,'missing_event_evidence':not bool(trace)})
        cases.append({'path':str(path),'checkpoint_sha256':result.get('checkpoint_sha256'),
            'passed_envs':(result.get('recovery_gate') or result.get('capability_gate') or {}).get('passed_envs'),
            'per_env':envs})
    actual=terminal.get('actual_updates',progress.get('actual_updates'))
    from ..domain.accounting import summary
    return {'run':str(run),'inputs':inputs,'status':terminal.get('status','MISSING_EVIDENCE'),
        'stop_reason':terminal.get('reason',terminal.get('early_stop_reason')),
        'updates':summary(manifest,terminal,progress,book),
        'evaluations':cases,'missing_files':missing,'simulation':0,'optimizer_updates':0,
        'scope':'policy-rate first-episode raw data; missing fields UNKNOWN, not zero'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--ledger',type=Path);p.add_argument('--output-dir',type=Path)
    a=p.parse_args();result=audit(a.run,a.ledger)
    if a.output_dir:publish(a.output_dir,{'audit.json':result},result['inputs'])
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
