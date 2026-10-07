"""Versioned completed-episode evidence; legacy aliases are checked, never guessed."""
import math


def normalize(value):
    if not isinstance(value,dict):raise ValueError('EpisodeSummary must be an object')
    version=value.get('schema_version',0)
    if type(version) is not int or version not in (0,1):raise ValueError('unknown EpisodeSummary version')
    names=('completed','completed_episodes')
    counts=[value[n] for n in names if n in value]
    if not counts or any(type(n) is not int or n<0 for n in counts):
        raise ValueError('EpisodeSummary completed count missing or invalid')
    if len(set(counts))!=1:raise ValueError('EpisodeSummary completed aliases conflict')
    result={**value,'schema_version':1,'completed':counts[0],'completed_episodes':counts[0]}
    for key in ('mean_duration_s','max_duration_s'):
        number=value.get(key)
        if number is not None and (isinstance(number,bool) or not isinstance(number,(int,float)) or
                                  not math.isfinite(number) or number<0):
            raise ValueError('EpisodeSummary duration invalid: '+key)
    if counts[0]>0 and value.get('max_duration_s') is None:
        raise ValueError('EpisodeSummary completed episodes need duration evidence')
    return result


def build(completed, mean_duration_s, max_duration_s, **fields):
    return normalize({'schema_version':1,'completed':completed,
                      'mean_duration_s':mean_duration_s,'max_duration_s':max_duration_s,**fields})
