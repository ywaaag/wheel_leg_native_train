"""Best-effort ordered cleanup; preserve the primary failure and report all others."""
import sys
import traceback

def run(steps,*,primary_error=None,on_errors=None):
    errors=[]
    for name,operation in steps:
        try:operation()
        except BaseException as error:
            errors.append({'step':name,'exception':repr(error),'traceback':traceback.format_exc()})
            if primary_error is not None:primary_error.add_note(name+' cleanup also failed: '+repr(error))
            print(errors[-1]['traceback'],file=sys.stderr,flush=True)
    if on_errors is not None:on_errors(errors)
    if errors and primary_error is None:raise RuntimeError('Runtime cleanup failed: '+str(errors))
    return errors
