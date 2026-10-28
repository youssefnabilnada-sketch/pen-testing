import os
import subprocess
import sys
import sqlite3

def test_migration_roundtrip_and_version_persistence(tmp_path):
    path=tmp_path/'migration.db'
    env={**os.environ,'DATABASE_URL':'sqlite:///'+str(path)}
    def run(*args):
        result=subprocess.run([sys.executable,'-m','alembic','-c','apps/api/alembic.ini',*args],env=env,text=True,capture_output=True)
        assert result.returncode==0,result.stdout+result.stderr
        return result.stdout
    run('upgrade','head')
    with sqlite3.connect(path) as db:
        assert db.execute('select version_num from alembic_version').fetchone()[0]=='017_evidence_legal_holds'
    run('upgrade','head') # Idempotence and revision commit.
    assert 'No new upgrade' in run('check')
    run('downgrade','base')
    with sqlite3.connect(path) as db:
        assert db.execute("select count(*) from sqlite_master where type='table' and name!='alembic_version'").fetchone()[0]==0
    run('upgrade','head')
    assert 'No new upgrade' in run('check')
