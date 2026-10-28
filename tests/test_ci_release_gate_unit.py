"""Pre-deployment CI must not pass on partial, skipped, or absent evidence."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'validate_ci_needs', Path(__file__).resolve().parents[1] / 'scripts' / 'validate_ci_needs.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ReleaseEvidenceTests(unittest.TestCase):
    def all_green(self):
        return {name: {'result': 'success'} for name in gate.REQUIRED}

    def test_all_eight_required_success(self):
        self.assertEqual(gate.evaluate(self.all_green()), (True, []))

    def test_browser_smoke_must_not_be_skipped_or_missing(self):
        for status in ('skipped', 'failure', 'cancelled'):
            evidence = self.all_green()
            evidence['browser-smoke'] = {'result': status}
            self.assertFalse(gate.evaluate(evidence)[0])
        evidence = self.all_green()
        evidence.pop('browser-smoke')
        self.assertFalse(gate.evaluate(evidence)[0])

    def test_native_runtime_requires_real_worker_success(self):
        evidence = self.all_green()
        evidence['native-runtime'] = {'result': 'skipped'}
        self.assertFalse(gate.evaluate(evidence)[0])

    def test_missing_job_fails_closed(self):
        evidence = self.all_green()
        evidence.pop('wordpress-runtime')
        self.assertFalse(gate.evaluate(evidence)[0])

    def test_skipped_or_cancelled_job_is_not_success(self):
        for status in ('skipped', 'cancelled', 'failure', None, 'neutral'):
            with self.subTest(status=status):
                evidence = self.all_green()
                evidence['backend'] = {'result': status}
                self.assertFalse(gate.evaluate(evidence)[0])

    def test_malformed_dependency_evidence_fails_closed(self):
        for data in ([], {}, None, 'success', {'backend': 'success'}):
            with self.subTest(data=data):
                self.assertFalse(gate.evaluate(data)[0])

    def test_optional_success_cannot_replace_required_failure(self):
        evidence = self.all_green()
        evidence['wordpress-runtime'] = {'result': 'failure'}
        evidence['optional-example'] = {'result': 'success'}
        self.assertFalse(gate.evaluate(evidence)[0])


if __name__ == '__main__':
    unittest.main()
