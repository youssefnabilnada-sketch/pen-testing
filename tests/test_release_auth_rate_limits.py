"""AEGIS release regression: rate-limit public logins fairly behind a shared proxy."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from aegis import main
from aegis.auth import digest


def test_public_account_uses_hashed_identity_and_broad_shared_source(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "throttle", lambda key, limit=12: calls.append((key, limit)))
    req = SimpleNamespace(
        client=SimpleNamespace(host="198.51.100.10"),
        headers={"x-forwarded-for": "1.2.3.4"},
    )
    main.throttle_public_account(req, "login", " Alice@Example.TEST ")
    assert calls == [
        ("public:login:source:198.51.100.10", 240),
        ("public:login:identity:" + digest("alice@example.test"), 12),
    ]
    assert "Alice@Example.TEST" not in str(calls)
    assert "1.2.3.4" not in str(calls)


def test_identity_caps_are_separate_from_source_caps(monkeypatch):
    seen = []
    monkeypatch.setattr(main, "throttle", lambda key, limit=12: seen.append((key, limit)))
    req = SimpleNamespace(client=SimpleNamespace(host="198.51.100.10"))
    main.throttle_public_account(req, "login", "one@example.test")
    main.throttle_public_account(req, "login", "two@example.test")
    assert seen[0] == seen[2]
    assert seen[1] != seen[3]
    assert seen[1][1] == seen[3][1] == 12


def test_throttle_enforces_configured_cap_fail_closed(monkeypatch):
    import redis

    class FakeRedis:
        def __init__(self):
            self.count = 0
        def eval(self, script, key_count, key):
            self.count += 1
            assert key_count == 1
            assert key.startswith("rate:")
            return 13

    fake = FakeRedis()
    monkeypatch.setenv("TESTING", "0")
    monkeypatch.setattr(redis.Redis, "from_url", lambda url: fake)

    main.throttle("public:source", limit=240)
    with pytest.raises(HTTPException) as error:
        main.throttle("public:identity", limit=12)
    assert error.value.status_code == 429


def test_public_registration_closed_in_production_before_database_writes(monkeypatch):
    from aegis import firebase_identity

    monkeypatch.setenv("AEGIS_ENV", "production")
    monkeypatch.delenv("AEGIS_PUBLIC_REGISTRATION_ENABLED", raising=False)
    req = SimpleNamespace(client=SimpleNamespace(host="198.51.100.10"))
    local = main.Credentials(email="pilot@example.test", password="strong-long-demo-password")
    firebase = firebase_identity.RegisterInput(
        id_token="dummy-id-token-long-enough-for-test",
        recovery_password="strong-long-demo-password",
    )
    with pytest.raises(HTTPException) as local_error:
        main.register(local, req, db=None)
    assert local_error.value.status_code == 503
    with pytest.raises(HTTPException) as firebase_error:
        firebase_identity.register(firebase, req, udb=None)
    assert firebase_error.value.status_code == 503


def test_public_registration_flag_is_explicit_exact_string(monkeypatch):
    monkeypatch.setenv("AEGIS_ENV", "production")
    req = SimpleNamespace(client=SimpleNamespace(host="198.51.100.10"))
    local = main.Credentials(email="pilot@example.test", password="strong-long-demo-password")
    for disabled in ["TRUE", "1", "yes", "false"]:
        monkeypatch.setenv("AEGIS_PUBLIC_REGISTRATION_ENABLED", disabled)
        with pytest.raises(HTTPException) as err:
            main.register(local, req, db=None)
        assert err.value.status_code == 503
