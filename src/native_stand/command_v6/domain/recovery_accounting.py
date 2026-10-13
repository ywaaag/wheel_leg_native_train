"""One cumulative budget calculation for engineering recovery and runtime checks."""
import math


def calculate(original_book,chain_terminal,supplement_book,*,formal_limit):
    if any(a.get('status')=='RUNNING' for b in (original_book,supplement_book) for a in b.get('attempts',{}).values()):
        raise ValueError('Recovery accounting has unsettled attempts')
    historical=original_book.get('historical_chain_wall_s',0.)
    chain=chain_terminal.get('chain_wall_s')
    if chain is None:raise ValueError('Complete chain wall including cleanup missing')
    supplement=sum(a.get('wall_s') for a in supplement_book.get('attempts',{}).values())
    ceiling=original_book.get('original_cumulative_wall_limit_s')
    if ceiling is None:raise ValueError('Original cumulative wall ceiling missing')
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (historical,chain,supplement,ceiling)):
        raise ValueError('Invalid cumulative wall accounting')
    for phase in ('smoke','formal'):
        actual=sum(a.get('updates',0) for a in original_book.get('attempts',{}).values() if a.get('phase')==phase)
        if original_book.get('used',{}).get(phase,0)!=actual:
            raise ValueError('Original settled updates differ from exact ledger attempts')
    old_used=sum(original_book.get('used',{}).get(k,0) for k in ('smoke','formal'))+original_book.get('historical_actual_online_updates',0)
    smoke_used=original_book.get('used',{}).get('smoke',0)
    formal_used=original_book.get('used',{}).get('formal',0)
    if any(type(v) is not int or v<0 for v in (old_used,smoke_used,formal_used,formal_limit)):
        raise ValueError('Invalid cumulative PPO usage')
    if any(a.get('updates',0)!=0 for a in supplement_book.get('attempts',{}).values()):raise ValueError('Supplement must be PPO0')
    inclusive=original_book.get('total_online_PPO_limit',sum(original_book['limits'].get(k,0) for k in ('smoke','formal')))
    remaining=min(original_book['limits']['formal']-formal_used,inclusive-old_used)
    if not 0<formal_limit<=remaining:raise ValueError('Formal budget exceeds remaining original allowance')
    consumed=historical+chain+supplement
    if consumed>=ceiling:raise ValueError('Original cumulative wall exhausted')
    return {'version':1,'original_wall_limit_s':ceiling,'historical_chain_wall_s':historical,
        'failed_retry_chain_wall_s':chain,'supplement_settled_wall_s':supplement,
        'consumed_wall_s':consumed,'remaining_wall_s':ceiling-consumed,
        'original_online_limit':inclusive,'consumed_online_updates':old_used,
        'consumed_smoke_updates':smoke_used,'consumed_formal_updates':formal_used,
        'new_smoke_updates':0,'new_formal_limit':formal_limit,'remaining_online_updates':inclusive-old_used,
        'scope':'historical chains + failed chain overhead/cleanup + settled PPO0; no transferred balance or fake attempts'}


def validate_remaining(spec,book,accounting):
    expected=accounting['new_formal_limit']
    if (spec['budget'].get('smoke_updates')!=0 or book['limits'].get('smoke')!=0 or
            book['limits'].get('source_eval')!=0 or spec['budget'].get('formal_updates')!=expected or book['limits'].get('formal')!=expected):
        raise ValueError('Recovery must preserve zero new smoke/source and exact formal cap')
    wall=spec['budget'].get('formal_wall_s')
    if type(wall) not in (int,float) or not 0<wall<=accounting['remaining_wall_s']:raise ValueError('Recovery formal wall exceeds cumulative remainder')
    if book.get('historical_usage')!=accounting:raise ValueError('Recovery historical usage binding differs')
    if book.get('used',{}).get('smoke',0)!=0 or book.get('used',{}).get('source_eval',0)!=0:
        raise ValueError('New recovery ledger cannot contain replacement smoke/source usage')
    attempts=book.get('attempts',{})
    if len(attempts)>1 or any(a.get('phase')!='formal' for a in attempts.values()):
        raise ValueError('Recovery ledger allows exactly one formal reservation')
    used=book.get('used',{}).get('formal',0)
    if used!=sum(a.get('updates',0) for a in attempts.values()):
        raise ValueError('Actual recovery updates differ from exact attempts')
    if used>expected or accounting['consumed_online_updates']+used>accounting['original_online_limit']:
        raise ValueError('Recovery cumulative PPO budget exceeded')
