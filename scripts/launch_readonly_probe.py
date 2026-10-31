#!/usr/bin/env python3
"""Non-invasive operator observation of public AEGIS gateway response codes.
No credentials, cookies, POST requests, response bodies or customer data.
Never describe this as a real customer sign-in or end-to-end acceptance.
"""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request

ORIGIN = "https://aegis-pentest-eg.vercel.app"
PATHS = ("/console", "/api/health", "/api/auth/me", "/api/auth/firebase/config")
TIMEOUT_SECONDS = 8


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def main() -> int:
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )
    results = {}
    for path in PATHS:
        request = urllib.request.Request(
            ORIGIN + path, method="GET", headers={
                "Accept": "application/json, text/html;q=0.5",
                "User-Agent": "AEGIS-Launch-Readonly-Probe/1.0",
            }
        )
        try:
            with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                results[path] = {"http_status": response.status}
        except urllib.error.HTTPError as exc:
            results[path] = {"http_status": exc.code}
            exc.close()
        except (OSError, urllib.error.URLError) as exc:
            results[path] = {"network_error_type": type(exc).__name__}
    print(json.dumps({"public_origin": ORIGIN, "observations": results}, indent=2))
    print("Observation only: does NOT validate credentials, cookies, Oracle, Firebase, Brevo or customer access.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
