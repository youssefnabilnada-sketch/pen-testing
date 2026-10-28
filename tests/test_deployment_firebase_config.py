"""Verify public config reaches the UI and missing configuration fails closed; no cloud connection."""
import json
from pathlib import Path

def test_online_template_serves_supplied_identity_config(client,monkeypatch):
    root=Path(__file__).resolve().parents[1]
    public=json.loads((root/'packages/configuration/firebase.public.json').read_text())
    for line in (root/'infrastructure/deployment/production.env.example').read_text().splitlines():
        if line.startswith('FIREBASE_'):
            key,value=line.split('=',1);monkeypatch.setenv(key,value)
    monkeypatch.delenv('FIREBASE_AUTH_EMULATOR_HOST',raising=False)
    response=client.get('/auth/firebase/config')
    assert response.status_code==200
    assert response.json()=={'enabled':True,'config':{
        key:public[key] for key in ('projectId','apiKey','appId','authDomain')}}
    assert 'private_key' not in response.text
    assert 'GOOGLE_APPLICATION_CREDENTIALS' not in response.text

    monkeypatch.setenv('FIREBASE_WEB_API_KEY','')
    assert client.get('/auth/firebase/config').json()=={'enabled':False}
