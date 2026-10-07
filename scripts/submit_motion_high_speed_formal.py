"""Compatibility entry: explicit spec/output, shared supervisor, plan-only by default."""


def main():
    import sys
    print('DEPRECATED: use python -m native_stand.command_v6.supervisor; this wrapper has identical behavior.',file=sys.stderr)
    from native_stand.command_v6.supervisor import main as supervise
    return supervise()


if __name__=='__main__':
    raise SystemExit(main())
