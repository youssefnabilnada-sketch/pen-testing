"""Standalone report-rendering checks; do not claim live uptime or real WordPress."""
import time
import unittest
from types import SimpleNamespace

from pypdf import PdfReader
from aegis.reporting import render_health_monitor_pdf


class HealthReportTests(unittest.TestCase):
    def monitor(self):
        return SimpleNamespace(id='monitor-1',enabled=True,last_status='up',interval_seconds=900)

    def sample(self,status='up',elapsed=126.5):
        return SimpleNamespace(created=time.time(),status=status,http_status=200 if status=='up' else None,
                               response_ms=elapsed,tls_expires=None)

    def test_health_pdf_distinguishes_samples_from_annual_uptime(self):
        output=render_health_monitor_pdf(self.monitor(),'https://owned.example',
            SimpleNamespace(expires=time.time()+3600),[self.sample(),self.sample('down',None)])
        self.assertTrue(output.getvalue().startswith(b'%PDF'))
        text=' '.join(page.extract_text() for page in PdfReader(output).pages)
        for fragment in ('WEBSITE HEALTH','monitor-1','Recorded observations: 2',
                         'down: 1','up: 1','No uptime guarantee'):
            self.assertIn(fragment,text)
        self.assertNotIn('99.9%',text)

    def test_no_samples_no_authorization_is_explicitly_unverified(self):
        text=' '.join(page.extract_text() for page in PdfReader(
            render_health_monitor_pdf(self.monitor(),'unavailable',None,[])).pages)
        self.assertIn('authorization unavailable',text)
        self.assertIn('none',text)
        self.assertIn('not a security scan',' '.join(text.split()))

    def test_html_like_untrusted_status_is_escaped_and_limited(self):
        status='<img src="file:///etc/passwd">' * 1000
        output=render_health_monitor_pdf(self.monitor(),'https://owned.example',None,
                                         [self.sample(status)])
        self.assertLess(len(output.getvalue()),500000)
        text=' '.join(page.extract_text() for page in PdfReader(output).pages)
        self.assertIn('Recorded observations: 1',text)
        self.assertIn('not a security scan',' '.join(text.split()))


if __name__=='__main__':
    unittest.main()
