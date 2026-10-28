"""Deployment diagnostics must not claim readiness with missing alert workers."""
import unittest
from unittest.mock import patch
from aegis import connections as c

class DeploymentDiagnosticsTests(unittest.TestCase):
    def test_production_requires_firebase_and_both_workers(self):
        # Mock dependency probes; do not touch customer accounts.
        with patch.dict('os.environ',{'AEGIS_ENV':'production'}):
            with patch.object(c,'readiness',return_value={'ready':True,'queue':{'status':'ready'}}),\
                 patch.object(c,'email_status',return_value={'status':'ready'}),\
                 patch.object(c,'firebase_status',return_value={'status':'ready'}),\
                 patch.object(c,'worker_status',return_value={'status':'ready','scanner_available':True,'intelligence_available':True,'notifier_available':False}):
                self.assertFalse(c.diagnose()['ready'])
            with patch.object(c,'readiness',return_value={'ready':True,'queue':{'status':'ready'}}),\
                 patch.object(c,'email_status',return_value={'status':'ready'}),\
                 patch.object(c,'firebase_status',return_value={'status':'ready'}),\
                 patch.object(c,'worker_status',return_value={'status':'ready','scanner_available':True,'intelligence_available':True,'notifier_available':True}):
                self.assertTrue(c.diagnose()['ready'])
                with patch.object(c,'firebase_status',return_value={'status':'disabled'}):
                    self.assertFalse(c.diagnose()['ready'])

if __name__=='__main__':unittest.main()
