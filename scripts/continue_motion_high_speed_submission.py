"""Compatibility entry for the shared owned-child supervisor; no external PID wait."""


def main():
    import sys
    print('DEPRECATED: use python -m native_stand.command_v6.supervisor; no external-PID continuation is supported.',file=sys.stderr)
    # Old external-PID continuation is unsafe after PID reuse. The public
    # supervisor owns source/smoke/formal children and defaults to plan-only.
    from native_stand.command_v6.supervisor import main as supervise
    return supervise()


if __name__=='__main__':
    raise SystemExit(main())
