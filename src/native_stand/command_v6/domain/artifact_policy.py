"""Pure artifact ceiling/log declaration validation, independent of reward recipe."""
from .checkpoint_policy import resolve as checkpoint_policy


def validate(spec):
    value=spec.get('artifacts',{})
    checkpoint_policy(spec)
    maximum=value.get('storage_max_bytes');reserve=value.get('terminal_reserve_bytes')
    if maximum is not None and (type(maximum) is not int or maximum<=0):raise ValueError('storage_max_bytes must be positive integer bytes')
    if reserve is not None and (type(reserve) is not int or reserve<=0):raise ValueError('terminal_reserve_bytes must be positive integer bytes')
    if maximum is not None and (reserve or 128*2**20)>=maximum:raise ValueError('terminal reserve must fit storage ceiling')
    log=value.get('runtime_log')
    if log is not None and (not isinstance(log,dict) or set(log)!={'max_bytes','backups'} or
            type(log['max_bytes']) is not int or log['max_bytes']<1 or type(log['backups']) is not int or log['backups']<1):
        raise ValueError('runtime_log requires positive max_bytes and backups')
    capture=value.get('optimizer_capture')
    if capture is not None:
        if (not isinstance(capture,dict) or set(capture)!={'version','updates','max_bytes'} or
                capture['version']!='optimizer_capture_v1' or not isinstance(capture['updates'],dict) or
                set(capture['updates'])-{'smoke','formal'} or type(capture['max_bytes']) is not int or capture['max_bytes']<1):
            raise ValueError('invalid bounded optimizer_capture declaration')
        for phase,updates in capture['updates'].items():
            ceiling=spec['budget'].get(phase+'_updates',0)
            if (not isinstance(updates,list) or updates!=sorted(set(updates)) or
                    any(type(u) is not int or not 1<=u<=ceiling for u in updates)):
                raise ValueError('optimizer_capture updates must be unique declared phase updates')
    return {'runtime_log':log,'storage_max_bytes':maximum,'terminal_reserve_bytes':reserve}
