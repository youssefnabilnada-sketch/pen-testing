"""Customer-safe assessment failure classifications.

Never expose raw exception details, network internals or traceback to customers.
Classify only well-known, deliberately raised errors. Unknown failures remain
generic and require an operator to inspect private logs.
"""
import socket
import ssl

from .safety import UnsafeTarget


def classify_assessment_failure(exc: Exception) -> tuple[str, str]:
    """Return (stable reason code, customer next step)."""
    reason = str(exc)

    if isinstance(exc, UnsafeTarget):
        if reason.startswith('Redirect not followed:'):
            return ('TARGET_REDIRECT', 'The website redirected outside the approved request. Confirm the website URL and ask its owner to authorize the final exact origin before a new assessment.')
        if reason in ('Hostname resolution failed.', 'No destination addresses.'):
            return ('TARGET_DNS', 'The approved website hostname could not be resolved. Confirm the domain is published and reachable before trying again.')
        if reason == 'Private, special-use or internal destinations are blocked.':
            return ('TARGET_SCOPE_BLOCKED', 'The resolved address is outside the supported public assessment scope. Internal or private destinations cannot be assessed.')
        if reason.startswith('Path not authorized.') or reason.startswith('Path is outside'):
            return ('PATH_NOT_AUTHORIZED', 'The requested website path is outside the approved assessment scope. Review the authorized paths.')
        return ('TARGET_VALIDATION', 'This website could not pass the safe target validation checks. Review the authorized website address and request scope.')

    if isinstance(exc, (TimeoutError, socket.timeout)):
        return ('TARGET_TIMEOUT', 'The website did not respond within the authorized request time limit. Check its availability before starting another assessment.')
    if isinstance(exc, ssl.SSLError):
        return ('TARGET_TLS', 'A secure TLS connection to the approved website could not be validated. Review its HTTPS certificate and configuration.')
    if isinstance(exc, socket.gaierror):
        return ('TARGET_DNS', 'The website hostname could not be resolved. Confirm the address is valid and published.')
    if isinstance(exc, (ConnectionError, OSError)):
        return ('TARGET_CONNECTION', 'The approved website could not be reached. Check public website availability before retrying.')

    if isinstance(exc, ValueError):
        if reason.startswith('Target cooldown active.'):
            return ('TARGET_COOLDOWN', 'A recent assessment already ran for this target. Try again after the safety cooldown.')
        if reason.startswith('Non-success response;'):
            return ('TARGET_HTTP_RESPONSE', 'The approved website path returned an unsuccessful HTTP response. Confirm that the public page is available without signing in.')
        if reason.startswith('Authorization expired') or reason.startswith('Outside the authorized assessment window'):
            return ('AUTHORIZATION_EXPIRED', 'The website verification or assessment authorization is no longer valid. Verify ownership and approve a new assessment scope if needed.')
        if reason.startswith('Scope changed') or reason.startswith('Exact authorized') or reason.startswith('Separate assessment authorization') or reason.startswith('Request budget') or reason.startswith('Invalid assessment scope') or reason.startswith('Unsupported assessment') or reason.startswith('Unsupported assessment timeout') or reason.startswith('Invalid authorized daily window'):
            return ('AUTHORIZATION_SCOPE', 'The assessment permissions or scope are no longer valid. Review the approved target, paths, and assessment window before submitting again.')

    return ('ASSESSMENT_INTERNAL', 'An unexpected error interrupted the assessment. No security result was produced. Contact AEGIS Support with the assessment ID.')


def public_assessment_error(exc: Exception) -> str:
    code, next_step = classify_assessment_failure(exc)
    return f'Assessment did not complete [{code}]. {next_step} No clean result is implied.'
