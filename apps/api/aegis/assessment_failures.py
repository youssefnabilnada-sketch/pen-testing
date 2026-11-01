"""Safe and actionable assessment-failure reasons.

Never expose raw exceptions, response bodies, target DNS answers, credentials, or
internal stack traces to customers. Failed jobs never imply a clean assessment.
"""
import socket
import ssl
from .safety import UnsafeTarget

NO_RESULT = ' No security assessment result was produced.'

class NonSuccessResponse(ValueError):
    """Approved target returned a non-2xx status (not a scan finding)."""
    def __init__(self, status: int):
        self.status = int(status)
        super().__init__('Target returned non-success HTTP response.')

def assessment_failure(exc: Exception) -> tuple[str, str]:
    """Return (stable diagnostic code, customer-safe explanation)."""
    if isinstance(exc, NonSuccessResponse):
        status = exc.status
        if status in (401, 403):
            return 'site_access_restricted', (
                f'The website returned HTTP {status} (access restricted). '
                'Confirm the approved URL is accessible to the scanner without authentication; '
                'do not disable security protections to run a test.' + NO_RESULT
            )
        if status == 429:
            return 'site_rate_limited', (
                'The website returned HTTP 429 (too many requests). '
                'Review the website access policy and retry later within an approved scope.' + NO_RESULT
            )
        if 500 <= status <= 599:
            return 'site_server_error', (
                f'The website returned HTTP {status} (server error). '
                'Check the website service and retry after it is healthy.' + NO_RESULT
            )
        return 'site_non_success', (
            f'The website returned HTTP {status} instead of a successful response. '
            'Confirm the approved public page is accessible and try again.' + NO_RESULT
        )

    if isinstance(exc, UnsafeTarget):
        reason = str(exc)
        if reason.startswith('Redirect not followed:'):
            return 'site_redirect', (
                'The website redirected the assessment request. '
                'For safety, AEGIS does not automatically follow redirects. '
                'If your website uses a different canonical address, add and verify that address separately.' + NO_RESULT
            )
        if reason in ('Hostname resolution failed.', 'No destination addresses.'):
            return 'site_dns', (
                'The website hostname could not be resolved by the scanner. '
                'Check that its DNS record exists and is publicly resolvable.' + NO_RESULT
            )
        if reason == 'Private, special-use or internal destinations are blocked.':
            return 'unsafe_destination', (
                'The website resolved to an address that is outside the approved public assessment scope. '
                'Only public, explicitly authorized websites can be assessed.' + NO_RESULT
            )
        return 'unsafe_target', (
            'The assessment was stopped by a website or scope safety check. '
            'Review the exact website address, verification status and authorized paths.' + NO_RESULT
        )

    if isinstance(exc, (ssl.CertificateError, ssl.SSLError)):
        return 'site_tls', (
            'The scanner could not establish a validated HTTPS connection. '
            'Check the website TLS certificate and HTTPS configuration.' + NO_RESULT
        )

    if isinstance(exc, (socket.timeout, TimeoutError)):
        return 'site_timeout', (
            'The website did not respond within the authorized request time limit. '
            'Check availability and retry when the site is responsive.' + NO_RESULT
        )

    if isinstance(exc, OSError):
        return 'site_connection', (
            'The scanner could not complete a connection to the website. '
            'Check public connectivity and try again later.' + NO_RESULT
        )

    if isinstance(exc, ValueError):
        reason = str(exc)
        if reason.startswith('Target cooldown active.'):
            return 'target_cooldown', (
                'An assessment of this website was started too recently. '
                'Wait at least one minute before starting a new authorized assessment.' + NO_RESULT
            )
        if 'Authorization expired' in reason or 'Authorization expired during' in reason or 'Outside the authorized assessment window' in reason:
            return 'authorization_expired', (
                'The assessment authorization expired or fell outside its approved time window. '
                'Confirm ownership and approve a new assessment before retrying.' + NO_RESULT
            )
        if 'Scope changed' in reason or 'Invalid assessment scope' in reason or 'scope mismatched' in reason or 'Unsupported assessment' in reason or 'Request budget' in reason or 'Exact authorized origin' in reason:
            return 'scope_changed', (
                'The assessment scope changed or no longer matches the approved authorization. '
                'Review the website and start a newly authorized assessment.' + NO_RESULT
            )

    return 'internal_processing', (
        'The assessment could not finish because of a processing error. '
        'Contact AEGIS Support with the assessment reference shown in your workspace.' + NO_RESULT
    )
