"""Single lifecycle state machine for detached experiment chains."""
from enum import Enum
from pathlib import Path
import time

from ..completion import read, write


class RunState(str, Enum):
    PLANNED = "PLANNED"
    SUBMITTED = "SUBMITTED"
    SOURCE_EVAL = "SOURCE_EVAL"
    SMOKE = "SMOKE"
    FORMAL = "FORMAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED_BOUNDED = "STOPPED_BOUNDED"


_NEXT = {
    RunState.PLANNED: {RunState.SUBMITTED, RunState.FAILED},
    RunState.SUBMITTED: {RunState.SOURCE_EVAL, RunState.FAILED},
    RunState.SOURCE_EVAL: {RunState.SMOKE, RunState.FAILED},
    RunState.SMOKE: {RunState.FORMAL, RunState.FAILED},
    RunState.FORMAL: {RunState.COMPLETED, RunState.FAILED},
    RunState.COMPLETED: set(), RunState.FAILED: set(),
}
for _state in (RunState.SUBMITTED, RunState.SOURCE_EVAL, RunState.SMOKE, RunState.FORMAL):
    _NEXT[_state].add(RunState.STOPPED_BOUNDED)
_NEXT[RunState.STOPPED_BOUNDED] = set()


def transition(previous, current):
    previous, current = RunState(previous), RunState(current)
    if current != previous and current not in _NEXT[previous]:
        raise ValueError(f"invalid RunState transition {previous.value}->{current.value}")
    return current.value


def record(chain, current, *, previous=None, phase=None, **evidence):
    """Write the canonical state and compatibility projections together."""
    chain = Path(chain)
    current = RunState(current)
    existing = read(chain / "run_state.json", {}) or {}
    old = previous or existing.get("state", RunState.PLANNED.value)
    transition(old, current)
    event = {"state": current.value, "previous_state": old, "phase": phase,
             "time_unix_s": time.time(), **evidence}
    write(chain / "run_state.json", event)
    # These files remain for old readers, but are projections of the same event.
    write(chain / "chain_progress.json", {**event, "status": current.value,
                                           "stage": phase or current.value.lower()})
    if current in (RunState.COMPLETED, RunState.FAILED, RunState.STOPPED_BOUNDED):
        write(chain / "supervisor_terminal.json", event)
    return event


def state_from_stage(stage):
    return {"submission": RunState.SUBMITTED.value, "source_eval": RunState.SOURCE_EVAL.value,
            "smoke": RunState.SMOKE.value, "formal": RunState.FORMAL.value,
            "finished": RunState.COMPLETED.value}.get(stage, RunState.SUBMITTED.value)


def write_handshake(chain, evidence):
    """A receipt observes state; it cannot advance or rewind the worker lifecycle."""
    event = read(Path(chain)/'run_state.json', {}) or {}
    state=event.get('state', RunState.SUBMITTED.value)
    result = {**evidence, 'state':state, 'status':state,
              'legacy_handshake_status':evidence.get('status'), 'run_state':state,
              'state_event_time_unix_s': event.get('time_unix_s')}
    write(Path(chain)/'startup_handshake.json', result)
    return result
