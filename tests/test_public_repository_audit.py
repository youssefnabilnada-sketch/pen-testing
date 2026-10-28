"""No external network or credentials needed for release-history unit tests."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location(
    'public_guard',Path(__file__).resolve().parents[1]/'scripts'/'check_public_repo_history.py')
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

def git(root,*args):
    subprocess.run(['git',*args],cwd=root,capture_output=True,check=True)

class PublicHistoryTests(unittest.TestCase):
    def test_sensitive_paths_and_template_exceptions(self):
        for path in ['.env','sub/.env.production','id_rsa','service-account.json']:
            self.assertTrue(guard.is_sensitive_path(path))
        for path in ['.env.example','production.env.example','README.md']:
            self.assertFalse(guard.is_sensitive_path(path))

    def test_secret_categories_do_not_print_values(self):
        token='ghp_'+'A'*36
        kinds=guard.analyze_blob('file.py',token.encode())
        self.assertIn('github-token',kinds)
        self.assertNotIn(token,str(kinds))
        self.assertIn('private-key',guard.analyze_blob('file.py',b'-----BEGIN '+b'PRIVATE KEY-----'))

    def test_oversized_blob_fails_closed(self):
        self.assertIn('oversized-object-requires-manual-review',
                      guard.analyze_blob('data',b'x'*(guard.MAX_BLOB_BYTES+1)))

    def test_deleted_sensitive_file_remains_visible_in_history(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            git(root,'init','-q')
            git(root,'config','user.name','CI')
            git(root,'config','user.email','ci@example.test')
            (root/'.env').write_text('TEST_VALUE=not-real',encoding='utf-8')
            git(root,'add','.')
            git(root,'commit','-qm','add fixture')
            (root/'.env').unlink()
            (root/'README.md').write_text('clean',encoding='utf-8')
            git(root,'add','-A')
            git(root,'commit','-qm','delete fixture')
            _,_,findings=guard.audit_history(td)
            self.assertTrue(any(k=='historical-sensitive-filename' for _,_,k in findings))

    def test_clean_history(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            git(root,'init','-q')
            git(root,'config','user.name','CI')
            git(root,'config','user.email','ci@example.test')
            (root/'README.md').write_text('clean',encoding='utf-8')
            git(root,'add','.')
            git(root,'commit','-qm','clean')
            _,count,findings=guard.audit_history(td)
            self.assertGreaterEqual(count,1)
            self.assertFalse(findings)

if __name__=='__main__':unittest.main()
