"""Dependency-light safety regression checks for missing or cross-tenant history targets."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from aegis.historical_records import asset_origin, authorization_expiry


class HistoricalRecordTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.model = object()

    def test_retained_history_with_deleted_asset_does_not_crash(self):
        self.db.get.return_value = None
        self.assertEqual(asset_origin(self.db, self.model, 'deleted', 'org-1'), 'unavailable')

    def test_history_does_not_expose_asset_from_another_tenant(self):
        self.db.get.return_value = SimpleNamespace(org_id='org-2', origin='https://private.org2.test')
        self.assertEqual(asset_origin(self.db, self.model, 'asset', 'org-1'), 'unavailable')

    def test_original_asset_origin_remains_visible_to_correct_workspace(self):
        self.db.get.return_value = SimpleNamespace(org_id='org-1', origin='https://owned.example')
        self.assertEqual(asset_origin(self.db, self.model, 'asset', 'org-1'), 'https://owned.example')

    def test_removed_authorization_does_not_crash(self):
        self.db.get.return_value = None
        self.assertIsNone(authorization_expiry(self.db, self.model, 'removed', 'asset-1'))

    def test_different_asset_authorization_cannot_be_misreported(self):
        self.db.get.return_value = SimpleNamespace(asset_id='asset-2', expires=999, revoked=False)
        self.assertIsNone(authorization_expiry(self.db, self.model, 'auth', 'asset-1'))

    def test_revoked_authorization_is_not_displayed_as_current(self):
        self.db.get.return_value = SimpleNamespace(asset_id='asset-1', expires=999, revoked=True)
        self.assertIsNone(authorization_expiry(self.db, self.model, 'auth', 'asset-1'))

    def test_live_expiry_remains_available(self):
        self.db.get.return_value = SimpleNamespace(asset_id='asset-1', expires=999, revoked=False)
        self.assertEqual(authorization_expiry(self.db, self.model, 'auth', 'asset-1'), 999)


if __name__ == '__main__':
    unittest.main()
