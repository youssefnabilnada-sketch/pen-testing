"""Origin regression checks for isolated Vercel preview acceptance.

No live Firebase, external HTTP, SMTP, or customer accounts are involved.
"""
import pytest
from aegis.request_origins import allowed_request_origins, valid_preview_origin
from aegis.runtime import validate_runtime
from test_production_runtime import configure

PRODUCTION = "https://aegis-pentest-eg.vercel.app"
PREVIEW = "https://pen-testing-aspz5rfpn-youssefnabilnada-1001s-projects.vercel.app"


def test_preview_origin_is_rejected_by_default(client, monkeypatch):
    monkeypatch.setenv("WEB_ORIGIN", PRODUCTION)
    monkeypatch.setenv("WEB_PREVIEW_ORIGIN", PREVIEW)
    monkeypatch.delenv("AEGIS_PREVIEW_AUTH_ENABLED", raising=False)
    assert client.post("/auth/login", json={}, headers={"Origin": PREVIEW}).status_code == 403
    assert client.post("/auth/login", json={}, headers={"Origin": PRODUCTION}).status_code == 422
    assert client.post("/auth/login", json={}).status_code == 422


def test_only_exact_explicit_preview_origin_is_accepted(client, monkeypatch):
    monkeypatch.setenv("WEB_ORIGIN", PRODUCTION)
    monkeypatch.setenv("WEB_PREVIEW_ORIGIN", PREVIEW)
    monkeypatch.setenv("AEGIS_PREVIEW_AUTH_ENABLED", "true")
    assert client.post("/auth/login", json={}, headers={"Origin": PREVIEW}).status_code == 422
    assert client.post("/auth/login", json={}, headers={"Origin": PRODUCTION}).status_code == 422
    for malicious in (
        "https://pen-testing-aspz5rfpn-youssefnabilnada-1001s-projects.vercel.app.evil.test",
        "https://other-team.vercel.app",
        "http://pen-testing-aspz5rfpn-youssefnabilnada-1001s-projects.vercel.app",
        "null",
    ):
        assert client.post("/auth/login", json={}, headers={"Origin": malicious}).status_code == 403


@pytest.mark.parametrize("value", [
    "", "https://vercel.app", "http://example.vercel.app",
    "https://example.vercel.app.evil.test",
    "https://user:pass@example.vercel.app",
    "https://example.vercel.app/path",
    "https://example.vercel.app/?cookie=abc",
    "https://example.vercel.app#fragment",
    "https://example.vercel.app:9999",
    "https://*.vercel.app",
    "https://example.vercel.app ",
])
def test_invalid_preview_origin_is_never_permitted(value, monkeypatch):
    monkeypatch.setenv("WEB_ORIGIN", PRODUCTION)
    monkeypatch.setenv("WEB_PREVIEW_ORIGIN", value)
    monkeypatch.setenv("AEGIS_PREVIEW_AUTH_ENABLED", "true")
    assert not valid_preview_origin(value)
    assert allowed_request_origins() == {PRODUCTION}


def test_production_runtime_rejects_unconfigured_preview(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv("AEGIS_PREVIEW_AUTH_ENABLED", "true")
    for value in ("", "https://*.vercel.app", "http://example.vercel.app"):
        monkeypatch.setenv("WEB_PREVIEW_ORIGIN", value)
        with pytest.raises(RuntimeError, match="valid exact HTTPS Vercel preview origin"):
            validate_runtime()


def test_production_runtime_accepts_exact_preview_with_opt_in(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv("AEGIS_PREVIEW_AUTH_ENABLED", "true")
    monkeypatch.setenv("WEB_PREVIEW_ORIGIN", PREVIEW)
    validate_runtime()
