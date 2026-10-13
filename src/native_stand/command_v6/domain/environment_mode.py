"""Explicit task execution intent; no simulator state or filesystem access."""
MODES=('training','evaluation','preview')

def resolve(mode,*,envs):
    if mode not in MODES:raise ValueError('Unknown environment mode: '+str(mode))
    if type(envs) is not int or envs<1:raise ValueError('Positive environment count required')
    if mode=='preview' and envs!=1:raise ValueError('Preview requires exactly one environment')
    return {'mode':mode,'envs':envs,'curriculum_training':mode=='training',
            'split':'train' if mode=='training' else 'holdout',
            'capture_terminal':mode!='training',
            'scope':'execution intent, not a change to the frozen task recipe'}
