"""Offline contract for scoped, customer-confirmed Cloudflare TXT assistance."""
import time
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from aegis import cloudflare_verify as cf


class ProviderContract(unittest.TestCase):
    zone_id = 'a' * 32
    token = 'short-lived-scoped-cloudflare-token'
    origin = 'https://shop.example.com'

    def challenge(self, **overrides):
        props = {'method': 'dns', 'token': 'existing-verification-secret',
                 'expires': time.time() + 600, 'consumed': False}
        props.update(overrides)
        return SimpleNamespace(**props)

    def fake_api(self, method, path, bearer, *, params=None, payload=None):
        self.assertEqual(bearer, self.token)
        if method == 'GET' and path.endswith('/dns_records'):
            self.assertEqual(params, {'type':'TXT','name':'_aegis.shop.example.com','per_page':100})
            return {'result': [], 'result_info': {'total_pages': 1}}
        if method == 'GET':
            return {'result': {'name':'example.com'}}
        if method == 'POST':
            self.assertEqual(path, '/zones/' + self.zone_id + '/dns_records')
            self.assertEqual(payload['name'], '_aegis.shop.example.com')
            self.assertEqual(payload['type'], 'TXT')
            self.assertEqual(payload['content'], 'aegis=existing-verification-secret')
            self.assertEqual(payload['ttl'], 300)
            return {'result': payload}
        self.fail('Unexpected Cloudflare operation')

    def test_dns_proof_derived_from_registered_host_and_server_challenge(self):
        self.assertEqual(cf.proof(self.origin, self.challenge()), {
            'type':'TXT','name':'_aegis.shop.example.com',
            'content':'aegis=existing-verification-secret','ttl':300})

    def test_expired_consumed_and_wrong_method_cannot_publish(self):
        for changed in ({'expires':time.time()-1},{'consumed':True},{'method':'file'}):
            with self.subTest(changed=changed), self.assertRaises(HTTPException):
                cf.proof(self.origin, self.challenge(**changed))

    def test_reject_invalid_zone_identifier_before_network(self):
        with patch.object(cf, '_cloudflare') as remote:
            with self.assertRaises(HTTPException) as ctx:
                cf.publish_record(self.origin, self.challenge(), 'not-a-zone-id', self.token)
            self.assertEqual(ctx.exception.status_code,422)
            remote.assert_not_called()

    def test_cross_zone_rejected_without_writing(self):
        with patch.object(cf,'_cloudflare',return_value={'result':{'name':'other-example.com'}}) as remote:
            with self.assertRaises(HTTPException) as ctx:
                cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token)
            self.assertEqual(ctx.exception.status_code,403)
            self.assertEqual(remote.call_count,1)

    def test_zone_hostname_must_have_label_boundary(self):
        with patch.object(cf,'_cloudflare',return_value={'result':{'name':'ample.com'}}):
            with self.assertRaises(HTTPException):
                cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token)

    def test_publish_only_one_txt_record_after_final_permission_check(self):
        operations=[]
        def remote(*args,**kwargs):
            operations.append(args[0]);return self.fake_api(*args,**kwargs)
        with patch.object(cf,'_cloudflare',side_effect=remote):
            result=cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token,
                before_write=lambda:operations.append('authorized'))
        self.assertEqual(operations,['GET','GET','authorized','POST'])
        self.assertTrue(result['published'])
        self.assertNotIn(self.token,str(result))

    def test_aborted_authorization_prevents_dns_write(self):
        ops=[]
        def remote(*args,**kwargs):
            ops.append(args[0]);return self.fake_api(*args,**kwargs)
        def revoked():raise HTTPException(403,'No longer authorized')
        with patch.object(cf,'_cloudflare',side_effect=remote):
            with self.assertRaises(HTTPException):
                cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token,before_write=revoked)
        self.assertEqual(ops,['GET','GET'])

    def test_existing_proof_is_idempotent(self):
        records=[{'type':'TXT','name':'_aegis.shop.example.com',
                  'content':'aegis=existing-verification-secret'}]
        def remote(method,path,token,**_):
            if path.endswith('/dns_records'):
                return {'result':records,'result_info':{'total_pages':1}}
            self.assertEqual(method,'GET')
            return {'result':{'name':'example.com'}}
        with patch.object(cf,'_cloudflare',side_effect=remote):
            result=cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token)
        self.assertTrue(result['already_present'])
        self.assertFalse(result['published'])

    def test_existing_proof_must_recheck_revoked_authorization(self):
        def remote(method, path, token, **_):
            if path.endswith('/dns_records'):
                return {'result':[{'type':'TXT','name':'_aegis.shop.example.com',
                    'content':'aegis=existing-verification-secret'}],
                    'result_info':{'total_pages':1}}
            return {'result':{'name':'example.com'}}
        with patch.object(cf,'_cloudflare',side_effect=remote):
            with self.assertRaises(HTTPException) as exc:
                cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token,
                    before_write=lambda: (_ for _ in ()).throw(HTTPException(403,'revoked')))
        self.assertEqual(exc.exception.status_code,403)

    def test_malformed_cloudflare_record_fields_fail_closed(self):
        for row in ({'type':'TXT','name':None,'content':'valid'},
                    {'type':'TXT','name':'_aegis.shop.example.com','content':None}):
            with self.subTest(row=row), patch.object(cf,'_cloudflare',side_effect=[
                {'result':{'name':'example.com'}}, {'result':[row],'result_info':{'total_pages':1}}]):
                with self.assertRaises(HTTPException) as exc:
                    cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token)
                self.assertEqual(exc.exception.status_code,502)

    def test_unicode_registered_host_matches_ascii_cloudflare_zone(self):
        origin='https://shop.bücher.example'
        challenge=self.challenge()
        name=cf.proof(origin,challenge)['name']
        self.assertEqual(name, '_aegis.shop.xn--bcher-kva.example')
        def remote(method,path,token,**kwargs):
            if method=='GET' and path.endswith('/dns_records'):
                return {'result':[],'result_info':{'total_pages':1}}
            if method=='GET':
                return {'result':{'name':'xn--bcher-kva.example'}}
            return {'result':kwargs['payload']}
        with patch.object(cf,'_cloudflare',side_effect=remote):
            self.assertTrue(cf.publish_record(origin,challenge,self.zone_id,self.token)['published'])

    def test_incomplete_record_listing_fails_closed(self):
        with patch.object(cf,'_cloudflare',side_effect=[{'result':{'name':'example.com'}},
                         {'result':[],'result_info':{'total_pages':2}}]) as remote:
            with self.assertRaises(HTTPException):
                cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token)
            self.assertEqual(remote.call_count,2)

    def test_bad_cloudflare_creation_response_not_reported_success(self):
        with patch.object(cf,'_cloudflare',side_effect=[{'result':{'name':'example.com'}},
                         {'result':[],'result_info':{'total_pages':1}},
                         {'result':{'type':'A','name':'_aegis.shop.example.com'}}]):
            with self.assertRaises(HTTPException) as ctx:
                cf.publish_record(self.origin,self.challenge(),self.zone_id,self.token)
            self.assertEqual(ctx.exception.status_code,502)

    def test_customer_confirmation_and_secret_redaction(self):
        with self.assertRaises(ValidationError):
            cf.CloudflarePublish(zone_id=self.zone_id,api_token='abc',confirm_dns_change=True)
        model=cf.CloudflarePublish(zone_id=self.zone_id,api_token=self.token)
        self.assertFalse(model.confirm_dns_change)
        self.assertNotIn(self.token,repr(model))
        self.assertEqual(model.api_token.get_secret_value(),self.token)

    def test_cloudflare_redirect_cannot_be_followed(self):
        class FakeClient:
            def __init__(self,**kwargs):
                self_outer.assertEqual(kwargs['follow_redirects'],False)
                self_outer.assertEqual(kwargs['trust_env'],False)
            def __enter__(self):return self
            def __exit__(self,*args):return False
            @contextmanager
            def stream(self,*args,**kwargs):
                self_outer.assertEqual(args[1],'https://api.cloudflare.com/client/v4/zones/'+self_outer.zone_id)
                yield SimpleNamespace(status_code=302)
        self_outer=self
        with patch.object(cf.httpx,'Client',FakeClient):
            with self.assertRaises(HTTPException) as ctx:
                cf._cloudflare('GET','/zones/'+self.zone_id,self.token)
            self.assertEqual(ctx.exception.status_code,502)

    def test_cloudflare_streaming_does_not_buffer_oversize_response(self):
        received=[]
        def handler(request):
            received.append(request.headers.get('authorization'))
            return httpx.Response(200, content=b'X'*66000)
        real_client=httpx.Client
        def make_client(**kwargs):
            return real_client(transport=httpx.MockTransport(handler), **kwargs)
        with patch.object(cf.httpx,'Client',side_effect=make_client):
            with self.assertRaises(HTTPException) as ctx:
                cf._cloudflare('GET','/zones/'+self.zone_id,self.token)
        self.assertEqual(ctx.exception.status_code,502)
        self.assertNotIn(self.token,str(ctx.exception.detail))
        self.assertEqual(received,['Bearer '+self.token])

    def test_oversized_declared_response_stops_before_streaming(self):
        read = []
        class NeverRead(httpx.SyncByteStream):
            def __iter__(self):
                read.append('read')
                yield b'{}'
        def handler(request):
            return httpx.Response(200,headers={'content-length':'100000'},stream=NeverRead())
        real_client=httpx.Client
        with patch.object(cf.httpx,'Client',side_effect=lambda **kwargs:
                          real_client(transport=httpx.MockTransport(handler),**kwargs)):
            with self.assertRaises(HTTPException) as ctx:
                cf._cloudflare('GET','/zones/'+self.zone_id,self.token)
        self.assertEqual(ctx.exception.status_code,502)
        self.assertEqual(read,[])

    def test_stream_stops_at_limit_without_reading_rest(self):
        read=[]
        class ManyChunks(httpx.SyncByteStream):
            def __iter__(self):
                for i in range(1000):
                    read.append(i)
                    yield b'X'*4096
        real_client=httpx.Client
        with patch.object(cf.httpx,'Client',side_effect=lambda **kwargs:
                          real_client(transport=httpx.MockTransport(lambda req:
                              httpx.Response(200,stream=ManyChunks())),**kwargs)):
            with self.assertRaises(HTTPException):
                cf._cloudflare('GET','/zones/'+self.zone_id,self.token)
        self.assertLessEqual(len(read),17)


if __name__=='__main__':
    unittest.main()
