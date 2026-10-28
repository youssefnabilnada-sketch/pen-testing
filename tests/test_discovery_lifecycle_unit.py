"""SQLite-isolated API unit tests for discovery authorization lifetime.

Run independently of Celery, PostgreSQL and live website/network services:
PYTHONPATH=apps/api python tests/test_discovery_lifecycle_unit.py -v
"""
import sys
import time
import types
import unittest
from unittest.mock import patch
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from aegis.db import Base
from aegis.models import Asset, Authorization, Membership, Organization, User
from aegis import discovery, safety


class DiscoveryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.user = User(email='owner@example.test',password='fixture',active=True)
        org = Organization(name='fixture')
        self.db.add_all([org,self.user]);self.db.flush()
        self.asset = Asset(org_id=org.id,origin='https://example.test',verified_until=time.time()+3600)
        self.db.add_all([self.asset,Membership(org_id=org.id,user_id=self.user.id,role='owner')]);self.db.commit()
        self.main_stub = types.ModuleType('aegis.main')
        self.main_stub.throttle=lambda *_: None
        self.patch_main = patch.dict(sys.modules, {'aegis.main':self.main_stub})
        self.patch_main.start()

    def tearDown(self):
        self.patch_main.stop()
        self.db.close()
        self.engine.dispose()

    def latest_grant(self):
        return self.db.scalar(select(Authorization).order_by(Authorization.created.desc()).limit(1))

    def test_root_success_revokes_one_use_grant(self):
        with patch.object(safety, 'fetch', return_value=safety.Observation(200,[('Content-Type','text/html')],b'<a href="/docs">Docs</a>')):
            result=discovery.discover(self.asset.id,discovery.Consent(accepted=True),self.user,self.db)
        self.assertEqual(result['paths'], ['/docs'])
        self.assertTrue(self.latest_grant().revoked)

    def test_root_rejects_revoked_grant_during_request(self):
        def revoke(*_args,**_kwargs):
            self.latest_grant().revoked=True
            self.db.commit()
            return safety.Observation(200,[('Content-Type','text/html')],b'<a href="/private">Private</a>')
        with patch.object(safety,'fetch',side_effect=revoke):
            with self.assertRaises(discovery.HTTPException) as raised:
                discovery.discover(self.asset.id,discovery.Consent(accepted=True),self.user,self.db)
        self.assertEqual(raised.exception.status_code,422)
        self.assertTrue(self.latest_grant().revoked)

    def test_root_rejects_ownership_drift_during_request(self):
        def drift(*_args,**_kwargs):
            self.asset.origin='https://different.test'
            self.db.commit()
            return safety.Observation(200,[('Content-Type','text/html')],b'<a href="/docs">Docs</a>')
        with patch.object(safety,'fetch',side_effect=drift):
            with self.assertRaises(discovery.HTTPException):
                discovery.discover(self.asset.id,discovery.Consent(accepted=True),self.user,self.db)
        self.assertTrue(self.latest_grant().revoked)

    def test_recursive_rejects_scope_tamper_during_run(self):
        def runner(_origin,*,check,**_kwargs):
            check()
            grant=self.latest_grant()
            grant.scope={**grant.scope,'max_pages':99}
            self.db.commit()
            check()
            return {'paths':['/docs']}
        with patch('aegis.crawler.run',side_effect=runner):
            with self.assertRaises(discovery.HTTPException) as raised:
                discovery.recursive(self.asset.id,discovery.RecursiveConsent(accepted=True),self.user,self.db)
        self.assertEqual(raised.exception.status_code,409)
        self.assertTrue(self.latest_grant().revoked)

    def test_recursive_rejects_revoked_grant_after_crawler_returns(self):
        def runner(_origin,*,check,**_kwargs):
            check()
            self.latest_grant().revoked=True
            self.db.commit()
            return {'paths':['/docs']}
        with patch('aegis.crawler.run',side_effect=runner):
            with self.assertRaises(discovery.HTTPException) as raised:
                discovery.recursive(self.asset.id,discovery.RecursiveConsent(accepted=True),self.user,self.db)
        self.assertEqual(raised.exception.status_code,409)

    def test_recursive_success_restriction_persists(self):
        def runner(_origin,*,check,**_kwargs):
            check();return {'paths':['/docs'],'requests_performed':1}
        with patch('aegis.crawler.run',side_effect=runner):
            result=discovery.recursive(self.asset.id,discovery.RecursiveConsent(accepted=True),self.user,self.db)
        self.assertEqual(result['paths'],['/docs'])
        grant=self.latest_grant()
        self.assertTrue(grant.revoked)
        self.assertEqual(grant.scope['result']['paths'],['/docs'])


if __name__ == '__main__':
    unittest.main()
