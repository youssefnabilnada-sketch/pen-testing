from fastapi.testclient import TestClient
from aegis.main import app
from conftest import signup
from test_assessment import authorized,launch,BAD
from aegis import worker

def test_delegation_is_explicit_revocable_and_does_not_grant_scan_rights(client,mail,monkeypatch):
    client_org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD)
    jid=launch(client,asset,auth);worker.assess(jid)
    agency=TestClient(app);agency_id=signup(agency,mail,'agency@example.test')
    assert agency.get(f'/organizations/{agency_id}/agency-portfolio').json()==[]
    assert agency.get(f'/organizations/{agency_id}/agency-reports/{jid}').status_code==403
    result=client.put(f'/organizations/{client_org}/agency-grant',json={'agency_id':agency_id,'accepted':True,'reports':False})
    assert result.status_code==200,result.text
    gid=result.json()['id']
    portfolio=agency.get(f'/organizations/{agency_id}/agency-portfolio').json()
    assert portfolio[0]['assets']==1 and portfolio[0]['client_id']==client_org
    assert agency.get(f'/organizations/{client_org}/assets').status_code==403
    assert agency.post(f'/assets/{asset}/authorize',json={'accepted':True}).status_code==403
    assert agency.get(f'/organizations/{agency_id}/agency-reports/{jid}').status_code==403
    client.put(f'/organizations/{client_org}/agency-grant',json={'agency_id':agency_id,'accepted':True,'reports':True})
    assert agency.put(f'/organizations/{agency_id}/agency-brand',json={'name':'Fixture Agency','color':'#123456','contact':'fixture@example.test','cover':'Client security review'}).status_code==200
    pdf=agency.get(f'/organizations/{agency_id}/agency-reports/{jid}')
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    from pypdf import PdfReader
    from io import BytesIO
    text=''.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
    assert 'Fixture Agency' in text and 'does not alter findings' in text
    assert agency.delete(f'/agency-grants/{gid}').status_code==403
    client.delete(f'/agency-grants/{gid}')
    assert agency.get(f'/organizations/{agency_id}/agency-portfolio').json()==[]
    assert agency.get(f'/organizations/{agency_id}/agency-reports/{jid}').status_code==403

def test_brand_rejects_external_logo_and_invalid_color(client,mail):
    org=signup(client,mail)
    assert client.put(f'/organizations/{org}/agency-brand',json={'name':'Agency','color':'red'}).status_code==422
    assert client.put(f'/organizations/{org}/agency-brand',json={'name':'Agency','logo_png':'https://external.example/logo.png'}).status_code==422
