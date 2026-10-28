from sqlalchemy import select
from fastapi.testclient import TestClient
from aegis.db import Session
from aegis.main import app
from aegis.models import PatchBackup, Report
from test_repositories import github,patch_setup
from conftest import signup

def test_backup_restore_preview_integrity_and_tenant(client,mail,monkeypatch,github):
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    with Session() as db:
        backup=db.scalar(select(PatchBackup).where(PatchBackup.patch_id==pid))
        assert backup.restore_verified and '{"version":2}' not in backup.encrypted_content
    result=client.post(f'/repository-patches/{pid}/rollback-preview')
    assert result.status_code==200,result.text
    assert result.json()['restore_verified'] and result.json()['applied'] is False
    assert 'nosniff' in result.json()['diff']
    other=TestClient(app);signup(other,mail,'rollback-other@example.test')
    assert other.post(f'/repository-patches/{pid}/rollback-preview').status_code==403
    with Session() as db:
        backup=db.scalar(select(PatchBackup).where(PatchBackup.patch_id==pid));backup.sha256='0'*64;db.commit()
    assert client.post(f'/repository-patches/{pid}/rollback-preview').status_code==409

def test_controlled_git_patch_staging_and_restore(tmp_path,github,monkeypatch):
    import subprocess,json,hashlib,threading
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    from aegis import github_client as gh,safety
    from aegis.repositories import propose_nosniff
    from aegis.autofix_recovery import restore_rehearsal
    root=tmp_path/'owned-repository';root.mkdir()
    original=b'{"version":2,"rewrites":[{"source":"/docs","destination":"/guide"}]}'
    config=root/'vercel.json';config.write_bytes(original)
    def git(*args):
        r=subprocess.run(['git','-c','safe.directory='+str(root),*args],cwd=root,capture_output=True,text=True)
        assert r.returncode==0,r.stderr
        return r.stdout
    git('init');git('add','vercel.json');git('-c','user.name=Fixture','-c','user.email=fixture@example.test','commit','-m','Controlled baseline')
    proposed=propose_nosniff(original.decode())
    backup=gh.cipher().encrypt(original).decode();digest=hashlib.sha256(original).hexdigest()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            for entry in json.loads(config.read_text()).get('headers',[]):
                for h in entry['headers']:self.send_header(h['key'],h['value'])
            self.end_headers()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setattr(safety,'resolve',lambda origin:('owned.fixture',server.server_port,'127.0.0.1','http'))
    try:
        assert ('X-Content-Type-Options','nosniff') not in safety.fetch('http://owned.fixture').headers
        config.write_text(proposed)
        assert 'nosniff' in git('diff','--','vercel.json')
        assert ('X-Content-Type-Options','nosniff') in safety.fetch('http://owned.fixture').headers
        config.write_bytes(restore_rehearsal(backup,digest,proposed))
        assert git('diff','--','vercel.json')==''
        assert ('X-Content-Type-Options','nosniff') not in safety.fetch('http://owned.fixture').headers
    finally:server.shutdown();server.server_close();thread.join(timeout=3)

def test_staging_link_requires_separate_new_completed_asset(client,mail,monkeypatch,github):
    from aegis import worker
    from test_assessment import GOOD,launch
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    stage=client.post(f'/organizations/{org}/assets',json={'origin':'https://staging.example.test'}).json()['id']
    challenge=client.post(f'/assets/{stage}/challenge',json={'method':'file'}).json()['id']
    assert client.post(f'/assets/{stage}/verify/{challenge}').status_code==200
    auth=client.post(f'/assets/{stage}/authorize',json={'accepted':True}).json()['id']
    jid=launch(client,stage,auth)
    endpoint=f'/repository-patches/{pid}/staging-evidence'
    assert client.post(endpoint,json={'job_id':jid,'accepted':True}).status_code==409
    monkeypatch.setattr(worker,'fetch',lambda origin:GOOD);worker.assess(jid)
    with Session() as db:
        report=db.scalar(select(Report).where(Report.job_id==jid))
        assert report is not None and report.snapshot['profile']['paths']==['/']
    assert client.post(endpoint,json={'job_id':jid,'accepted':False}).status_code==403
    r=client.post(endpoint,json={'job_id':jid,'accepted':True})
    assert r.status_code==200,r.text
    assert r.json()['supported_checks_passed'] is True
    assert r.json()['deployment_revision_verified'] is False
