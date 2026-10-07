"""Retired historical source/smoke driver; use the explicit shared supervisor."""
import json
import os
import time
from pathlib import Path

from native_stand.command_v6.completion import read,write
from native_stand.command_v6.stand_chain import run_phase

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'configs/experiments/motion_high_speed_course_20261007/spec.json'
RUN=ROOT/'runs/motion_high_speed_course_20261007'


def main():
    from native_stand.command_v6.tools.entrypoints import historical_cli_guard
    historical_cli_guard('scripts/run_motion_high_speed_preparation.py')
    assert os.environ.get('CUDA_VISIBLE_DEVICES')=='1', 'physical GPU1 required'
    assert os.environ.get('HAPI_SESSION_ID')==read(SPEC.with_name('course_config.json'))['hapi_session']
    RUN.mkdir(exist_ok=False)
    book=read(SPEC.with_name('budget.json'))
    assert not book['attempts']
    book['chain_started_unix_s']=time.time()
    write(SPEC.with_name('budget.json'),book)
    write(RUN/'preparation_manifest.json',{'spec':str(SPEC),'physical_gpu':1,
        'hapi_session':os.environ['HAPI_SESSION_ID'],'started_unix_s':book['chain_started_unix_s']})
    for phase in ('source_eval','smoke'):
        result=run_phase(SPEC,phase,RUN/phase)
        write(RUN/(phase+'_preparation.json'),result)
        if result['exit_code'] or result['status']!='COMPLETED':
            raise RuntimeError(f'{phase} failed; see phase log and exact terminal')
        if phase=='source_eval' and not result['progress'].get('source_pass'):
            raise RuntimeError('source capability recheck failed; no PPO authorized downstream')
        if phase=='smoke':
            assert result['progress']['actual_updates']==10
            assert result['progress']['actor_parameters_changed']
            metrics=[json.loads(line) for line in (RUN/phase/'metrics.jsonl').read_text().splitlines()]
            assert any(row.get('task_metrics') and any(
                cohort.get('width_phase_diagnostics',{}).get('hold_fraction',0)>0
                for cohort in row['task_metrics']) for row in metrics), 'smoke never reached holding'
    write(RUN/'preparation_pass.json',{'status':'PREPARATION_PASS','smoke_updates':10,
        'actor_parameters_changed':True,'holding_samples_observed':True})
    print(json.dumps({'status':'PREPARATION_PASS','run':str(RUN),'smoke_updates':10}))


if __name__=='__main__':
    main()
