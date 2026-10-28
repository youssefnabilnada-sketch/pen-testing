"""No real internet requests; controlled HTTP fixture for the optional cloud smoke command."""
import importlib.util
import unittest
from pathlib import Path

import httpx

spec = importlib.util.spec_from_file_location(
    'verify_cloud_staging', Path(__file__).resolve().parents[1] / 'scripts' / 'verify_cloud_staging.py')
cloud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud)


class StagingCloudContractTests(unittest.TestCase):
    web = 'https://web.example.test'
    api = 'https://api.example.test'

    def transport(self, *, payments=False, ready=True, healthy=True, headers=True):
        def respond(request):
            if request.url.host == 'web.example.test' and request.url.path == '/':
                return httpx.Response(200 if healthy else 503,
                                      headers={'X-Content-Type-Options':'nosniff'} if headers else {},
                                      text='Staging web')
            if request.url.host == 'api.example.test' and request.url.path == '/health':
                return httpx.Response(200,json={'database':'reachable',
                                                'payments_enabled':payments,
                                                'billing_mode':'disabled'})
            if request.url.host == 'api.example.test' and request.url.path == '/ready':
                return httpx.Response(200 if ready else 503,json={'ready':ready})
            return httpx.Response(404)
        return httpx.MockTransport(respond)

    def test_valid_isolated_staging_checks_pass(self):
        self.assertEqual(len(cloud.verify_staging(self.web,self.api,
                         transport=self.transport())),3)

    def test_missing_tls_credentials_queries_and_local_origins_are_rejected(self):
        for url in ('', 'http://web.example.test', 'https://localhost',
                    'https://alice:secret@web.example.test', 'https://web.example.test/x',
                    'https://web.example.test?token=foo', 'https://web.example.test:9443'):
            with self.subTest(url=url), self.assertRaises(cloud.StagingSmokeError):
                cloud.verify_staging(url,self.api,transport=self.transport())
        with self.assertRaises(cloud.StagingSmokeError):
            cloud.verify_staging(self.web,self.web,transport=self.transport())

    def test_readiness_failure_cannot_be_misreported_as_production_success(self):
        for options in ({'payments':True}, {'ready':False}, {'healthy':False}, {'headers':False}):
            with self.subTest(options=options), self.assertRaises(cloud.StagingSmokeError):
                cloud.verify_staging(self.web,self.api,transport=self.transport(**options))

    def test_redirect_cannot_be_followed(self):
        with self.assertRaises(cloud.StagingSmokeError):
            cloud.verify_staging(self.web,self.api,transport=httpx.MockTransport(
                lambda request:httpx.Response(302,headers={'location':'https://attacker.invalid'})))


if __name__ == '__main__':
    unittest.main()
