from aegis import auth

def test_account_email_fragment_and_transport(monkeypatch):
    messages=[]
    class Transport:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def send_message(self,m):messages.append(m)
    monkeypatch.setattr(auth,'smtp_connection',Transport)
    monkeypatch.setenv('WEB_ORIGIN','https://aegis.example.test')
    for purpose in ('verify','reset'):
        auth.send_token('owner@example.test','a'*32,purpose)
        text=messages[-1].get_content()
        assert 'https://aegis.example.test/console#'+purpose+'='+'a'*32 in text
        assert 'Opening the link alone does not change your account.' in text
        assert messages[-1]['To']=='owner@example.test'
