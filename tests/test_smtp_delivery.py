"""Real loopback SMTP transport; no external recipient or service is contacted."""
import socketserver
import threading
from email.parser import BytesParser
from email.policy import default
import pytest
from aegis import auth,main

@pytest.fixture
def smtp_inbox(monkeypatch):
    inbox=[]
    class SMTP(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(5)
            self.wfile.write(b'220 owned-fixture ESMTP\r\n')
            while True:
                line=self.rfile.readline(8192)
                if not line:return
                command=line.split(b' ',1)[0].strip().upper()
                if command in (b'EHLO',b'HELO'):self.wfile.write(b'250 owned-fixture\r\n')
                elif command in (b'MAIL',b'RCPT',b'RSET',b'NOOP'):self.wfile.write(b'250 OK\r\n')
                elif command==b'DATA':
                    self.wfile.write(b'354 End with dot\r\n');data=bytearray()
                    while True:
                        item=self.rfile.readline(8192)
                        if item==b'.\r\n':break
                        if not item or len(data)>65536:return
                        data.extend(item[1:] if item.startswith(b'..') else item)
                    inbox.append(BytesParser(policy=default).parsebytes(bytes(data)))
                    self.wfile.write(b'250 Stored in isolated inbox\r\n')
                elif command==b'QUIT':self.wfile.write(b'221 Bye\r\n');return
                else:self.wfile.write(b'502 Unsupported fixture command\r\n')
    with socketserver.ThreadingTCPServer(('127.0.0.1',0),SMTP) as server:
        server.daemon_threads=True
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        monkeypatch.setenv('SMTP_HOST','127.0.0.1');monkeypatch.setenv('SMTP_PORT',str(server.server_address[1]))
        monkeypatch.setenv('SMTP_TLS','none');monkeypatch.delenv('SMTP_USERNAME',raising=False)
        monkeypatch.setenv('WEB_ORIGIN','https://aegis.fixture.test')
        try:yield inbox
        finally:server.shutdown();thread.join(timeout=2)

def test_registration_delivery_and_single_use_verification(client,smtp_inbox,monkeypatch):
    monkeypatch.setattr(main,'send_token',auth.send_token)
    response=client.post('/auth/register',json={'email':'recipient@example.test','password':'Long-password123!'})
    assert response.status_code==201
    assert len(smtp_inbox)==1
    message=smtp_inbox[0]
    assert message['To']=='recipient@example.test'
    text=message.get_content().replace('\r\n','\n')
    assert 'https://aegis.fixture.test/console#verify=' in text
    token=text.split('Alternative one-time token:\n')[1].splitlines()[0]
    assert client.post('/auth/verify',json={'token':token}).status_code==200
    assert client.post('/auth/verify',json={'token':token}).status_code!=200

def test_real_smtp_reset_template_and_health(smtp_inbox):
    auth.send_token('owned@example.test','isolated-reset-token','reset')
    assert '/console#reset=isolated-reset-token' in smtp_inbox[0].get_content()
    from aegis.connections import email_status
    assert email_status()=={'status':'ready','delivery_tested':False}
