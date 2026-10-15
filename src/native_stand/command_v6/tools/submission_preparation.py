"""Review-only package over existing publisher, shared-source CPU validator and supervisor."""
import json
from pathlib import Path
import shlex
import sys
from .experiment_preparation import checked_input,publish
from .execution_identity import identity


def package(spec_path,validation_dir,validation):
    spec_path=Path(spec_path).resolve();validation_dir=Path(validation_dir).resolve()
    if not validation.get('passed'):raise ValueError('Passed complete CPU validation required')
    spec=json.loads(spec_path.read_text());ledger=spec_path.with_name('budget.json');book=json.loads(ledger.read_text())
    if book.get('authorization')!='UNAUTHORIZED' or book.get('attempts') or any(book['used'].values()):
        raise ValueError('Submission package requires unused UNAUTHORIZED declaration')
    inputs=dict([checked_input(spec_path),checked_input(ledger)])
    device=spec['device']
    from ..domain.execution_limits import wall_seconds
    walls=[wall_seconds(spec['budget'].get('evaluation_wall_s' if p=='evaluate' else p+'_wall_s'),name=p+'_wall_s') for p in ('source_eval','smoke','formal','evaluate') if book['limits'].get(p,0)>0]
    phase_wall=None if None in walls else sum(walls)
    online=sum(book['limits'].get(p,0) for p in ('smoke','formal'))
    from ..domain.execution_plan import samples_for_updates
    samples=samples_for_updates(spec,online)
    template={'approval_id':'<explicit-user-approval-id>','user_scope':'<explicit-authorized-scope>',
        'session':'<current-owner-session>','physical_gpu':device['physical_index'],'gpu_uuid':device['uuid'],
        'max_online_updates':online,'max_phase_wall_s':phase_wall,
        'arms':[{'spec':str(spec_path),'spec_sha256':inputs[str(spec_path)],'budget_sha256':inputs[str(ledger)]}]}
    output=Path(__file__).resolve().parents[4]/'runs'/spec['experiment']
    command=[sys.executable,'-m','native_stand.command_v6.supervisor','--spec',str(spec_path),'--output-dir',str(output),
             '--physical-gpu',str(device['physical_index']),'--hapi-session','<current-owner-session>']
    readme={'version':'submission_preparation_v1','status':'PREPARED_UNAUTHORIZED','original_declaration':str(spec_path),
        'original_ledger':str(ledger),'CPU_validation':str(validation_dir/'validation_result.json'),
        'plan_only':'PYTHONPATH=src '+shlex.join(command),
        'submit_command_requires_new_authorization':'PYTHONPATH=src '+shlex.join(command+['--launch']),
        'resource_check':'same supervisor --check-submission after explicit authorization; no resource query performed',
        'budget':{'online_updates':online,'samples':samples,'wall_s':phase_wall},
        'not_authorized':True,'not_submitted':True,'copies_are_review_only':True}
    destination=validation_dir/'submission_preparation'
    from .source_identity import read_identity
    record=validation_dir/'identity.json'
    execution={'source_identity_reference':str(record),'sha256':checked_input(record)[1]}
    publish(destination,{'spec.json':spec,'budget.json':book,'identity.json':execution,
        'CPU_validation.json':{'passed':True,'tests':validation['tests'],'tests_result':validation.get('tests_result'),
             'schema':validation['schema'],'validation_source':str(validation_dir/'validation_result.json')},
        'zero_write_plan.json':{'command':validation['plan_only']['command'],'returncode':validation['plan_only']['returncode'],
             'plan':json.loads(validation['plan_only']['stdout']),'run_created':validation['plan_only']['run_created']},
        'authorization_template.json':template,'submission_commands.json':readme},inputs,completion_marker=True)
    return {'path':str(destination),'status':'PREPARED_UNAUTHORIZED','files_written':8,'submitted':False}
