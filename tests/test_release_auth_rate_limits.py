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
