"""Task-specific pure request schemas; no simulator or evidence IO."""
import math
import re


COMMON = {'checkpoint', 'sha256', 'target', 'seconds', 'seed', 'role', 'diagnostic_profile','required_diagnostic_fields','evaluation_group','on_group_failure'}


def _common(request, allowed, default_seconds,task='recovery'):
    if not isinstance(request,dict):
        raise ValueError('evaluation request must be an object')
    unknown = set(request) - allowed
    if unknown:
        raise ValueError('unknown or foreign evaluation request fields: '+str(sorted(unknown)))
    if 'evaluation_group' in request and (not isinstance(request['evaluation_group'],str) or not request['evaluation_group']):raise ValueError('group name required')
    if request.get('on_group_failure','continue') not in ('continue','stop'):raise ValueError('unknown group continuation policy')
    for required in ('checkpoint', 'sha256', 'target'):
        if required not in request:
            raise ValueError('missing evaluation request field: '+required)
    if not isinstance(request['checkpoint'],str) or not request['checkpoint']:
        raise ValueError('request checkpoint must be a nonempty path string')
    if not isinstance(request['sha256'],str) or not re.fullmatch('[0-9a-f]{64}', request['sha256']):
        raise ValueError('request SHA256 must be lowercase 64-hex')
    target = request['target']
    if not isinstance(target, (list, tuple)) or len(target)!=2 or any(
            isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in target):
        raise ValueError('invalid evaluation target')
    seconds = request.get('seconds', default_seconds)
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=100:
        raise ValueError('invalid evaluation duration')
    seed = request.get('seed',104)
    if isinstance(seed,bool) or not isinstance(seed,int) or seed<0:
        raise ValueError('invalid evaluation seed')
    from .diagnostic_profiles import resolve as diagnostic_profile
    diagnostic_profile(request.get('diagnostic_profile'),required=request.get('required_diagnostic_fields',[]),task=task)
    return {**request,'seconds':float(seconds),'seed':seed}


def motion_request(request):
    result=_common(request, COMMON | {'evaluation_mode'}, 30.,task='motion')
    if result.get('evaluation_mode','full') not in ('full','light'):
        raise ValueError('unknown Motion evaluation_mode')
    return result


def recovery_request(request, *, rising=False, required_seconds=None):
    seconds=required_seconds if required_seconds is not None else (23. if rising else 10.)
    result = _common(request, COMMON | {'family'}, seconds)
    if result['target'] != [0,0] or result['seconds'] != seconds:
        raise ValueError('Recovery batch requires zero target and task-specific10s/23s duration')
    if not isinstance(result.get('family'),str) or not result['family']:
        raise ValueError('Recovery batch requires family')
    return result
