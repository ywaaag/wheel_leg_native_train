"""Compatibility entry: explicit spec/output, shared supervisor, plan-only by default."""


def main():
    from native_stand.command_v6.supervisor import main as supervise
    return supervise()


if __name__=='__main__':
    raise SystemExit(main())
