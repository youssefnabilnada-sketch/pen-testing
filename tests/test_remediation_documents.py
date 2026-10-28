from io import BytesIO
from pypdf import PdfReader
from fastapi.testclient import TestClient
from aegis.main import app
from aegis import worker
from conftest import signup
from test_monitoring_regression import setup_fix,applied,approve,age_jobs
from test_assessment import GOOD,launch

def pdf_text(response):
    assert response.status_code==200,response.text
    assert response.headers['content-type']=='application/pdf'
    return '\n'.join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)

def test_customer_documents_permissions_and_completion_gate(client,mail,monkeypatch):
    org,a,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    base=f'/remediations/{rid}/document/'
    quote=pdf_text(client.get(base+'quotation'))
    assert 'Example organization' in quote and 'Approved staging-only' in quote
    assert 'No payment has been collected' in quote and 'Pricing and payment processing are disabled' in quote
    assert '0.00 EGP' not in quote
    assert 'No approved reassessment' in pdf_text(client.get(base+'progress'))
    assert client.get(base+'completion').status_code==409
    outsider=TestClient(app);signup(outsider,mail,'outsider@example.test')
    for kind in ('quotation','progress','completion'):
        assert outsider.get(base+kind).status_code==403
    client.post(f'/remediations/{rid}/messages',json={'body':'PRIVATE-INTERNAL-NOTE','internal':True})
    assert 'PRIVATE-INTERNAL-NOTE' not in pdf_text(client.get(base+'progress'))
    tid=applied(client,rid);age_jobs();jid=approve(client,tid,auth)
    monkeypatch.setattr(worker,'fetch',lambda o:GOOD);worker.assess(jid)
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==200
    summary=pdf_text(client.get(base+'completion'))
    assert 'verified_original' in summary and 'does not certify' in summary
    assert jid in summary and 'Resolved: 6' in summary
    worker.assess(launch(client,a,auth))
    assert client.get(base+'completion').status_code==409 # newer evidence requires review
