"""Dependency-light checks of fail-closed discovery grant semantics."""
import unittest
from types import SimpleNamespace as Row
from aegis.discovery_grants import discovery_grant_active


class DiscoveryGrantTests(unittest.TestCase):
    def setUp(self):
        self.user = Row(id='person', active=True)
        self.asset = Row(id='site', org_id='team', origin='https://example.test', verified_until=200)
        self.scope = {'origin':self.asset.origin, 'paths':['/']}
        self.auth = Row(user_id='person', asset_id='site', scope=self.scope.copy(),
                        expires=200, revoked=False)
        self.inputs = dict(authorization=self.auth, asset=self.asset, user=self.user,
                           asset_id='site', org_id='team', expected_origin='https://example.test',
                           expected_scope=self.scope.copy(), now=100, paused=False)

    def test_valid_grant(self):
        self.assertTrue(discovery_grant_active(**self.inputs))

    def test_revocation_and_deletion_fail_closed(self):
        for key in ('authorization', 'asset', 'user'):
            with self.subTest(key=key):
                self.assertFalse(discovery_grant_active(**{**self.inputs,key:None}))
        for field, value in (('revoked',True), ('expires',100), ('asset_id','different'),
                             ('user_id','different')):
            with self.subTest(field=field):
                auth = Row(**{**vars(self.auth),field:value})
                self.assertFalse(discovery_grant_active(**{**self.inputs,'authorization':auth}))

    def test_scope_origin_user_and_team_drift_fail_closed(self):
        for field, value in (('org_id','other'), ('origin','https://other.test'), ('verified_until',100)):
            with self.subTest(field=field):
                asset = Row(**{**vars(self.asset),field:value})
                self.assertFalse(discovery_grant_active(**{**self.inputs,'asset':asset}))
        with self.subTest(case='scope changed'):
            self.assertFalse(discovery_grant_active(**{**self.inputs,'authorization':Row(
                **{**vars(self.auth),'scope':{'origin':'https://example.test','paths':['/private']}})}))
        with self.subTest(case='inactive account'):
            self.assertFalse(discovery_grant_active(**{**self.inputs,'user':Row(id='person',active=False)}))
        self.assertFalse(discovery_grant_active(**{**self.inputs,'paused':True}))


if __name__ == '__main__':
    unittest.main()
