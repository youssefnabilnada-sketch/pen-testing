"""Production role isolation and email routing release guard regressions."""
import os
import unittest
from unittest.mock import patch
from aegis.runtime import validate_runtime

COMMON={
    'AEGIS_ENV':'production',
    'DATABASE_URL':'postgresql+psycopg://aegis:fixture@localhost:5432/aegis',
    'REDIS_URL':'redis://localhost:6379/0',
    'WEB_ORIGIN':'https://security.example.test',
    'COOKIE_SECURE':'true',
    'LOCAL_FIXTURE_MODE':'false',
    'PAYMENTS_ENABLED':'false',
    'BILLING_MODE':'disabled',
    'FIREBASE_AUTH_ENABLED':'false',
    'SMTP_HOST':'disabled',
}

class ProductionRoleTests(unittest.TestCase):
    def check(self,role,updates=None):
        data={**COMMON,'AEGIS_SERVICE_ROLE':role,**(updates or {})}
        with patch.dict(os.environ,data,clear=True):
            validate_runtime()

    def test_workers_do_not_need_api_secrets(self):
        for role in ('scanner','intelligence','scheduler'):
            with self.subTest(role=role): self.check(role)

    def test_api_cannot_start_without_firebase_and_mail(self):
        for role in ('api','migrate'):
            with self.subTest(role=role):
                with self.assertRaisesRegex(RuntimeError,'Firebase authentication'):
                    self.check(role)

    def test_notifier_requires_encrypted_mail_but_no_identity_secrets(self):
        with self.assertRaisesRegex(RuntimeError,'SMTP'):
            self.check('notifier')
        self.check('notifier',{'SMTP_TLS':'starttls', 'SMTP_HOST':'smtp.example.test', 'MAIL_FROM':'security@example.test'})

    def test_worker_rejects_disabled_scan_safety(self):
        for value in ('true','1'):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RuntimeError,'test/fixture'):
                    self.check('scanner',{'LOCAL_FIXTURE_MODE':value})

    def test_unknown_role_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,'unknown AEGIS production service role'):
            self.check('typo-worker')

    def test_no_paid_ai_in_initial_release(self):
        for role in ('api','notifier','scanner'):
            with self.subTest(role=role):
                with self.assertRaisesRegex(RuntimeError,'AI services'):
                    self.check(role,{'AI_PROVIDER_ENABLED':'true'})

if __name__=='__main__': unittest.main()
