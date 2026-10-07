"""Recovery batch request adapter; shared runtime stays in evaluate_checkpoint."""
from ..domain.evaluation_requests import recovery_request


def validate_request(spec, request):
    if spec.get('task') != 'recovery':
        raise ValueError('recovery_batch requires a Recovery spec')
    return recovery_request(request)
