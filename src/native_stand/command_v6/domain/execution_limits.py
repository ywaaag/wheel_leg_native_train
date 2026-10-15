"""One pure update/sample/wall contract, independent of task and reward version."""
import math
from dataclasses import dataclass
from .execution_plan import samples_per_update


def wall_seconds(value, *, name='wall_s', nullable=True):
    if value is None and nullable:return None
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
        raise ValueError(name+' must be positive finite seconds or explicit null')
    return float(value)


@dataclass(frozen=True)
class ExecutionLimits:
    phase: str
    updates: int
    samples: int
    wall_s: float | None

    @classmethod
    def resolve(cls,spec,phase):
        budget=spec['budget']
        if phase not in ('source_eval','smoke','formal','evaluate','play'):raise ValueError('unknown execution phase')
        updates=budget.get(phase+'_updates',0) if phase in ('smoke','formal') else 0
        if type(updates) is not int or updates<0:raise ValueError('updates must be a nonnegative integer')
        key='evaluation_wall_s' if phase in ('evaluate','play') else phase+'_wall_s'
        if key not in budget:raise ValueError('explicit '+key+' required')
        seconds=wall_seconds(budget[key],name=key,nullable=phase in ('smoke','formal'))
        if seconds is None and updates==0:raise ValueError('null wall requires a positive update ceiling')
        return cls(phase,updates,updates*samples_per_update(spec) if updates else 0,seconds)

    def deadline(self,started):return float('inf') if self.wall_s is None else started+self.wall_s

    def monitor_bound(self,override=None):
        if override is None:return self.wall_s
        override=wall_seconds(override,nullable=False)
        if self.wall_s is not None and override>self.wall_s:raise ValueError('wall override cannot enlarge declaration')
        return override


def validate_budget(spec):
    """Inclusive ceilings only; never allocate or reset a ledger."""
    b=spec['budget'];counts=[]
    for phase in ('smoke','formal'):
        n=b.get(phase+'_updates',0)
        if type(n) is not int or n<0:raise ValueError('invalid '+phase+' update ceiling')
        counts.append(n)
        if n:ExecutionLimits.resolve(spec,phase)
    scope='all_online'
    if sum(counts) and 'sample_limit' in b:
        unit=samples_per_update(spec);limit=b['sample_limit']
        if type(limit) is not int or limit<=0 or (limit<sum(counts)*unit and limit!=counts[1]*unit):raise ValueError('update/sample ceilings differ')
        if limit==counts[1]*unit and counts[0]:scope='historical_formal_only; authorization still requires inclusive total'
        elif limit>sum(counts)*unit:scope='declared upper ceiling; updates stop first'
    if 'chain_wall_s' in b:wall_seconds(b['chain_wall_s'],name='chain_wall_s')
    return {'updates':sum(counts),'samples':sum(counts)*samples_per_update(spec) if sum(counts) else 0,
            'chain_wall_s':b.get('chain_wall_s'),'declared_sample_limit_scope':scope,'null_wall_semantics':'no wall ceiling; updates/samples still bounded'}
