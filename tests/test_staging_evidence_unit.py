"""Failure-safe staging evidence checks, separate from live provider assertions."""
import unittest
from aegis.staging_evidence import evaluate_staging


class StagingEvidenceTests(unittest.TestCase):
    paths = ['/']
    required = {'header.nosniff'}

    def report(self, *, executed=None, findings=None):
        return {'profile':{'paths':['/'], 'executed':['header.nosniff'] if executed is None else executed,
                            'not_performed':{}}, 'findings':[] if findings is None else findings}

    def test_completed_supported_clean_observation_passes_narrow_check(self):
        self.assertTrue(evaluate_staging(self.report(), self.paths, self.required))

    def test_required_detector_not_executed_does_not_pass(self):
        self.assertFalse(evaluate_staging(self.report(executed=[]),self.paths,self.required))

    def test_observed_failure_does_not_pass(self):
        self.assertFalse(evaluate_staging(self.report(findings=[{'rule':'header.nosniff'}]),self.paths,self.required))

    def test_incomplete_or_malformed_evidence_rejected(self):
        for report in ({}, {'profile':{}}, {'profile':{'executed':'header.nosniff'},'findings':[]},
                       {'profile':{'executed':['header.nosniff']},'findings':[None]},
                       {'profile':{'executed':['header.nosniff']},'findings':None}):
            with self.subTest(report=report):
                with self.assertRaises(ValueError):
                    evaluate_staging(report,self.paths,self.required)

    def test_missing_or_excessive_baseline_paths_rejected(self):
        for paths in ([], ['/'] * 21, [None]):
            with self.subTest(paths=paths):
                with self.assertRaises(ValueError):
                    evaluate_staging(self.report(),paths,self.required)

    def test_staging_report_must_cover_exact_authorized_paths(self):
        for observed in ([], ['/wrong'], ['/', '/extra'], ['/missing', '/'], 'not-a-list'):
            with self.subTest(observed=observed):
                report = self.report()
                report['profile']['paths'] = observed
                with self.assertRaises(ValueError):
                    evaluate_staging(report, self.paths, self.required)
        missing = self.report()
        del missing['profile']['paths']
        with self.assertRaises(ValueError):
            evaluate_staging(missing, self.paths, self.required)

    def test_conflicting_detector_evidence_is_rejected(self):
        report = self.report()
        report['profile']['not_performed'] = {'header.nosniff': 'network timeout'}
        with self.assertRaises(ValueError):
            evaluate_staging(report, self.paths, self.required)
        report['profile']['not_performed'] = None
        with self.assertRaises(ValueError):
            evaluate_staging(report, self.paths, self.required)

    def test_different_authorized_path_cannot_borrow_root_check(self):
        report = self.report()
        report['profile']['paths'] = ['/account']
        with self.assertRaises(ValueError):
            evaluate_staging(report, ['/'], self.required)

    def test_no_required_rules_cannot_claim_success(self):
        with self.assertRaises(ValueError):
            evaluate_staging(self.report(),self.paths,set())


if __name__ == '__main__':
    unittest.main()
