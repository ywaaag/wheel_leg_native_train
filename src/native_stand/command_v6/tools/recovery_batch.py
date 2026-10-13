"""Recovery batch request adapter; shared runtime stays in evaluate_checkpoint."""
from ..domain.evaluation_requests import recovery_request


def validate_request(spec, request):
    if spec.get('task') != 'recovery':
        raise ValueError('recovery_batch requires a Recovery spec')
    from native_stand.recovery.task_protocol import batch_seconds
    return recovery_request(request,required_seconds=batch_seconds(spec))
