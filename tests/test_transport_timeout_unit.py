"""No-network tests for enforced approved GET transport timeouts."""
import unittest
from unittest.mock import patch
from aegis.safety import fetch

class Socket:
    def close(self):pass
    def shutdown(self,*_):pass
class Response:
    status=200
    def getheaders(self):return [('Content-Type','application/json')]
    def read(self,*_):return b""
class Conn:
    timeouts=[]
    def __init__(self,*args,**kwargs):self.timeouts.append(kwargs['timeout'])
    def request(self,*args,**kwargs):pass
    def getresponse(self):return Response()
    def close(self):pass
class Timer:
    timeouts=[]
    def __init__(self,timeout,callback):self.timeouts.append(timeout)
    def start(self):pass
    def cancel(self):pass

class TransportTimeoutTest(unittest.TestCase):
    def setUp(self):
        Conn.timeouts=[];Timer.timeouts=[]

    def test_scope_timeout_is_enforced_for_normal_get(self):
        scope={'origin':'https://public.example','paths':['/health'],'type':'explicit-path-response',
               'method':'GET','request_limit':1,'timeout_seconds':5}
        with patch('aegis.safety.resolve',return_value=('public.example',80,'93.184.216.34','http')), \
             patch('aegis.safety.socket.create_connection',return_value=Socket()) as connect, \
             patch('aegis.safety.http.client.HTTPConnection',Conn), \
             patch('aegis.safety.threading.Timer',Timer):
            self.assertEqual(fetch('https://public.example','/health',assessment_scope=scope).status,200)
        self.assertEqual(Conn.timeouts,[5]);self.assertEqual(Timer.timeouts,[5]);self.assertEqual(connect.call_args.kwargs['timeout'],5)

    def test_discovery_shorter_timeout_is_honored(self):
        scope={'origin':'https://public.example','paths':['/'],'type':'explicit-path-response',
               'method':'GET','request_limit':1,'timeout_seconds':0.2,'purpose':'link-discovery'}
        with patch('aegis.safety.resolve',return_value=('public.example',80,'93.184.216.34','http')), \
             patch('aegis.safety.socket.create_connection',return_value=Socket()) as connect, \
             patch('aegis.safety.http.client.HTTPConnection',Conn), \
             patch('aegis.safety.threading.Timer',Timer):
            self.assertEqual(fetch('https://public.example','/',discovery=True,assessment_scope=scope).status,200)
        self.assertEqual(Conn.timeouts,[0.2]);self.assertEqual(Timer.timeouts,[0.2]);self.assertEqual(connect.call_args.kwargs['timeout'],0.2)

if __name__=='__main__':unittest.main()
