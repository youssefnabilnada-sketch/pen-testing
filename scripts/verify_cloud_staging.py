"""Read-only HTTPS smoke verification of an explicitly configured AEGIS staging deployment.

No website assessments, DNS changes, customer logins or writes are performed.
Passing these probes does NOT certify the full application for public launch.
"""
import os
import sys
from urllib.parse import urlsplit

import httpx


class StagingSmokeError(ValueError):
    pass


def staging_origin(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise StagingSmokeError('Explicit HTTPS staging origin is required.')
    try:
        parts = urlsplit(raw)
        host = parts.hostname
        # Require a public host and TLS to prevent accidental local or plain-HTTP probes.
        if (parts.scheme != 'https' or not host or not '.' in host
            or host.lower() in {'localhost', '127.0.0.1'}
            or parts.username is not None or parts.password is not None
            or parts.path not in ('', '/') or parts.query or parts.fragment):
            raise StagingSmokeError('Staging endpoint must be a public HTTPS origin without credentials or paths.')
        # urlsplit accepts a malformed port until accessed.
        port = parts.port
        if port not in (None, 443):
            raise StagingSmokeError('Staging must use the standard HTTPS port.')
    except ValueError as exc:
        raise StagingSmokeError('Invalid staging HTTPS origin.') from exc
    return f'https://{host.lower()}'


def verify_staging(web_origin: str, api_origin: str, *, transport=None) -> list[str]:
    web = staging_origin(web_origin)
    api = staging_origin(api_origin)
    if web == api:
        raise StagingSmokeError('Web and API must be configured as distinct staging origins.')
    with httpx.Client(timeout=httpx.Timeout(10, connect=4), follow_redirects=False,
                      trust_env=False, transport=transport) as client:
        checks = []
        try:
            home = client.get(web + '/')
            if home.status_code != 200:
                raise StagingSmokeError('Staging web homepage is not healthy.')
            if home.headers.get('x-content-type-options', '').lower() != 'nosniff':
                raise StagingSmokeError('Staging web security headers are missing.')
            checks.append('web homepage and basic security headers')

            health = client.get(api + '/health')
            if health.status_code != 200:
                raise StagingSmokeError('Staging API health endpoint is not healthy.')
            body = health.json()
            if (not isinstance(body, dict) or body.get('database') != 'reachable'
                or body.get('payments_enabled') is not False
                or body.get('billing_mode') != 'disabled'):
                raise StagingSmokeError('Staging health or payment-disable evidence is invalid.')
            checks.append('API database health and disabled payment mode')

            ready = client.get(api + '/ready')
            ready_body = ready.json()
            if (ready.status_code != 200 or not isinstance(ready_body, dict)
                or ready_body.get('ready') is not True):
                raise StagingSmokeError('Staging API dependencies are not ready.')
            checks.append('API dependency readiness')
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            if isinstance(exc, StagingSmokeError):
                raise
            raise StagingSmokeError('Staging health probe failed or returned invalid data.') from exc
    return checks


def main() -> int:
    try:
        checks = verify_staging(os.getenv('AEGIS_STAGING_WEB_URL', ''),
                                os.getenv('AEGIS_STAGING_API_URL', ''))
    except StagingSmokeError as exc:
        print('STAGING NOT VERIFIED: ' + str(exc), file=sys.stderr)
        return 1
    for label in checks:
        print('PASS: ' + label)
    print('Read-only staging smoke passed. Full authenticated journeys, workers,')
    print('email, backup/restore and security acceptance are NOT certified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
