"""Summarize immutable motion forward diagnostics and milestone evaluations."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/motion_forward_cohort_20261006'
SOURCE=ROOT/'runs/motion_retention_ab_20261006/off_formal'
OUT=RUN/'analysis.json'


def percentile_stats(array):
    return {key:np.round(value,6).tolist() for key,value in {
        'mean':np.nanmean(array,axis=0),'p05':np.nanpercentile(array,5,axis=0),
        'p50':np.nanpercentile(array,50,axis=0),'p95':np.nanpercentile(array,95,axis=0),
        'max_abs':np.nanmax(np.abs(array),axis=0)}.items()}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    report={'diagnostic':{},'evaluations':{}}
    for side in ('pos','neg'):
        data=json.loads((RUN/f'start_{side}_diagnostic.json').read_text())
        diag=data['control_diagnostics']
        rows=np.full((len(diag['rows']),8,54),np.nan)
        for i,step in enumerate(diag['rows']):
            for j,row in enumerate(step[:8]):
                if row is not None:
                    rows[i,j]=row
        hold=rows[199:600].reshape(-1,54)
        groups={}
        for name,(left,right) in diag['groups'].items():
            groups[name]=percentile_stats(hold[:,left:right])
        groups['raw_action']['clip_fraction']=np.nanmean(np.abs(hold[:,12:18])>1,axis=0).tolist()
        groups['physical_clipped_nm']['saturation_fraction']=np.nanmean(
            np.abs(hold[:,42:48])>=np.array([40,40,5.5,40,40,5.5])-1e-4,axis=0).tolist()
        report['diagnostic'][side]={'groups':groups,'valid_hold_rows':int(np.isfinite(hold[:,0]).sum()),
            'terminal_diagnostics_missing':diag['terminal_diagnostics_missing']}
    for title,base,update in (('start',SOURCE,49),('update25',RUN/'formal',25)):
        report['evaluations'][title]={}
        for command in ('0_0','0.5_0','-0.5_0'):
            data=json.loads((base/f'evaluation_{update}_{command}.json').read_text())
            gate=data.get('standing_gate',data.get('motion_gate'))
            keys=('outcome','continuous_s','mean_abs_vx_error_mps','mean_vx_mps',
                  'vx_direction_fraction','stop_vx_abs_mps','net_drift_m','max_excursion_m',
                  'dual_contact_fraction','saturation_fraction','peak_tilt_rad','closure_max_m')
            report['evaluations'][title][command]={
                'passed_envs':gate['passed_envs'],'scored_envs':gate['scored_envs'],
                'per_env':[{**{k:row.get(k) for k in keys},'env_id':row['env_id'],
                            'failed_checks':check['failed_checks']}
                           for row,check in zip(data['per_env'],gate['per_env'])]}
    OUT.write_text(json.dumps(report,indent=2)+'\n')
    print(OUT)


if __name__=='__main__':
    main()
