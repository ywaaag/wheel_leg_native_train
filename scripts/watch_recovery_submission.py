"""RETIRED: use the existing supervisor/monitor owner, never an extra watcher."""
def finish(*args,**kwargs):
    raise RuntimeError('RETIRED_ENTRY: watcher cannot write reports or send notifications; use public completion tools')

def main():
    from native_stand.command_v6.tools.entrypoints import historical_cli_guard
    historical_cli_guard('scripts/watch_recovery_submission.py')

if __name__=='__main__':main()
