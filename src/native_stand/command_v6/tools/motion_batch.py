"""Motion batch request adapter; shared runtime stays in evaluate_checkpoint."""
from ..domain.evaluation_requests import motion_request


def validate_request(spec, request):
    if spec.get('task') == 'recovery':
        raise ValueError('motion_batch cannot consume a Recovery spec')
    return motion_request(request)
