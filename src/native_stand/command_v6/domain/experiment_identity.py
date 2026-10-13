"""Behavior, budget, collection and full requested declaration are distinct identities."""
import copy
from .evaluation_config import split


def sections(spec):
    behavior={k:copy.deepcopy(spec[k]) for k in ('task','initialization','source_checkpoint','source_sha256',
        'source_input_dim','source_update','source_spec_sha256','source_asset_sha256',
        'asset_path','asset_sha256','asset_module_path','asset_module_sha256','colleague_config_path','colleague_config_sha256',
        'observation','history','action','control','ground','termination','reward','ppo','objective','curriculum',
        'recovery','cohort_width_ab','straight_high_speed_course','motion_posture') if k in spec}
    if 'motion_posture' in behavior:behavior['motion_posture'].pop('chain_wall_s',None)
    if spec.get('evaluation'):
        parts=split(spec['evaluation']);behavior['evaluation_scoring']=parts['scoring']
    else:parts={'schedule':{},'storage':{}}
    return {'behavior':behavior,'budget':copy.deepcopy(spec.get('budget',{})),
        'storage':{'evaluation':parts['storage'],'diagnostics':copy.deepcopy(spec.get('diagnostics')),
                   'selected_diagnostics':copy.deepcopy(spec.get('selected_diagnostics')),'input_capture':copy.deepcopy(spec.get('input_capture'))},
        'evaluation_schedule':parts['schedule'],'requested':copy.deepcopy(spec)}
