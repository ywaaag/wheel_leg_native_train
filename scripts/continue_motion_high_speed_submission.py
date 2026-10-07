"""Deprecated entry; print migration information only, never wait or submit."""


def main():
    import sys
    print('DEPRECATED: use python -m native_stand.command_v6.supervisor; no external-PID continuation is supported.',file=sys.stderr)
    # Old external-PID continuation is unsafe after PID reuse. The public
    # supervisor owns source/smoke/formal children and defaults to plan-only.
    return 2


if __name__=='__main__':
    raise SystemExit(main())
