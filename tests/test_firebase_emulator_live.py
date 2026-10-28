"""Opt-in real local Auth emulator journey. Never calls a live Firebase project."""
import os
import uuid
import httpx
import pytest

@pytest.mark.skipif(os.getenv('AEGIS_TEST_FIREBASE_EMULATOR') != '1', reason='Local Auth emulator opt-in')
def test_real_emulator_registration_verification_login_and_disable(client, monkeypatch):
    for key,value in {'AEGIS_ENV':'test','AEGIS_FIREBASE_EMULATOR':'true',
        'FIREBASE_AUTH_ENABLED':'true','FIREBASE_PROJECT_ID':'demo-aegis',
        'FIREBASE_AUTH_EMULATOR_HOST':'127.0.0.1:9099','WEB_ORIGIN':'http://localhost:3000'}.items():
        monkeypatch.setenv(key,value)
    base='http://127.0.0.1:9099'
    def post(action,body):
        r=httpx.post(base+'/identitytoolkit.googleapis.com/v1/accounts:'+action,
                     params={'key':'demo-key'},json=body,timeout=5,trust_env=False)
        r.raise_for_status();return r.json()
    email='aegis-'+uuid.uuid4().hex+'@example.test'
    password='Local-emulator-only-123!'
    signup=post('signUp',{'email':email,'password':password,'returnSecureToken':True})
    from firebase_admin import auth
    from aegis.firebase_identity import firebase_app
    app=firebase_app('demo-aegis')
    try:
        assert client.post('/auth/firebase/register',json={'id_token':signup['idToken'],'recovery_password':password}).status_code==401
        post('sendOobCode',{'requestType':'VERIFY_EMAIL','idToken':signup['idToken']})
        codes=httpx.get(base+'/emulator/v1/projects/demo-aegis/oobCodes',timeout=5,trust_env=False).json()['oobCodes']
        code=next(c['oobCode'] for c in codes if c['email']==email and c['requestType']=='VERIFY_EMAIL')
        post('update',{'oobCode':code})
        signed=post('signInWithPassword',{'email':email,'password':password,'returnSecureToken':True})
        result=client.post('/auth/firebase/register',json={'id_token':signed['idToken'],'recovery_password':password})
        assert result.status_code==201, result.text
        login=client.post('/auth/firebase/login',json={'id_token':signed['idToken']})
        assert login.status_code==200,login.text
        client.headers['x-csrf-token']=login.json()['csrf']
        assert client.get('/auth/me').status_code==200
        assert client.post('/auth/logout').status_code==200
        assert client.get('/auth/me').status_code==401
        post('sendOobCode',{'requestType':'PASSWORD_RESET','email':email})
        codes=httpx.get(base+'/emulator/v1/projects/demo-aegis/oobCodes',timeout=5,trust_env=False).json()['oobCodes']
        reset=next(c['oobCode'] for c in codes if c['email']==email and c['requestType']=='PASSWORD_RESET')
        new_password='New-local-emulator-password-456!'
        post('resetPassword',{'oobCode':reset,'newPassword':new_password})
        with pytest.raises(httpx.HTTPStatusError):
            post('signInWithPassword',{'email':email,'password':password,'returnSecureToken':True})
        signed=post('signInWithPassword',{'email':email,'password':new_password,'returnSecureToken':True})
        auth.update_user(signup['localId'],disabled=True,app=app)
        assert client.post('/auth/firebase/login',json={'id_token':signed['idToken']}).status_code==401
    finally:
        auth.delete_user(signup['localId'],app=app)
