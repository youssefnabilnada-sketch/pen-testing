"""Isolated owner-scoped Evidence Vault legal-hold tests, independent of Celery."""
import unittest
from sqlalchemy import create_engine, select, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from aegis.db import Base
from aegis.models import (
    Organization, User, Membership, Asset, Authorization, Job,
    Report, EvidenceLegalHold, Audit,
)
from aegis import evidence_vault
from aegis.auth import current
from aegis.db import database
from aegis.evidence_vault import (
    LegalHoldRequest, place_legal_hold, release_legal_hold,
    legal_hold_history, listing,
)


class LegalHoldTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        @event.listens_for(self.engine, 'connect')
        def foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(self.engine)()
        self.org = Organization(name='Owned test org')
        self.other_org = Organization(name='Unrelated test org')
        self.owner = User(email='owner@example.test',password='placeholder',active=True)
        self.viewer = User(email='viewer@example.test',password='placeholder',active=True)
        self.outsider = User(email='outsider@example.test',password='placeholder',active=True)
        self.db.add_all([self.org,self.other_org,self.owner,self.viewer,self.outsider])
        self.db.flush()
        self.db.add_all([
            Membership(org_id=self.org.id,user_id=self.owner.id,role='owner'),
            Membership(org_id=self.org.id,user_id=self.viewer.id,role='viewer'),
            Membership(org_id=self.other_org.id,user_id=self.outsider.id,role='owner'),
        ])
        self.asset=Asset(org_id=self.org.id,origin='https://owned.example',verified_until=1)
        self.db.add(self.asset);self.db.flush()
        self.auth=Authorization(asset_id=self.asset.id,user_id=self.owner.id,scope={'paths':['/']},expires=1)
        self.db.add(self.auth);self.db.flush()
        self.job=Job(org_id=self.org.id,asset_id=self.asset.id,authorization_id=self.auth.id)
        self.db.add(self.job);self.db.flush()
        self.report=Report(org_id=self.org.id,job_id=self.job.id,snapshot={'profile':{'version':'1'}})
        self.db.add(self.report);self.db.commit()

    def tearDown(self):
        self.db.close();self.engine.dispose()

    def test_place_release_history_audit_and_no_delete(self):
        rid=self.report.id
        placed=place_legal_hold(rid,LegalHoldRequest(reason='Ongoing internal investigation'),
                                u=self.owner,db=self.db)
        self.assertTrue(placed['active'])
        self.assertTrue(listing(self.org.id,u=self.owner,db=self.db)['items'][0]['legal_hold'])
        with self.assertRaises(HTTPException) as caught:
            place_legal_hold(rid,LegalHoldRequest(reason='Repeated legal hold'),u=self.owner,db=self.db)
        self.assertEqual(caught.exception.status_code,409)
        released=release_legal_hold(rid,LegalHoldRequest(reason='Review formally concluded'),
                                    u=self.owner,db=self.db)
        self.assertFalse(released['active'])
        self.assertFalse(listing(self.org.id,u=self.owner,db=self.db)['items'][0]['legal_hold'])
        self.assertEqual(len(legal_hold_history(rid,u=self.owner,db=self.db)['items']),1)
        self.assertEqual(self.db.get(EvidenceLegalHold,placed['id']).release_reason,'Review formally concluded')
        self.assertIsNotNone(self.db.get(Report,rid))
        actions=[a.action for a in self.db.scalars(select(Audit).where(Audit.org_id==self.org.id))]
        self.assertIn('evidence.legal_hold_placed',actions)
        self.assertIn('evidence.legal_hold_released',actions)
        again=place_legal_hold(rid,LegalHoldRequest(reason='Second preservation request'),u=self.owner,db=self.db)
        self.assertNotEqual(again['id'],placed['id'])
        self.assertEqual(len(legal_hold_history(rid,u=self.owner,db=self.db)['items']),2)

    def test_viewer_and_cross_tenant_cannot_manage_or_read_private_reasons(self):
        for u in [self.viewer,self.outsider]:
            for attempt in (
                lambda: place_legal_hold(self.report.id,LegalHoldRequest(reason='Restricted legal hold'),u=u,db=self.db),
                lambda: release_legal_hold(self.report.id,LegalHoldRequest(reason='Unauthorized release'),u=u,db=self.db),
                lambda: legal_hold_history(self.report.id,u=u,db=self.db),
            ):
                with self.assertRaises(HTTPException) as exc:
                    attempt()
                self.assertEqual(exc.exception.status_code,403)
        self.assertEqual(self.db.scalar(select(EvidenceLegalHold)),None)

    def test_http_routes_validate_payloads_roles_and_legal_hold_state(self):
        app=FastAPI()
        app.include_router(evidence_vault.router)
        app.dependency_overrides[current]=lambda: self.owner
        app.dependency_overrides[database]=lambda: self.db
        client=TestClient(app)
        rid=self.report.id
        path=f'/evidence-vault/{rid}/legal-hold'
        self.assertEqual(client.post(path,json={'reason':'short'}).status_code,422)
        self.assertEqual(client.post(path,json={'reason':'Regulatory evidence preservation'}).status_code,200)
        self.assertTrue(client.get(f'/organizations/{self.org.id}/evidence-vault').json()['items'][0]['legal_hold'])
        app.dependency_overrides[current]=lambda: self.outsider
        self.assertEqual(client.get(f'/evidence-vault/{rid}/legal-holds').status_code,403)
        self.assertEqual(client.post(path+'/release',json={'reason':'Not authorized to release'}).status_code,403)
        app.dependency_overrides[current]=lambda: self.owner
        response=client.post(path+'/release',json={'reason':'Retention review concluded'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(client.get(f'/organizations/{self.org.id}/evidence-vault').json()['items'][0]['legal_hold'])

    def test_unknown_reports_and_missing_active_hold_fail_closed(self):
        for attempt in (
            lambda: place_legal_hold('missing',LegalHoldRequest(reason='Not a real report'),u=self.owner,db=self.db),
            lambda: release_legal_hold(self.report.id,LegalHoldRequest(reason='No active hold'),u=self.owner,db=self.db),
        ):
            with self.assertRaises(HTTPException) as exc:
                attempt()
            self.assertEqual(exc.exception.status_code,404)


if __name__=='__main__':
    unittest.main()
