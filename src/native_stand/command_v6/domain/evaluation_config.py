"""Separate scoring declarations from schedule/storage metadata, no runtime or IO."""
from .evidence import PROTOCOL_FIELDS

SCHEDULE_FIELDS=frozenset(('checkpoint_every_updates','full_every_updates','light_every_updates',
    'unlock_full_updates','full_at_final','zero_every_updates','final_evaluation_seeds',
    'durability_only_for_selected','run_final_durability'))
STORAGE_FIELDS=frozenset(('full_trace_updates','diagnostic_profile','required_diagnostic_fields'))


def split(config):
    if not isinstance(config,dict):raise ValueError('evaluation configuration must be an object')
    unknown=set(config)-PROTOCOL_FIELDS-SCHEDULE_FIELDS-STORAGE_FIELDS
    if unknown:raise ValueError('unknown evaluation configuration fields: '+','.join(sorted(unknown)))
    return {'scoring':{k:v for k,v in config.items() if k not in SCHEDULE_FIELDS|STORAGE_FIELDS},
            'schedule':{k:v for k,v in config.items() if k in SCHEDULE_FIELDS},
            'storage':{k:v for k,v in config.items() if k in STORAGE_FIELDS}}


def scoring(config):
    return split(config)['scoring']


def identities(config):
    """Versioned comparison identity; retain archived protocol SHA separately."""
    import hashlib,json
    ignored={'actual_duration_seconds','observed_duration_per_env_s','effective_protocol_sha256',
        'scoring_protocol_sha256','diagnostics','motion_commands','full_trace_updates',
        'diagnostic_profile','required_diagnostic_fields'}|SCHEDULE_FIELDS
    collection={'light_seconds','light_window_s','durability_seconds','durability_steady_window_s'}
    # Collection fields do not change a realized per-command scoring window.
    scoring={k:v for k,v in config.items() if k not in ignored|collection}
    schedule={k:v for k,v in config.items() if k in SCHEDULE_FIELDS or k=='motion_commands' or k in collection}
    storage={k:v for k,v in config.items() if k in STORAGE_FIELDS or k=='diagnostics'}
    def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return {'version':'evaluation_components_v1','scoring':scoring,'schedule':schedule,'storage':storage,
        'scoring_sha256':digest(scoring),'schedule_sha256':digest(schedule),'storage_sha256':digest(storage),
        'original_effective_protocol_sha256':config.get('effective_protocol_sha256'),
        'original_scoring_protocol_sha256':config.get('scoring_protocol_sha256')}
