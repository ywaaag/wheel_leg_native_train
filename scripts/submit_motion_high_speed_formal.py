"""Deprecated entry; print migration information only, never submit a task."""


def main():
    import sys
    print('DEPRECATED: use python -m native_stand.command_v6.supervisor; this entry no longer submits tasks.',file=sys.stderr)
    return 2


if __name__=='__main__':
    raise SystemExit(main())
