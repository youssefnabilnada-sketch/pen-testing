import pytest
from fastapi import HTTPException
from aegis.firebase_identity import emulator_enabled, config

def setup(monkeypatch):
    for key,value in {'AEGIS_ENV':'development','AEGIS_FIREBASE_EMULATOR':'true',
                      'FIREBASE_AUTH_EMULATOR_HOST':'127.0.0.1:9099','FIREBASE_PROJECT_ID':'demo-aegis',
                      'FIREBASE_AUTH_ENABLED':'true','FIREBASE_WEB_API_KEY':'demo-key',
                      'FIREBASE_WEB_APP_ID':'demo-web','WEB_ORIGIN':'http://localhost:3000'}.items():
        monkeypatch.setenv(key,value)

def test_local_demo_configuration(monkeypatch):
    setup(monkeypatch)
    assert emulator_enabled()
    assert config()['config']['emulatorUrl']=='http://127.0.0.1:9099'

@pytest.mark.parametrize('key,value',[('AEGIS_ENV','production'),('FIREBASE_PROJECT_ID','aegis-d034c'),
    ('AEGIS_FIREBASE_EMULATOR','false'),('WEB_ORIGIN','https://public.example'),
    ('FIREBASE_AUTH_EMULATOR_HOST','evil.example:9099')])
def test_emulator_fails_closed(monkeypatch,key,value):
    setup(monkeypatch);monkeypatch.setenv(key,value)
    with pytest.raises(HTTPException):emulator_enabled()
    assert config()=={'enabled':False}
