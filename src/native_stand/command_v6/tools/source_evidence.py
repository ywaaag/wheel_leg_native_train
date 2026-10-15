"""Read-only complete source certificate. No imported attempts or budget credits."""
import argparse,json
from pathlib import Path
from .experiment_preparation import checked_input
from .evaluation_loader import load
from .execution_identity import identity
from ..domain.evaluation_config import identities


def recipe(spec):
    from ..domain.experiment_identity import sections
    return sections(spec)['behavior']


def check(spec,folder):
    folder=Path(folder).resolve();evidence=[];missing=[];conflicts=[];warnings=[]
    try:
        manifest=json.loads((folder/'manifest.json').read_text());terminal=json.loads((folder/'terminal_report.json').read_text())
        frozen=json.loads((folder/'source_snapshot/spec.json').read_text());registry=json.loads((folder/'candidate_registry.json').read_text())
        if terminal.get('status')!='COMPLETED':missing.append('completed source terminal')
        if terminal.get('actual_updates',0)!=0:conflicts.append('source evidence contains PPO updates')
        if manifest.get('spec_sha256')!=checked_input(folder/'source_snapshot/spec.json')[1]:conflicts.append('frozen spec SHA differs')
        if recipe(spec)!=recipe(frozen):conflicts.append('effective recipe differs')
        actual=identity(spec)
        from .execution_identity import recorded
        old=recorded(folder,manifest)
        from .execution_identity import execution_dependencies
        if old.get('relative_modules_sha256'):
            old_scope=execution_dependencies(old['relative_modules_sha256'],spec.get('task','motion'))
            if old_scope['modules_sha256']!=actual['execution_dependencies']['modules_sha256']:warnings.append('recorded source execution differs from current code; not a strict same-code claim')
        elif old.get('execution_dependencies') is None:missing.append('scoped execution dependencies')
        elif old.get('execution_dependencies')!=actual.get('execution_dependencies'):warnings.append('recorded source execution differs from current code; not a strict same-code claim')
        for field in ('PPO_sha256','dependencies'):
            if field not in old:missing.append('execution_identity.'+field)
            elif old[field]!=actual[field]:warnings.append('recorded dependency differs: '+field)
        if manifest.get('asset_sha256')!=spec['asset_sha256']:conflicts.append('manifest asset differs')
        source=[r for r in registry if r.get('role')=='source']
        if not source:missing.append('source registry')
        specsha=checked_input(folder/'source_snapshot/spec.json')[1]
        targets=[]
        for entry in source:
            if entry['checkpoint_sha256']!=spec['source_sha256']:conflicts.append('checkpoint SHA differs');continue
            raw,ref=load(folder,entry,spec_sha256=specsha,checkpoint_sha256=spec['source_sha256'],asset_sha256=spec['asset_sha256'])
            protocol=raw['effective_protocol'];rows=raw['per_env'];n=protocol['scored_envs']
            if manifest.get('evaluator_sha256') is None:missing.append('evaluator_sha256')
            if entry.get('identity',{}).get('evaluator_sha256') not in (None,manifest.get('evaluator_sha256')):conflicts.append('evaluator identity differs')
            if len(rows)!=n or len({r['env_id'] for r in rows})!=n:missing.append('scored environments')
            for row in rows:
                complete=(row.get('post_rise_evidence_status')=='COMPLETE' if raw.get('task')=='recovery' else
                    row.get('continuous_s',0)>=protocol['requested_seconds']-1e-5)
                if not complete:missing.append('complete window '+str(row['env_id']))
                if row.get('runtime_fault') or row.get('outcome')=='runtime_fault':conflicts.append('runtime fault')
            from .evaluate_checkpoint import protocol_for_spec
            expected=protocol_for_spec(spec,raw.get('seconds',protocol['requested_seconds']))
            if identities(expected)['scoring_sha256']!=identities(protocol)['scoring_sha256']:conflicts.append('scoring identity differs')
            target=raw.get('target',[0,0])[:2];targets.append(target)
            evidence.append({**ref,'scoring_sha256':identities(protocol)['scoring_sha256'],
                'evaluator_sha256':manifest.get('evaluator_sha256')})
        required=[[0,0],*spec.get('source_evaluation_commands',[])]
        if spec.get('task')!='recovery' and any(t not in targets for t in required):missing.append('required source commands')
        checkpoint,sha=checked_input(spec['source_checkpoint'],spec['source_sha256'])
    except (OSError,KeyError,ValueError,TypeError) as exc:missing.append(str(exc))
    return {'status':'CONFLICTING' if conflicts else 'MISSING' if missing else 'REUSABLE',
        'folder':str(folder),'conflicts':sorted(set(conflicts)),'missing':sorted(set(missing)),
        'warnings':sorted(set(warnings)),'evidence':evidence,'scope':'read-only certificate; preserves old accounting, grants no runtime permission'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--source-run',type=Path,required=True)
    a=p.parse_args();print(json.dumps(check(json.loads(a.spec.read_text()),a.source_run),indent=2))

if __name__=='__main__':main()
