"""Task-specific pure request schemas; no simulator or evidence IO."""
import math
import re


COMMON = {'checkpoint', 'sha256', 'target', 'seconds', 'seed', 'role'}


def _common(request, allowed, default_seconds):
    if not isinstance(request,dict):
        raise ValueError('evaluation request must be an object')
    unknown = set(request) - allowed
    if unknown:
        raise ValueError('unknown or foreign evaluation request fields: '+str(sorted(unknown)))
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
    return {**request,'seconds':float(seconds),'seed':seed}


def motion_request(request):
    return _common(request, COMMON, 30.)


def recovery_request(request):
    result = _common(request, COMMON | {'family'}, 10.)
    if result['target'] != [0,0] or result['seconds'] != 10.:
        raise ValueError('Recovery batch requires zero target,10s')
    if not isinstance(result.get('family'),str) or not result['family']:
        raise ValueError('Recovery batch requires family')
    return result
