"""One-shot Motion comparison from explicit checkpoint/evaluation files; no polling."""
import argparse
import json
import math
from pathlib import Path
from ..domain.evaluation_config import identities
from ..domain.time_axis import window_indices
from ..domain.evidence import validate_effective_protocol
from .experiment_preparation import checked_input,publish
from .evaluation_loader import load


def compare(request):
    if set(request)!={'models'} or not isinstance(request['models'],list) or not request['models']:
        raise ValueError('Explicit models list required')
    models={};inputs={};contracts={};common_asset=None
    for model in request['models']:
        if set(model)!={'name','checkpoint','checkpoint_sha256','evaluations'}:raise ValueError('Unknown model fields')
        name=model['name']
        if not isinstance(name,str) or not name or name in models:raise ValueError('Unique model names required')
        checkpoint,sha=checked_input(model['checkpoint'],model['checkpoint_sha256']);inputs[checkpoint]=sha
        commands={}
        for item in model['evaluations']:
            if set(item)!={'path','sha256'}:raise ValueError('Evaluation requires path and SHA')
            path,rawsha=checked_input(item['path'],item['sha256']);path=Path(path);inputs[str(path)]=rawsha
            manifest=json.loads((path.parent/'manifest.json').read_text());inputs.update([checked_input(path.parent/'manifest.json')])
            asset=manifest['asset_sha256']
            if common_asset is not None and common_asset!=asset:raise ValueError('Comparison asset differs')
            common_asset=asset
            payload,evidence=load(path.parent,{'evaluation':path.name,'evaluation_sha256':rawsha,
                'checkpoint_sha256':sha},spec_sha256=manifest['spec_sha256'],checkpoint_sha256=sha,
                asset_sha256=asset,required_fields=('env_id','continuous_s'))
            target=tuple(payload['target'][:2]);key=str(list(target))
            if len(target)!=2 or any(not math.isfinite(v) for v in target) or (target[0] and target[1]) or key in commands:
                raise ValueError('Duplicate or unsupported straight/yaw command')
            protocol=payload['effective_protocol']
            if 'effective_protocol_sha256' in protocol:validate_effective_protocol(protocol)
            identity=identities(protocol)
            if key in contracts and contracts[key]!=identity['scoring_sha256']:raise ValueError('Same-command scoring identity differs')
            contracts[key]=identity['scoring_sha256']
            expected=protocol['scored_envs'];rows=payload['per_env']
            if len(rows)!=expected or len({r['env_id'] for r in rows})!=expected:raise ValueError('Scored env coverage differs')
            gates={r['env_id']:r for r in payload.get('capability_gate',{}).get('per_env',[])}
            axis=3 if target[0] or not any(target) else 5;value=target[0] if axis==3 else target[1]
            window=protocol['motion_window_s'] if any(target) else protocol['steady_window_s']
            output=[]
            for row in rows:
                trace=row.get('trace');timing=None;metrics=None;complete=False
                if trace:
                    timing=window_indices(len(trace),dt=payload['dt'],window_s=window)
                    start,stop=timing['index_half_open'];values=[float(r[axis]) for r in trace[start:stop]]
                    if values and all(math.isfinite(v) for v in values):
                        metrics={'mean':sum(values)/len(values),'mean_absolute':sum(abs(v) for v in values)/len(values),
                            'mean_absolute_error':sum(abs(v-value) for v in values)/len(values),
                            'direction_fraction':sum(v*value>0 for v in values)/len(values) if value else None}
                        complete=(timing['complete'] and row['continuous_s']>=protocol['requested_seconds']-1e-5
                            and row.get('outcome','completed')=='completed')
                output.append({'env_id':row['env_id'],'window':timing,'full_episode_complete':row['continuous_s']>=protocol['requested_seconds']-1e-5,
                    'response_certifiable':complete,'metric_scope':'COMPLETE_WINDOW' if complete else 'PARTIAL_OR_MISSING_DIAGNOSTIC',
                    'zero_window_mean_yaw':sum(float(r[5]) for r in trace[start:stop])/(stop-start) if trace and stop>start else None,
                    'window_metrics':metrics,'reported_metrics':{k:v for k,v in row.items() if k!='trace'},
                    'gate':gates.get(row['env_id']),'termination_reason':row.get('termination_reason')})
            complete=all(r['response_certifiable'] for r in output)
            average=sum(r['window_metrics']['mean'] for r in output)/len(output) if all(r['window_metrics'] for r in output) else None
            commands[key]={'target':list(target),'evidence':evidence,'identities':identity,'per_env':output,
                'complete':complete,'mean_response':average,'metric_scope':'COMPLETE_WINDOW' if complete else 'DIAGNOSTIC_ONLY',
                'original_gate':payload.get('capability_gate')}
        pairs={}
        for axis in (0,1):
            zero=commands.get(str([0,0])) or next((r for r in commands.values() if r['target']==[0,0]),None)
            positives=[r for r in commands.values() if r['target'][axis]>0]
            for pos in positives:
                c=pos['target'][axis];neg=next((r for r in commands.values() if r['target'][axis]==-c),None)
                group=[zero,pos,neg];eligible=all(r and r['complete'] and r['mean_response'] is not None for r in group)
                # zero velocity metric is vx; yaw asymmetry needs zero yaw, not zero vx.
                b=(sum(float(r['zero_window_mean_yaw']) if r['zero_window_mean_yaw'] is not None else float('nan') for r in zero['per_env'])/len(zero['per_env']) if axis==1 and zero else zero['mean_response'] if zero else None)
                if b is None or not math.isfinite(b):eligible=False
                pairs[f'{axis}:{c}']={'scope':'COMPLETE_WINDOW' if eligible else 'MISSING_OR_PARTIAL',
                    'bias':b if eligible else None,
                    'gain':(pos['mean_response']-neg['mean_response'])/(2*c) if eligible else None,
                    'asymmetry':(pos['mean_response']+neg['mean_response'])/2-b if eligible else None}
        models[name]={'checkpoint':checkpoint,'checkpoint_sha256':sha,'commands':commands,'pairs':pairs}
    reference=next(iter(models));paired={}
    for name,model in models.items():
        if name==reference:continue
        comparisons=[]
        for command in model['commands'].values():
            baseline=next((r for r in models[reference]['commands'].values() if r['target']==command['target']),None)
            if baseline is None:continue
            b={r['env_id']:r for r in baseline['per_env']};rows=[]
            if set(b)!={r['env_id'] for r in command['per_env']}:raise ValueError('Paired env identities differ')
            for row in command['per_env']:
                old=b[row['env_id']];complete=row['response_certifiable'] and old['response_certifiable']
                metrics=row['window_metrics'];previous=old['window_metrics']
                rows.append({'env_id':row['env_id'],'scope':'COMPLETE_WINDOW' if complete else 'DIAGNOSTIC_ONLY',
                    'mean_delta':metrics['mean']-previous['mean'] if metrics and previous else None,
                    'MAE_delta':metrics['mean_absolute_error']-previous['mean_absolute_error'] if metrics and previous else None,
                    'current_termination_reason':row['termination_reason']})
            comparisons.append({'target':command['target'],'per_env':rows,'complete':all(r['scope']=='COMPLETE_WINDOW' for r in rows)})
        paired[name]={'reference':reference,'commands':comparisons}
    return {'version':1,'models':models,'paired_comparisons':paired,'inputs_sha256':inputs,'asset_sha256':common_asset,
        'simulation':0,'optimizer_updates':0,'scope':'new window audit; archived gate/SHA retained; no new capability claim'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True)
    p.add_argument('--output-dir',type=Path);a=p.parse_args()
    result=compare(json.loads(a.request.read_text()))
    if a.output_dir:publish(a.output_dir,{'comparison.json':result},result['inputs_sha256'],completion_marker=True)
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
