"""One authoritative validator for the supported bounded response profiles."""
def require_supported_scope(scope,origin,*,allow_auxiliary=False):
    if not isinstance(scope,dict):raise ValueError('Invalid assessment scope.')
    if scope.get('purpose') and (not allow_auxiliary or scope['purpose'] not in ('link-discovery','health-monitoring')):
        raise ValueError('Separate assessment authorization is required.')
    multi=scope.get('type') in ('explicit-path-response','api-response-configuration')
    if multi:
        from .multipath import validate_paths
        validate_paths(scope.get('paths'))
    if scope.get('origin')!=origin or (not multi and scope.get('paths')!=['/']):
        raise ValueError('Exact authorized origin and root path required.')
    if scope.get('method','GET')!='GET' or scope.get('type') not in ('root-response-configuration','explicit-path-response','api-response-configuration'):
        raise ValueError('Unsupported assessment method or profile.')
    if type(scope.get('request_limit')) is not int or scope['request_limit']!=(len(scope['paths']) if multi else 1):
        raise ValueError('Request budget must match the explicitly authorized path count.')
    # Only ephemeral, separately authorized passive discovery may shorten its
    # transport timeout to fit the remaining crawl budget. Ordinary assessment
    # profiles still require the original fixed five-second timeout.
    timeout = scope.get('timeout_seconds')
    discovery = allow_auxiliary and scope.get('purpose') == 'link-discovery'
    if discovery:
        import math
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise ValueError('Invalid discovery timeout.')
    elif type(timeout) is not int or timeout != 5:
        raise ValueError('Unsupported assessment timeout.')
