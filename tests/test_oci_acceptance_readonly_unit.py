"""Offline safety tests for the read-only Oracle acceptance diagnostic.

No DNS lookup, API mutation, scanning, account login, email or customer data.
"""
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

FILE = Path(__file__).resolve().parents[1] / "scripts" / "oci-acceptance-readonly.py"
spec = importlib.util.spec_from_file_location("oci_acceptance_readonly", FILE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class OracleAcceptanceProbeTests(unittest.TestCase):
    @staticmethod
    def valid_metadata():
        return {
            "enabled": True,
            "config": {
                "projectId": "aegis-d034c",
                "apiKey": "public-web-config-for-test-only",
                "appId": "test-public-app",
                "authDomain": "aegis-d034c.firebaseapp.com",
            },
        }

    def test_public_firebase_metadata_requires_complete_safe_shape(self):
        self.assertTrue(probe.valid_public_firebase(json.dumps(self.valid_metadata()).encode()))
        for broken in ('', '{', 'null', '[]', '"secret"', '{}'):
            with self.subTest(broken=broken):
                self.assertFalse(probe.valid_public_firebase(broken))

    def test_missing_or_sensitive_config_must_fail(self):
        for name, value in (
            ("projectId", "other-project"),
            ("apiKey", ""),
            ("appId", None),
            ("authDomain", 25),
            ("private_key", "fake-secret-must-not-leak"),
            ("client_email", "fake-admin@example.test"),
            ("emulatorUrl", "http://127.0.0.1:9099"),
        ):
            data = self.valid_metadata()
            data["config"][name] = value
            with self.subTest(name=name):
                self.assertFalse(probe.valid_public_firebase(json.dumps(data)))

    def test_disabled_config_fails(self):
        data = self.valid_metadata()
        data["enabled"] = False
        self.assertFalse(probe.valid_public_firebase(json.dumps(data)))

    def test_redirect_handler_never_follows_off_origin_redirects(self):
        handler = probe.DenyRedirect()
        self.assertIsNone(handler.redirect_request(
            object(), None, 302, "redirect", {"Location": "https://untrusted.invalid"},
            "https://untrusted.invalid/token"))

    def test_status_returns_blocked_http_error_without_following_redirect(self):
        with patch.object(probe, "build_opener") as opener_factory:
            opener_factory.return_value.open.side_effect = HTTPError(
                "https://aegis-pentest-eg-api.duckdns.org/auth/me", 401,
                "Unauthorized", {}, io.BytesIO(b"blocked"))
            code, body = probe.status("https://aegis-pentest-eg-api.duckdns.org/auth/me")
        self.assertEqual((code, body), (401, b"blocked"))
        self.assertIs(opener_factory.call_args.args[0], probe.DenyRedirect)
        self.assertEqual(opener_factory.return_value.open.call_args.kwargs["timeout"], 9)


if __name__ == "__main__":
    unittest.main()
