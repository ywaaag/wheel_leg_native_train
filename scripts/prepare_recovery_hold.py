"""Prepare the separately authorized R0 holding experiment; no simulator import."""
import argparse
import hashlib
import json
from pathlib import Path

from native_stand.command_v6.config import validate
from native_stand.command_v6.domain.execution_plan import samples_for_updates


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(parent, output, *, session, authorize=False):
    parent, output = Path(parent).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    spec = json.loads(parent.read_text())
    for path, digest in [('source_checkpoint','source_sha256'), ('asset_path','asset_sha256'),
                         ('asset_module_path','asset_module_sha256'), ('colleague_config_path','colleague_config_sha256')]:
        if sha(spec[path]) != spec[digest]:
            raise ValueError(path+' identity changed')
    spec.update(experiment=output.name, recipe_parent_spec_sha256=sha(parent),
                restore_source_rng=False, restore_recovery_curriculum=False)
    spec['reward']['success_once'] = 0.
    spec['curriculum']['episode_length_s'] = 10.
    recovery = spec['recovery']
    recovery['active_family'] = 'R0'
    recovery['curriculum']['max_enabled_stage'] = 0
    recovery['standing_task']['training_episode'] = {
        'mode':'fixed_horizon','seconds':10.,'success_ends_episode':False,'timeout_bootstrap':True}
    recovery['standing_task']['source_baseline_run'] = None
    recovery['standing_task']['retention'].update(gradient_diagnostics=False,
                                                 save_gradient_updates=[1,8,25,50,100])
    recovery['scope'] = 'R0 only, continuous10s training; no R1/R2/R3 promotion.'
    recovery['autonomous_stability_note'] = 'Training completes10s before window certification; no success reset or bonus.'
    spec['evaluation'].update(checkpoint_every_updates=25, light_every_updates=0,
                              full_every_updates=100, unlock_full_updates=[25,50,100],
                              run_final_durability=False)
    spec['budget'].update(source_eval_updates=0, source_eval_wall_s=300,
                          smoke_updates=10, smoke_wall_s=450, formal_updates=100,
                          formal_wall_s=2400, durability_wall_s=0,
                          chain_wall_s=3300, sample_limit=samples_for_updates(spec,110))
    scope = ('2026-10-07 current user approved execution of R0 holding plan: source10s/PPO0, '
             'bounded10-update smoke covering normal10s timeout, formal<=100updates, '
             'full evaluations25/50/100; same physics, no success bonus/reset, no R1 or automatic continuation.')
    spec['authorization'] = {'hapi_session':session,'user_scope':scope if authorize else 'Preparation only, runtime pending'}
    recovery['authorization_note'] = spec['authorization']['user_scope']
    spec['phase_initialization'] = 'Strict source50 actor/critic/Adam; LR3e-5; fresh R0 resets/curriculum; no critic warmup.'
    spec['experiment_variable'] = 'Combined fixed10s training horizon and zero success event reward; all continuous weights, PPO and physics retained.'
    spec['diagnostics'].update(enabled=True, record_updates=[1,8,25,50,100],
        record_reward_components=True, record_ppo_summary=True, record_retention_summary=True)
    spec['artifacts']['run_name'] = output.name
    errors = validate(spec)
    if errors:
        raise ValueError(errors)
    library = Path(recovery['pose_library'])
    if sha(library) != recovery['pose_library_sha256']:
        raise ValueError('Pose library identity changed')
    # The exact pose data are copied unchanged into the new experiment.
    recovery['pose_library'] = str(output/'poses.json')
    book = {'authorization':'AUTHORIZED' if authorize else 'UNAUTHORIZED',
        'authorization_evidence':spec['authorization']['user_scope'], 'experiment':output.name,
        'limits':{'source_eval':1,'evaluate':0,'smoke':10,'formal':100},
        'used':{'source_eval':0,'evaluate':0,'smoke':0,'formal':0},'attempts':{},
        'source_eval_wall_used_s':0.,'sample_limit':samples_for_updates(spec,110)}
    output.mkdir(parents=True)
    for name, value in [('spec.json',spec),('budget.json',book)]:
        with (output/name).open('x') as stream:
            json.dump(value,stream,indent=2); stream.write('\n')
    with (output/'poses.json').open('xb') as stream:
        stream.write(library.read_bytes())
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    from native_stand.command_v6.tools.entrypoints import add_historical_option,require_historical_option
    add_historical_option(parser)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--hapi-session',required=True)
    parser.add_argument('--authorize',action='store_true')
    args = parser.parse_args()
    require_historical_option(parser,args)
    spec = prepare(args.parent,args.output_dir,session=args.hapi_session,authorize=args.authorize)
    print(json.dumps({'spec':str(args.output_dir/'spec.json'),'authorization':bool(args.authorize),
                      'simulation':0,'ppo':0,'sample_limit':spec['budget']['sample_limit']}))


if __name__ == '__main__':
    main()
