"""No services required: verify historical intelligence is safe under broken references."""
import unittest
from types import SimpleNamespace as Record
from unittest.mock import Mock
from aegis.intelligence.safe_history import (
    inventory_view, impact_view, schedule_view, baseline_paths,
)
from aegis.models import Asset, Advisory, Authorization, Finding, InventoryItem, Job


class SafeIntelligenceHistoryTests(unittest.TestCase):
    def setUp(self):
        self.objects = {}
        self.db = Mock()
        self.db.get.side_effect = lambda model, key: self.objects.get((model, key))
        self.asset = Record(id='asset-1', org_id='tenant-1')
        self.objects[(Asset, self.asset.id)] = self.asset
        self.item = Record(id='item-1', org_id='tenant-1', asset_id='asset-1', ecosystem='npm',
                           package='testpkg', version='1.0', evidence='customer supplied', updated=5)
        self.objects[(InventoryItem, self.item.id)] = self.item
        self.advisory = Record(id='adv-1', identifier='CVE-TEST-1')
        self.objects[(Advisory, self.advisory.id)] = self.advisory
        self.impact = Record(id='impact-1', inventory_id='item-1', advisory_id='adv-1',
                             status='potentially_affected', reason='inventory version match', revision_ids=['rev'])
        self.auth = Record(id='auth-1', asset_id='asset-1', revoked=False, expires=99999,
                           scope={'recurring': True, 'daily_window_utc': [1, 18], 'paths': ['/']})
        self.objects[(Authorization, self.auth.id)] = self.auth
        self.schedule = Record(id='sched-1', asset_id='asset-1', authorization_id='auth-1',
                               cadence='daily', enabled=True, next_due=120, last_run=100,
                               status='scheduled', on_advisory=False, reverify=True)
        self.finding = Record(id='finding-1', org_id='tenant-1', asset_id='asset-1')
        self.objects[(Finding, self.finding.id)] = self.finding
        self.job = Record(id='job-1', org_id='tenant-1', asset_id='asset-1', authorization_id='auth-1')
        self.objects[(Job, self.job.id)] = self.job
        self.remediation = Record(finding_id=self.finding.id)
        self.retest = Record(baseline_job_id=self.job.id)

    def test_owned_inventory_is_visible(self):
        view = inventory_view(self.db, self.item, 'tenant-1')
        self.assertEqual(view['asset_id'], 'asset-1')
        self.assertTrue(view['asset_available'])

    def test_missing_or_cross_tenant_inventory_asset_is_hidden(self):
        for value in (None, Record(id='asset-1', org_id='tenant-2')):
            self.objects[(Asset, 'asset-1')] = value
            with self.subTest(asset=value):
                view = inventory_view(self.db, self.item, 'tenant-1')
                self.assertIsNone(view['asset_id'])
                self.assertFalse(view['asset_available'])

    def test_valid_advisory_impact_is_not_confirmed_vulnerability(self):
        view = impact_view(self.db, self.impact, 'tenant-1')
        self.assertEqual(view['identifier'], 'CVE-TEST-1')
        self.assertEqual(view['status'], 'potentially_affected')
        self.assertTrue(view['record_available'])

    def test_missing_cross_tenant_inventory_or_advisory_fails_closed(self):
        for model, id_, value in (
            (InventoryItem, 'item-1', None),
            (InventoryItem, 'item-1', Record(id='item-1', org_id='tenant-2', asset_id='asset-1')),
            (Asset, 'asset-1', None),
            (Asset, 'asset-1', Record(id='asset-1', org_id='tenant-2')),
            (Advisory, 'adv-1', None),
        ):
            original = self.objects[(model, id_)]
            self.objects[(model, id_)] = value
            with self.subTest(model=model.__name__, value=value):
                view = impact_view(self.db, self.impact, 'tenant-1')
                self.assertEqual(view['identifier'], 'unavailable')
                self.assertIsNone(view['asset_id'])
                self.assertEqual(view['status'], 'unverified')
                self.assertFalse(view['record_available'])
            self.objects[(model, id_)] = original

    def test_schedule_with_current_consent_reports_scope(self):
        view = schedule_view(self.db, self.schedule, 'tenant-1', now=200)
        self.assertTrue(view['authorization_active'])
        self.assertEqual(view['daily_window_utc'], [1, 18])

    def test_schedule_with_revoked_or_expired_consent_is_blocked(self):
        for revoked, expires in ((True, 99999), (False, 100)):
            self.auth.revoked, self.auth.expires = revoked, expires
            with self.subTest(revoked=revoked, expires=expires):
                view = schedule_view(self.db, self.schedule, 'tenant-1', now=200)
                self.assertFalse(view['authorization_active'])
                self.assertEqual(view['status'], 'blocked_no_current_consent')
                self.assertIsNone(view['daily_window_utc'])
        self.auth.revoked, self.auth.expires = False, 99999

    def test_stale_cross_asset_or_missing_schedule_authorization_is_blocked(self):
        for value in (None, Record(asset_id='asset-2', revoked=False, expires=99999,
                                   scope={'recurring': True, 'daily_window_utc': [0, 24]})):
            self.objects[(Authorization, 'auth-1')] = value
            with self.subTest(value=value):
                self.assertFalse(schedule_view(self.db, self.schedule, 'tenant-1', now=200)['authorization_active'])
        self.objects[(Authorization, 'auth-1')] = self.auth

    def test_non_recurring_or_malformed_window_does_not_display_fake_consent(self):
        self.auth.scope = {'recurring': False, 'daily_window_utc': [0, 24]}
        self.assertFalse(schedule_view(self.db, self.schedule, 'tenant-1', now=200)['authorization_active'])
        self.auth.scope = {'recurring': True, 'daily_window_utc': ['0', 24]}
        view = schedule_view(self.db, self.schedule, 'tenant-1', now=200)
        self.assertTrue(view['authorization_active'])
        self.assertIsNone(view['daily_window_utc'])
        self.auth.scope = {'recurring': True, 'daily_window_utc': [1, 18], 'paths': ['/']}

    def test_baseline_paths_scope_is_tenant_and_asset_bound(self):
        self.assertEqual(baseline_paths(self.db, self.retest, 'tenant-1', self.remediation), ['/'])
        self.job.asset_id = 'asset-2'
        self.assertIsNone(baseline_paths(self.db, self.retest, 'tenant-1', self.remediation))
        self.job.asset_id = 'asset-1'
        self.job.org_id = 'tenant-2'
        self.assertIsNone(baseline_paths(self.db, self.retest, 'tenant-1', self.remediation))
        self.job.org_id = 'tenant-1'
        self.objects[(Authorization, 'auth-1')] = None
        self.assertIsNone(baseline_paths(self.db, self.retest, 'tenant-1', self.remediation))

    def test_malformed_baseline_paths_are_never_exposed(self):
        for scope in ({}, {'paths': '/*'}, {'paths': ['/', 42]}):
            self.auth.scope = scope
            with self.subTest(scope=scope):
                self.assertIsNone(baseline_paths(self.db, self.retest, 'tenant-1', self.remediation))


if __name__ == '__main__':
    unittest.main()
