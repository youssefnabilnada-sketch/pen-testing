"""Exact Origin allowlist for a protected Vercel preview during authorized acceptance.

The preview origin is opt-in; production's canonical WEB_ORIGIN remains unchanged.
No wildcards, subdomain suffix matching for requests, or CORS relaxation.
"""
import os
import re
from urllib.parse import urlsplit


def valid_preview_origin(value: str) -> bool:
    if not value or value.strip() != value or any(c.isspace() for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname is not None
            and re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+vercel\.app", parsed.hostname) is not None
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and not parsed.path
            and not parsed.query
            and not parsed.fragment
            and value == parsed.geturl()
        )
    except ValueError:
        return False


def allowed_request_origins() -> set[str]:
    allowed = {os.getenv("WEB_ORIGIN", "http://localhost:3000")}
    if os.getenv("AEGIS_PREVIEW_AUTH_ENABLED") == "true":
        preview = os.getenv("WEB_PREVIEW_ORIGIN", "")
        if valid_preview_origin(preview):
            allowed.add(preview)
    return allowed
