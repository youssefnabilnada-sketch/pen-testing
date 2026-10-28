"""Offline conservative release-risk classification; no GitHub or scanning needed."""
import unittest
from aegis.launch_guard import change_review_categories, summarize

class LaunchGuardReviewTests(unittest.TestCase):
    def test_dependency_ecosystems_are_not_missed(self):
        files=['apps/web/package-lock.json','backend/requirements-dev.txt',
               'backend/pyproject.toml','frontend/pnpm-lock.yaml','service/poetry.lock']
        for filename in files:
            with self.subTest(filename=filename):
                self.assertIn('dependency_manifest_review',change_review_categories(filename))

    def test_high_impact_paths_require_explicit_review(self):
        examples={'.github/workflows/ci.yml':'ci_workflow_review',
                  'apps/api/migrations/versions/017.py':'database_migration_review',
                  'apps/api/aegis/safety.py':'security_boundary_review',
                  'infrastructure/deployment/production.env.example':'deployment_configuration_review'}
        for path,category in examples.items():
            with self.subTest(path=path):
                self.assertIn(category,change_review_categories(path))
        self.assertEqual(change_review_categories('apps/web/app/page.tsx'),[])

    def test_review_remains_advisory_even_with_successful_ci(self):
        checks={'total_count':1,'check_runs':[{'name':'CI','head_sha':'a'*40,'status':'completed','conclusion':'success'}]}
        statuses={'total_count':0,'statuses':[]}
        changes=[{'filename':'apps/web/package-lock.json','status':'modified'}]
        result=summarize(checks,statuses,changes)
        self.assertEqual(result['ci'],'passed')
        self.assertFalse(result['certification'])
        self.assertEqual(result['staging'],'not_run')
        self.assertEqual(result['dependency_audit'],'not_performed')
        self.assertIn('dependency_manifest_review',result['required_reviews'])

if __name__=='__main__':unittest.main()
