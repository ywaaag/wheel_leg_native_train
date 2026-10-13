"""Task-aware network boundary shared by train, evaluate, preview and CPU audits."""
def model(obs,*,actor,spec):
    if spec.get('interface_version') in ('multiskill_student_v1','multiskill_mcu_v2'):
        from native_stand.students.model import Student
        return Student(actor,version=spec["interface_version"])
    if spec.get('interface_version') not in (None,'legacy150D'):
        raise ValueError('Unknown interface version')
    from ..domain.action_distribution import validate
    validate(spec)
    if spec.get('task')=='recovery':
        from native_stand.recovery.learning import model as constructor
    else:
        from ..learning import model as constructor
    return constructor(obs,actor=actor,spec=spec)
