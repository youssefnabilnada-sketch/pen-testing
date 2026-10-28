"""Isolated Launch Guard evidence report contracts; does not perform GitHub calls."""
import time
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pypdf import PdfReader
from aegis.reporting import render_launch_review_pdf
from aegis import launch_guard


class LaunchReportPDFTests(unittest.TestCase):
    def review(self):
        return SimpleNamespace(id='review-1', org_id='tenant-one',
            created=time.time(), repository='<img src="file:///etc/passwd">/owned',
            revision='a'*40,
            result={'pull_request':12, 'ci':'passed', 'evidence_complete':True,
                'checks':[{'name':'build <img src=x>','status':'completed','conclusion':'success'}],
                'changed_files':[{'path':'apps/api/auth.py <h1>unsafe</h1>','status':'modified'}],
                'required_reviews':['security_boundary_review'],
                'staging':'not_run','dependency_audit':'not_performed','release_gate':'advisory_only'})

    def test_pdf_explicitly_not_a_release_certification(self):
        data=render_launch_review_pdf(self.review()).getvalue()
        self.assertTrue(data.startswith(b'%PDF'))
        text=' '.join(page.extract_text() for page in PdfReader(BytesIO(data)).pages)
        for phrase in ('NOT A CERTIFICATION', 'advisory_only', 'not_run',
                       'not_performed', 'security_boundary_review', 'review-1'):
            self.assertIn(phrase,text)
        self.assertNotIn('/etc/passwd/',text)
        self.assertLess(len(data),500000)

    def test_missing_optional_evidence_fails_safe_in_report(self):
        row=self.review();row.result={}
        text=' '.join(page.extract_text() for page in PdfReader(render_launch_review_pdf(row)).pages)
        self.assertIn('No complete checks recorded',text)
        self.assertIn('No changed-file evidence recorded',text)
        self.assertIn('NOT A CERTIFICATION',text)

    def test_pdf_route_requires_tenant_membership_before_export(self):
        row=self.review()
        db=SimpleNamespace(get=lambda model, key:row)
        with patch.object(launch_guard,'member',side_effect=HTTPException(403,'Forbidden')) as guard:
            with patch('aegis.reporting.render_launch_review_pdf') as render:
                with self.assertRaises(HTTPException) as exc:
                    launch_guard.pdf_report(row.id, u=SimpleNamespace(id='outsider'), db=db)
                self.assertEqual(exc.exception.status_code,403)
                guard.assert_called_once()
                render.assert_not_called()

    def test_authorized_export_returns_private_download(self):
        row=self.review();db=SimpleNamespace(get=lambda model,key:row)
        with patch.object(launch_guard,'member') as guard:
            response=launch_guard.pdf_report(row.id,u=SimpleNamespace(id='member'),db=db)
        guard.assert_called_once()
        self.assertEqual(response.media_type,'application/pdf')
        self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertEqual(response.headers['x-content-type-options'],'nosniff')
        self.assertTrue(response.body.startswith(b'%PDF'))


if __name__=='__main__':
    unittest.main()
